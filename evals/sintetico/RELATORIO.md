# Relatorio inicial de avaliacao - Dataset sintetico (Issue #24)

## 1. Objetivo

Estabelecer uma avaliacao reproduzivel da extracao e da classificacao de certidoes, antes de
alteracoes no pipeline semantico. Este relatorio registra a linha de base (baseline) do
comportamento atual do sistema sobre um conjunto sintetico rotulado.

**Os numeros abaixo valem apenas para este conjunto de 22 documentos sinteticos. Eles nao
representam o desempenho do sistema em producao nem sao metas.**

## 2. Como reproduzir

```bash
uv sync --all-packages --all-extras
uv run python evals/sintetico/gerar_dataset.py     # gera os 22 PDFs em evals/sintetico/pdfs/
uv run python evals/sintetico/validar_gabarito.py  # confere o gabarito contra os PDFs
uv run python evals/sintetico/avaliar.py           # roda o pipeline e compara com o gabarito
```

Requer Tesseract com o pacote de portugues (`tesseract-ocr` e `tesseract-ocr-por`).

| Arquivo | Funcao |
|---|---|
| `gerar_dataset.py` | Gera os PDFs sinteticos de forma deterministica (sem sorteio) |
| `gabarito.json` | Resultado esperado por documento e por campo, com trecho de evidencia e pagina |
| `validar_gabarito.py` | Confere se toda evidencia do gabarito existe literalmente no PDF |
| `avaliar.py` | Executa extracao + motor de regras e compara com o gabarito |

## 3. Conjunto avaliado

22 documentos ficticios (empresa e CNPJ inventados), de dois tipos: CND Federal
(`RULE-BNDES-001`) e CRF do FGTS (`RULE-BNDES-002`).

| Situacao | Descricao | Qtd |
|---|---|---|
| valido | sem pendencia, dentro do prazo | 4 |
| vencido | prazo expirado (inclui data em formato alternativo e erro de OCR simulado) | 6 |
| pendente | certidao positiva / situacao irregular | 4 |
| ilegivel | erro de digitacao no titulo, data desfocada ou titulo coberto por carimbo | 6 |
| sem_validade | documento sem linha de validade | 2 |

| Formato | Como foi gerado | Qtd |
|---|---|---|
| nativo | PDF com texto selecionavel | 12 |
| digitalizado | pagina renderizada como imagem (150 DPI, inclinacao de 0,8 grau, desfoque leve) | 10 |

Decisoes de construcao:

- Datas distantes da data atual (2001 para vencido, 2099 para valido), porque o motor compara a
  validade com `datetime.now()`; datas proximas mudariam o resultado com o passar do tempo.
- CND usa "Valida ate dd/mm/aaaa" e CRF usa a faixa "Validade: X a Y", imitando o formato oficial.
- Cada digitalizado usa o mesmo texto de um nativo (campo `origem` no gabarito), para isolar
  erros de OCR.
- Cada caso ilegivel danifica um unico campo, para que a causa do erro seja identificavel.
- O status esperado segue as regras do projeto (`.agents/AGENTS.md`), e nao o comportamento
  atual do sistema. Ex.: certidao sem data legivel deve ser `MANUAL_REVIEW_REQUIRED`.

## 4. Metodologia

A avaliacao mede tres camadas, para separar onde esta cada problema:

1. **Extracao:** o trecho de evidencia do gabarito aparece no texto extraido?
2. **Campos:** o valor que o sistema informa e igual ao valor esperado?
3. **Classificacao:** o status obtido e igual ao esperado? Se nao, qual a gravidade?

O motor de regras nao devolve campos estruturados. Os valores foram lidos do dicionario
`evidence` do resultado:

| Campo | Como o valor do sistema foi obtido |
|---|---|
| tipo_documento | confirmado se nao houve palavra-chave faltando nem termo de pendencia |
| cnpj | nao disponivel: o motor confere o formato do CNPJ, mas nao devolve o valor |
| validade | `evidence["validity_date"]` |
| pendencia | verdadeiro se `evidence["matched_anti_keywords"]` tiver algum termo |

Gravidade dos erros de classificacao:

| Gravidade | Definicao |
|---|---|
| critico | obtido `COMPLIANT` quando o esperado era outro (falso positivo) |
| seguro | esperado `NON_COMPLIANT`, obtido `MANUAL_REVIEW_REQUIRED` |
| custo operacional | esperado `COMPLIANT` ou `MANUAL_REVIEW_REQUIRED`, obtido `NON_COMPLIANT` |

A "causa provavel" de cada erro e uma heuristica: examina os campos na ordem em que o motor
avalia (palavras-chave do titulo, pendencia, validade) e aponta o primeiro que explica o erro.

## 5. Resultados

Execucao em 2026-10-19T10:36:47, com tesseract 4.1.1.

| Camada | Resultado |
|---|---|
| Extracao | 82 de 82 trechos de evidencia encontrados (46/46 nativos, 36/36 digitalizados) |
| Classificacao | 10 de 22 documentos com o status esperado |

Classificacao por situacao:

