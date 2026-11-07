## Descrição das Alterações
<!-- Descreva de forma concisa o objetivo desta alteração e o contexto no Conform.IA BNDES. -->

## Épico / Requisito Associado
<!-- Relacione a Issue, Épico ou Item da Consulta Pública BNDES nº 01/2025 -->
- Issue / Tarefa: #
- Módulo afetado: [ ] Backend Core [ ] IDP Pipeline [ ] AI / Evals [ ] Motor de Regras [ ] Frontend [ ] Infra/DevOps [ ] Documentação

## Tipo de Mudança
- [ ] Nova funcionalidade (`feat`)
- [ ] Correção de bug (`fix`)
- [ ] Refatoração de código (`refactor`)
- [ ] Infraestrutura e CI/CD (`chore` / `infra`)
- [ ] Documentação (`docs`)
- [ ] Testes ou Evals (`test`)
- [ ] Segurança / Governança (`sec`)

---

## Checklist Estrito de Definition of Done (DoD)

Antes de solicitar a revisão, marque todos os itens que foram validados:

### 1. Testes e Qualidade
- [ ] Testes unitários implementados e cobrindo os novos cenários.
- [ ] Testes de integração/regressão executados com sucesso no pipeline local (`make test`).
- [ ] Sem quebra de contratos de API ou esquemas JSON (`rules/schemas`).
- [ ] Cobertura de testes mantida ou aumentada sem mocks indevidos no core de regras.

### 2. Segurança e Segredos
- [ ] Nenhuma credencial, token, chave de API privada ou arquivo `.env` foi incluído no commit.
- [ ] Validação estrita de schema de dados em todos os endpoints públicos (Pydantic v2).
- [ ] Tratamento seguro de caminhos de arquivos para evitar Path Traversal em uploads do IDP.
- [ ] Execução limpa do scanner de vulnerabilidades e segredos.

### 3. Observabilidade e Auditoria
- [ ] Logs estruturados adicionados sem expor dados pessoais sensíveis (PII / LGPD).
- [ ] Trilha de auditoria preservada para decisões do motor de conformidade e Maker-Checker.
- [ ] Métricas e spans de telemetria adicionados quando aplicável.

### 4. Documentação e Compatibilidade
- [ ] README e documentação técnica (docs/) atualizados caso rotas, envs ou comandos tenham mudado.
- [ ] Migrations do banco de dados (Alembic) testadas em upgrade e downgrade (quando aplicável).
- [ ] Interface visual verificada em múltiplos tamanhos de tela e sem erros de console.

---

## Como Reproduzir / Testar Localmente
```bash
# Comandos para inicializar e validar esta mudança:
make up
# Exemplo de chamada ou teste específico:
curl http://localhost:8000/api/v1/health
```

## Evidências (Frontend ou Testes)
<!-- Cole aqui outputs de testes bem-sucedidos ou registros de execução -->
