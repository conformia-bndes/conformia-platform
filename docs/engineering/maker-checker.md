# Maker-Checker e Guardrails de IA

O LLM só participa da decisão nas regras híbridas e sempre sob o padrão **Maker-Checker**: um
modelo propõe, outro audita e uma verificação determinística confirma a evidência. Qualquer
falha nesse ciclo leva à revisão humana, nunca à aprovação.

Implementação: `backend/app/ai/llm_client.py` (`MakerCheckerValidator`).

---

## 1. Ciclo de avaliação

```mermaid
sequenceDiagram
    autonumber
    participant R as Motor de regras
    participant M as Maker (LLM)
    participant C as Checker (LLM)
    participant G as Verificação de citação

    R->>M: Regra + até 3.000 caracteres do documento
    M-->>R: assessment, citação literal, confiança, justificativa
    R->>C: Texto do documento + proposta do Maker
    C-->>R: APPROVED ou REJECTED, alucinação detectada?
    R->>G: A citação do Maker existe no texto?
    alt Checker aprovou, sem alucinação, status válido e citação encontrada
        R-->>R: Status proposto pelo Maker
    else Qualquer outra combinação
        R-->>R: MANUAL_REVIEW_REQUIRED
    end
```

| Papel | Responsabilidade |
| :-- | :-- |
| **Maker** | Propor `COMPLIANT`, `NON_COMPLIANT` ou `MANUAL_REVIEW_REQUIRED` com a citação literal (`extracted_value`) que fundamenta a proposta |
| **Checker** | Receber o texto e a proposta do Maker e avaliar, em chamada separada, se a proposta é sustentada pelo texto e se há alucinação |
| **Verificação de citação** | Confirmar de forma determinística que a citação aparece no documento, ignorando acentos, caixa e espaços |

A confiança final é a média das confianças do Maker e do Checker quando a proposta é aceita, e
zero quando não é.

---

## 2. Comportamento em falhas (fail-closed)

| Situação | Resultado |
| :-- | :-- |
| `OPENAI_API_KEY` ausente ou erro do provedor (`LLMUnavailableError`) | `MANUAL_REVIEW_REQUIRED`, com `error: LLM_UNAVAILABLE` na evidência |
| Resposta do Maker ou do Checker que não é JSON válido | `MANUAL_REVIEW_REQUIRED` |
| Status proposto fora do domínio | `MANUAL_REVIEW_REQUIRED` |
| Checker rejeita ou aponta alucinação | `MANUAL_REVIEW_REQUIRED` |
| Citação vazia ou inexistente no documento | `MANUAL_REVIEW_REQUIRED` |

Configuração: `LLM_MODEL` (padrão `gpt-4o-mini`), `LLM_TEMPERATURE` (padrão `0.0`) e
timeout de 30 segundos por chamada.

---

## 3. Guardrails do produto

1. **Sem validade legível, sem aprovação.** Certidões fiscais e trabalhistas sem data de validade
   identificada vão para `MANUAL_REVIEW_REQUIRED` antes de qualquer etapa de IA.
2. **O LLM não tem ferramentas.** Ele recebe apenas a regra e um trecho do texto, e devolve JSON.
   Somente a camada de serviços grava no banco.
3. **Revisão humana com segregação de funções.** A decisão final sobre um laudo em revisão é
   proposta por um analista e confirmada por outro (quem propõe não pode confirmar), e fica
   registrada em `review_events` (somente inserção).
4. **Regra nova exige caso de teste.** Toda regra entra com casos no benchmark de
   [avaliação contínua](harness-evals.md), e o CI bloqueia falsos positivos.

---

## 3.1 Provedor de LLM

O cliente fala a API de chat da OpenAI e funciona com qualquer provedor compatível. A escolha é
feita por variáveis de ambiente, sem mudar código: `LLM_BASE_URL`, `LLM_MODEL`,
`OPENAI_API_KEY` (a chave do provedor configurado), `LLM_TIMEOUT_SECONDS` e `LLM_MAX_RETRIES`.
A requisição pede `response_format: json_object`, aceita JSON dentro de cerca de código e repete
a chamada com espera crescente em 429 e 5xx. Sem chave ou com falha, a regra vai para revisão
manual; nunca há resposta simulada.

**Modelo gratuito avaliado (OpenRouter, 13/11/2026).** Cinco modelos gratuitos foram comparados na
regra RULE-BNDES-004 com quatro casos (nada consta, falência decretada, texto ilegível e sem
resultado informado), medindo o veredito final do Maker-Checker:

| Modelo | Resultado | Observação |
| :-- | :-- | :-- |
| `particle-ai/particle-1:free` | 4 de 4 corretos | 5 a 11 s por avaliação; escolhido |
| `nvidia/nemotron-3.5-super-vl:free` | 3 de 4 corretos | ~20 s; decide sem evidência no caso "sem resultado" |
| `openrouter/free` | Checker não aprovou os casos | Maker correto, mas o veredito caiu em revisão manual |
| `inclusionai/ling-3.2-flash:free` | falhou | 115 s no primeiro caso e 429 no segundo |
| `google/gemma-4-31b-it:free`, `gemma-4-26b-a4b-it:free` | indisponíveis | 429 do provedor upstream nas três tentativas |

Limites desta avaliação: quatro casos sintéticos por modelo e uma única rodada. A disponibilidade
dos modelos gratuitos muda e a conta gratuita tem teto diário de requisições. Dados enviados a
modelos gratuitos podem ser retidos pelo provedor: usar apenas documentos sintéticos ou
anonimizados nesse modo.

---

## 4. Harness de desenvolvimento

O mesmo princípio vale para agentes de IA que ajudam a construir o software. As regras ficam
em `AGENTS.md` na raiz do repositório: nada de comandos destrutivos, commits pequenos em
Conventional Commits, validação com testes reais antes de declarar uma tarefa concluída e nenhum
segredo em código, logs ou relatórios. Os hooks do pre-commit e os checks obrigatórios do CI
aplicam essas regras independentemente de quem escreveu o código.
