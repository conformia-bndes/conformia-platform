import { isAxiosError } from 'axios';

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
  success: 'bg-emerald-100 text-emerald-800',
  danger: 'bg-rose-100 text-rose-800',
  warning: 'bg-amber-100 text-amber-800',
  neutral: 'bg-slate-100 text-slate-600',
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

import type { ExtractedField, PageEvidence } from '../services/api';

/**
 * Formata o valor de um campo extraído para exibição no laudo.
 * - strings/null: retorna o próprio valor ou "—" (em dash) quando vazio.
 * - números: retorna String(value)
 * - outros: retorna JSON.stringify
 */
export function formatExtractedValue(value: unknown, rawValue?: string | null): string {
  if (value === null || value === undefined) {
    return rawValue && rawValue.trim() ? rawValue : '—';
  }
  if (typeof value === 'string') {
    return value.trim() || '—';
  }
  if (typeof value === 'number' || typeof value === 'boolean') {
    return String(value);
  }
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

/**
 * Determina se o campo extraído possui evidência atrelada.
 */
export function hasEvidence(field: ExtractedField): boolean {
  return Boolean(field.evidence);
}

/**
 * Recupera a evidência de um campo extraído, retornando null quando não há evidência.
 */
export function getFieldEvidence(field: ExtractedField): PageEvidence | null {
  return field.evidence ?? null;
}

/**
 * Verifica se um campo extraído possui evidência não vazia (texto com tamanho > 0).
 */
export function hasNonEmptyEvidence(field: ExtractedField): boolean {
  const ev = field.evidence;
  if (!ev) return false;
  return ev.text != null && ev.text.trim().length > 0;
}

/**
 * Recupera a evidência de um campo extraído; se não houver, retorna um PageEvidence
 * marcado com texto vazio, para que o componente exiba o estado vazio corretamente.
 */
export function getFieldEvidenceOrEmpty(field: ExtractedField): PageEvidence {
  if (field.evidence) {
    return field.evidence;
  }
  return { text: '', page: 0, confidence: 0, bounding_box: null };
}

