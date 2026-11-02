"""Parametros de paginacao com limites explicitos, compartilhados pelos endpoints de listagem."""

from typing import Annotated

from fastapi import Query

# Tamanho maximo de pagina: impede ler a tabela inteira numa unica requisicao.
MAX_PAGE_SIZE = 200
# Deslocamento maximo: valores absurdos estouravam o inteiro do banco (HTTP 500).
MAX_OFFSET = 1_000_000

SkipParam = Annotated[
    int, Query(ge=0, le=MAX_OFFSET, description="Registros a pular (paginacao por deslocamento)")
]
LimitParam = Annotated[
    int, Query(ge=1, le=MAX_PAGE_SIZE, description=f"Registros por pagina (maximo {MAX_PAGE_SIZE})")
]
