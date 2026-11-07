# Guia de Início Rápido (Quickstart)

Este guia orienta a inicialização e a execução do ambiente local de desenvolvimento da plataforma Conform.IA BNDES, do clone do repositório ao teste de fumaça.

---

## 1. Pré-requisitos do Sistema

Certifique-se de possuir instalado em sua estação de trabalho:

- **Docker Engine** >= 24.0 e **Docker Compose Plugin** >= 2.20 (necessário para `up --wait`)
- **Make** e **Bash** (no Windows, use WSL2 ou Git Bash)
- **Astral `uv`** >= 0.5.0 (gerenciador de dependências e workspace Python ultrarrápido) ou Python 3.11+, apenas para desenvolvimento fora do Docker
- **Node.js** >= 22.0 e **npm** >= 10.0, apenas para desenvolvimento na camada frontend

---

## 2. Inicialização Rápida em 3 Passos

### Passo 1: Preparação do Ambiente

Gere o arquivo `.env` com segredos aleatórios (nenhuma credencial é versionada; o `.env` está no `.gitignore`):

```bash
make env
```

O comando copia `.env.example` para `.env` trocando cada `CHANGE_ME` por um valor aleatório. As senhas ficam no seu `.env` (por exemplo, o login do console MinIO é `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD`). `make up` executa `make env` antes, portanto este passo pode ser omitido.

### Passo 2: Subir a Infraestrutura Conteinerizada

Inicialize a stack completa (PostgreSQL, Redis, MinIO, Backend API, Worker e Frontend SPA) e aguarde
todos os serviços ficarem saudáveis:

```bash
make up
```

### Passo 3: Teste de Fumaça

Valida o caminho completo upload -> fila Redis -> worker Celery -> estado da tarefa:

```bash
make smoke   # deve terminar com "OK - ambiente sobe e processa pela fila."
```

Sem Make, os comandos equivalentes são:

```bash
bash scripts/setup-env.sh
docker compose --env-file .env -f infra/docker-compose.yml up --build -d --wait
docker compose --env-file .env -f infra/docker-compose.yml exec -T backend python scripts/smoke_test.py
```

!!! note "O `--env-file .env` é obrigatório"
    O Compose resolve o `.env` relativo à pasta `infra/`, não à raiz do repositório.

---

## 3. Pontos de Acesso

Após a inicialização, os serviços ficam disponíveis nas portas locais abaixo. As credenciais não são fixas: ficam no `.env` gerado por `make env`.

| Serviço                        | URL / Ponto de Acesso                                                       | Observação                                         |
| :----------------------------- | :-------------------------------------------------------------------------- | :------------------------------------------------- |
| **Frontend SPA**               | [http://localhost:5173](http://localhost:5173)                              | Painel do analista                                 |
| **Backend API (Swagger Docs)** | [http://localhost:8000/docs](http://localhost:8000/docs)                    | OpenAPI interativo                                 |
| **Healthcheck da API**         | [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health) | JSON com o estado de PostgreSQL, Redis e MinIO     |
| **MinIO Console**              | [http://localhost:9001](http://localhost:9001)                              | Credenciais em `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` no `.env` |
| **PostgreSQL 16**              | `localhost:5432`                                                            | Banco relacional (porta ajustável por `POSTGRES_PORT`) |
| **Redis 7**                    | `localhost:6380`                                                            | Broker Celery e cache (porta no host)              |
| **Documentação (MkDocs)**      | [http://127.0.0.1:8001](http://127.0.0.1:8001)                              | Servida localmente por `make docs`                 |

!!! note "Sobre a imagem do MinIO"
    O repositório oficial `minio/minio` foi arquivado e as imagens deixaram de ser publicadas no Docker Hub. O compose usa o fork mantido `pgsty/minio` (variável `MINIO_IMAGE`). Fixe uma tag/digest na variável após validar no seu ambiente.

---

## 4. Teste de Fumaça em Detalhe

`make smoke` roda `backend/scripts/smoke_test.py` dentro do container `backend` (somente
biblioteca padrão do Python, sem fixtures: o PDF é gerado pelo próprio script) e valida:

1. `GET /api/v1/health` retorna `healthy` (PostgreSQL, Redis e MinIO respondendo);
2. `POST /api/v1/documents/upload` retorna `201` com um `task_id` (tarefa despachada à fila);
3. `GET /api/v1/documents/tasks/{task_id}` evolui para `SUCCESS` (só ocorre se o **worker**
   consumiu a fila);
4. `GET /api/v1/documents/{id}` retorna `status: COMPLETED`.

Saída esperada (resumida):

```text
[smoke] 1/4 health OK: {'database': 'healthy', 'redis': 'healthy', 'minio': 'healthy'}
[smoke] 2/4 upload OK: document_id=... task_id=...
[smoke]      estado da tarefa: STARTED
[smoke]      estado da tarefa: SUCCESS
[smoke] 4/4 documento COMPLETED (paginas: 1)
[smoke] OK - ambiente sobe e processa pela fila.
```

O código de saída é `0` em caso de sucesso e `1` em qualquer falha (inclusive worker parado
ou Redis fora do ar). Para repetir manualmente com `curl`:

```bash
curl -s -F "file=@documento.pdf" http://localhost:8000/api/v1/documents/upload   # -> id e task_id
curl -s http://localhost:8000/api/v1/documents/tasks/<task_id>                   # -> state
curl -s http://localhost:8000/api/v1/documents/<id>                              # -> status
```

Estados da tarefa: `PENDING` (na fila), `STARTED`, `RETRY`, `SUCCESS`, `FAILURE`. O Celery não
distingue um `task_id` inexistente de uma tarefa ainda na fila (ambos `PENDING`).

---

## 5. Comandos Essenciais do Dia a Dia

```bash
# Executar todos os testes automatizados (backend + frontend)
make test

# Executar o benchmark contínuo de Harness Evals
make eval

# Executar linters (Black, Flake8 e ESLint)
make lint

# Formatar o código-fonte Python
make format

# Visualizar logs consolidados em tempo real
make logs

# Validar o ambiente (upload -> fila -> worker)
make smoke

# Encerrar todos os contêineres da stack
make down

# Apagar também os volumes (reset total; necessário ao regenerar o .env)
make clean
```

### Dependências locais (opcional)

Para trabalhar fora do Docker:

```bash
make setup   # gera .env + uv sync + npm install
uv run pytest backend/tests/ -v
uv run python evals/eval_pipeline.py
```

---

## 6. Problemas Comuns

| Sintoma                                              | Causa e solução                                                                                                                       |
| :--------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------ |
| `Segredos nao configurados: ... CHANGE_ME`           | `.env` copiado à mão. Rode `bash scripts/setup-env.sh --force`.                                                                       |
| `password authentication failed` no Postgres / MinIO | Volumes antigos com outras senhas. Rode `make clean` e depois `make up` (apaga os dados locais).                                      |
| `make up` expira esperando `backend` saudável        | Veja `docker compose --env-file .env -f infra/docker-compose.yml logs backend`; `/api/v1/health` mostra qual serviço está `degraded`. |
| `port is already allocated`                          | Ajuste `*_PORT` no `.env` (ex.: `POSTGRES_PORT=5433`).                                                                                |
| Upload retorna `503`                                 | Redis ou MinIO indisponível; confira `make ps` e `/api/v1/health`.                                                                    |
