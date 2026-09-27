# Diretrizes de Contribuicao - Conform.IA BNDES

O projeto Conform.IA BNDES adota normas tecnicas rigorosas de padronizacao, automacao e qualidade de engenharia. Todas as contribuicoes devem aderir aos protocolos detalhados neste documento antes de serem integradas a branch principal.

---

## 1. Fluxo de Trabalho e Estrategia de Ramificacao (Branching)

1. **Rastreabilidade**: Todas as alteracoes devem estar vinculadas a uma Issue cadastrada ou a um requisito formal da Consulta Publica BNDES no 01/2025.
2. **Nomenclatura de Branches**: Crie branches de trabalho a partir da branch `main` utilizando os prefixos padronizados:
   - `feat/descricao-curta`: Novas funcionalidades do pipeline IDP, motor de regras ou interface.
   - `fix/descricao-curta`: Correcao de falhas funcionais ou bugs em regras.
   - `chore/descricao-curta`: Manutencao de infraestrutura, Docker, dependencias e automacoes.
   - `docs/descricao-curta`: Alteracoes na base de documentacao tecnica MkDocs.
3. **Submissao de Pull Request**: Todo Pull Request deve ser submetido contra a branch `main`, acompanhado do preenchimento integral do checklist de Definition of Done (DoD).

---

## 2. Padronizacao de Commits (Conventional Commits)

O historico do repositorio deve seguir estritamente o padrao **Conventional Commits**, com proibicao absoluta do uso de emojis:

```text
<tipo>[escopo opcional]: <descricao concisa em letras minusculas>
```

### Tipos Permitidos
- `feat`: Adicao de nova funcionalidade.
- `fix`: Correcao de defeito ou inconsistencia.
- `docs`: Modificacoes exclusivas na documentacao tecnica.
- `chore`: Atualizacoes de dependencias, scripts de automacao ou infraestrutura.
- `refactor`: Refatoracao de codigo sem alteracao de comportamento observavel.
- `test`: Criacao ou ajuste de suites de teste ou benchmarks de Evals.
- `style`: Ajustes estritos de formatacao de codigo (espacamento, linter).

**Exemplo de Commit Valido:**
`feat(idp): implementa extracao tabular nativa via pdfplumber`

---

## 3. Padroes de Codigo e Engenharia

- **Backend (Python 3.11+)**: Formatacao via Black (comprimento de linha de 100 caracteres) e verificacao via Flake8. Tipagem estrita com anotacoes de tipo em todas as funcoes publicas e validacao de dados via Pydantic v2.
- **Frontend (React 18 / TypeScript)**: Componentizacao modular, TypeScript em modo estrito (`strict: true`), icones via Lucide React e estilizacao utilitaria via Tailwind CSS.
- **Regras de Conformidade (`rules/schemas/`)**: Regras declarativas estruturadas em JSON compativeis com o schema formal `rule_schema.json`.
- **Harness e Evals (`evals/`)**: Nenhum commit que altere extracao ou avaliacao pode introduzir falsos positivos no benchmark `eval_pipeline.py`.

---

## 4. Validacao Local Obrigatoria Antes de Submissao

Antes de submeter o PR, o desenvolvedor deve rodar localmente:
```bash
# Validacao de suites de teste
make test

# Validacao de regressao de Evals
make eval

# Validacao de linters e formatacao
make lint
```
