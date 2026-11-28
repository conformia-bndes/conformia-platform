# Identidade Visual e Sistema de Design — Conform.IA BNDES

Guia visual dos padrões de marca, cores, tipografia, semântica de status e acessibilidade implementados no frontend da plataforma **Conform.IA BNDES**, baseados no **Manual de Marca BNDES (Fev/2026)**.

<div style="height: 6px; width: 100%; border-radius: 4px; margin: 16px 0 24px 0; background: linear-gradient(90deg, #6493B2 0%, #6493B2 8%, #0077C0 8%, #0077C0 22%, #004A8F 22%, #004A8F 58%, #00984A 58%, #00984A 82%, #62BB46 82%, #62BB46 93%, #49C0B6 93%, #49C0B6 100%);"></div>

---

## 1. Marca, Logos e Favicon

### Amostras Oficiais

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; margin: 16px 0;">
  <div style="background: #FFFFFF; border: 1px solid #D4DFE9; border-radius: 8px; padding: 20px; text-align: center;">
    <div style="font-size: 12px; font-weight: 700; color: #004A8F; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 14px;">
      Logo Principal (Fundo Claro)
    </div>
    <img src="../../assets/brand/logo-bndes-conformia.svg" alt="Logo BNDES Conform.IA em cores" style="max-height: 68px; width: auto; margin: 0 auto; display: block;" />
    <div style="font-size: 11px; color: #546A7E; margin-top: 12px;">
      <code>logo-bndes-conformia.svg</code> (873 × 249)
    </div>
  </div>

  <div style="background: #004A8F; border: 1px solid #00386E; border-radius: 8px; padding: 20px; text-align: center;">
    <div style="font-size: 12px; font-weight: 700; color: #FFFFFF; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 14px;">
      Logo Negativa (Fundo Escuro / Azul)
    </div>
    <img src="../../assets/brand/logo-bndes-conformia-negativa.svg" alt="Logo BNDES Conform.IA negativa" style="max-height: 68px; width: auto; margin: 0 auto; display: block;" />
    <div style="font-size: 11px; color: rgba(255,255,255,0.85); margin-top: 12px;">
      <code>logo-bndes-conformia-negativa.svg</code> (873 × 249)
    </div>
  </div>

  <div style="background: #EDF2F7; border: 1px solid #D4DFE9; border-radius: 8px; padding: 20px; text-align: center;">
    <div style="font-size: 12px; font-weight: 700; color: #004A8F; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 14px;">
      Favicon / Símbolo Isolado
    </div>
    <img src="../../assets/brand/favicon.svg" alt="Favicon Conform.IA BNDES" style="height: 56px; width: 56px; margin: 6px auto; display: block;" />
    <div style="font-size: 11px; color: #546A7E; margin-top: 12px;">
      <code>favicon.svg</code> (85 × 85)
    </div>
  </div>
</div>

### Onde cada versão vive no código

| Ativo | Arquivo Fonte no Frontend | Onde é Aplicado | Regras de Uso |
| :--- | :--- | :--- | :--- |
| **Logo Principal** | `frontend/src/assets/logo-bndes-conformia.svg` | `Header.tsx` (barra superior) | Usar exclusivamente em fundo branco (`0%` preto) com área de respiro, sem sombras ou distorções. |
| **Logo Negativa** | `frontend/src/assets/logo-bndes-conformia-negativa.svg` | `Footer.tsx` (rodapé azul) | Usar sobre fundos escuros (`> 50%` preto) ou Azul BNDES (`#004A8F`). |
| **Favicon** | `frontend/public/favicon.svg` | `index.html` (aba do navegador) | Símbolo verde (`#00984A`) isolado sobre fundo branco arredondado. |

---

## 2. Paleta de Cores (`frontend/src/index.css`)

Os tokens abaixo são declarados no `@theme` do Tailwind CSS v4 em `frontend/src/index.css`.

### 2.1 Cores Institucionais

