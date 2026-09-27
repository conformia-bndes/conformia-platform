# Guia de Inicio Rapido (Quickstart)

Este guia orienta a inicialização e a execução do ambiente local de desenvolvimento da plataforma Conform.IA BNDES.

---

## 1. Pré-requisitos do Sistema

Certifique-se de possuir instalado em sua estacao de trabalho:

- **Docker Engine** >= 24.0 e **Docker Compose Plugin** >= 2.20
- **Make** (utilitario de automacao de comandos)
- **Astral `uv`** >= 0.5.0 (gerenciador de dependências e workspace Python ultrarrápido) ou Python 3.11+
- **Node.js** >= 20.0 e **npm** >= 10.0 (para desenvolvimento na camada frontend)

---

## 2. Inicialização Rápida em 3 Passos

### Passo 1: Preparacao do Ambiente

Execute o comando de preparação para criar o arquivo `.env` e sincronizar as dependências:

=== "Com Make"
`bash
    make setup
    `

=== "Com Astral uv e npm"
`bash
    cp .env.example .env
    uv sync --all-packages --all-extras
    cd frontend && npm install
    `

### Passo 2: Subir a Infraestrutura Conteinerizada

Inicialize a stack completa de servicos (PostgreSQL, Redis, MinIO, Backend API, Worker e Frontend SPA):

```bash
make up
```

### Passo 3: Verificação dos Pontos de Acesso

Após a inicialização, os serviços estarão disponíveis nas seguintes portas locais:

| Servico                        | URL / Ponto de Acesso                                                      | Credenciais Padrao                                                  |
| :----------------------------- | :------------------------------------------------------------------------- | :------------------------------------------------------------------ |
| **Frontend SPA**               | [http://localhost:5173](http://localhost:5173)                             | Acesso direto                                                       |
| **Backend API (Swagger Docs)** | [http://localhost:8000/docs](http://localhost:8000/docs)                   | OpenAPI interativo                                                  |
| **Healthcheck da API**         | [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health) | Retorno JSON com status dos servicos                                |
| **MinIO Console**              | [http://localhost:9001](http://localhost:9001)                             | User: `conformia_minio_admin`<br>Pass: `conformia_minio_secret`     |
| **PostgreSQL 16**              | `localhost:5432`                                                           | DB: `conformia_db`<br>User: `postgres` / Pass: `conformia_password` |
| **Redis 7**                    | `localhost:6379`                                                           | Broker Celery                                                       |

---

## 3. Comandos Essenciais do Dia a Dia

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

# Encerrar todos os contêineres da stack
make down
```
