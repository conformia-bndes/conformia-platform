"""Parser and structured entity extractor for Intelligent Document Processing (IDP)."""

from datetime import datetime, timezone
import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

from app.db.models.document import Document
from app.schemas.enums import ProcessingStatus
from app.schemas.error import ErrorDetail
from app.schemas.evidence import PageEvidence
from app.schemas.extraction import ExtractedField, ExtractionResult
from app.schemas.processing import ProcessingStatusResponse


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

    text_norm = normalize_text(text)
    fields: Dict[str, ExtractedField] = {}
    evidences: List[PageEvidence] = []

    # 1. Identificacao de Tipologia Documental
    detected_type: Optional[str] = None
    if "CERTIDAO NEGATIVA" in text_norm and (
        "TRIBUTOS FEDERAIS" in text_norm
        or "DIVIDA ATIVA DA UNIAO" in text_norm
        or "RECEITA FEDERAL" in text_norm
    ):
        detected_type = "CND_FEDERAL"
        page_num, snippet = _find_page_and_snippet(r"CERTID[AÃ]O NEGATIVA", pages, text)
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
    elif "DEBITOS TRABALHISTAS" in text_norm or "CNDT" in text_norm:
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
    elif "FALENCIA" in text_norm or "RECUPERACAO JUDICIAL" in text_norm:
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

    # 3. Extracao de Data de Validade
    validity_patterns = [
        (
            r"(?:v[aá]lid[ao]\s+at[eé]|validade|vig[eê]ncia|data\s+de\s+validade)"
            r"[\s:]+(\d{2})[/\-.](\d{2})[/\-.](\d{4})"
        ),
        r"at[eé]\s+(\d{2})[/\-.](\d{2})[/\-.](\d{4})",
    ]
    for pattern in validity_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            day, month, year = match.groups()
            raw_date = f"{day}/{month}/{year}"
            iso_date = f"{year}-{month}-{day}"
            page_num, snippet = _find_page_and_snippet(pattern, pages, text)
            ev = PageEvidence(text=snippet or raw_date, page=page_num, confidence=1.0)
            evidences.append(ev)
            fields["data_validade"] = ExtractedField(
                name="data_validade",
                value=iso_date,
                raw_value=raw_date,
                confidence=1.0,
                evidence=ev,
            )
            break

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