| Grupo | Amostra | Token CSS | Hex | Aplicação Principal |
| :--- | :---: | :--- | :--- | :--- |
| **Primária** | <span style="display:inline-block;width:22px;height:22px;border-radius:4px;background:#004A8F;border:1px solid rgba(0,0,0,0.15);vertical-align:middle;"></span> | `--color-bndes-blue` (`-1`) | `#004A8F` | Navegação, rodapé, títulos e botões primários |
| **Primária** | <span style="display:inline-block;width:22px;height:22px;border-radius:4px;background:#00984A;border:1px solid rgba(0,0,0,0.15);vertical-align:middle;"></span> | `--color-bndes-green` (`-1`) | `#00984A` | Símbolo da marca, borda do rodapé e confirmações |
| **Secundária** | <span style="display:inline-block;width:22px;height:22px;border-radius:4px;background:#0077C0;border:1px solid rgba(0,0,0,0.15);vertical-align:middle;"></span> | `--color-bndes-blue-2` | `#0077C0` | Anéis de foco (`focus-visible`), links e destaques |
| **Secundária** | <span style="display:inline-block;width:22px;height:22px;border-radius:4px;background:#62BB46;border:1px solid rgba(0,0,0,0.15);vertical-align:middle;"></span> | `--color-bndes-green-2` | `#62BB46` | Indicador de aba ativa e faixa institucional |
| **Terciária** | <span style="display:inline-block;width:22px;height:22px;border-radius:4px;background:#005687;border:1px solid rgba(0,0,0,0.15);vertical-align:middle;"></span> | `--color-bndes-blue-3` | `#005687` | Estado `hover` em botões e abas azuis |
| **Terciária** | <span style="display:inline-block;width:22px;height:22px;border-radius:4px;background:#6493B2;border:1px solid rgba(0,0,0,0.15);vertical-align:middle;"></span> | `--color-bndes-blue-4` | `#6493B2` | Faixa institucional |
| **Terciária** | <span style="display:inline-block;width:22px;height:22px;border-radius:4px;background:#00947D;border:1px solid rgba(0,0,0,0.15);vertical-align:middle;"></span> | `--color-bndes-green-3` | `#00947D` | Tom complementar de destaque |
| **Terciária** | <span style="display:inline-block;width:22px;height:22px;border-radius:4px;background:#49C0B6;border:1px solid rgba(0,0,0,0.15);vertical-align:middle;"></span> | `--color-bndes-green-4` | `#49C0B6` | Faixa institucional |
| **Apoio** | <span style="display:inline-block;width:22px;height:22px;border-radius:4px;background:#C15C29;border:1px solid rgba(0,0,0,0.15);vertical-align:middle;"></span> | `--color-bndes-orange` | `#C15C29` | Erros críticos, não conformidade e rejeições |
| **Apoio** | <span style="display:inline-block;width:22px;height:22px;border-radius:4px;background:#CD8627;border:1px solid rgba(0,0,0,0.15);vertical-align:middle;"></span> | `--color-bndes-ochre` | `#CD8627` | Avisos de atenção, revisão manual e exceções |
| **Apoio** | <span style="display:inline-block;width:22px;height:22px;border-radius:4px;background:#83227A;border:1px solid rgba(0,0,0,0.15);vertical-align:middle;"></span> | `--color-bndes-purple` | `#83227A` | Regras híbridas (`HYBRID` — IA + Regras) |

### 2.2 Pares Semânticos e Contraste Acessível (WCAG AA / AAA)

Para garantir legibilidade em badges, alertas e textos pequenos, os estados combinam **fundo suave (`-tint`)**, **borda (`-border`)** e **texto escuro de alto contraste (`-ink`)**:

| Estado | Amostra Visual | Fundo (`-tint`) | Borda (`-border`) | Texto (`-ink`) |
| :--- | :--- | :--- | :--- | :--- |
| **Base / Página** | <span style="display:inline-block;padding:3px 10px;border-radius:4px;background:#F4F7FA;border:1px solid #D4DFE9;color:#142638;font-size:12px;font-weight:600;">Texto Base</span> | `#F4F7FA` (`bndes-bg`) | `#D4DFE9` | `#142638` (`bndes-ink`) |
| **Informativo** | <span style="display:inline-block;padding:3px 10px;border-radius:4px;background:#EBF3FA;border:1px solid #B6CFE8;color:#004A8F;font-size:12px;font-weight:600;">Informativo</span> | `#EBF3FA` (`blue-tint`) | `#B6CFE8` | `#004A8F` (`bndes-blue`) |
| **Conforme / Sucesso** | <span style="display:inline-block;padding:3px 10px;border-radius:4px;background:#E7F6EE;border:1px solid #9AD6B7;color:#006631;font-size:12px;font-weight:600;">Conforme</span> | `#E7F6EE` (`green-tint`) | `#9AD6B7` | `#006631` (`green-ink`) |
| **Revisão / Atenção** | <span style="display:inline-block;padding:3px 10px;border-radius:4px;background:#FCF5E8;border:1px solid #E6C891;color:#784B0B;font-size:12px;font-weight:600;">Revisão Manual</span> | `#FCF5E8` (`ochre-tint`) | `#E6C891` | `#784B0B` (`ochre-ink`) |
| **Não Conforme / Erro** | <span style="display:inline-block;padding:3px 10px;border-radius:4px;background:#FDF2EC;border:1px solid #E5B8A1;color:#873912;font-size:12px;font-weight:600;">Não Conforme</span> | `#FDF2EC` (`orange-tint`) | `#E5B8A1` | `#873912` (`orange-ink`) |
| **Regra Híbrida (IA)** | <span style="display:inline-block;padding:3px 10px;border-radius:4px;background:#F6ECF5;border:1px solid #D9B3D5;color:#66195F;font-size:12px;font-weight:600;">Híbrida (IA + Regras)</span> | `#F6ECF5` (`purple-tint`) | `#D9B3D5` | `#66195F` (`purple-ink`) |

