"""Avalia o pipeline real (extracao + motor de regras) contra o gabarito sintetico (issue #24).

Para cada PDF do dataset:
1. Extracao: confere se cada trecho de evidencia do gabarito aparece no texto extraido.
2. Campos: compara os valores que o sistema expoe hoje com os valores esperados.
3. Classificacao: compara o status obtido com o status esperado e classifica a gravidade do erro.

Os numeros valem apenas para este conjunto sintetico; nao representam desempenho em producao.
"""

import argparse
import json
import os
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "backend"))
# O avaliar.py nao usa banco, fila nem storage; valores descartaveis apenas satisfazem a
# validacao de Settings no import (segredos nao possuem default no codigo).
for _name in (
    "SECRET_KEY",
    "API_KEY",
    "POSTGRES_PASSWORD",
    "MINIO_ROOT_USER",
    "MINIO_ROOT_PASSWORD",
):
    os.environ.setdefault(_name, "eval-only")

from app.idp.extractor import DocumentExtractor  # noqa: E402
from app.services.rules_engine import RulesEngine  # noqa: E402

PASTA = Path(__file__).parent
PASTA_PDFS = PASTA / "pdfs"
ARQUIVO_GABARITO = PASTA / "gabarito.json"
ARQUIVO_RESULTADO = PASTA / "resultados" / "resultado.json"

# Tipo de documento que cada regra confirma quando todas as palavras-chave sao encontradas
TIPO_POR_REGRA = {"RULE-BNDES-001": "CND_FEDERAL", "RULE-BNDES-002": "CRF_FGTS"}


def normalizar_espacos(texto):
    """Junta espacos e quebras de linha em um so espaco, para comparar trechos."""
    return " ".join(texto.split())


def campos_obtidos(resultado, regra):
    """Traduz a saida do motor de regras para os mesmos 4 campos do gabarito.

    O motor nao devolve campos estruturados; usamos o que ele expoe em 'evidence'.
    None significa que o sistema nao informou aquele valor.
    """
    evidencia = resultado.get("evidence", {})
    if evidencia.get("missing_keywords") or evidencia.get("matched_anti_keywords"):
        tipo = None  # o motor parou antes de confirmar o tipo do documento
    else:
        tipo = TIPO_POR_REGRA.get(regra)
    return {
        "tipo_documento": tipo,
        "cnpj": None,  # o motor nao extrai o valor do CNPJ
        "validade": evidencia.get("validity_date"),
        "pendencia": bool(evidencia.get("matched_anti_keywords")),
    }


def comparar_campo(esperado, obtido):
    """Classifica a comparacao de um campo."""
    if esperado is None and obtido is None:
        return "correto"
    if esperado is None:
        return "valor_indevido"  # o sistema informou um valor que nao pode ser provado
    if obtido is None:
        return "nao_extraido"
    return "correto" if esperado == obtido else "divergente"


def gravidade(esperado, obtido):
    """Gravidade de um erro de classificacao (ver plano do dataset)."""
    if esperado == obtido:
        return None
    if obtido == "COMPLIANT":
        return "critico"  # falso positivo: aprovou o que nao deveria
    if esperado == "NON_COMPLIANT" and obtido == "MANUAL_REVIEW_REQUIRED":
        return "seguro"
    return "custo_operacional"


def causa_provavel(caso, comparacoes):
    """Aponta o campo que explica um erro de classificacao."""
    esperados = caso["campos"]
    if esperados["tipo_documento"]["valor"] is None:
        return "titulo_ilegivel_ou_com_erro"
    if comparacoes["pendencia"] != "correto":
        return "pendencia_nao_detectada"
    if esperados["validade"]["valor"] is None:
        return "validade_ausente_ou_ilegivel"
    if comparacoes["validade"] == "nao_extraido":
        return "validade_nao_reconhecida"
    if comparacoes["validade"] == "divergente":
        return "validade_lida_errada"
    return "outra"


def avaliar_caso(caso, extrator, motor):
    caminho = PASTA_PDFS / caso["arquivo"]
    extraido = extrator.extract(str(caminho))
    texto = normalizar_espacos(extraido["full_text"])

    resposta = motor.evaluate({"full_text": extraido["full_text"]}, target_rule_ids=[caso["regra"]])
    resultado = resposta["results"][0]
    status_obtido = resultado["status"]

    obtidos = campos_obtidos(resultado, caso["regra"])
    campos = {}
    for nome, esperado in caso["campos"].items():
        campos[nome] = {
            "esperado": esperado["valor"],
            "obtido": obtidos[nome],
            "resultado": comparar_campo(esperado["valor"], obtidos[nome]),
        }

    evidencias_no_texto = {
        nome: campo["evidencia"] in texto
        for nome, campo in caso["campos"].items()
        if campo["evidencia"] is not None
    }

    erro = gravidade(caso["status_esperado"], status_obtido)
    comparacoes = {nome: c["resultado"] for nome, c in campos.items()}
    return {
        "id": caso["id"],
        "formato": caso["formato"],
        "situacao": caso["situacao"],
        "status_esperado": caso["status_esperado"],
        "status_obtido": status_obtido,
        "acerto": erro is None,
        "gravidade": erro,
        "causa": causa_provavel(caso, comparacoes) if erro else None,
        "campos": campos,
        "evidencias_no_texto": evidencias_no_texto,
    }


