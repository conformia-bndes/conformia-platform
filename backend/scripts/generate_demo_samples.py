#!/usr/bin/env python3
"""Gera PDFs ficticios complementares para o roteiro de demonstracao (Issue #63).

Todos os documentos sao exclusivamente ficticios (CNPJs sinteticos, sem dados reais).
Uso:
    uv run python backend/scripts/generate_demo_samples.py
"""

import io
from pathlib import Path
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLES_DIR = REPO_ROOT / "docs" / "samples"


def _escape_pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_styled_native_pdf(
    header_title: str,
    subtitle: str,
    doc_title: str,
    doc_subtitle: str,
    body_lines: List[Tuple[str, int, str]],
) -> bytes:
    """Constroi um PDF A4 nativo com diagramacao institucional e camada de texto extraivel."""
    commands = [
        "0.15 0.25 0.38 RG 1.5 w 36 36 523 770 re S",
        "0.15 0.25 0.38 RG 0.5 w 42 42 511 758 re S",
        "0.94 0.96 0.98 rg 43 720 509 79 re f",
        "0 0 0 rg",
        "0.8 0.84 0.88 RG 0.8 w 60 398 m 535 398 l S",
        "0.8 0.84 0.88 RG 0.8 w 60 140 m 535 140 l S",
        f"BT /F2 11 Tf 130 774 Td ({_escape_pdf_text(header_title)}) Tj ET",
        f"BT /F1 10 Tf 175 758 Td ({_escape_pdf_text(subtitle)}) Tj ET",
        f"BT /F2 12 Tf 75 734 Td ({_escape_pdf_text(doc_title)}) Tj ET",
        f"BT /F2 11 Tf 175 695 Td ({_escape_pdf_text(doc_subtitle)}) Tj ET",
    ]
    y = 655
    for font_key, size, line in body_lines:
        if line:
            commands.append(f"BT /{font_key} {size} Tf 60 {y} Td ({_escape_pdf_text(line)}) Tj ET")
        y -= 18 if size >= 10 else 15

    stream = "\n".join(commands).encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R /F2 6 0 R >> >> >>"
        ),
        b"<< /Length "
        + str(len(stream)).encode("ascii")
        + b" >>\nstream\n"
        + stream
        + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
    ]

    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for idx, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out.extend(f"{idx} 0 obj\n".encode("ascii"))
        out.extend(obj)
        out.extend(b"\nendobj\n")

    xref_pos = len(out)
    out.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    out.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        out.extend(f"{off:010d} 00000 n \n".encode("ascii"))
    out.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_pos}\n%%EOF\n"
        ).encode("ascii")
    )
    return bytes(out)


def build_scanned_cnd_pdf() -> bytes:
    """Gera uma CND Federal ficticia rasterizada (200 DPI, sem camada de texto) para OCR."""
    lines = [
        "REPUBLICA FEDERATIVA DO BRASIL (DOCUMENTO FICTICIO)",
        "MINISTERIO DA FAZENDA - RECEITA FEDERAL / PGFN",
        "CERTIDAO NEGATIVA DE DEBITOS RELATIVOS AOS TRIBUTOS FEDERAIS",
        "E A DIVIDA ATIVA DA UNIAO",
        "Razao Social: CONSTRUTORA HORIZONTE VERDE LTDA",
        "CNPJ: 12.345.678/0001-90",
        "E certificado que NAO CONSTAM pendencias relativas a tributos",
        "federais e a Divida Ativa da Uniao em nome do sujeito passivo.",
        "Emitida em: 17/11/2026",
        "Valida ate: 15/05/2027",
        "Codigo de Controle: A1B2.C3D4.E5F6.9999",
        "AVISO: Documento ficticio rasterizado para demonstracao de OCR.",
    ]
    img = Image.new("L", (1654, 2339), 255)
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=36)
    y = 180
    for line in lines:
        draw.text((120, y), line, fill=0, font=font)
        y += 85
    buffer = io.BytesIO()
    img.save(buffer, format="PDF", resolution=200.0)
    return buffer.getvalue()


