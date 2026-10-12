# Guia de Inicio Rapido (Quickstart)

Este guia orienta a inicialização e a execução do ambiente local de desenvolvimento da plataforma Conform.IA BNDES.

---

## 1. Pré-requisitos do Sistema

Certifique-se de possuir instalado em sua estacao de trabalho:

- **Docker Engine** >= 24.0 e **Docker Compose Plugin** >= 2.20
- **Make** (utilitario de automacao de comandos)
- **Astral `uv`** >= 0.5.0 (gerenciador de dependências e workspace Python ultrarrápido) ou Python 3.11+
- **Node.js** >= 22.0 e **npm** >= 10.0 (para desenvolvimento na camada frontend)

---

## 2. Inicialização Rápida em 3 Passos

### Passo 1: Preparacao do Ambiente

Gere o arquivo `.env` com segredos aleatorios (nenhuma credencial e versionada; o `.env` esta no `.gitignore`):

```bash
make env
```

### Passo 2: Subir a Infraestrutura Conteinerizada

Inicialize a stack completa (PostgreSQL, Redis, MinIO, Backend API, Worker e Frontend SPA) e aguarde
todos os servicos ficarem saudaveis:

```bash
make up
```

### Passo 3: Teste de Fumaca

Valida o caminho completo upload -> fila Redis -> worker Celery -> estado da tarefa:

```bash
make smoke   # deve terminar com "OK - ambiente sobe e processa pela fila."
```

### Passo 4: Pontos de Acesso

| Servico                        | URL / Ponto de Acesso                                                      | Credenciais                                    |
| :---

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

# Validar o ambiente (upload -> fila -> worker)
make smoke

# Encerrar todos os contêineres da stack
make down

# Apagar tambem os volumes (reset total; necessario ao regenerar o .env)
make clean
```
