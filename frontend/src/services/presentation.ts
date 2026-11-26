import { isAxiosError } from 'axios';
import type { ReviewDecision, ReviewState } from './api';

export type CheckStatus = 'COMPLIANT' | 'NON_COMPLIANT' | 'MANUAL_REVIEW_REQUIRED' | 'NOT_APPLICABLE';

export type StatusTone = 'success' | 'danger' | 'warning' | 'neutral';

export interface StatusPresentation {
  label: string;
  tone: StatusTone;
}

const STATUS_PRESENTATION: Record<CheckStatus, StatusPresentation> = {
  COMPLIANT: { label: 'Conforme', tone: 'success' },
  NON_COMPLIANT: { label: 'Não Conforme', tone: 'danger' },
  MANUAL_REVIEW_REQUIRED: { label: 'Revisão Manual', tone: 'warning' },
  NOT_APPLICABLE: { label: 'Não Aplicável', tone: 'neutral' },
};

/**
 * Rótulo e tom visual de um status de regra ou laudo. Status desconhecido nunca é
 * apresentado como conforme: cai em revisão manual.
 */
export function presentStatus(status: string): StatusPresentation {
  return STATUS_PRESENTATION[status as CheckStatus] ?? STATUS_PRESENTATION.MANUAL_REVIEW_REQUIRED;
}

export const TONE_CLASSES: Record<StatusTone, string> = {
  success: 'bg-bndes-green-tint text-bndes-green-ink border border-bndes-green-border',
  danger: 'bg-bndes-orange-tint text-bndes-orange-ink border border-bndes-orange-border',
  warning: 'bg-bndes-ochre-tint text-bndes-ochre-ink border border-bndes-ochre-border',
  neutral: 'bg-bndes-surface-muted text-bndes-ink-secondary border border-bndes-border',
};

/** Mensagem legível para o analista a partir de uma falha de chamada à API. */
export function describeApiError(error: unknown, fallback: string): string {
  if (isAxiosError(error)) {
    const detail: unknown = error.response?.data?.detail;
    if (typeof detail === 'string' && detail.trim()) {
      return detail;
    }
    if (!error.response) {
      return `${fallback} A API não respondeu; verifique se o backend está em execução.`;
    }
    return `${fallback} (HTTP ${error.response.status})`;
  }
  return fallback;
}

const REVIEW_STATE_PRESENTATION: Record<ReviewState, StatusPresentation> = {
  NO_REVIEW: { label: 'Sem Revisão', tone: 'neutral' },
  PENDING_CHECK: { label: 'Aguardando 2º Analista', tone: 'warning' },
  FINAL: { label: 'Revisão Concluída', tone: 'success' },
  RETURNED: { label: 'Devolvida para Nova Proposta', tone: 'danger' },
};

export function presentReviewState(state: string): StatusPresentation {
  return REVIEW_STATE_PRESENTATION[state as ReviewState] ?? REVIEW_STATE_PRESENTATION.NO_REVIEW;
}

/**
 * Rótulo e tom semântico do resumo da revisão humana.
 * Quando FINAL, o tom reflete a decisão final (REJEITAR = danger, EXCEÇÃO = warning, APROVAR = success).
 */
export function presentReviewSummary(
  state: string,
  finalDecision: string | null | undefined,
): StatusPresentation {
  const base = presentReviewState(state);
  if (state !== 'FINAL' || !finalDecision) {
    return base;
  }

  let tone: StatusTone = 'success';
  if (finalDecision === 'REJECT') {
    tone = 'danger';
  } else if (finalDecision === 'EXCEPTION') {
    tone = 'warning';
  }

  return {
    label: `${base.label} • ${presentReviewDecision(finalDecision)}`,
    tone,
  };
}

const REVIEW_EVENT_PRESENTATION: Record<string, StatusPresentation> = {
  PROPOSED: { label: 'Proposta', tone: 'neutral' },
  CONFIRMED: { label: 'Confirmada', tone: 'success' },
  RETURNED: { label: 'Devolvida', tone: 'danger' },
};

export function presentReviewEventType(eventType: string): StatusPresentation {
  return REVIEW_EVENT_PRESENTATION[eventType] ?? { label: eventType, tone: 'neutral' };
}

const RULE_TYPE_LABELS: Record<string, string> = {
  DETERMINISTIC: 'Determinística',
  HYBRID: 'Híbrida (IA + Regras)',
};

export function presentRuleType(ruleType: string): string {
  return RULE_TYPE_LABELS[ruleType] ?? ruleType;
}

const DOCUMENT_TYPE_LABELS: Record<string, string> = {
  CND_FEDERAL: 'CND Federal (RFB / PGFN)',
  CRF_FGTS: 'CRF FGTS (Caixa)',
  CNDT_TRABALHISTA: 'CNDT Trabalhista (TST)',
  FALENCIA_RECUPERACAO: 'Certidão de Falência e Recuperação',
  LICENCA_AMBIENTAL: 'Licença Ambiental',
  INTEGRIDADE_CEIS_CNEP: 'Consulta CEIS / CNEP',
};

