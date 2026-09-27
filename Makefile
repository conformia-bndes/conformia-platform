# ==============================================================================
# Conform.IA BNDES Platform - Automacao de Tarefas e Infraestrutura
# ==============================================================================

COMPOSE_FILE := infra/docker-compose.yml
DOCKER_COMPOSE := docker compose -f $(COMPOSE_FILE)

# Deteccao automatica do Astral uv
UV := $(shell command -v uv 2> /dev/null)
PYTHON := $(if $(UV),uv run python,python)
PYTEST := $(if $(UV),uv run pytest,pytest)
BLACK := $(if $(UV),uv run black,black)
FLAKE8 := $(if $(UV),uv run flake8,flake8)
ALEMBIC := $(if $(UV),uv run alembic,alembic)
MKDOCS := $(if $(UV),uv run --with-requirements docs/requirements.txt mkdocs,mkdocs)

.PHONY: help setup up down restart logs ps test lint format eval docs docs-build clean uv-sync uv-lock

help:
	@echo "Comandos disponiveis no Conform.IA BNDES:"
	@echo "  make setup      - Prepara .env e sincroniza dependencias (uv ou pip/npm)"
	@echo "  make uv-sync    - Sincroniza ambiente virtual do workspace via uv"
	@echo "  make uv-lock    - Gera uv.lock e exporta backend/requirements.lock"
	@echo "  make up         - Constroi e inicializa os servicos via infra/docker-compose.yml"
	@echo "  make down       - Encerra e remove todos os conteineres da stack"
	@echo "  make restart    - Reinicia a stack completa"
	@echo "  make logs       - Visualiza logs unificados da aplicacao"
	@echo "  make ps         - Lista status dos conteineres da stack"
	@echo "  make test       - Executa testes automatizados (pytest e vitest)"
	@echo "  make eval       - Executa o pipeline de regressao e Harness Evals"
	@echo "  make lint       - Executa verificacoes de linter (Flake8, Black e ESLint)"
	@echo "  make format     - Formata o codigo do backend com Black"
	@echo "  make docs       - Inicia servidor local de documentacao MkDocs"
	@echo "  make docs-build - Compila documentacao estatica MkDocs"
	@echo "  make clean      - Limpa arquivos temporarios, caches e volumes locais"

setup:
	@test -f .env || cp .env.example .env
	@echo "Arquivo .env configurado."
	@echo "Instalando dependencias locais..."
	$(if $(UV),uv sync --all-packages --all-extras,pip install -e ./backend || true)
	cd frontend && (npm install || true)

uv-sync:
	uv sync --all-packages --all-extras

uv-lock:
	uv lock
	uv export --no-dev --no-emit-project --format requirements-txt -o backend/requirements.lock

up:
	$(DOCKER_COMPOSE) up --build -d
	@echo ""
	@echo "======================================================================"
	@echo "Plataforma Conform.IA BNDES inicializada com sucesso."
	@echo "Frontend SPA:      http://localhost:5173"
	@echo "Backend API Docs:  http://localhost:8000/docs"
	@echo "MinIO Console:     http://localhost:9001 (User: conformia_minio_admin)"
	@echo "======================================================================"

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

lint:
	$(FLAKE8) backend/ --count --max-line-length=100 --statistics
	$(BLACK) --check backend/
	cd frontend && npm run lint

format:
	$(BLACK) backend/

docs:
	$(MKDOCS) serve

docs-build:
	$(MKDOCS) build --strict

clean:
	$(DOCKER_COMPOSE) down -v --remove-orphans
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov frontend/dist site 2>/dev/null || true