| Situacao | Acertos |
|---|---|
| pendente | 4 de 4 |
| vencido | 4 de 6 |
| valido | 2 de 4 |
| ilegivel | 0 de 6 |
| sem_validade | 0 de 2 |

Erros por gravidade: **6 criticos (falsos positivos)** e 6 de custo operacional.

Campos:

| Campo | Resultado |
|---|---|
| tipo_documento | 18 corretos, 4 nao informados (o motor para antes ao detectar pendencia) |
| cnpj | 22 nao extraidos (o sistema nao expoe o valor) |
| validade | 8 corretos, 4 divergentes, 10 nao extraidos |
| pendencia | 22 corretos |

**Conclusao:** a extracao de texto leu todos os trechos de evidencia, mas a classificacao acertou
menos da metade dos documentos. Neste conjunto, os erros vem das regras de decisao do motor, e
nao da leitura do PDF.

## 6. Falhas por tipo

### 6.1 Certidao sem data legivel e aprovada (critico) - 4 casos

CND-SEM-VALIDADE-NAT, CRF-SEM-VALIDADE-NAT, CND-ILEGIVEL-DIG-DATA, CRF-ILEGIVEL-DIG-DATA.

Quando a data de validade nao e encontrada, o motor aprova a certidao. A verificacao de data
ausente (`rules_engine.py`, linha 260) so roda se a regra tiver `strict_validity`, e nenhuma regra
de `rules/schemas/bndes_sample_checklist.json` define esse campo. Contraria o `.agents/AGENTS.md`:
"Nunca Assumir Validade por Ausencia de Dados".

### 6.2 Data de validade nao reconhecida em certidao vencida (critico) - 2 casos

CND-VENCIDA-FMTDATA-NAT ("Validade da certidão: 01/01/2001") e CND-VENCIDA-OCRDATA-NAT
("Válida até: 0l/01/2001", erro de OCR simulado).

A expressao regular de `_extract_validity_date` (linha 99) exige a data logo apos a palavra-chave
e apenas digitos. Variacoes de redacao ou um erro comum de OCR fazem a data nao ser encontrada, e
o documento cai no caso 6.1: certidao vencida aprovada.

### 6.3 Data inicial da faixa lida como data final (custo operacional) - 2 casos

CRF-VALIDA-NAT e CRF-VALIDA-DIG.

A CRF informa a validade como faixa ("Validade: 01/01/2001 a 31/12/2099"). O motor usa a primeira
data encontrada (`re.search`, linha 109), que e a data de inicio, e reprova a certidao valida como
expirada. Como a data de inicio de uma CRF real esta sempre no passado, toda CRF valida tende a ser
reprovada. O mesmo defeito aparece em CRF-VENCIDA-NAT/DIG (validade lida 01/01/2000, esperada
01/01/2001), mas sem mudar o status, porque as duas datas ja passaram.

### 6.4 Titulo ilegivel ou com erro reprovado em vez de revisao manual (custo operacional) - 4 casos

CND-ILEGIVEL-NAT, CRF-ILEGIVEL-NAT, CND-ILEGIVEL-DIG-TITULO, CRF-ILEGIVEL-DIG-TITULO.

Quando falta uma palavra-chave obrigatoria (por erro de digitacao ou carimbo sobre o titulo), o
motor reprova (`NON_COMPLIANT`). O documento nao foi provado irregular, apenas nao pode ser
confirmado; o esperado e `MANUAL_REVIEW_REQUIRED`.

## 7. Observacoes adicionais

- **Eval existente:** `evals/eval_pipeline.py` reporta 100% de acuracia e 0 falsos positivos
  porque seus 5 casos nao exercitam os caminhos onde o motor falha (texto digitado, sem PDF, sem
  OCR, sem datas ausentes ou em outros formatos). O CASE-001 e uma certidao sem data de validade
  com resultado esperado `COMPLIANT`, o que trata o defeito 6.1 como comportamento correto.
- **Quebra de linha em palavra-chave (risco, sem falha neste conjunto):** o titulo da CND e
  extraido em duas linhas, separando "DIVIDA ATIVA DA" de "UNIAO". O caso so passa porque a
  expressao aparece inteira em outra frase do documento.
- **Efeito colateral da degradacao:** no CND-ILEGIVEL-DIG-TITULO, o carimbo fez o OCR errar a
  linha vizinha ("FICTICIA" lido como "FICTÍICIA"), que nao foi carimbada.
- **Reprodutibilidade:** a avaliacao gerou resultados identicos em duas maquinas, com Tesseract 4
  e Tesseract 5.

## 8. Limitacoes

- Conjunto pequeno (22 documentos) e sintetico, com dois tipos de certidao e uma unica empresa.
- Degradacao leve nos digitalizados; scans de pior qualidade nao foram avaliados.
- O resultado do OCR pode variar com a versao do Tesseract, que nao e controlada pelo `uv.lock`.
- Os campos do sistema foram inferidos do dicionario `evidence` (secao 4); a causa provavel e
  uma heuristica.
- As regras hibridas (Maker-Checker com LLM) nao foram avaliadas: as duas regras usadas sao
  deterministicas.
