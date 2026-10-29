# ==============================================================================
# Conform.IA BNDES Platform - Automacao de Tarefas e Infraestrutura
# ==============================================================================

COMPOSE_FILE := infra/docker-compose.yml
# --env-file .env: o compose resolve .env relativo a infra/, entao apontamos a raiz explicitamente
DOCKER_COMPOSE := docker compose --env-file .env -f $(COMPOSE_FILE)

# Deteccao automatica do Astral uv
UV := $(shell command -v uv 2> /dev/null)
PYTHON := $(if $(UV),uv run python,python)
PYTEST := $(if $(UV),uv run pytest,pytest)
BLACK := $(if $(UV),uv run black,black)
FLAKE8 := $(if $(UV),uv run flake8,flake8)
ALEMBIC := $(if $(UV),uv run alembic,alembic)
MKDOCS := $(if $(UV),uv run --frozen mkdocs,mkdocs)

.PHONY: help env setup up smoke down restart logs ps test lint format eval eval-report eval-mlflow llm-eval hooks docs docs-build clean uv-sync uv-lock migrate

help:
	@echo "Comandos disponiveis no Conform.IA BNDES:"
	@echo "  make env        - Gera .env com segredos aleatorios (nao sobrescreve o existente)"
	@echo "  make setup      - Gera .env e sincroniza dependencias (uv ou pip/npm)"
	@echo "  make uv-sync    - Sincroniza ambiente virtual do workspace via uv"
	@echo "  make uv-lock    - Gera uv.lock e exporta backend/requirements.lock"
	@echo "  make up         - Constroi, sobe os servicos e espera ficarem saudaveis"
	@echo "  make smoke      - Teste de fumaca: upload -> fila -> worker -> estado da tarefa"
	@echo "  make down       - Encerra e remove todos os conteineres da stack"
	@echo "  make restart    - Reinicia a stack completa"
	@echo "  make logs       - Visualiza logs unificados da aplicacao"
	@echo "  make ps         - Lista status dos conteineres da stack"
	@echo "  make test       - Executa testes automatizados (pytest e vitest)"
	@echo "  make eval       - Executa o pipeline de regressao e Harness Evals"
	@echo "  make eval-report - Executa os evals e grava evals/reports/eval_report.json"
	@echo "  make eval-mlflow - Executa os evals e registra a execucao no MLflow (mlflow.db)"
	@echo "  make llm-eval   - Testes do Maker-Checker com LLM real via promptfoo (OPENAI_API_KEY)"
	@echo "  make hooks      - Instala os hooks pre-commit no clone local"
	@echo "  make lint       - Executa verificacoes de linter (Flake8, Black e ESLint)"
	@echo "  make format     - Formata o codigo do backend com Black"
	@echo "  make docs       - Inicia servidor local de documentacao MkDocs"
	@echo "  make docs-build - Compila documentacao estatica MkDocs"
	@echo "  make clean      - Limpa arquivos temporarios, caches e volumes locais"

env:
	@bash scripts/setup-env.sh

setup: env
	@echo "Instalando dependencias locais..."
	$(if $(UV),uv sync --all-packages --all-extras,pip install -e ./backend || true)
	cd frontend && (npm install || true)

uv-sync:
	uv sync --all-packages --all-extras

uv-lock:
	uv lock
	uv export --frozen --no-dev --no-emit-project --package conformia-backend --format requirements-txt -o backend/requirements.lock

up: env
	$(DOCKER_COMPOSE) up --build -d --wait --wait-timeout 300
	@echo ""
	@echo "======================================================================"
	@echo "Plataforma Conform.IA BNDES inicializada com sucesso."
	@echo "Frontend SPA:      http://localhost:5173"
	@echo "Backend API Docs:  http://localhost:8000/docs"
	@echo "MinIO Console:     http://localhost:9001  (credenciais em .env: MINIO_ROOT_USER/PASSWORD)"
	@echo "Valide o ambiente: make smoke"
	@echo "======================================================================"

smoke:
	$(DOCKER_COMPOSE) exec -T backend python scripts/smoke_test.py

down:
	$(DOCKER_COMPOSE) down --remove-orphans

restart: down up

logs:
	$(DOCKER_COMPOSE) logs -f

ps:
	$(DOCKER_COMPOSE) ps

migrate:
	$(ALEMBIC) -c backend/alembic.ini upgrade head

test:
	$(PYTEST) backend/tests/ -v --cov=backend/app --cov-report=term-missing
	cd frontend && npm test

eval:
	$(PYTHON) evals/eval_pipeline.py

eval-report:
	mkdir -p evals/reports
	$(PYTHON) evals/eval_pipeline.py --json-report evals/reports/eval_report.json

eval-mlflow:
	mkdir -p evals/reports
	uv run --with mlflow==3.17.2 python evals/eval_pipeline.py --mlflow --json-report evals/reports/eval_report.json

llm-eval:
	mkdir -p evals/reports
	uv run --frozen npx --yes promptfoo@0.125.1 eval -c evals/promptfoo/promptfooconfig.yaml -o evals/reports/promptfoo.json

hooks:
	uvx pre-commit install --install-hooks

lint:
	$(FLAKE8) backend/ --count --max-line-length=100 --statistics
	$(BLACK) --check backend/
	cd frontend && npm run lint

format:
	$(BLACK) backend/

docs:
	$(MKDOCS) serve -a 127.0.0.1:8001

docs-build:
	$(MKDOCS) build --strict

clean:
	$(DOCKER_COMPOSE) down -v --remove-orphans
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov frontend/dist site 2>/dev/null || true
