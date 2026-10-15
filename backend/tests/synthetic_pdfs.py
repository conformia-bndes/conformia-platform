"""Gerador de PDFs sinteticos reproduzíveis (nativo e digitalizado) para testes do IDP."""

import io
import sys
from pathlib import Path
from typing import List

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


if __name__ == "__main__":
    # Uso (a partir de backend/): python -m tests.synthetic_pdfs ../evals/datasets/pdfs
    target = Path(sys.argv[1] if len(sys.argv) > 1 else "synthetic_pdfs")
    target.mkdir(parents=True, exist_ok=True)
    (target / "cnd_nativo.pdf").write_bytes(build_native_pdf([SYNTHETIC_LINES]))
    (target / "cnd_digitalizado.pdf").write_bytes(build_scanned_pdf(SYNTHETIC_LINES))
    print(f"PDFs sinteticos gerados em {target.resolve()}")