def imprimir_resumo(resultados):
    total = len(resultados)
    acertos = sum(r["acerto"] for r in resultados)

    print("\n" + "=" * 78)
    print(f"CLASSIFICACAO: {acertos} de {total} casos com o status esperado")
    for chave in ("formato", "situacao"):
        print(f"\n  Por {chave}:")
        grupos = sorted({r[chave] for r in resultados})
        for grupo in grupos:
            do_grupo = [r for r in resultados if r[chave] == grupo]
            certos = sum(r["acerto"] for r in do_grupo)
            print(f"    {grupo:14} {certos} de {len(do_grupo)}")

    erros = [r for r in resultados if not r["acerto"]]
    print("\n  Erros por gravidade:")
    for nome, qtd in Counter(r["gravidade"] for r in erros).most_common():
        print(f"    {nome:20} {qtd}")
    print("\n  Erros por causa provavel:")
    for nome, qtd in Counter(r["causa"] for r in erros).most_common():
        print(f"    {nome:30} {qtd}")

    print("\nCAMPOS (valor que o sistema expoe x valor esperado):")
    for nome in ("tipo_documento", "cnpj", "validade", "pendencia"):
        contagem = Counter(r["campos"][nome]["resultado"] for r in resultados)
        detalhes = ", ".join(f"{k}={v}" for k, v in sorted(contagem.items()))
        print(f"    {nome:15} {detalhes}")

    print("\nEXTRACAO (trecho de evidencia encontrado no texto extraido):")
    for formato in sorted({r["formato"] for r in resultados}):
        marcas = [
            achou
            for r in resultados
            if r["formato"] == formato
            for achou in r["evidencias_no_texto"].values()
        ]
        print(f"    {formato:14} {sum(marcas)} de {len(marcas)} trechos")

    print("=" * 78)
    print(f"Resultados validos apenas para este conjunto sintetico de {total} documentos.")


def metricas(resultados):
    """Numeros do resumo que sao registrados no MLflow."""
    gravidades = Counter(r["gravidade"] for r in resultados if not r["acerto"])
    trechos = [achou for r in resultados for achou in r["evidencias_no_texto"].values()]
    return {
        "total_casos": len(resultados),
        "acertos": sum(r["acerto"] for r in resultados),
        "erros_criticos": gravidades["critico"],
        "erros_seguros": gravidades["seguro"],
        "erros_custo_operacional": gravidades["custo_operacional"],
        "trechos_encontrados": sum(trechos),
        "trechos_total": len(trechos),
    }


def commit_atual():
    """Hash do commit em que a avaliacao rodou (None fora de um repositorio Git)."""
    try:
        saida = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=RAIZ, check=True
        )
        return saida.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def registrar_no_mlflow(resultados):
    """Registra a execucao no MLflow, como o evals/eval_pipeline.py (docs/engineering/mlops.md)."""
    try:
        import mlflow
    except ImportError as exc:
        raise SystemExit(
            "MLflow nao instalado. Execute com: "
            "uv run --with mlflow==3.17.2 python evals/sintetico/avaliar.py --mlflow"
        ) from exc
    import pytesseract

    if not os.environ.get("MLFLOW_TRACKING_URI"):
        mlflow.set_tracking_uri(f"sqlite:///{RAIZ / 'mlflow.db'}")
    mlflow.set_experiment("conformia-evals-sintetico")
    with mlflow.start_run(run_name=f"sintetico-{datetime.now():%Y-%m-%d}"):
        mlflow.log_params(
            {
                "git_commit": commit_atual() or "desconhecido",
                "tesseract": str(pytesseract.get_tesseract_version()),
                "selecao_de_regra": "gabarito (target_rule_ids)",
            }
        )
        mlflow.log_metrics(metricas(resultados))
        mlflow.log_artifact(str(ARQUIVO_RESULTADO))
    print("Execucao registrada no MLflow (experimento 'conformia-evals-sintetico').")


def main(usar_mlflow=False):
    gabarito = json.loads(ARQUIVO_GABARITO.read_text(encoding="utf-8"))
    faltando = [c["arquivo"] for c in gabarito if not (PASTA_PDFS / c["arquivo"]).exists()]
    if faltando:
        print(f"[ERRO] {len(faltando)} PDF(s) nao encontrados. Rode antes:")
        print("  uv run python evals/sintetico/gerar_dataset.py")
        sys.exit(1)

    extrator = DocumentExtractor()
    motor = RulesEngine()
    resultados = []
    for caso in gabarito:
        r = avaliar_caso(caso, extrator, motor)
        resultados.append(r)
        marca = "OK  " if r["acerto"] else "ERRO"
        detalhe = "" if r["acerto"] else f"  [{r['gravidade']}: {r['causa']}]"
        print(
            f"[{marca}] {r['id']:26} esperado={r['status_esperado']:22} "
            f"obtido={r['status_obtido']}{detalhe}"
        )

    imprimir_resumo(resultados)

    ARQUIVO_RESULTADO.parent.mkdir(parents=True, exist_ok=True)
    saida = {
        "executado_em": datetime.now().isoformat(timespec="seconds"),
        "total_casos": len(resultados),
        "casos": resultados,
    }
    ARQUIVO_RESULTADO.write_text(json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Resultado detalhado salvo em {ARQUIVO_RESULTADO.relative_to(RAIZ)}")
    if usar_mlflow:
        registrar_no_mlflow(resultados)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Avalia o pipeline contra o gabarito sintetico.")
    parser.add_argument("--mlflow", action="store_true", help="Registra a execucao no MLflow")
    args = parser.parse_args()
    main(usar_mlflow=args.mlflow)
