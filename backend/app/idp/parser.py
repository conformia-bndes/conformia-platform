"""Parser and structured entity extractor for Intelligent Document Processing (IDP)."""

from dataclasses import dataclass
from datetime import date, datetime, timezone
import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

from app.db.models.document import Document
from app.schemas.enums import ProcessingStatus
from app.schemas.error import ErrorDetail
from app.schemas.evidence import PageEvidence
from app.schemas.extraction import ExtractedField, ExtractionResult
from app.schemas.processing import ProcessingStatusResponse

# Fonte unica para localizar datas rotuladas como validade/vigencia no texto.
# Datas de emissao ("Emitida em", "Emissao", "Expedicao") nao entram neste padrao.
VALIDITY_DATE_PATTERN = re.compile(
    r"(?:"
    r"v[aá]lid[ao]\s+at[eé]"
    r"|data\s+de\s+validade"
    r"|prazo\s+de\s+validade"
    r"|validade(?:\s+at[eé])?"
    r"|vig[eê]ncia(?:\s+at[eé])?"
    r"|\bat[eé](?:\s+o\s+dia)?"
    r")"
    r"[\s:\-]+(\d{2})[/\-.](\d{2})[/\-.](\d{4})",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ValidityDateMatch:
    """Uma ocorrencia rotulada de data de validade encontrada no documento."""

    raw_match: str
    raw_date: str
    parsed_date: Optional[date]


@dataclass(frozen=True)
class ValidityScanResult:
    """Resultado consolidado de todas as datas de validade rotuladas no texto."""

    matches: Tuple[ValidityDateMatch, ...]
    valid_dates: Tuple[date, ...]
    invalid_raw_dates: Tuple[str, ...]


def scan_validity_dates(text: str) -> ValidityScanResult:
    """
    Extrai todas as datas rotuladas como validade/vigencia no texto (fonte unica
    compartilhada entre parser IDP e motor de regras).

    - Datas validas sao deduplicadas preservando a ordem de aparicao (repeticao da
      mesma data em cabecalho/rodape de varias paginas conta como uma unica data).
    - Datas impossiveis (ex.: 31/02/2026) ficam registradas em `invalid_raw_dates`
      para impedir aprovacao automatica.
    """
    if not text:
        return ValidityScanResult(matches=(), valid_dates=(), invalid_raw_dates=())

    normalized = unicodedata.normalize("NFC", text)
    matches: List[ValidityDateMatch] = []
    valid_dates: List[date] = []
    seen_valid: set[date] = set()
    invalid_raw_dates: List[str] = []

    for match in VALIDITY_DATE_PATTERN.finditer(normalized):
        day_str, month_str, year_str = match.groups()
        raw_date = f"{day_str}/{month_str}/{year_str}"
        parsed: Optional[date] = None
        try:
            parsed = date(int(year_str), int(month_str), int(day_str))
        except ValueError:
            if raw_date not in invalid_raw_dates:
                invalid_raw_dates.append(raw_date)
        else:
            if parsed not in seen_valid:
                seen_valid.add(parsed)
                valid_dates.append(parsed)
        matches.append(
            ValidityDateMatch(
                raw_match=match.group(0).strip(),
                raw_date=raw_date,
                parsed_date=parsed,
            )
        )

    return ValidityScanResult(
        matches=tuple(matches),
        valid_dates=tuple(valid_dates),
        invalid_raw_dates=tuple(invalid_raw_dates),
    )


def normalize_text(text: str) -> str:
    """Normaliza texto removendo acentos e convertendo para caixa alta."""
    nfkd = unicodedata.normalize("NFKD", text)
    return nfkd.encode("ASCII", "ignore").decode("ASCII").upper()


def _find_page_and_snippet(
    pattern: str,
    pages: Optional[List[Dict[str, Any]]] = None,
    full_text: str = "",
) -> Tuple[int, str]:
    """
    Localiza a pagina (1-indexed) e o trecho de texto correspondente a um padrao regex.
    """
    regex = re.compile(pattern, re.IGNORECASE)

    if pages:
        for page_data in pages:
            page_num = page_data.get("page_number", 1)
            p_text = page_data.get("text", "")
            match = regex.search(p_text)
            if match:
                # Extrai a linha inteira correspondente como snippet de evidencia
                lines = p_text.splitlines()
                for line in lines:
                    if regex.search(line):
                        snippet = line.strip()
                        return page_num, snippet
                return page_num, match.group(0).strip()

    # Fallback se pages nao foi fornecido ou nao encontrou
    match = regex.search(full_text)
    if match:
        lines = full_text.splitlines()
        for line in lines:
            if regex.search(line):
                return 1, line.strip()
        return 1, match.group(0).strip()

    return 1, ""


def _find_page_and_snippet_normalized(
    pattern: str,
    pages: Optional[List[Dict[str, Any]]] = None,
    full_text: str = "",
) -> Tuple[int, str]:
    """
    Como _find_page_and_snippet, mas compara cada linha sem acento e em caixa alta (o mesmo
    texto usado na deteccao). Assim tipologia e evidencia saem sempre juntas, mesmo com
    acentos em NFD ou trocados. Devolve a linha original em NFC.
    """
    regex = re.compile(pattern)
    sources = [(p.get("page_number", 1), p.get("text", "")) for p in pages] if pages else []
    sources.append((1, full_text))
    for page_num, source in sources:
        for line in source.splitlines():
            if regex.search(normalize_text(line)):
                return page_num, unicodedata.normalize("NFC", line).strip()
    return 1, ""


def extract_fields_and_evidence(
    text: str,
    pages: Optional[List[Dict[str, Any]]] = None,
) -> ExtractionResult:
    """
    Extrai entidades, campos tipados e evidencias ancoradas em paginas a partir do texto.
    """
    if not text:
        return ExtractionResult(
            document_type=None,
            fields={},
            evidences=[],
            total_pages=len(pages) if pages else 0,
            tables=[],
            full_text_preview=None,
        )

    # Texto e paginas em NFC: acentos decompostos (NFD) passam a casar com os padroes
    # de evidencia ([AÃ], [EÉ]...). As paginas sao copiadas; o dicionario original nao muda.
    text = unicodedata.normalize("NFC", text)
    if pages:
        pages = [{**p, "text": unicodedata.normalize("NFC", p.get("text", ""))} for p in pages]

    text_norm = normalize_text(text)
    fields: Dict[str, ExtractedField] = {}
    evidences: List[PageEvidence] = []

    # 1. Identificacao de Tipologia Documental
    detected_type: Optional[str] = None

    # CEIS/CNEP e licenca ambiental: a deteccao e a propria busca da evidencia, com o mesmo
    # padrao, entao uma nunca sai sem a outra.
    ceis_page, ceis_snippet = _find_page_and_snippet_normalized(
        r"\bCEIS\b|\bCNEP\b|CADASTRO NACIONAL DE EMPRESAS (INIDONEAS E SUSPENSAS|PUNIDAS)",
        pages,
        text,
    )
    # Licenca exige a expressao E um orgao ambiental: "licenca" e "ambiental" soltos nao bastam
    # (licenca sanitaria, de software, de pesca do IBAMA, de operacao da ANATEL/ANAC).
    lic_page, lic_snippet = _find_page_and_snippet_normalized(
        r"LICENCA (AMBIENTAL|PREVIA|DE INSTALACAO|DE OPERACAO)", pages, text
    )
    has_environmental_agency = bool(
        re.search(r"\bIBAMA\b|ORGAO AMBIENTAL|MEIO AMBIENTE|\b(INEA|CETESB|FEPAM)\b", text_norm)
    )
    is_ceis = bool(ceis_snippet)
    is_licenca = bool(lic_snippet) and has_environmental_agency
    # Precedencia: CNDT e falencia disparam pela palavra solta. Elas so vencem CEIS/licenca
    # com o sinal forte da propria certidao ("DEBITOS TRABALHISTAS"; distribuidor + falencia).
    # Assim uma consulta CEIS que cita "certidao de falencia" ou "anexo: CNDT", ou uma
    # licenca que cita falencia nas condicionantes, nao muda de tipologia.
    newer_type_found = is_ceis or is_licenca
    cndt_strong = "DEBITOS TRABALHISTAS" in text_norm
    falencia_word = "FALENCIA" in text_norm or "RECUPERACAO JUDICIAL" in text_norm
    falencia_strong = falencia_word and bool(re.search(r"DISTRIBUI(DOR|CAO)", text_norm))

    # Certidao positiva tambem e a mesma tipologia: precisa ser avaliada (e reprovada)
    # pela regra da CND, e nao cair em "tipologia nao identificada".
    if ("CERTIDAO NEGATIVA" in text_norm or "CERTIDAO POSITIVA" in text_norm) and (
        "TRIBUTOS FEDERAIS" in text_norm
        or "DIVIDA ATIVA DA UNIAO" in text_norm
        or "RECEITA FEDERAL" in text_norm
    ):
        detected_type = "CND_FEDERAL"
        page_num, snippet = _find_page_and_snippet(r"CERTID[AÃ]O (NEGATIVA|POSITIVA)", pages, text)
        if snippet:
            ev = PageEvidence(text=snippet, page=page_num, confidence=1.0)
            evidences.append(ev)
            fields["document_type"] = ExtractedField(
                name="document_type",
                value="CND_FEDERAL",
                raw_value=snippet,
                confidence=1.0,
                evidence=ev,
            )
    elif "FGTS" in text_norm and ("CERTIFICADO DE REGULARIDADE" in text_norm or "CRF" in text_norm):
        detected_type = "CRF_FGTS"
        page_num, snippet = _find_page_and_snippet(r"CERTIFICADO DE REGULARIDADE|CRF", pages, text)
        if snippet:
            ev = PageEvidence(text=snippet, page=page_num, confidence=1.0)
            evidences.append(ev)
            fields["document_type"] = ExtractedField(
                name="document_type",
                value="CRF_FGTS",
                raw_value=snippet,
                confidence=1.0,
                evidence=ev,
            )
    elif cndt_strong or ("CNDT" in text_norm and not newer_type_found):
        detected_type = "CNDT_TRABALHISTA"
        page_num, snippet = _find_page_and_snippet(r"D[EÉ]BITOS TRABALHISTAS|CNDT", pages, text)
        if snippet:
            ev = PageEvidence(text=snippet, page=page_num, confidence=1.0)
            evidences.append(ev)
            fields["document_type"] = ExtractedField(
                name="document_type",
                value="CNDT_TRABALHISTA",
                raw_value=snippet,
                confidence=1.0,
                evidence=ev,
            )
    elif falencia_strong or (falencia_word and not newer_type_found):
        detected_type = "FALENCIA_RECUPERACAO"
        page_num, snippet = _find_page_and_snippet(
            r"FAL[EÊ]NCIA|RECUPERA[CÇ][AÃ]O JUDICIAL", pages, text
        )
        if snippet:
            ev = PageEvidence(text=snippet, page=page_num, confidence=0.95)
            evidences.append(ev)
            fields["document_type"] = ExtractedField(
                name="document_type",
                value="FALENCIA_RECUPERACAO",
                raw_value=snippet,
                confidence=0.95,
                evidence=ev,
            )
    # CEIS/CNEP vem antes da licenca porque uma consulta de sancoes pode citar o IBAMA ou
    # uma licenca ambiental.
    elif is_ceis:
        detected_type = "INTEGRIDADE_CEIS_CNEP"
        page_num, snippet = ceis_page, ceis_snippet
        if snippet:
            ev = PageEvidence(text=snippet, page=page_num, confidence=0.95)
            evidences.append(ev)
            fields["document_type"] = ExtractedField(
                name="document_type",
                value="INTEGRIDADE_CEIS_CNEP",
                raw_value=snippet,
                confidence=0.95,
                evidence=ev,
            )
    # "RECUPERACAO" sozinha (ex.: de area degradada) nao dispara o ramo de falencia
    # acima, que exige "RECUPERACAO JUDICIAL".
    elif is_licenca:
        detected_type = "LICENCA_AMBIENTAL"
        page_num, snippet = lic_page, lic_snippet
        if snippet:
            ev = PageEvidence(text=snippet, page=page_num, confidence=0.95)
            evidences.append(ev)
            fields["document_type"] = ExtractedField(
                name="document_type",
                value="LICENCA_AMBIENTAL",
                raw_value=snippet,
                confidence=0.95,
                evidence=ev,
            )

    # 2. Extracao de CNPJ
    cnpj_pattern = r"\b(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})\b"
    cnpj_match = re.search(cnpj_pattern, text)
    if cnpj_match:
        cnpj_val = cnpj_match.group(1)
        page_num, snippet = _find_page_and_snippet(re.escape(cnpj_val), pages, text)
        ev = PageEvidence(text=snippet or cnpj_val, page=page_num, confidence=1.0)
        evidences.append(ev)
        fields["cnpj"] = ExtractedField(
            name="cnpj",
            value=cnpj_val,
            raw_value=cnpj_val,
            confidence=1.0,
            evidence=ev,
        )

    # 3. Extracao de Data de Validade (fonte unica compartilhada com o motor de regras)
    # So preenche o campo quando ha uma unica data valida inequivoca e nenhuma data
    # impossivel conflitante; multiplas datas distintas ficam sem escolha arbitraria.
    validity_scan = scan_validity_dates(text)
    if len(validity_scan.valid_dates) == 1 and not validity_scan.invalid_raw_dates:
        validity_date = validity_scan.valid_dates[0]
        first_valid_match = next(m for m in validity_scan.matches if m.parsed_date == validity_date)
        raw_date = validity_date.strftime("%d/%m/%Y")
        iso_date = validity_date.isoformat()
        page_num, snippet = _find_page_and_snippet(
            re.escape(first_valid_match.raw_match), pages, text
        )
        ev = PageEvidence(
            text=snippet or first_valid_match.raw_match or raw_date,
            page=page_num,
            confidence=1.0,
        )
        evidences.append(ev)
        fields["data_validade"] = ExtractedField(
            name="data_validade",
            value=iso_date,
            raw_value=raw_date,
            confidence=1.0,
            evidence=ev,
        )

    # 4. Extracao de Data de Emissao
    emission_patterns = [
        (
            r"(?:emiss[aã]o|emitid[ao]\s+em|expedi[cç][aã]o|data\s+de\s+emiss[aã]o)"
            r"[\s:]+(\d{2})[/\-.](\d{2})[/\-.](\d{4})"
        ),
        r"emitid[ao]\s+em\s+(\d{2})[/\-.](\d{2})[/\-.](\d{4})",
    ]
    for pattern in emission_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            day, month, year = match.groups()
            raw_date = f"{day}/{month}/{year}"
            iso_date = f"{year}-{month}-{day}"
            page_num, snippet = _find_page_and_snippet(pattern, pages, text)
            ev = PageEvidence(text=snippet or raw_date, page=page_num, confidence=1.0)
            evidences.append(ev)
            fields["data_emissao"] = ExtractedField(
                name="data_emissao",
                value=iso_date,
                raw_value=raw_date,
                confidence=1.0,
                evidence=ev,
            )
            break

    # 5. Extracao de Numero de Certidao ou Codigo de Controle
    code_patterns = [
        r"\b(CRF\d{8,14})\b",
        r"\b([0-9A-Fa-f]{4}\.[0-9A-Fa-f]{4}\.[0-9A-Fa-f]{4}\.[0-9A-Fa-f]{4})\b",
        r"\b(\d{4}/\d{4})\b",
    ]
    for pattern in code_patterns:
        match = re.search(pattern, text)
        if match:
            code_val = match.group(1)
            page_num, snippet = _find_page_and_snippet(re.escape(code_val), pages, text)
            ev = PageEvidence(text=snippet or code_val, page=page_num, confidence=1.0)
            evidences.append(ev)
            fields["numero_certidao"] = ExtractedField(
                name="numero_certidao",
                value=code_val,
                raw_value=code_val,
                confidence=1.0,
                evidence=ev,
            )
            break

    # 6. Extracao de Situacao Cadastral/Regularidade
    if "NAO CONSTAM PENDENCIAS" in text_norm:
        page_num, snippet = _find_page_and_snippet(r"n[aã]o\s+constam\s+pend[eê]ncias", pages, text)
        ev = PageEvidence(text=snippet or "Nao constam pendencias", page=page_num, confidence=1.0)
        evidences.append(ev)
        fields["situacao"] = ExtractedField(
            name="situacao",
            value="REGULAR",
            raw_value=snippet or "nao constam pendencias",
            confidence=1.0,
            evidence=ev,
        )
    elif "SITUACAO REGULAR" in text_norm:
        page_num, snippet = _find_page_and_snippet(r"situa[cç][aã]o\s+regular", pages, text)
        ev = PageEvidence(text=snippet or "Situacao regular", page=page_num, confidence=1.0)
        evidences.append(ev)
        fields["situacao"] = ExtractedField(
            name="situacao",
            value="REGULAR",
            raw_value=snippet or "situacao regular",
            confidence=1.0,
            evidence=ev,
        )
    elif "CONSTA PENDENCIA" in text_norm or "DEBITOS EXISTENTES" in text_norm:
        page_num, snippet = _find_page_and_snippet(
            r"consta\s+pend[eê]ncia|d[eé]bitos\s+existentes", pages, text
        )
        ev = PageEvidence(text=snippet or "Consta pendencia", page=page_num, confidence=1.0)
        evidences.append(ev)
        fields["situacao"] = ExtractedField(
            name="situacao",
            value="IRREGULAR",
            raw_value=snippet or "consta pendencia",
            confidence=1.0,
            evidence=ev,
        )
    elif "CONSTA DISTRIBUICAO DE PROCESSO DE FALENCIA" in text_norm:
        page_num, snippet = _find_page_and_snippet(
            r"consta\s+distribui[cç][aã]o\s+de\s+processo\s+de\s+fal[eê]ncia", pages, text
        )
        ev = PageEvidence(
            text=snippet or "Consta distribuicao de processo de falencia",
            page=page_num,
            confidence=1.0,
        )
        evidences.append(ev)
        fields["situacao"] = ExtractedField(
            name="situacao",
            value="FALENCIA_DETECTADA",
            raw_value=snippet or "falencia detectada",
            confidence=1.0,
            evidence=ev,
        )

    # 7. Extracao de Razao Social / Nome Empresarial
    razao_patterns = [
        r"(?:Raz[aã]o\s+Social|Nome Empresarial|Empregador)[\s:]+([^\n\r]+)",
    ]
    for pattern in razao_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            razao_val = match.group(1).strip()
            page_num, snippet = _find_page_and_snippet(pattern, pages, text)
            ev = PageEvidence(text=snippet or razao_val, page=page_num, confidence=0.9)
            evidences.append(ev)
            fields["razao_social"] = ExtractedField(
                name="razao_social",
                value=razao_val,
                raw_value=razao_val,
                confidence=0.9,
                evidence=ev,
            )
            break

    # Consolidar tabelas extraidas
    all_tables: List[Any] = []
    if pages:
        for p in pages:
            for t in p.get("tables", []):
                all_tables.append(t)

    total_p = len(pages) if pages else (1 if text else 0)
    preview = (text[:1000] + "...") if len(text) > 1000 else text

    return ExtractionResult(
        document_type=detected_type,
        fields=fields,
        evidences=evidences,
        total_pages=total_p,
        tables=all_tables,
        full_text_preview=preview if text else None,
    )


def build_extraction_result_from_document(doc: Document) -> ExtractionResult:
    """
    Constrói a estrutura ExtractionResult a partir de um registro Document do banco.
    """
    if doc.extracted_metadata and isinstance(doc.extracted_metadata, dict):
        saved_extraction = doc.extracted_metadata.get("extraction")
        if saved_extraction and isinstance(saved_extraction, dict):
            try:
                return ExtractionResult.model_validate(saved_extraction)
            except Exception:
                pass

    pages = None
    if doc.extracted_metadata and isinstance(doc.extracted_metadata, dict):
        pages = doc.extracted_metadata.get("pages")

    return extract_fields_and_evidence(doc.extracted_text or "", pages=pages)


def build_processing_status_response(doc: Document) -> ProcessingStatusResponse:
    """
    Constrói o ProcessingStatusResponse tipado a partir do estado do Document.
    """
    status_str = doc.status or ProcessingStatus.PENDING.value
    created_at = doc.created_at or datetime.now(timezone.utc)
    updated_at = doc.updated_at or created_at

    extraction_result: Optional[ExtractionResult] = None
    error_detail: Optional[ErrorDetail] = None
    progress: float = 0.0
    message: str = ""

    if status_str == ProcessingStatus.COMPLETED.value:
        progress = 1.0
        message = "Processamento e extracao concluidos com sucesso."
        extraction_result = build_extraction_result_from_document(doc)
    elif status_str == ProcessingStatus.PROCESSING.value:
        progress = 0.5
        message = "Documento em processamento na esteira de extracao IDP e OCR."
    elif status_str == ProcessingStatus.PENDING.value:
        progress = 0.0
        message = "Documento aguardando inicio do processamento na fila IDP."
    elif status_str in (
        ProcessingStatus.EXTRACTION_FAILED.value,
        ProcessingStatus.FAILED.value,
    ):
        progress = 0.0
        message = "Falha durante o processamento documental."

        error_meta = None
        if doc.extracted_metadata and isinstance(doc.extracted_metadata, dict):
            error_meta = doc.extracted_metadata.get("error_detail")
            if not error_meta:
                raw_error = doc.extracted_metadata.get("error")
                if raw_error:
                    error_meta = {
                        "code": status_str,
                        "message": str(raw_error),
                        "details": {"stage": "idp_extraction"},
                        "timestamp": updated_at.isoformat(),
                    }

        if error_meta and isinstance(error_meta, dict):
            try:
                error_detail = ErrorDetail.model_validate(error_meta)
            except Exception:
                error_detail = ErrorDetail(
                    code=status_str,
                    message=str(error_meta.get("message", "Falha de extracao desconhecida")),
                    details=error_meta.get("details"),
                    timestamp=updated_at,
                )
        else:
            error_detail = ErrorDetail(
                code=status_str,
                message="Falha desconhecida durante a extracao documental.",
                details={"stage": "idp_extraction"},
                timestamp=updated_at,
            )

    return ProcessingStatusResponse(
        document_id=doc.id,
        filename=doc.original_filename,
        status=ProcessingStatus(status_str),
        progress=progress,
        message=message,
        extraction=extraction_result,
        error=error_detail,
        created_at=created_at,
        updated_at=updated_at,
    )
