"""Gerador de PDFs sinteticos reproduzíveis (nativo e digitalizado) para testes do IDP.

Inclui os 5 PDFs de referencia exigidos pela base de testes do fluxo inicial:
- valido: CND regular, dentro do prazo -> COMPLETED / COMPLIANT
- vencido: CND com data de validade expirada -> COMPLETED / NON_COMPLIANT (temporal)
- pendente: CND com debitos pendentes -> COMPLETED / NON_COMPLIANT (pendencia)
- ilegivel: PDF digitalizado sem texto nativo (OCR falha) -> EXTRACTION_FAILED
- invalido: arquivo nao-PDF (assinatura binaria ausente) -> rejeicao 400
"""

import io
import sys
from pathlib import Path
from typing import List, Dict, Any

from PIL import Image, ImageDraw, ImageFont

SYNTHETIC_LINES: List[str] = [
    "REPUBLICA FEDERATIVA DO BRASIL - MINISTERIO DA FAZENDA",
    "SECRETARIA ESPECIAL DA RECEITA FEDERAL DO BRASIL",
    "CERTIDAO NEGATIVA DE DEBITOS RELATIVOS AOS TRIBUTOS",
    "FEDERAIS E A DIVIDA ATIVA DA UNIAO",
    "CNPJ: 12.345.678/0001-90",
    "E certificado que nao constam pendencias.",
    "Valida ate: 31/12/2030",
]


def _page_stream(lines: List[str]) -> bytes:
    """Conteudo de uma pagina PDF: uma linha de texto por linha da lista."""
    parts = ["BT", "/F1 12 Tf", "50 780 Td", "16 TL"]
    for line in lines:
        safe = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        parts.append(f"({safe}) Tj T*")
    parts.append("ET")
    return "\n".join(parts).encode("latin-1")


def build_native_pdf(pages: List[List[str]]) -> bytes:
    """PDF com texto nativo (fonte Helvetica). Cada item de `pages` vira uma pagina."""
    total = len(pages)
    first_page_obj = 4
    kids = " ".join(f"{first_page_obj + 2 * i} 0 R" for i in range(total))

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        f"<< /Type /Pages /Kids [{kids}] /Count {total} >>".encode(),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    for i, lines in enumerate(pages):
        content_obj = first_page_obj + 2 * i + 1
        stream = _page_stream(lines)
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            f"/Contents {content_obj} 0 R "
            f"/Resources << /Font << /F1 3 0 R >> >> >>".encode()
        )
        objects.append(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream")

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + obj + b"\nendobj\n"

    xref_pos = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n" f"startxref\n{xref_pos}\n%%EOF\n"
    ).encode()
    return bytes(out)


def build_scanned_pdf(lines: List[str]) -> bytes:
    """PDF de 1 pagina que e so uma imagem (sem texto nativo), simulando um scan."""
    img = Image.new("L", (1654, 2339), 255)  # A4 a 200 dpi
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=40)
    y = 150
    for line in lines:
        draw.text((120, y), line, fill=0, font=font)
        y += 70
    buffer = io.BytesIO()
    img.save(buffer, format="PDF", resolution=200.0)
    return buffer.getvalue()


# ==============================================================================
# 5 PDFs de referencia do fluxo inicial (com resultado esperado registrado)
# ==============================================================================

VALID_PDF_LINES: List[str] = [
    "REPUBLICA FEDERATIVA DO BRASIL - MINISTERIO DA FAZENDA",
    "SECRETARIA ESPECIAL DA RECEITA FEDERAL DO BRASIL",
    "CERTIDAO NEGATIVA DE DEBITOS RELATIVOS AOS TRIBUTOS FEDERAIS",
    "E A DIVIDA ATIVA DA UNIAO",
    "CNPJ: 12.345.678/0001-90",
    "E certificado que nao constam pendencias em nome do sujeito passivo.",
    "Valida ate: 31/12/2030",
]

EXPIRED_PDF_LINES: List[str] = [
    "REPUBLICA FEDERATIVA DO BRASIL - MINISTERIO DA FAZENDA",
    "SECRETARIA ESPECIAL DA RECEITA FEDERAL DO BRASIL",
    "CERTIDAO NEGATIVA DE DEBITOS RELATIVOS AOS TRIBUTOS FEDERAIS",
    "E A DIVIDA ATIVA DA UNIAO",
    "CNPJ: 12.345.678/0001-90",
    "E certificado que nao constam pendencias em nome do sujeito passivo.",
    "Valida ate: 01/01/2020",
]

