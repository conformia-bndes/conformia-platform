# Harness Engineering e Avaliação Contínua de IA (Evals)

Em aplicações que envolvem auditoria de crédito público e contratações de grande porte no BNDES, a aplicação de modelos de linguagem (LLMs) requer governança rigorosa contra alucinações, vieses e instabilidades de geração. O Conform.IA BNDES adota os princípios de **Harness Engineering**.

---

## 1. O Padrão Maker-Checker

Para eliminar o risco de alucinações em que o modelo infere erroneamente a conformidade de uma empresa, o sistema implementa a arquitetura de **Quatro Olhos Algorítmico (Maker-Checker)**:

```mermaid
sequenceDiagram
    autonumber
    actor Engine as Motor de Regras
    participant Maker as Agente Maker (Propositor)
    participant Checker as Agente Checker (Auditor)
    participant Postgres as Banco de Dados / Auditoria

    Engine->>Maker: Envia Texto do Documento e Definição da Regra
    Note over Maker: Analisa o texto e formula hipotese com citacao literal
    Maker-->>Engine: Retorna Proposta (Status, Evidencia, Confianca)

    Engine->>Checker: Envia Texto Original e Proposta do Maker
    Note over Checker: Verifica se a citacao existe literalmente no documento original
    Checker-->>Engine: Retorna Parecer (APPROVED / REJECTED, Alucinacao detectada?)

    alt Checker Aprovou e Sem Alucinacao
        Engine->>Postgres: Registra Status da Proposta do Maker
    else Divergencia ou Alucinacao
        Engine->>Postgres: Degrada Status para MANUAL_REVIEW_REQUIRED
    end
```

### 1.1 Responsabilidades do Maker

- Formula uma hipótese preliminar de avaliação baseada exclusivamente no trecho documental fornecido.
- Deve obrigatoriamente indicar o valor exato extraido e a justificativa lógica.
- Restrito a esquemas de saida estruturados em JSON via Pydantic.

### 1.2 Responsabilidades do Checker

- Opera de forma totalmente desacoplada e independente do Maker.
- Audita se o trecho citado pelo Maker esta realmente contido no texto original do PDF.
- Em caso de inconsistência textual ou extrapolação de contexto, o Checker invalida a hipótese, forçando o encaminhamento para análise humana.

---

## 2. Métricas e Limiares Operacionais de Evals

O pipeline de avaliação continua (`evals/eval_pipeline.py`) monitora regressões através de casos de teste sintéticos e reais anonimizados:

| Dimensão              | Indicador                        | Meta                       | Limiar de Alerta        |
| :-------------------- | :------------------------------- | :------------------------- | :---------------------- |
| **Segurança**         | Falsos Positivos de Conformidade | **0.0%** (Tolerância Zero) | $> 0.0\%$ (Bloqueia CI) |
| **Qualidade IDP**     | Character Error Rate (CER)       | $\le 1.5\%$                | $> 3.0\%$               |
| **Extração**          | Recall de Entidades Chave        | $\ge 98.5\%$               | $< 95.0\%$              |
| **Confiabilidade IA** | Taxa de Detecção de Alucinação   | $\ge 99.0\%$               | $< 98.0\%$              |
| **Consenso**          | Maker-Checker Agreement Rate     | $\ge 95.0\%$               | $< 90.0\%$              |

---

## 3. Execução de Benchmarks de Regressão

O benchmark de Evals e executado localmente via:

```bash
python evals/eval_pipeline.py
```

O comando realiza o teste funcional completo contra o conjunto de regras do BNDES, verificando se documentos com falência decretada ou pendências fiscais são rejeitados com precisão absoluta.
