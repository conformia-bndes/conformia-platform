# Diretrizes de Contribuição - Conform.IA BNDES

O projeto Conform.IA BNDES adota normas técnicas rigorosas de padronização, automação e qualidade de engenharia. Todas as contribuições devem aderir aos protocolos detalhados neste documento antes de serem integradas a branch principal.

---

## 1. Fluxo de Trabalho e Estratégia de Ramificação (Branching)

1. **Rastreabilidade**: Todas as alterações devem estar vinculadas a uma Issue cadastrada ou a um requisito formal da Consulta Publica BNDES no 01/2025.
2. **Nomenclatura de Branches**: Crie branches de trabalho a partir da branch `main` utilizando os prefixos padronizados:
   - `feat/descricao-curta`: Novas funcionalidades do pipeline IDP, motor de regras ou interface.
   - `fix/descricao-curta`: Correção de falhas funcionais ou bugs em regras.
   - `chore/descricao-curta`: Manutenção de infraestrutura, Docker, dependências e automações.
   - `docs/descricao-curta`: Alterações na base de documentação técnica MkDocs.
3. **Submissão de Pull Request**: Todo Pull Request deve ser submetido contra a branch `main`, acompanhado do preenchimento integral do checklist de Definition of Done (DoD).

---

## 2. Padronização de Commits (Conventional Commits)

O histórico do repositório deve seguir estritamente o padrão **Conventional Commits**, com proibição absoluta do uso de emojis:

```text
<tipo>[escopo opcional]: <descricao concisa em letras minusculas>
```

### Tipos Permitidos
- `feat`: Adição de nova funcionalidade.
- `fix`: Correção de defeito ou inconsistência.
- `docs`: Modificações exclusivas na documentação técnica.
- `chore`: Atualizações de dependências, scripts de automação ou infraestrutura.
- `refactor`: Refatoração de código sem alteração de comportamento observavel.
- `test`: Criação ou ajuste de suítes de teste ou benchmarks de Evals.
- `style`: Ajustes estritos de formatação de código (espacamento, linter).

**Exemplo de Commit Valido:**
`feat(idp): implementa extracao tabular nativa via pdfplumber`

---

## 3. Padrões de Código e Engenharia

- **Backend (Python 3.11+)**: Formatação via Black (comprimento de linha de 100 caracteres) e verificação via Flake8. Tipagem estrita com anotações de tipo em todas as funções públicas e validação de dados via Pydantic v2.
- **Frontend (React 18 / TypeScript)**: Componentização modular, TypeScript em modo estrito (`strict: true`), icones via Lucide React e estilização utilitária via Tailwind CSS.
- **Regras de Conformidade (`rules/schemas/`)**: Regras declarativas estruturadas em JSON compatíveis com o schema formal `rule_schema.json`.
- **Harness e Evals (`evals/`)**: Nenhum commit que altere extração ou avaliação pode introduzir falsos positivos no benchmark `eval_pipeline.py`.

---

## 4. Validação Local Obrigatória Antes de Submissão

Antes de submeter o PR, o desenvolvedor deve rodar localmente:
```bash
# Validacao de suites de teste
make test

# Validacao de regressao de Evals
make eval

# Validacao de linters e formatacao
make lint
```