export function presentDocumentType(docType: string | null | undefined): string {
  if (!docType) return 'Não identificada (revisão manual)';
  return DOCUMENT_TYPE_LABELS[docType] ?? docType;
}

const EXTRACTED_FIELD_LABELS: Record<string, string> = {
  document_type: 'Tipo de Documento',
  cnpj: 'CNPJ',
  razao_social: 'Razão Social',
  data_validade: 'Data de Validade',
  data_emissao: 'Data de Emissão',
  numero_certidao: 'Número da Certidão',
  codigo_controle: 'Código de Controle',
  situacao: 'Situação',
};

export function presentExtractedFieldName(name: string): string {
  return EXTRACTED_FIELD_LABELS[name] ?? name;
}

const AUDIT_ACTION_LABELS: Record<string, string> = {
  DOCUMENT_UPLOADED: 'Documento Enviado',
  COMPLIANCE_VERIFIED: 'Conformidade Avaliada',
  REVIEW_PROPOSED: 'Revisão Proposta',
  REVIEW_CONFIRMED: 'Revisão Confirmada',
  REVIEW_RETURNED: 'Revisão Devolvida',
};

export function presentAuditAction(action: string): string {
  return AUDIT_ACTION_LABELS[action] ?? action;
}

const AUDIT_ENTITY_LABELS: Record<string, string> = {
  DOCUMENT: 'Documento',
  COMPLIANCE: 'Laudo',
  REVIEW: 'Revisão',
};

export function presentAuditEntity(entityType: string): string {
  return AUDIT_ENTITY_LABELS[entityType] ?? entityType;
}

const REVIEW_DECISION_LABELS: Record<ReviewDecision, string> = {
  APPROVE: 'Aprovar Laudo',
  REJECT: 'Reprovar Laudo',
  EXCEPTION: 'Aprovar com Exceção Motivada',
};

export function presentReviewDecision(decision: string | null | undefined): string {
  if (!decision) return '-';
  return REVIEW_DECISION_LABELS[decision as ReviewDecision] ?? decision;
}

export type DocumentProcessingStatus =
  | 'PENDING'
  | 'PROCESSING'
  | 'COMPLETED'
  | 'FAILED'
  | 'EXTRACTION_FAILED';

const DOCUMENT_STATUS_PRESENTATION: Record<DocumentProcessingStatus, StatusPresentation> = {
  PENDING: { label: 'Na Fila', tone: 'neutral' },
  PROCESSING: { label: 'Processando OCR/IDP...', tone: 'warning' },
  COMPLETED: { label: 'Concluído', tone: 'success' },
  FAILED: { label: 'Falhou', tone: 'danger' },
  EXTRACTION_FAILED: { label: 'Falha na Extração', tone: 'danger' },
};

export function presentDocumentStatus(status: string): StatusPresentation {
  return (
    DOCUMENT_STATUS_PRESENTATION[status as DocumentProcessingStatus] ?? {
      label: status || 'Desconhecido',
      tone: 'neutral',
    }
  );
}

const RULE_EVIDENCE_LABELS: Record<string, string> = {
  matched_keywords: 'Palavras-chave encontradas',
  matched_anti_keywords: 'Termos impeditivos',
  missing_keywords: 'Termos ausentes',
  matched_regex_patterns: 'Padrões validados',
  validity_date: 'Validade extraída',
  document_type: 'Tipologia',
  evidence: 'Citação literal',
  reasoning: 'Fundamentação',
  hallucination_detected: 'Inconsistência detectada',
};

function formatEvidenceValue(value: unknown): string {
  if (Array.isArray(value)) {
    return value.map((item) => formatEvidenceValue(item)).join(', ');
  }
  if (typeof value === 'boolean') {
    return value ? 'Sim' : 'Não';
  }
  if (typeof value === 'object' && value !== null) {
    try {
      return JSON.stringify(value);
    } catch {
      return String(value);
    }
  }
  return String(value);
}

export interface FormattedRuleEvidence {
  key: string;
  label: string;
  displayValue: string;
}

/** Formata o dicionário de evidência por regra para exibição legível sem [object Object]. */
export function formatRuleEvidenceEntries(
  evidence: Record<string, unknown> | null | undefined,
): FormattedRuleEvidence[] {
  if (!evidence) return [];

  return Object.entries(evidence)
    .filter(([, value]) => {
      if (value === null || value === undefined) return false;
      if (Array.isArray(value) && value.length === 0) return false;
      return true;
    })
    .map(([key, value]) => ({
      key,
      label: RULE_EVIDENCE_LABELS[key] ?? key,
      displayValue: formatEvidenceValue(value),
    }));
}
