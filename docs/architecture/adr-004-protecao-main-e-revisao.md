# ADR-004: Nível de Proteção da Branch `main` e Revisão por Pares

## Metadados

- **Status**: Aprovado
- **Data**: 2026-11-16
- **Autores**: Conform.IA Engineering Team
- **Revisores**: `maintainers`, `devops`
- **Épico / Requisito**: Issue #105 (alertas Code-Review e Branch-Protection do OpenSSF Scorecard)

---

## 1. Contexto e Declaração do Problema

O OpenSSF Scorecard aponta **Code-Review 0/11** (PRs recentes mergeados pela mesma pessoa que os
abriu) e **Branch-Protection** abaixo de 10. A nota máxima de Branch-Protection exige 2 aprovações,
revisão obrigatória de CODEOWNERS e regras valendo também para administradores.

O time tem 6 pessoas, uma única administradora da organização e o MVP vence em 05/12/2026.
Revisores de áreas específicas (por exemplo, `devops`) são 1 ou 2 pessoas.

---

## 2. Opções Consideradas

### Opção 1: Manter `main-protection` como está (1 aprovação)

- 1 aprovação de quem não fez o último push, descartada a cada push; check **CI OK** obrigatório.
- _Vantagens_: já em vigor, não trava o time pequeno.
- _Desvantagens_: Branch-Protection não chega a 10.

### Opção 2: 2 aprovações, CODEOWNERS obrigatório e sem bypass

- _Vantagens_: nota máxima no Scorecard.
- _Desvantagens_: times com 1 pessoa (`maintainers`, `qa` na prática) bloqueariam PRs de `docs/`,
  `.github/` e `rules/`; sem bypass, uma correção emergencial dependeria de duas pessoas.

---

## 3. Decisão Adotada

**Opção 1**, com estas regras de processo:

1. Todo PR para `main` recebe aprovação de uma pessoa diferente de quem fez o último push.
   Quem revisa é o time dono da área no `CODEOWNERS` (tabela em
   [Governança](../development/governance.md)).
2. PRs para `dev` exigem PR e **CI OK**; a revisão por pares é recomendada, mas não obrigatória.
3. O bypass dos `maintainers` em `main` é só para emergência (pipeline quebrado ou revisor
   indisponível perto de entrega). Todo uso é justificado em comentário no PR.
4. Dois aprovadores e CODEOWNERS obrigatório serão reavaliados se o time passar de 8 pessoas ou
   se houver pelo menos 2 revisores por área.

---

## 4. Consequências e Compensações (Trade-offs)

### Impactos Positivos

- Revisão por outra pessoa em tudo que chega a `main`, que é o que o Code-Review do Scorecard mede.
- Sem bloqueio por falta de revisores em áreas com 1 pessoa.

### Impactos Negativos e Riscos

- Branch-Protection do Scorecard permanece abaixo de 10 (aceito conscientemente).
- O bypass pode ser usado em excesso. Mitigação: justificativa obrigatória no PR e revisão
  mensal dos merges feitos com bypass.

---

## 5. Diretrizes de Implementação e Auditoria

- O ruleset `main-protection` já reflete esta decisão; nenhuma mudança de configuração é necessária.
- Auditoria: `gh pr list --state merged --base main` e conferência de que cada PR tem aprovação,
  ou justificativa de bypass.
- O projeto está cadastrado em [bestpractices.dev](https://www.bestpractices.dev/projects/16430)
  e o selo consta no `README.md`.

---

## 6. Adendo de Endurecimento (2026-11-27 — Issue #171 / `AUD-17b`)

Após a auditoria de 23/11/2026 (`AUD-17b`), que comprovou uso do bypass de revisão nos PRs `#155` e
`#157` (ambos com `CI OK` verde) e ausência de verificação de CI no disparo de `cd.yml`, esta ADR
é complementada pelas regras abaixo (sujeitas à aprovação do time `devops` para aplicação no
ruleset `24061709`):

1. **Redução de `bypass_mode` em `main-protection`:** alterar de `always` para `pull_request` para
   bloquear tecnicamente push direto em `main`, mantendo o bypass restrito ao merge de PR.
2. **Gate técnico no CD:** o job `verify-ci` em `.github/workflows/cd.yml` (`scripts/verify_release_ci.py`)
   exige `CI OK` com conclusão `success` no SHA exato da tag antes de publicar imagens no GHCR.
3. **Mitigação de conflito de interesse:** enquanto `maintainers` possuir um único membro, toda
   exceção de revisão em `main` exige comentário de justificativa no PR e revisão periódica pelo
   time `devops`.
