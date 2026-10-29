# Motor de Regras e Conformidade Declarativa

O Motor de Regras do Conform.IA BNDES (`app.services.rules_engine.RulesEngine`) e o nucleo responsável por interpretar os requisitos normativos do BNDES e avaliar o texto extraido dos documentos.

---

## 1. Tipologia de Regras de Conformidade

O sistema suporta três modalidades de avaliação:

```mermaid
flowchart LR
    Texto[Texto Extraido pelo IDP] --> Engine[RulesEngine]
    Engine --> Det[Regra Deterministica\nEx: CND, CRF FGTS]
    Engine --> Sem[Regra Semantica\nEx: Interpretacao Contratual]
    Engine --> Hyb[Regra Hibrida\nEx: Falencia, Licenca Ambiental]

    Det -->|Validacao Regex e Anti-Keywords| LaudoDet[Status Deterministico Imediato]
    Sem -->|LLM Prompt Delimitado| LaudoSem[Harness Maker-Checker]
    Hyb -->|Triagem Deterministica Positiva| LaudoSem
```

### 1.1 Regras Determinísticas (`DETERMINISTIC`)

- Executadas via busca booleana exata, correspondência de expressões regulares e validação de termos impeditivos (_anti-keywords_).
- **Exemplo**: Certidão Negativa de Débitos Federais. Se os termos `"CERTIDAO NEGATIVA"`, `"TRIBUTOS FEDERAIS"` e `"DIVIDA ATIVA DA UNIAO"` estiverem presentes, e nenhum termo como `"CONSTA PENDENCIA"` for detectado, o resultado e `COMPLIANT`.

### 1.2 Regras Híbridas (`HYBRID`)

- Aplicadas a documentos onde o vocabulário pode variar por comarca ou órgão regional (ex: certidões de falência).
- O motor realiza uma triagem determinística inicial. Se os termos fundamentais forem localizados, o texto relevante é submetido ao orquestrador **Maker-Checker** para auditoria semântica e confirmação de ausência de passivos.

---

## 2. Estrutura do Esquema Declarativo (JSON Schema)

As regras são externalizadas do código-fonte da aplicação e versionadas em `rules/schemas/rule_schema.json`. O checklist de referência reside em `rules/schemas/bndes_sample_checklist.json`.

Propriedades fundamentais de cada regra:

- `id`: Identificador único (ex: `RULE-BNDES-001`).
- `code`: Mnemonico operacional (ex: `CND_FEDERAL`).
- `category`: Classificação tematica (`FISCAL`, `TRABALHISTA`, `JURIDICA`, `AMBIENTAL`, `INTEGRIDADE`).
- `severity`: Nível de bloqueio no crédito (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`).
- `required_keywords`: Termos textuais obrigatórios.
- `anti_keywords`: Termos cuja presença reprova a certidão sumariamente.
- `regex_patterns`: Padrões formais (CNPJ, formato de datas, códigos alfanumericos).
- `failure_message`: Mensagem institucional exibida no laudo.

---

## 3. Estados de Conformidade e Pontuação

Cada verificação resulta em um dos seguintes estados formais:

- `COMPLIANT`: O documento atende plenamente aos requisitos legais.
- `NON_COMPLIANT`: Identificada irregularidade insuperável, pendência fiscal ou ausência de requisito mandatório.
- `MANUAL_REVIEW_REQUIRED`: Incerteza semântica, divergência no Maker-Checker ou informação com baixa legibilidade.
- `NOT_APPLICABLE`: Requisito dispensado conforme a modalidade do proponente.

O **Score de Conformidade** e calculado pela razão entre regras cumpridas e o total de regras ativas aplicáveis:

$$\text{Compliance Score} = \frac{\sum \text{Regras Aprovadas}}{\text{Total de Regras Aplicaveis}}$$
