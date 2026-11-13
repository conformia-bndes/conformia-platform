#!/usr/bin/env python3
"""Valida a extracao OCR (tesseract-ocr-por) com um PDF digitalizado dentro do container.

Execucao direta no container da stack:
    docker compose --env-file .env -f infra/docker-compose.yml exec -T backend \
        python scripts/validate_ocr_container.py

Execucao isolada na imagem construida (Settings exige SECRET_KEY, API_KEY, POSTGRES_PASSWORD,
MINIO_ROOT_USER e MINIO_ROOT_PASSWORD; valores descartaveis bastam):
    docker run --rm -e SECRET_KEY=x -e API_KEY=x -e POSTGRES_PASSWORD=x -e MINIO_ROOT_USER=x \
        -e MINIO_ROOT_PASSWORD=x scan/backend:ci python scripts/validate_ocr_container.py
"""

import io
from pathlib import Path
import shutil
import sys
import tempfile
from typing import List

from PIL import Image, ImageDraw, ImageFont

# Garante que /app (ou backend/) esteja no sys.path
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.idp.extractor import DocumentExtractor  # noqa: E402
from app.idp.parser import extract_fields_and_evidence  # noqa: E402

SCANNED_CND_LINES: List[str] = [
    "REPUBLICA FEDERATIVA DO BRASIL - MINISTERIO DA FAZENDA",
    "SECRETARIA ESPECIAL DA RECEITA FEDERAL DO BRASIL",
    "CERTIDAO NEGATIVA DE DEBITOS RELATIVOS AOS TRIBUTOS FEDERAIS",
    "E A DIVIDA ATIVA DA UNIAO",
    "CNPJ: 12.345.678/0001-90",
    "E certificado que nao constam pendencias em nome do sujeito passivo.",
    "Valida ate: 31/12/2030",
]


def build_scanned_pdf(lines: List[str]) -> bytes:
    """Gera um PDF de 1 pagina contendo apenas imagem rasterizada (200 DPI), sem camada de texto."""
    img = Image.new("L", (1654, 2339), 255)
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=40)
    y = 150
    for line in lines:
        draw.text((120, y), line, fill=0, font=font)
        y += 70
    buffer = io.BytesIO()
    img.save(buffer, format="PDF", resolution=200.0)
    return buffer.getvalue()


def validate_ocr(extractor: DocumentExtractor = None) -> dict:
    """Executa o pipeline IDP sobre o PDF digitalizado e valida os campos extraidos via OCR."""
    extractor = extractor or DocumentExtractor()
    with tempfile.TemporaryDirectory() as tmp_dir:
        pdf_path = Path(tmp_dir) / "cnd_digitalizada_ocr.pdf"
        pdf_path.write_bytes(build_scanned_pdf(SCANNED_CND_LINES))
        result = extractor.extract(str(pdf_path), document_id="ocr-container-validation")

    pages = result.get("pages") or []
    if len(pages) != 1:
        raise RuntimeError(f"Esperada 1 pagina extraida, obtido: {len(pages)}")

    page = pages[0]
    if page.get("extraction_method") != "ocr" or not page.get("ocr_attempted"):
        raise RuntimeError(f"Fallback de OCR nao foi acionado na pagina digitalizada: {page}")
    if page.get("error"):
        raise RuntimeError(f"OCR retornou erro na pagina digitalizada: {page.get('error')}")

    full_text = result.get("full_text") or ""
    if "CERTIDAO NEGATIVA" not in full_text.upper():
        raise RuntimeError(f"Texto extraido pelo OCR nao contem cabecalho esperado: {full_text!r}")

    parsed = extract_fields_and_evidence(text=full_text, pages=pages)
    cnpj_field = parsed.fields.get("cnpj")
    validity_field = parsed.fields.get("data_validade")
    if parsed.document_type != "CND_FEDERAL" or not cnpj_field or not cnpj_field.value:
        raise RuntimeError(f"Parser nao identificou CND_FEDERAL/CNPJ apos OCR: {parsed}")
    if not validity_field or not validity_field.value:
        raise RuntimeError(f"Parser nao identificou data_validade apos OCR: {parsed}")

    return {
        "document_id": result["document_id"],
        "extraction_method": page["extraction_method"],
        "document_type": parsed.document_type,
        "cnpj": cnpj_field.value,
        "validity_date": validity_field.value,
    }


def main() -> int:
    if shutil.which("tesseract") is None:
        print(
            "[ocr-check] FALHA: binario 'tesseract' nao encontrado no PATH.",
            file=sys.stderr,
        )
        return 1

    try:
        summary = validate_ocr()
    except Exception as exc:
        print(f"[ocr-check] FALHA: {exc}", file=sys.stderr)
        return 1

    print(
        "[ocr-check] OK - OCR validado com PDF digitalizado: "
        f"method={summary['extraction_method']} "
        f"type={summary['document_type']} "
        f"cnpj={summary['cnpj']} "
        f"validade={summary['validity_date']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
