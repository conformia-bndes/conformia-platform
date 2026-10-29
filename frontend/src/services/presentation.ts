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
