"""Gera os PDFs sinteticos do dataset de avaliacao (issue #24)."""

from pathlib import Path
import pdfplumber
import pypdfium2 as pdfium
from fpdf import FPDF
from PIL import ImageDraw, ImageFilter

PASTA_SAIDA = Path(__file__).parent / "pdfs"
# ---------------------------------------------------------------------------
# Pedacos de texto da CND Federal
# ---------------------------------------------------------------------------
CND_TITULO_NEGATIVA = (
    "CERTIDÃO NEGATIVA DE DÉBITOS RELATIVOS AOS TRIBUTOS FEDERAIS E À DÍVIDA ATIVA DA UNIÃO"
)
CND_TITULO_POSITIVA = (
    "CERTIDÃO POSITIVA DE DÉBITOS RELATIVOS AOS TRIBUTOS FEDERAIS E À DÍVIDA ATIVA DA UNIÃO"
)
CND_FRASE_REGULAR = (
    "Não constam pendências em seu nome relativas a créditos tributários administrados pela "
    "Secretaria Especial da Receita Federal do Brasil e a inscrições em Dívida Ativa da União."
)
CND_FRASE_PENDENTE = "CONSTA PENDÊNCIA relativa a tributos federais."


def texto_cnd(titulo=CND_TITULO_NEGATIVA, frase=CND_FRASE_REGULAR, linha_validade=None):
    """Monta o texto de uma CND. Se linha_validade for None, a linha da data nao aparece."""
    linhas = [
        "MINISTÉRIO DA FAZENDA",
        "SECRETARIA ESPECIAL DA RECEITA FEDERAL DO BRASIL",
        "PROCURADORIA-GERAL DA FAZENDA NACIONAL",
        titulo,
        "Nome: EMPRESA FICTICIA ALFA LTDA",
        "CNPJ: 12.345.678/0001-90",
        frase,
    ]
    if linha_validade:
        linhas.append(linha_validade)
    return "\n".join(linhas)

    # ---------------------------------------------------------------------------


# Pedacos de texto da CRF do FGTS
# ---------------------------------------------------------------------------
CRF_TITULO = "CERTIFICADO DE REGULARIDADE DO FGTS - CRF"
CRF_SITUACAO_REGULAR = "SITUAÇÃO REGULAR"
CRF_SITUACAO_IRREGULAR = "SITUAÇÃO IRREGULAR"


def texto_crf(titulo=CRF_TITULO, situacao=CRF_SITUACAO_REGULAR, linha_validade=None):
    """Monta o texto de uma CRF. Se linha_validade for None, a linha da data nao aparece."""
    linhas = [
        "CAIXA ECONÔMICA FEDERAL",
        titulo,
        "Inscrição: 12.345.678/0001-90",
        "Razão Social: EMPRESA FICTICIA ALFA LTDA",
        f"A Caixa Econômica Federal certifica que o empregador acima encontra-se em {situacao} "
        "perante o Fundo de Garantia do Tempo de Serviço - FGTS.",
    ]
    if linha_validade:
        linhas.append(linha_validade)
    return "\n".join(linhas)

    # ---------------------------------------------------------------------------


# Casos nativos (um PDF por item)
# ---------------------------------------------------------------------------
CASOS_NATIVOS = [
    {"id": "CND-VALIDA-NAT", "texto": texto_cnd(linha_validade="Válida até: 31/12/2099")},
    {"id": "CND-VENCIDA-NAT", "texto": texto_cnd(linha_validade="Válida até: 01/01/2001")},
    {
        "id": "CND-PENDENTE-NAT",
        "texto": texto_cnd(
            titulo=CND_TITULO_POSITIVA,
            frase=CND_FRASE_PENDENTE,
            linha_validade="Válida até: 31/12/2099",
        ),
    },
    {
        "id": "CND-ILEGIVEL-NAT",
        "texto": texto_cnd(
            titulo=CND_TITULO_NEGATIVA.replace("NEGATIVA", "NEGATTVA"),
            linha_validade="Válida até: 31/12/2099",
        ),
    },
    {"id": "CND-SEM-VALIDADE-NAT", "texto": texto_cnd(linha_validade=None)},
    {
        "id": "CND-VENCIDA-FMTDATA-NAT",
        "texto": texto_cnd(linha_validade="Validade da certidão: 01/01/2001"),
    },
    {
        "id": "CND-VENCIDA-OCRDATA-NAT",
        "texto": texto_cnd(linha_validade="Válida até: 0l/01/2001"),
    },
    {
        "id": "CRF-VALIDA-NAT",
        "texto": texto_crf(linha_validade="Validade: 01/01/2001 a 31/12/2099"),
    },
    {
        "id": "CRF-VENCIDA-NAT",
        "texto": texto_crf(linha_validade="Validade: 01/01/2000 a 01/01/2001"),
    },
    {
        "id": "CRF-PENDENTE-NAT",
        "texto": texto_crf(
            situacao=CRF_SITUACAO_IRREGULAR,
            linha_validade="Validade: 01/01/2001 a 31/12/2099",
        ),
    },
    {
        "id": "CRF-ILEGIVEL-NAT",
        "texto": texto_crf(
            titulo=CRF_TITULO.replace("REGULARIDADE", "REGULARIDDE"),
            linha_validade="Validade: 01/01/2001 a 31/12/2099",
        ),
    },
    {"id": "CRF-SEM-VALIDADE-NAT", "texto": texto_crf(linha_validade=None)},
]
# ---------------------------------------------------------------------------
# Casos digitalizados: mesmo texto de um caso nativo, transformado em imagem
# ---------------------------------------------------------------------------
CASOS_DIGITALIZADOS = [
    {"id": "CND-VALIDA-DIG", "origem": "CND-VALIDA-NAT"},
    {"id": "CND-VENCIDA-DIG", "origem": "CND-VENCIDA-NAT"},
    {"id": "CND-PENDENTE-DIG", "origem": "CND-PENDENTE-NAT"},
    {"id": "CRF-VALIDA-DIG", "origem": "CRF-VALIDA-NAT"},
    {"id": "CRF-VENCIDA-DIG", "origem": "CRF-VENCIDA-NAT"},
    {"id": "CRF-PENDENTE-DIG", "origem": "CRF-PENDENTE-NAT"},
    {"id": "CND-ILEGIVEL-DIG-DATA", "origem": "CND-VALIDA-NAT", "efeito": "borrar_data"},
    {"id": "CND-ILEGIVEL-DIG-TITULO", "origem": "CND-VALIDA-NAT", "efeito": "carimbar_titulo"},
    {"id": "CRF-ILEGIVEL-DIG-DATA", "origem": "CRF-VALIDA-NAT", "efeito": "borrar_data"},
    {"id": "CRF-ILEGIVEL-DIG-TITULO", "origem": "CRF-VALIDA-NAT", "efeito": "carimbar_titulo"},
]

