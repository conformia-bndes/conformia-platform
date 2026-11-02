# Testes e Robustez

A confiabilidade do Conform.IA depende de mais do que testes de unidade: o produto decide
conformidade de crédito público, então a API precisa ser segura, estável sob falha de
dependência e previsível sob carga. Esta página reúne os métodos usados, o que cada um pega e o
que foi encontrado ao aplicá-los.

---

## 1. Métodos e onde rodam

| Método | O que pega | Onde roda | Bloqueia o merge? |
| :-- | :-- | :-- | :-- |
| Testes de unidade e integração (pytest, Vitest) | Regressões de comportamento | CI: Backend / Test (3.11 e 3.12), Frontend / Test | Sim |
| Cobertura de autenticação | Rota nova sem autenticação em produção | pytest: `test_api_authentication.py` percorre todas as rotas do OpenAPI | Sim |
| Contrato da API | Timestamps sem fuso, erros não documentados, paginação sem limite | pytest: `test_api_contract.py` | Sim |
| Gate de regressão dos evals | Queda de acurácia e falso positivo | CI: Backend / Evals ([MLOps](mlops.md)) | Sim |
| Fuzzing das regras (Atheris) | Entrada que derruba o motor ou viola invariantes | CI: Backend / Fuzz | Sim |
| Fuzz de contrato da API (Schemathesis) | Respostas 5xx, respostas fora do esquema | CI: Infra / Stack | Sim |
| Resiliência (queda de Redis, MinIO e Postgres) | 500 por dependência fora, healthcheck travado, falta de recuperação | CI: Infra / Stack (`scripts/resilience_test.sh`) | Sim |
| Carga (k6) | Regressão de latência e de erros sob concorrência | CI: Infra / Stack (`tests/load/api.js`, limites folgados) | Sim |
| Scan de imagens (Trivy) | CVEs HIGH/CRITICAL com correção, segredos na imagem | CI: Build do Backend e do Frontend; semanal | Sim |
| Lint de Dockerfiles (hadolint) | Más práticas de build e de execução | CI: Infra / Lint | Sim |
| Auditoria de dependências | Pacotes vulneráveis | CI: Backend / Security, Frontend / Security | Sim |

Tudo isso roda localmente: `make test`, `make eval`, `make resilience`, `make load` e `make scan`.

---

## 2. O que esses testes encontraram

Ao aplicar os métodos acima pela primeira vez, houve achados reais, todos corrigidos e com teste
de regressão:

| Achado | Método | Impacto | Correção |
| :-- | :-- | :-- | :-- |
| `limit=9223372036854775808` em `/documents` e `/compliance/audit-trail` gerava **HTTP 500**; sem limite máximo de página | Schemathesis | Instabilidade e leitura da tabela inteira numa requisição | `limit` de 1 a 200 e `skip` até 1.000.000, em um módulo compartilhado |
| Com o **Postgres** fora do ar, a listagem e o upload respondiam 500 | Resiliência | Erro opaco para o cliente | Erros de conexão viram **503** com `Retry-After`; timeout de conexão de 3 s |
| Com o **MinIO** fora do ar, o health e o upload **não respondiam** | Resiliência | Healthcheck travado derruba o contêiner no orquestrador | Cliente com timeout curto e poucas tentativas; o health usa cliente próprio sem reintentos |
| Com o **Redis** fora do ar, o upload **travava indefinidamente** | Resiliência | Requisição presa, esgotando threads | Limites de reconexão do publicador e do backend de resultados do Celery: 503 em segundos |
| Com 4 workers, **"too many connections"** no Postgres | Carga | Falha sob concorrência | Pool configurável (`DB_POOL_SIZE`, `DB_MAX_OVERFLOW`) com padrão seguro |
| `created_at` saía **sem fuso** (`2026-11-02T04:26:27`) apesar do OpenAPI declarar `date-time` | Schemathesis | Clientes interpretam o horário no fuso errado | Tipo `UTCDateTime`: toda resposta sai com `+00:00` |
| Erro 404 documentado como `{"error": ...}` mas devolvido como `{"detail": ...}`; 401, 403 e 404 não documentados | Schemathesis | Clientes gerados do OpenAPI tratam errado os erros | Modelo `HTTPErrorResponse` e respostas comuns declaradas nas rotas protegidas |
| Imagem do frontend rodava como **root** e com 1 CRITICAL e 2 HIGH (brotli, curl) | Trivy e inspeção | Superfície de ataque | `apk upgrade`, usuário `101`, porta 8080, cabeçalhos de segurança no nginx |
| Imagem do backend com 2 HIGH (pacotes do Python do sistema, sem uso em runtime) | Trivy | CVEs em código que o app não usa | Remoção de `pip`, `setuptools` e `wheel` da imagem de runtime |

---

## 3. Desempenho e escalabilidade

Medido em uma máquina de desenvolvimento (Docker Desktop, 7,6 GB), com a stack completa e o k6 de
`tests/load/api.js` (leituras + 5 uploads/s). São números de referência, não garantias:

| Configuração | Usuários simultâneos | Vazão | p95 leitura | p95 upload | Erros |
| :-- | --: | --: | --: | --: | --: |
| 1 processo (padrão antigo) | 20 | 150 req/s | 142 ms | 453 ms | 0% |
| 1 processo | 100 | 157 req/s (saturado) | 889 ms | 1,8 s | 0% |
| 4 workers, pool 5+5 | 100 | **451 req/s** | 331 ms | 995 ms | 0% |

A vazão de um processo satura perto de 150 req/s e o excedente vira latência; mais workers
escalam quase linearmente (2,9x com 4). Para dimensionar:

- `WEB_CONCURRENCY` (padrão 2 na imagem) define os workers do uvicorn por réplica.
- **Conexões com o banco = (workers + processos do Celery) x (`DB_POOL_SIZE` + `DB_MAX_OVERFLOW`)**
  e precisam ficar abaixo do `max_connections` do Postgres (100 por padrão). O padrão 5+5 permite
  até 8 processos por instância de banco sem ajuste.
- O worker do Celery usa cerca de 900 MB por causa do OCR; dimensione a concorrência dele pela
  memória, não pela CPU.
- A API é sem estado: várias réplicas atrás de um balanceador são possíveis, compartilhando
  Postgres, Redis e MinIO.

### Limitações conhecidas

- Com um serviço **parado** no Docker, a falha de upload leva de 12 a 25 s: o tempo vai para a
  resolução de nome do contêiner parado, que o timeout de conexão não cobre. Em uma queda real
  (serviço no ar e inacessível) o limite é de 2 s por tentativa.
- Os limites do teste de carga no CI são folgados (leitura p95 abaixo de 1,5 s) por causa da
  variação dos runners compartilhados; eles pegam regressões graves, não pequenas.
- Não há teste de longa duração (soak) nem de estresse com falhas simultâneas.