---

## 3. Tipografia (`frontend/index.html` e `frontend/src/index.css`)

| Família | Token CSS | Onde é Usada | Exemplo |
| :--- | :--- | :--- | :--- |
| **Fira Sans** (fallback: Arial, sans-serif) | `--font-sans` | Títulos, menus, botões, formulários e textos gerais | <span style="font-family: 'Fira Sans', Arial, sans-serif; font-weight: 600;">Conform.IA BNDES — Análise Documental</span> |
| **Lora** (fallback: Cormorant Garamond, serif) | `--font-serif` | Destaques editoriais e citações formais | <span style="font-family: 'Lora', Georgia, serif; font-style: italic;">Consulta Pública BNDES nº 01/2025</span> |
| **Fira Mono** (fallback: ui-monospace) | `--font-mono` | Códigos de regra, CNPJs, hashes SHA-256 e trechos literais | <code style="font-family: 'Fira Mono', monospace;">RULE-BNDES-001 • 12.345.678/0001-90</code> |

---

## 4. Semântica de Status e Tradução (`presentation.ts`)

A camada [`frontend/src/services/presentation.ts`](https://github.com/conformia-bndes/conformia-platform/blob/dev/frontend/src/services/presentation.ts) centraliza a tradução de enums do backend para português e garante coerência entre **cor**, **ícone** e **texto**:

- **Conformidade (`presentStatus`):**
  - `COMPLIANT` → *Conforme* (`success` / verde + ícone de check).
  - `NON_COMPLIANT` → *Não Conforme* (`danger` / laranja + ícone de X).
  - `MANUAL_REVIEW_REQUIRED` → *Revisão Manual* (`warning` / ocre + ícone de alerta). Status desconhecidos sempre caem em *Revisão Manual*.
  - `NOT_APPLICABLE` → *Não Aplicável* (`neutral` / cinza + ícone neutro).
- **Revisão Humana (`presentReviewSummary`):**
  - Quando o estado é `FINAL`, a cor do badge reflete a decisão final: `APPROVE` → `success` (verde), `EXCEPTION` → `warning` (ocre), `REJECT` → `danger` (laranja).
- **Traduções centralizadas:** Tipologias (`CND_FEDERAL`, `CRF_FGTS`, etc.), campos extraídos (`cnpj`, `data_validade`, etc.), tipos de regra (`DETERMINISTIC`, `HYBRID`), ações de auditoria (`DOCUMENT_UPLOADED`, `COMPLIANCE_VERIFIED`, etc.) e chaves de evidência de regra.

---

## 5. Acessibilidade e Responsividade

- **Navegação por abas WAI-ARIA:** `role="tablist"`, `role="tab"`, `aria-selected`, `aria-controls` em `Header.tsx` e `role="tabpanel"` / `aria-labelledby` em `App.tsx`.
- **Modais e teclado (`ApiKeyModal.tsx`):** `role="dialog"` com `aria-modal="true"`, fechamento por `Esc` ou clique no fundo, restauração de foco ao fechar e `spellCheck={false}` / `autoCapitalize="none"` no campo da chave pessoal.
- **Feedback acessível:** Alertas de erro com `role="alert"`, avisos de upload/polling com `role="status"` e `aria-live="polite"`, `aria-label` em botões só com ícone, `focus-visible:ring-2` e `motion-reduce:animate-none`.
- **Mobile-first:** Menu de abas em `grid-cols-3` abaixo de `sm` (todas as 3 seções visíveis sem rolagem horizontal), botões principais em `w-full sm:w-auto` e detalhes JSON expansíveis na trilha de auditoria.
