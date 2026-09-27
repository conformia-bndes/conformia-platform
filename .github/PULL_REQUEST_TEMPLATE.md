## Descricao das Alteracoes
<!-- Descreva de forma concisa o objetivo desta alteracao e o contexto no Conform.IA BNDES. -->

## Epico / Requisito Associado
<!-- Relacione a Issue, Epico ou Item da Consulta Publica BNDES no 01/2025 -->
- Issue / Tarefa: #
- Modulo afetado: [ ] Backend Core [ ] IDP Pipeline [ ] AI / Evals [ ] Motor de Regras [ ] Frontend [ ] Infra/DevOps [ ] Documentacao

## Tipo de Mudanca
- [ ] Nova funcionalidade (`feat`)
- [ ] Correcao de bug (`fix`)
- [ ] Refatoracao de codigo (`refactor`)
- [ ] Infraestrutura e CI/CD (`chore` / `infra`)
- [ ] Documentacao (`docs`)
- [ ] Testes ou Evals (`test`)
- [ ] Seguranca / Governanca (`sec`)

---

## Checklist Estrito de Definition of Done (DoD)

Antes de solicitar a revisao, marque todos os itens que foram validados:

### 1. Testes e Qualidade
- [ ] Testes unitarios implementados e cobrindo os novos cenarios.
- [ ] Testes de integracao/regressao executados com sucesso no pipeline local (`make test`).
- [ ] Sem quebra de contratos de API ou esquemas JSON (`rules/schemas`).
- [ ] Cobertura de testes mantida ou aumentada sem mocks indevidos no core de regras.

### 2. Seguranca e Segredos
- [ ] Nenhuma credencial, token, chave de API privada ou arquivo `.env` foi incluido no commit.
- [ ] Validacao estrita de schema de dados em todos os endpoints publicos (Pydantic v2).
- [ ] Tratamento seguro de caminhos de arquivos para evitar Path Traversal em uploads do IDP.
- [ ] Execucao limpa do scanner de vulnerabilidades e segredos.

### 3. Observabilidade e Auditoria
- [ ] Logs estruturados adicionados sem expor dados pessoais sensiveis (PII / LGPD).
- [ ] Trilha de auditoria preservada para decisoes do motor de conformidade e Maker-Checker.
- [ ] Metricas e spans de telemetria adicionados quando aplicavel.

### 4. Documentacao e Compatibilidade
- [ ] README e documentacao tecnica (docs/) atualizados caso rotas, envs ou comandos tenham mudado.
- [ ] Migrations do banco de dados (Alembic) testadas em upgrade e downgrade (quando aplicavel).
- [ ] Interface visual verificada em multiplos tamanhos de tela e sem erros de console.

---

## Como Reproduzir / Testar Localmente
```bash
# Comandos para inicializar e validar esta mudanca:
make up
# Exemplo de chamada ou teste especifico:
curl http://localhost:8000/api/v1/health
```

## Evidencias (Frontend ou Testes)
<!-- Cole aqui outputs de testes bem-sucedidos ou registros de execucao -->
