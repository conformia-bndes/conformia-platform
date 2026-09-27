# Changelog

Todas as mudancas notaveis neste projeto serao documentadas neste arquivo.

O formato e baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semantico](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Adicionado
- Setup fundacional do monorepo Conform.IA BNDES Platform.
- Backend FastAPI com modulos para IDP, Rules Engine, AI Maker-Checker e DB.
- Integracao de armazenamento de objetos MinIO para ingestao de documentos.
- Pipeline de processamento assincrono Celery com broker Redis.
- Motor de regras deterministicas com suporte a regex_patterns e validade temporal.
- Pipeline de benchmarks continuos em evals/eval_pipeline.py.
- Frontend SPA com React 18, TypeScript, Tailwind CSS e Lucide Icons.
- Suite de testes Vitest para o frontend.
- Migracoes estruturadas de banco de dados via Alembic.
- Camada de autenticacao e seguranca baseline com API Key.
- Configuracao de infraestrutura Docker Compose multi-container.
- Documentacao tecnica completa com MkDocs Material e ADRs.
- Governanca de repositorio com CODEOWNERS, templates de issue/PR, dependabot e workflows CI/CD.