PENDING_PDF_LINES: List[str] = [
    "SECRETARIA DA RECEITA FEDERAL DO BRASIL",
    "CERTIDAO POSITIVA DE DEBITOS RELATIVOS AOS TRIBUTOS FEDERAIS",
    "E A DIVIDA ATIVA DA UNIAO",
    "CONSTA PENDENCIA RELATIVA AOS TRIBUTOS FEDERAIS E DIVIDA ATIVA",
    "CNPJ: 98.765.432/0001-11",
    "Valor total do debito: R$ 150.000,00",
]

ILLEGIBLE_PDF_LINES: List[str] = [
    # Texto intencionalmente ilegível / digitalizado de baixa qualidade
    "XXXX XXXX XXXX XXXX",
    "???? ???? ???? ????",
    "~~~~ ~~~~ ~~~~ ~~~~",
]

INVALID_FILE_CONTENT: bytes = (
    b"ESTE NAO E UM ARQUIVO PDF - CONTEUDO ALEATORIO SEM ASSINATURA BINARIA"
)

# Resultado esperado para cada PDF de referencia (ground truth)
REFERENCE_PDF_EXPECTED_RESULTS: Dict[str, Dict[str, Any]] = {
    "valido": {
        "upload_status": 201,
        "processing_status": "COMPLETED",
        "document_type": "CND_FEDERAL",
        "rule_status": "COMPLIANT",
        "rule_id": "RULE-BNDES-001",
        "error": None,
    },
    "vencido": {
        "upload_status": 201,
        "processing_status": "COMPLETED",
        "document_type": "CND_FEDERAL",
        "rule_status": "NON_COMPLIANT",
        "rule_id": "RULE-BNDES-001",
        "error": None,
        "error_contains": "expirada",
    },
    "pendente": {
        "upload_status": 201,
        "processing_status": "COMPLETED",
        "document_type": "CND_FEDERAL",
        "rule_status": "NON_COMPLIANT",
        "rule_id": "RULE-BNDES-001",
        "error": None,
        "error_contains": "pendencia",
    },
    "ilegivel": {
        "upload_status": 201,
        "processing_status": "EXTRACTION_FAILED",
        "document_type": None,
        "rule_status": None,
        "rule_id": None,
        "error_contains": "sem texto legivel",
    },
    "invalido": {
        "upload_status": 400,
        "processing_status": None,
        "document_type": None,
        "rule_status": None,
        "rule_id": None,
        "error_contains": "assinatura binaria",
    },
}


def build_reference_pdf(pdf_type: str) -> bytes:
    """Constrói um PDF de referencia conforme o tipo solicitado.

    Tipos suportados: 'valido', 'vencido', 'pendente', 'ilegivel'.
    Para 'invalido' use INVALID_FILE_CONTENT diretamente (não é um PDF).
    """
    lines_map = {
        "valido": VALID_PDF_LINES,
        "vencido": EXPIRED_PDF_LINES,
        "pendente": PENDING_PDF_LINES,
        "ilegivel": ILLEGIBLE_PDF_LINES,
    }
    if pdf_type not in lines_map:
        raise ValueError(f"Tipo de PDF de referencia não suportado: {pdf_type}")

    lines = lines_map[pdf_type]

    if pdf_type == "ilegivel":
        # PDF digitalizado (apenas imagem, sem texto nativo) -> OCR não consegue ler
        return build_scanned_pdf(lines)

    return build_native_pdf([lines])


def get_expected_result(pdf_type: str) -> Dict[str, Any]:
    """Retorna o resultado esperado registrado para um PDF de referencia."""
    if pdf_type not in REFERENCE_PDF_EXPECTED_RESULTS:
        raise ValueError(f"Tipo de PDF de referencia não conhecido: {pdf_type}")
    return REFERENCE_PDF_EXPECTED_RESULTS[pdf_type]


def list_reference_types() -> List[str]:
    """Lista os tipos de PDF de referencia disponíveis."""
    return list(REFERENCE_PDF_EXPECTED_RESULTS.keys())


if __name__ == "__main__":
    # Uso (a partir de backend/): python -m tests.synthetic_pdfs ../evals/datasets/pdfs
    target = Path(sys.argv[1] if len(sys.argv) > 1 else "synthetic_pdfs")
    target.mkdir(parents=True, exist_ok=True)
    (target / "cnd_nativo.pdf").write_bytes(build_native_pdf([SYNTHETIC_LINES]))
    (target / "cnd_digitalizado.pdf").write_bytes(build_scanned_pdf(SYNTHETIC_LINES))
    # Gera também os PDFs de referencia do fluxo inicial
    for ref_type in list_reference_types():
        if ref_type != "invalido":
            (target / f"ref_{ref_type}.pdf").write_bytes(build_reference_pdf(ref_type))
    (target / "ref_invalido.bin").write_bytes(INVALID_FILE_CONTENT)
    print(f"PDFs sinteticos gerados em {target.resolve()}")
