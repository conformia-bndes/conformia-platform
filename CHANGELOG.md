# Changelog

Todas as mudancas notaveis neste projeto serao documentadas neste arquivo.

O formato e baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semantico](https://semver.org/lang/pt-BR/).

## [0.4.1](https://github.com/conformia-bndes/conformia-platform/compare/v0.4.0...v0.4.1) (2026-11-22)


### Corrigido

* **cd:** injetar envs obrigatorias de Settings na validacao runtime do backend ([f8ff591](https://github.com/conformia-bndes/conformia-platform/commit/f8ff5918fe7a860746db81a41659898b03a25a3c))
* **cd:** injetar envs obrigatorias na validacao runtime do backend ([98a57c5](https://github.com/conformia-bndes/conformia-platform/commit/98a57c5e463dab33f8bf0eb95184121b42ce8d59))
* **cd:** promover correcao da validacao runtime do backend em main ([764df36](https://github.com/conformia-bndes/conformia-platform/commit/764df3637ec4b193ca9e4c332c35e444891fa97f))

## [0.4.0](https://github.com/conformia-bndes/conformia-platform/compare/v0.3.0...v0.4.0) (2026-11-22)


### Adicionado

* **ai:** JSON mode, retentativas e timeout configuravel para provedores de LLM ([cb8e911](https://github.com/conformia-bndes/conformia-platform/commit/cb8e911296ae263b9139390ddaeeb060679d66b0)), closes [#129](https://github.com/conformia-bndes/conformia-platform/issues/129)
* **ai:** provedor de LLM configuravel (OpenRouter), JSON mode e retentativas ([a9359a9](https://github.com/conformia-bndes/conformia-platform/commit/a9359a9db2ca160c68609bf87d51aceb042bb9f9))
* **ai:** tornar a URL base do LLM configuravel (LLM_BASE_URL) ([0615c1d](https://github.com/conformia-bndes/conformia-platform/commit/0615c1d4d9c35a12e19c012885c928895825e78c)), closes [#129](https://github.com/conformia-bndes/conformia-platform/issues/129)
* **demo,docs:** roteiro de demo, provedor LLM e checklist Go/No-Go ([#63](https://github.com/conformia-bndes/conformia-platform/issues/63), [#64](https://github.com/conformia-bndes/conformia-platform/issues/64), [#129](https://github.com/conformia-bndes/conformia-platform/issues/129)) ([657f459](https://github.com/conformia-bndes/conformia-platform/commit/657f459bf7eb0c04fe0c1b870802bd1a5fcd3b6c))
* **demo,docs:** roteiro de demo, provedor LLM e checklist Go/No-Go ([#63](https://github.com/conformia-bndes/conformia-platform/issues/63), [#64](https://github.com/conformia-bndes/conformia-platform/issues/64), [#129](https://github.com/conformia-bndes/conformia-platform/issues/129)) ([79cd973](https://github.com/conformia-bndes/conformia-platform/commit/79cd973c8fe610c1c4848d45d47ba3f9c98b9b7c))
* **frontend:** adicionar entrada em memoria de X-API-Key na sessao (T06c) ([c406237](https://github.com/conformia-bndes/conformia-platform/commit/c4062372ce1c8d59acaed9dc47e66f7e4fd56ad3))
* **frontend:** adicionar polling de processamento, estados vazios e badges de status ([fa01bee](https://github.com/conformia-bndes/conformia-platform/commit/fa01beee4aeb909e7188707f5d126777e18869d9))
* **frontend:** adicionar revisao humana maker-checker e evidencias por pagina (T06b) ([56ddb28](https://github.com/conformia-bndes/conformia-platform/commit/56ddb2855fe8ea929cee33c5e3c650d1b05eb094))
* **frontend:** componentizacao, X-API-Key em memoria e revisao humana (T06b/T06c) ([535cbd8](https://github.com/conformia-bndes/conformia-platform/commit/535cbd86dc446937a95d70a778b9addba226d0c6))
* **infra:** definir limites de recursos, concorrencia e perfil de pr… ([7148804](https://github.com/conformia-bndes/conformia-platform/commit/714880428def5201dd975431b820a95d79d2f3f3))
* **infra:** definir limites de recursos, concorrencia e perfil de producao ([#103](https://github.com/conformia-bndes/conformia-platform/issues/103)) ([d5362ae](https://github.com/conformia-bndes/conformia-platform/commit/d5362ae08f2094b24eea123b14db6a0e655cee1e))
* **smoke:** validar laudo de conformidade e revisao humana no smoke … ([ef761e0](https://github.com/conformia-bndes/conformia-platform/commit/ef761e09f470d0f8c6e4f7a40ca7902bd32e841a))
* **smoke:** validar laudo de conformidade e revisao humana no smoke ([#57](https://github.com/conformia-bndes/conformia-platform/issues/57)) ([a5080ea](https://github.com/conformia-bndes/conformia-platform/commit/a5080ea44aa67340f82d2ca5a7c194526906ca87))


### Corrigido

* **backend:** upgrade apt packages in runtime image build ([a51cb62](https://github.com/conformia-bndes/conformia-platform/commit/a51cb6294ff8adba61bca18ac66a09479735d910))
* **ci:** declarar e atribuir separadamente os segredos do passo de OCR (SC2155) ([e73cde9](https://github.com/conformia-bndes/conformia-platform/commit/e73cde96025fdbc65ed621232ead3d2eb4a8b7dc)), closes [#128](https://github.com/conformia-bndes/conformia-platform/issues/128)
* **ci:** passar as variaveis obrigatorias ao validar o OCR no container ([e7ac57a](https://github.com/conformia-bndes/conformia-platform/commit/e7ac57a731be657181e4e7b6418403c009175689)), closes [#128](https://github.com/conformia-bndes/conformia-platform/issues/128)
* **env:** falhar com mensagem clara quando o .env esta desatualizado … ([4b306a4](https://github.com/conformia-bndes/conformia-platform/commit/4b306a46ee48ca59d98b6a92a72fb04dffd20c16))
* **env:** falhar com mensagem clara quando o .env esta desatualizado ([#101](https://github.com/conformia-bndes/conformia-platform/issues/101)) ([d77c0fd](https://github.com/conformia-bndes/conformia-platform/commit/d77c0fdaa070374abdfd909c03ab1df231dd5ecb))
* **env:** remover o alias --update nao documentado do setup-env ([6b35b2c](https://github.com/conformia-bndes/conformia-platform/commit/6b35b2cc55f49f791128512e9622727a572aa5f7)), closes [#101](https://github.com/conformia-bndes/conformia-platform/issues/101)
* **infra:** invalidar o cache do apk upgrade da imagem do frontend (Trivy) ([7093d82](https://github.com/conformia-bndes/conformia-platform/commit/7093d823937eaadec37f9614f4c05805da9068fb)), closes [#126](https://github.com/conformia-bndes/conformia-platform/issues/126)
* **infra:** invalidar o cache do apk upgrade da imagem do frontend (Trivy) ([9427831](https://github.com/conformia-bndes/conformia-platform/commit/9427831723fced17fb04b825b57a42e15fa66632)), closes [#126](https://github.com/conformia-bndes/conformia-platform/issues/126)
* **infra:** invalidar o cache do apt/apk upgrade das imagens (Trivy) ([4d7c250](https://github.com/conformia-bndes/conformia-platform/commit/4d7c250cdd50f4f7f5bf0f24d2776e97574cccc2))
* **infra:** invalidar o cache do apt/apk upgrade das imagens (Trivy) ([928e5ad](https://github.com/conformia-bndes/conformia-platform/commit/928e5ad9671fdfbcad810af4733627c0ecfb8723))
* **infra:** invalidar tambem o cache do apt-get install da imagem do backend (Trivy) ([4dc0724](https://github.com/conformia-bndes/conformia-platform/commit/4dc07243ccd6e0679572bfb5a0033020144a54ba)), closes [#126](https://github.com/conformia-bndes/conformia-platform/issues/126)
* **infra:** invalidar tambem o cache do apt-get install da imagem do backend (Trivy) ([80d8634](https://github.com/conformia-bndes/conformia-platform/commit/80d8634fb1aba5a7c9c3a6f1677ab0559270be17)), closes [#126](https://github.com/conformia-bndes/conformia-platform/issues/126)
* **rules:** RULE-BNDES-006 nao aprova mais so com CEIS + nada consta ([7a6dce3](https://github.com/conformia-bndes/conformia-platform/commit/7a6dce3acd02370806559700f906e06eeb05aa32))
* **rules:** RULE-BNDES-006 nao aprova so com CEIS + nada consta ([2e4ab1d](https://github.com/conformia-bndes/conformia-platform/commit/2e4ab1d6052f6e724621eb16ea40788fb66cf09a))
* **smoke:** proteger API_USERS com aspas simples e nao engolir erros no make env ([e431400](https://github.com/conformia-bndes/conformia-platform/commit/e43140013f30b6ca0871f3852108b134d116880a)), closes [#127](https://github.com/conformia-bndes/conformia-platform/issues/127)
* **smoke:** validar .env gerado por --setup-env contra Settings em config.py ([#127](https://github.com/conformia-bndes/conformia-platform/issues/127)) ([95d1f35](https://github.com/conformia-bndes/conformia-platform/commit/95d1f35280e1138481b16683640aab098572a51b))


### Seguranca

* **smoke:** eliminar armazenamento em texto claro de chaves no .env e alinhar assercoes ([#57](https://github.com/conformia-bndes/conformia-platform/issues/57)) ([38109c4](https://github.com/conformia-bndes/conformia-platform/commit/38109c402ebcb2897733e592ef19c5823688c3c1))


### Refatoracao

* **frontend:** extrair componentes de UI do App.tsx ([3817a2c](https://github.com/conformia-bndes/conformia-platform/commit/3817a2ce155dd66364b137772cdf7f5e0683eaad))


### Documentacao

* **evals:** reavalia dataset sintetico apos o PR [#44](https://github.com/conformia-bndes/conformia-platform/issues/44) ([f5f286a](https://github.com/conformia-bndes/conformia-platform/commit/f5f286aeb314a2171d8b9560cb8a201a41f9fe58))
* **governance:** ADR-004 protecao de main e revisao por pares ([7b5243d](https://github.com/conformia-bndes/conformia-platform/commit/7b5243d1fd5e9bdd5bd55abb3d029600439c1680))
* **governance:** ADR-004 sobre protecao de main e revisao por pares ([#105](https://github.com/conformia-bndes/conformia-platform/issues/105)) ([658221f](https://github.com/conformia-bndes/conformia-platform/commit/658221fbd782aadecd7b936a97b61df6d49b3884))
* **samples:** adicionar PDFs de CRF, CNDT e licenca ambiental multipagina ([03b7b67](https://github.com/conformia-bndes/conformia-platform/commit/03b7b6746d203dd69e143a6599541d57b4c76107))
* **samples:** adicionar PDFs ficticios de CND conforme e nao conforme para demonstracao ([9b3441f](https://github.com/conformia-bndes/conformia-platform/commit/9b3441f87a945aa0a88c95d95a7b75baa620cb38))

## [0.3.0](https://github.com/conformia-bndes/conformia-platform/compare/v0.2.1...v0.3.0) (2026-11-07)


### Adicionado

* **db:** executar migrations Alembic antes da API e do worker ([c735097](https://github.com/conformia-bndes/conformia-platform/commit/c7350974c895b33651e3e1778e289cf871229c81))
* **db:** executar migrations Alembic antes da API e do worker ([85f54a7](https://github.com/conformia-bndes/conformia-platform/commit/85f54a7694f40642d4723dca77e39ffdd6dd29ad)), closes [#50](https://github.com/conformia-bndes/conformia-platform/issues/50)


### Corrigido

* **infra:** atualizar a base nginx do frontend para corrigir libexpat (Trivy) ([86a05e2](https://github.com/conformia-bndes/conformia-platform/commit/86a05e28297a28748a5a883ffcb8d1e2c37e7150))
* **infra:** atualizar apt e zlib1g na imagem do backend (Trivy) ([7eab2c7](https://github.com/conformia-bndes/conformia-platform/commit/7eab2c7139815619bf2f2f0811cb34b1ba0624ab))
* **infra:** atualizar apt e zlib1g na imagem do backend (Trivy) ([9c615ed](https://github.com/conformia-bndes/conformia-platform/commit/9c615ed3bc3d910bb2db058851eb603fe5adec27))
* **security:** padroes seguros de ENVIRONMENT e DEBUG com opt-in de acesso anonimo ([78c3240](https://github.com/conformia-bndes/conformia-platform/commit/78c324052f1f2811821d09723c139d184cedd68e))
* **security:** padroes seguros de ENVIRONMENT e DEBUG com opt-in de acesso anonimo ([7f660db](https://github.com/conformia-bndes/conformia-platform/commit/7f660db32689b8d171d8acee1e6c346cf123bc9c)), closes [#52](https://github.com/conformia-bndes/conformia-platform/issues/52)


### Documentacao

* corrigir acentuacao, quickstart e escopo dos RFs ([ca8aaf6](https://github.com/conformia-bndes/conformia-platform/commit/ca8aaf6347a4b726d177aabe5a849dbfd7a8be44))
* corrigir acentuacao, quickstart truncado e porta do make docs ([b88755b](https://github.com/conformia-bndes/conformia-platform/commit/b88755b6f3ed7a6b97f67448dfa69e6f534f9856))
* corrigir residuos de acentuacao e esclarecer escopo dos RFs ([c2836a1](https://github.com/conformia-bndes/conformia-platform/commit/c2836a1429bf99d30d4750d560429a64491f8452))

## [0.2.1](https://github.com/conformia-bndes/conformia-platform/compare/v0.2.0...v0.2.1) (2026-11-02)


### Corrigido

* **rules:** termo obrigatorio ausente vai para revisao manual (D2) ([95d08f9](https://github.com/conformia-bndes/conformia-platform/commit/95d08f9bced085131f0ed0e9a5c6ecd155cab72c))
* **rules:** termo obrigatorio ausente vai para revisao manual (D2) ([8129aa2](https://github.com/conformia-bndes/conformia-platform/commit/8129aa2149e5fadb06accd121c897b1a8d7e47f2)), closes [#91](https://github.com/conformia-bndes/conformia-platform/issues/91)
* **storage:** ping do MinIO cria o bucket ausente ([cfd3f13](https://github.com/conformia-bndes/conformia-platform/commit/cfd3f13ccd3811cb17353d4ff9c88f18d4b68f55))
* **upload:** leitura limitada do arquivo e erros sem detalhes internos ([7a937f8](https://github.com/conformia-bndes/conformia-platform/commit/7a937f8ac1c0b4e43263ca12d9bca09ca455b2a6))
* **upload:** limita leitura a MAX_FILE_SIZE+1 e torna genericas as mensagens de erro 400/500 ([844ff48](https://github.com/conformia-bndes/conformia-platform/commit/844ff488e1e05f6df37202a9b7a7fab98c1aced2))


### Documentacao

* registrar as decisoes D2 e D3 ([6b94449](https://github.com/conformia-bndes/conformia-platform/commit/6b94449701e9ed7c7e5bc6bbe7145b8a3464c8c2))
* registrar as decisoes D2 e D3 e fixar o Python 3.11 no Dependabot ([418f7bd](https://github.com/conformia-bndes/conformia-platform/commit/418f7bd4838304e20ca583eaa2a948fd3dc30bc0))

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
