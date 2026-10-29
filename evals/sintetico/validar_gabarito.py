"""Confere a consistencia do gabarito do dataset sintetico (issue #24).

Verifica que:
- todo PDF gerado tem exatamente uma entrada no gabarito, e vice-versa;
- os IDs sao unicos e os status esperados sao validos;
- toda evidencia citada existe literalmente no texto do PDF nativo de origem.
"""

import json
import sys
from pathlib import Path

import pdfplumber

PASTA = Path(__file__).parent
PASTA_PDFS = PASTA / "pdfs"
ARQUIVO_GABARITO = PASTA / "gabarito.json"

STATUS_VALIDOS = {"COMPLIANT", "NON_COMPLIANT", "MANUAL_REVIEW_REQUIRED"}
CAMPOS_OBRIGATORIOS = {"tipo_documento", "cnpj", "validade", "pendencia"}
MOTIVOS_VALIDOS = {"ilegivel", "ausente", "erro_digitacao"}


def texto_do_pdf(caminho):
    """Extrai o texto nativo do PDF e junta todos os espacos e quebras de linha em um so espaco."""
    with pdfplumber.open(str(caminho)) as pdf:
        texto = " ".join(pagina.extract_text() or "" for pagina in pdf.pages)
    return " ".join(texto.split())


def main():
    gabarito = json.loads(ARQUIVO_GABARITO.read_text(encoding="utf-8"))
    problemas = []

    ids = [caso["id"] for caso in gabarito]
    repetidos = {i for i in ids if ids.count(i) > 1}
    if repetidos:
        problemas.append(f"IDs repetidos: {sorted(repetidos)}")

    arquivos_gabarito = {caso["arquivo"] for caso in gabarito}
    arquivos_gerados = {pdf.name for pdf in PASTA_PDFS.glob("*.pdf")}
    for nome in sorted(arquivos_gerados - arquivos_gabarito):
        problemas.append(f"{nome}: PDF gerado sem entrada no gabarito")
    for nome in sorted(arquivos_gabarito - arquivos_gerados):
        problemas.append(f"{nome}: esta no gabarito mas o PDF nao existe (rode gerar_dataset.py)")

    for caso in gabarito:
        if caso["status_esperado"] not in STATUS_VALIDOS:
            problemas.append(f"{caso['id']}: status_esperado invalido '{caso['status_esperado']}'")

        faltando = CAMPOS_OBRIGATORIOS - set(caso["campos"])
        if faltando:
            problemas.append(f"{caso['id']}: campos faltando no gabarito: {sorted(faltando)}")

        if caso["formato"] == "digitalizado" and "origem" not in caso:
            problemas.append(f"{caso['id']}: caso digitalizado precisa do campo 'origem'")
            continue

        # Digitalizados sao conferidos no texto do nativo de origem (a imagem nao tem texto)
        origem = caso.get("origem", caso["id"])
        caminho_origem = PASTA_PDFS / f"{origem}.pdf"
        if not caminho_origem.exists():
            continue
        texto = texto_do_pdf(caminho_origem)

        for nome_campo, campo in caso["campos"].items():
            if "motivo" in campo and campo["motivo"] not in MOTIVOS_VALIDOS:
                problemas.append(
                    f"{caso['id']}.{nome_campo}: motivo '{campo['motivo']}' invalido; "
                    f"use um de {sorted(MOTIVOS_VALIDOS)}"
                )
            evidencia = campo["evidencia"]
            if evidencia is None:
                if campo["valor"] is not None or "motivo" not in campo:
                    problemas.append(
                        f"{caso['id']}.{nome_campo}: sem evidencia, entao valor deve ser null "
                        "e o motivo deve ser informado"
                    )
            elif evidencia not in texto:
                problemas.append(
                    f"{caso['id']}.{nome_campo}: evidencia '{evidencia}' nao encontrada no PDF"
                )

    if problemas:
        print(f"[FALHA] {len(problemas)} problema(s) no gabarito:")
        for problema in problemas:
            print(f"  - {problema}")
        sys.exit(1)

    print(f"[OK] Gabarito consistente: {len(gabarito)} casos, todas as evidencias conferidas.")


if __name__ == "__main__":
    main()