# Parametros fixos do "scanner" simulado (sem sorteio, para o resultado ser sempre igual)
RESOLUCAO_DPI = 150
INCLINACAO_GRAUS = 0.8
DESFOQUE_RAIO = 0.6


def gerar_pdf_nativo(texto, caminho):
    """Escreve o texto num PDF de uma pagina, com texto selecionavel."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=11)
    for linha in texto.splitlines():
        pdf.multi_cell(0, 7, linha, new_x="LMARGIN", new_y="NEXT")
    pdf.output(str(caminho))


def localizar_linha(caminho_nativo, palavras_alvo):
    """Devolve (topo, base) em pontos da primeira palavra encontrada entre as palavras_alvo."""
    with pdfplumber.open(str(caminho_nativo)) as pdf:
        palavras = pdf.pages[0].extract_words()
    for palavra in palavras:
        if palavra["text"] in palavras_alvo:
            return palavra["top"], palavra["bottom"]
    raise ValueError(f"Nenhuma das palavras {palavras_alvo} foi encontrada em {caminho_nativo}")


def borrar_data(imagem, caminho_nativo, escala):
    """Desfoca com forca apenas a faixa horizontal da linha de validade."""
    topo, base = localizar_linha(caminho_nativo, ["Válida", "Validade:"])
    faixa = (0, int(topo * escala) - 5, imagem.width, int(base * escala) + 5)
    trecho = imagem.crop(faixa).filter(ImageFilter.GaussianBlur(6))
    imagem.paste(trecho, faixa)


def carimbar_titulo(imagem, caminho_nativo, escala):
    """Desenha um carimbo escuro por cima do titulo, sem cobrir a linha seguinte."""
    topo, _ = localizar_linha(caminho_nativo, ["CERTIDÃO", "CERTIFICADO"])
    proxima_linha, _ = localizar_linha(caminho_nativo, ["Nome:", "Inscrição:"])
    caixa = (40, int(topo * escala) - 5, imagem.width - 40, int(proxima_linha * escala) - 3)
    desenho = ImageDraw.Draw(imagem)
    desenho.rectangle(caixa, fill=90)


EFEITOS = {"borrar_data": borrar_data, "carimbar_titulo": carimbar_titulo}


def digitalizar(caminho_nativo, caminho_saida, efeito=None):
    """Simula um documento escaneado: vira imagem, inclina um pouco e desfoca levemente.

    Se 'efeito' for informado, estraga uma parte especifica antes (caso ilegivel).
    """
    escala = RESOLUCAO_DPI / 72
    documento = pdfium.PdfDocument(str(caminho_nativo))
    pagina = documento[0]
    imagem = pagina.render(scale=escala).to_pil()
    documento.close()

    imagem = imagem.convert("L")
    if efeito:
        EFEITOS[efeito](imagem, caminho_nativo, escala)
    imagem = imagem.rotate(INCLINACAO_GRAUS, expand=True, fillcolor=255)
    imagem = imagem.filter(ImageFilter.GaussianBlur(DESFOQUE_RAIO))
    imagem.save(caminho_saida, "PDF", resolution=RESOLUCAO_DPI)


def main():
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)
    for caso in CASOS_NATIVOS:
        caminho = PASTA_SAIDA / f"{caso['id']}.pdf"
        gerar_pdf_nativo(caso["texto"], caminho)
        print(f"[OK] {caminho.name}")

    for caso in CASOS_DIGITALIZADOS:
        origem = PASTA_SAIDA / f"{caso['origem']}.pdf"
        caminho = PASTA_SAIDA / f"{caso['id']}.pdf"
        digitalizar(origem, caminho, caso.get("efeito"))
        print(f"[OK] {caminho.name}")


if __name__ == "__main__":
    main()
