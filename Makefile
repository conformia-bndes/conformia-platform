# ==============================================================================
# Conform.IA BNDES Platform - Automacao de Tarefas e Infraestrutura
# ==============================================================================

COMPOSE_FILE := infra/docker-compose.yml
DOCKER_COMPOSE := docker compose -f $(COMPOSE_FILE)

.PHONY: help setup up down restart logs ps test lint format eval docs docs-build clean

help:
	@echo "Comandos disponiveis no Conform.IA BNDES:"
	@echo "  make setup      - Copia .env.example para .env e prepara dependencias"
	@echo "  make up         - Constroi e inicializa os servicos via infra/docker-compose.yml"
	@echo "  make down       - Encerra e remove todos os conteineres da stack"
	@echo "  make restart    - Reinicia a stack completa"
	@echo "  make logs       - Visualiza logs unificados da aplicacao"
	@echo "  make ps         - Lista status dos conteineres da stack"
	@echo "  make test       - Executa a suite de testes automatizados do backend"
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
	pip install -e ./backend || true
	cd frontend && (npm install || true)

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

test:
	pytest backend/tests/ -v --cov=backend/app --cov-report=term-missing

eval:
	python evals/eval_pipeline.py

lint:
	flake8 backend/ --count --max-line-length=100 --statistics || true
	black --check backend/ || true
	cd frontend && npm run lint || true

format:
	black backend/

docs:
	mkdocs serve

docs-build:
	mkdocs build --strict

clean:
	$(DOCKER_COMPOSE) down -v --remove-orphans
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov frontend/dist site 2>/dev/null || true