def generate_all(output_dir: Path = SAMPLES_DIR) -> List[Path]:
    """Gera os PDFs ficticios complementares em docs/samples/ e retorna os caminhos."""
    output_dir.mkdir(parents=True, exist_ok=True)
    generated: List[Path] = []

    expired_pdf = build_styled_native_pdf(
        header_title="REPUBLICA FEDERATIVA DO BRASIL (DOCUMENTO FICTICIO)",
        subtitle="MINISTERIO DA FAZENDA - PGFN / RECEITA FEDERAL",
        doc_title="CERTIDAO NEGATIVA DE DEBITOS RELATIVOS AOS TRIBUTOS FEDERAIS",
        doc_subtitle="E A DIVIDA ATIVA DA UNIAO",
        body_lines=[
            ("F2", 10, "DADOS DO CONTRIBUINTE / PROPONENTE:"),
            ("F1", 10, "Nome Empresarial (Razao Social): LOGISTICA ATLANTICO SUL LTDA"),
            ("F1", 10, "CNPJ: 23.456.789/0001-12"),
            ("F1", 10, "Endereco: Av. Brasil, 2500 - Rio de Janeiro/RJ"),
            ("F1", 10, ""),
            ("F2", 10, "ATESTADO DE REGULARIDADE FISCAL:"),
            ("F1", 10, "Certifica-se que NAO CONSTAM pendencias relativas a creditos"),
            ("F1", 10, "tributarios administrados pela RFB e a Divida Ativa da Uniao"),
            ("F1", 10, "ate a data de encerramento da vigencia indicada abaixo."),
            ("F1", 10, ""),
            ("F2", 10, "INFORMACOES DE CONTROLE E VALIDADE (EXPIRADA):"),
            ("F1", 10, "Emitida em: 10/01/2025"),
            ("F2", 10, "Valida ate: 10/07/2025"),
            ("F1", 10, "Codigo de Controle da Certidao: 1122.3344.5566.7788"),
            ("F1", 10, ""),
            ("F1", 9, "AVISO: Documento exclusivamente ficticio (CND vencida) para demonstracao"),
            ("F1", 9, "da plataforma Conform.IA BNDES (Issue #63). Nao possui valor legal."),
        ],
    )
    expired_path = output_dir / "cnd_federal_vencida.pdf"
    expired_path.write_bytes(expired_pdf)
    generated.append(expired_path)

    no_validity_pdf = build_styled_native_pdf(
        header_title="REPUBLICA FEDERATIVA DO BRASIL (DOCUMENTO FICTICIO)",
        subtitle="MINISTERIO DA FAZENDA - PGFN / RECEITA FEDERAL",
        doc_title="CERTIDAO NEGATIVA DE DEBITOS RELATIVOS AOS TRIBUTOS FEDERAIS",
        doc_subtitle="E A DIVIDA ATIVA DA UNIAO",
        body_lines=[
            ("F2", 10, "DADOS DO CONTRIBUINTE / PROPONENTE:"),
            ("F1", 10, "Nome Empresarial (Razao Social): INDUSTRIA SOLAR BRASIL LTDA"),
            ("F1", 10, "CNPJ: 34.567.890/0001-45"),
            ("F1", 10, "Endereco: Rua das Flores, 88 - Belo Horizonte/MG"),
            ("F1", 10, ""),
            ("F2", 10, "ATESTADO DE REGULARIDADE FISCAL:"),
            ("F1", 10, "Certifica-se que NAO CONSTAM pendencias relativas a creditos"),
            ("F1", 10, "tributarios administrados pela RFB e a Divida Ativa da Uniao."),
            ("F1", 10, ""),
            ("F2", 10, "INFORMACOES DE CONTROLE E VALIDADE:"),
            ("F1", 10, "Emitida em: 17/11/2026"),
            ("F1", 10, "Data de validade: [campo ilegivel / rasurado na emissao]"),
            ("F1", 10, "Codigo de Controle da Certidao: AA11.BB22.CC33.DD44"),
            ("F1", 10, ""),
            ("F1", 9, "AVISO: Documento exclusivamente ficticio (sem data de validade legivel)"),
            ("F1", 9, "para demonstracao de revisao manual no Conform.IA BNDES (Issue #63)."),
        ],
    )
    no_validity_path = output_dir / "cnd_federal_sem_validade.pdf"
    no_validity_path.write_bytes(no_validity_pdf)
    generated.append(no_validity_path)

    scanned_path = output_dir / "cnd_federal_digitalizada_ocr.pdf"
    scanned_path.write_bytes(build_scanned_cnd_pdf())
    generated.append(scanned_path)

    return generated


if __name__ == "__main__":
    for path in generate_all():
        print(f"Gerado: {path.relative_to(REPO_ROOT)} ({path.stat().st_size} bytes)")
