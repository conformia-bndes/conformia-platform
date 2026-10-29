# Changelog

Todas as mudancas notaveis neste projeto serao documentadas neste arquivo.

O formato e baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semantico](https://semver.org/lang/pt-BR/).

## [0.2.0](https://github.com/conformia-bndes/conformia-platform/compare/v0.1.0...v0.2.0) (2026-10-29)


### Adicionado

* **api:** implementar endpoint de consulta de processamento e extracao ([#22](https://github.com/conformia-bndes/conformia-platform/issues/22)) ([29fdda6](https://github.com/conformia-bndes/conformia-platform/commit/29fdda6bdff3d270b14374c031cda1c29afd82c3))
* **audit:** registrar SHA-256 do upload na trilha de auditoria ([863985c](https://github.com/conformia-bndes/conformia-platform/commit/863985c8cd5d17f5bd306f96a47e19457c419c8f))
* **auth:** identidade por chave de API pessoal com perfis ([8fcef81](https://github.com/conformia-bndes/conformia-platform/commit/8fcef81142a1434985d49955c2ef0db0c20085ba))
* **backend:** implementar modelos e api de processamento ([#22](https://github.com/conformia-bndes/conformia-platform/issues/22)) ([#31](https://github.com/conformia-bndes/conformia-platform/issues/31)) ([e39217b](https://github.com/conformia-bndes/conformia-platform/commit/e39217b62665ee7231a20d48e35566a89114f601))
* **docs:** aprimorar documentação com novos plugins e melhorias de interatividade ([b9e17ee](https://github.com/conformia-bndes/conformia-platform/commit/b9e17eede27663aeeb014d74e0a85754b5ec2c17))
* **idp:** implementar parser estruturado de entidades e evidencias documentais ([8d97c24](https://github.com/conformia-bndes/conformia-platform/commit/8d97c24c316fe102052cc1fadee217d0a3e2760a))
* **idp:** valida e integra pipeline de PDF nativo e digitalizado (OCR Tesseract) ([4fbcdca](https://github.com/conformia-bndes/conformia-platform/commit/4fbcdca153c12bd7da17c11b27971bc0dcd4f4dd))
* **mlops:** relatorio de evals, rastreio no MLflow e testes de LLM ([4c70449](https://github.com/conformia-bndes/conformia-platform/commit/4c70449daf68a16ae5ced3edf4a6fde0c1baa41a))
* **review:** revisao humana Maker-Checker com segregacao de funcoes ([6adb60f](https://github.com/conformia-bndes/conformia-platform/commit/6adb60fe972933b6659f4788fd3d0641c2486aa0))
* revisao humana Maker-Checker com chaves de API pessoais (RF09) ([0c4a9fe](https://github.com/conformia-bndes/conformia-platform/commit/0c4a9fee410eb5bc1d3e689aa835fd18f4650676))
* **schemas:** adicionar modelos pydantic v2 para extracao e documentos ([fd53f14](https://github.com/conformia-bndes/conformia-platform/commit/fd53f1466e0bd0c80c64f08858aa26e4118c8ca5))
* **toolchain:** integrar astral uv no workspace, dockerfile, makefile e ci ([8e5f52f](https://github.com/conformia-bndes/conformia-platform/commit/8e5f52f8176d47702f56dbd8c024e1e4ca73d189))
* **ui:** adotar design system minimalista e premium estilo apple para documentacao ([b22a889](https://github.com/conformia-bndes/conformia-platform/commit/b22a8893874f00dd914160abee159e9f3a8b94a3))
* **ui:** aprimorar landing page com hero section, bento grid, pipeline interativo e novo design system ([8f86922](https://github.com/conformia-bndes/conformia-platform/commit/8f86922542df7de8b0a34b83eeefd43281c38d5b))


### Corrigido

* **ai:** Maker-Checker fail-closed sem respostas simuladas ([dcd939c](https://github.com/conformia-bndes/conformia-platform/commit/dcd939c2c44b4f6bd85125dd61c1edddd196dd08))
* **backend:** inicializar storage_path para garantir fallback seguro quando minio estiver offline ([f79a612](https://github.com/conformia-bndes/conformia-platform/commit/f79a612a4a7f53cbaf3c74c879fc92eac3d7bda9))
* **ci:** configurar black com pyproject e migrar gitleaks para cli open-source ([fba27c8](https://github.com/conformia-bndes/conformia-platform/commit/fba27c831ac5b5ab7bfd2b6c7a5a20bb84287395))
* **ci:** remover filtros de caminho para evitar jobs pulados e estilizar botao do repositorio ([d16a716](https://github.com/conformia-bndes/conformia-platform/commit/d16a71661ec3a5d3abde37013a1c509df426c236))
* conformidade fail-closed (validade, tipologia, LLM e frontend) e plano de entrega 05/12 ([2627e87](https://github.com/conformia-bndes/conformia-platform/commit/2627e8730533bdce9f0dc5a0fe96510a40676f65))
* correcoes de ci lint, lockfiles, seguranca, alembic e regras de conformidade ([19b593a](https://github.com/conformia-bndes/conformia-platform/commit/19b593a806fff9ef03b9b356970b20398b9389aa))
* **db:** fixar driver psycopg2 na URL do PostgreSQL ([c6a8171](https://github.com/conformia-bndes/conformia-platform/commit/c6a817167c91f548f0d0b9343f40a7393d2b037a))
* **docs:** atualizar comando de sincronização de dependências para incluir todos os pacotes e extras ([5e2baae](https://github.com/conformia-bndes/conformia-platform/commit/5e2baaef59a51f20feeedf5977e22951ef33fb8b))
* **docs:** configurar pipeline oficial de deploy para github pages e ajustar nav ([e5a1d32](https://github.com/conformia-bndes/conformia-platform/commit/e5a1d32c352ca967b25ef83cb6e71178add151b7))
* **frontend:** remover dados simulados e exibir erros reais ([3c5f0e8](https://github.com/conformia-bndes/conformia-platform/commit/3c5f0e808f4f68be477c42c2b74007817aeba6e3))
* **rules:** exigir validade e escopar regras pela tipologia documental ([bcc3d7f](https://github.com/conformia-bndes/conformia-platform/commit/bcc3d7f90ef3275a89de6bd7e3cf8094aec22681))


### Seguranca

* **auth:** gravar a chave gerada em arquivo privado, fora do terminal ([f735c68](https://github.com/conformia-bndes/conformia-platform/commit/f735c68e0a6736e4f253eb553662910eae9ac568))
* **auth:** hash PBKDF2 com sal para as chaves de API pessoais ([9910502](https://github.com/conformia-bndes/conformia-platform/commit/991050255e21e528d86f13ec495bacfdbdddd05a))
* **deps:** corrigir dependencias com vulnerabilidades conhecidas ([4ca9e64](https://github.com/conformia-bndes/conformia-platform/commit/4ca9e64dbc0679fb52f8a5f5099a74a142db7e47))
* **deps:** elevar versoes minimas declaradas acima das vulneraveis ([0759d2c](https://github.com/conformia-bndes/conformia-platform/commit/0759d2ca7dcb278c4872a27aab7b65b01db15e5b))


### Refatoracao

* **compliance:** servico unico de avaliacao para worker e API ([7c2e00f](https://github.com/conformia-bndes/conformia-platform/commit/7c2e00fe22904acb8bbec4a5f8a74e25c4eb8310))


### Documentacao

* descrever as regras atuais de main e dev ([eb3f00c](https://github.com/conformia-bndes/conformia-platform/commit/eb3f00c2bcf316c4d51ca95fe2f8c36065e57b5f))
* **evals:** adiciona relatorio inicial de falhas do dataset sintetico ([a4238c5](https://github.com/conformia-bndes/conformia-platform/commit/a4238c5a97dd5087e9c3d9168c6a709bcb4cd853))
* **evals:** registra cobertura da verificacao de data ausente no relatorio ([363129f](https://github.com/conformia-bndes/conformia-platform/commit/363129ff1fc7c9ba968e46870678822c26652604))
* manter o texto dentro dos cartoes das grades ([74a7909](https://github.com/conformia-bndes/conformia-platform/commit/74a7909ec92fde44617b362718604073d246cf05))
* ortografia, navegacao por tarefa e guias de DevOps, MLOps e governanca ([beb4613](https://github.com/conformia-bndes/conformia-platform/commit/beb46132cf8e371ca90ddaf68986c1446b71cc9a))
* **planning:** integrar planejamento inicial do projeto e navegacao no mkdocs ([d73d209](https://github.com/conformia-bndes/conformia-platform/commit/d73d2097bc894f8e6a7562b008ad29070358cba9))
* **planning:** plano de entrega, backlog e relatorio de validacao ([ba34a3a](https://github.com/conformia-bndes/conformia-platform/commit/ba34a3a7817ad1e6969f95fd00ebd455ae63b17e))
* **planning:** registrar build estrito da documentacao aprovado ([debed4c](https://github.com/conformia-bndes/conformia-platform/commit/debed4c7bf497e89d66f171307591996cb230c70))
* **portal:** reestruturar documentacao em capitulos modulares, animacoes css e adrs ([f8ffd01](https://github.com/conformia-bndes/conformia-platform/commit/f8ffd01ff95beaf924ae26b95cceb85250d7a116))
* refactor code structure for improved readability and maintainability ([17c4e34](https://github.com/conformia-bndes/conformia-platform/commit/17c4e344d84e209eb088ad652579c7c28e221ee8))
* referencia da API de revisao e planejamento apos decisao D1 ([f744697](https://github.com/conformia-bndes/conformia-platform/commit/f744697f8801e0e614dfdd0ad03a39310a8a2b01))
* Refine documentation in requirements and sprints-roadmap ([b33935e](https://github.com/conformia-bndes/conformia-platform/commit/b33935e6a1adf690ae47d4ad60c13e02987464c8))
* regras atuais de main e dev e texto dentro dos cartoes ([2de4660](https://github.com/conformia-bndes/conformia-platform/commit/2de4660041ea1e0e884fc1c3c686c71038355d73))
* reorganizar a documentacao e alinhar o conteudo ao codigo ([f1f4cfd](https://github.com/conformia-bndes/conformia-platform/commit/f1f4cfd9be0c2784c1b35fd273ae607eb543fafe)), closes [#61](https://github.com/conformia-bndes/conformia-platform/issues/61)
* reorganizar a documentacao, alinhar ao codigo e verificar o site no build ([aee9eda](https://github.com/conformia-bndes/conformia-platform/commit/aee9eda4c6d8c717940abcd1bb0bf2b876373f4f))
* verificar o site gerado e tornar legiveis os fluxos longos ([5093ff6](https://github.com/conformia-bndes/conformia-platform/commit/5093ff6c5c00858711d009b57ca1261b987ab5ac))

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
