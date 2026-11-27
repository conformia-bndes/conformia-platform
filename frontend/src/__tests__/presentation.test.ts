import { describe, it, expect } from 'vitest';
import { AxiosError, AxiosHeaders } from 'axios';
import {
  describeApiError,
  formatConfidence,
  formatExtractedValue,
  presentDocumentStatus,
  presentReviewDecision,
  presentReviewState,
  presentStatus,
} from '../services/presentation';

function axiosError(status?: number, data?: unknown): AxiosError {
  const config = { headers: new AxiosHeaders() };
  const response =
    status === undefined
      ? undefined
      : { status, statusText: '', headers: {}, config, data };
  return new AxiosError('falha', 'ERR', config, undefined, response);
}

describe('presentStatus', () => {
  it('labels each compliance status distinctly', () => {
    expect(presentStatus('COMPLIANT')).toEqual({ label: 'Conforme', tone: 'success' });
    expect(presentStatus('NON_COMPLIANT').tone).toBe('danger');
    expect(presentStatus('MANUAL_REVIEW_REQUIRED')).toEqual({ label: 'Revisão Manual', tone: 'warning' });
    expect(presentStatus('NOT_APPLICABLE')).toEqual({ label: 'Não Aplicável', tone: 'neutral' });
  });

  it('never presents an unknown status as compliant', () => {
    expect(presentStatus('ALGO_NOVO').tone).toBe('warning');
    expect(presentStatus('').label).toBe('Revisão Manual');
  });
});

describe('describeApiError', () => {
  it('uses the backend detail when available', () => {
    const error = axiosError(400, { detail: 'Arquivo fornecido nao possui assinatura binaria valida de PDF (%PDF-).' });
    expect(describeApiError(error, 'Falha no envio.')).toContain('assinatura binaria');
  });

  it('reports the HTTP status when there is no detail', () => {
    expect(describeApiError(axiosError(503, {}), 'Falha no envio.')).toBe('Falha no envio. (HTTP 503)');
  });

  it('explains when the API did not respond', () => {
    expect(describeApiError(axiosError(), 'Falha no envio.')).toContain('A API não respondeu');
  });

  it('falls back to the generic message for non-HTTP errors', () => {
    expect(describeApiError(new Error('x'), 'Falha no envio.')).toBe('Falha no envio.');
  });
});

describe('review presentation helpers', () => {
  it('labels each review state distinctly', () => {
    expect(presentReviewState('NO_REVIEW').tone).toBe('neutral');
    expect(presentReviewState('PENDING_CHECK')).toEqual({
      label: 'Aguardando 2º Analista',
      tone: 'warning',
    });
    expect(presentReviewState('FINAL').tone).toBe('success');
    expect(presentReviewState('RETURNED').tone).toBe('danger');
  });

  it('formats review decisions in Portuguese', () => {
    expect(presentReviewDecision('APPROVE')).toBe('Aprovar Laudo');
    expect(presentReviewDecision('REJECT')).toBe('Reprovar Laudo');
    expect(presentReviewDecision('EXCEPTION')).toBe('Aprovar com Exceção Motivada');
    expect(presentReviewDecision(null)).toBe('-');
  });

  it('labels document processing statuses with distinct tones', () => {
    expect(presentDocumentStatus('PENDING').tone).toBe('neutral');
    expect(presentDocumentStatus('PROCESSING').tone).toBe('warning');
    expect(presentDocumentStatus('COMPLETED')).toEqual({ label: 'Concluído', tone: 'success' });
    expect(presentDocumentStatus('FAILED').tone).toBe('danger');
    expect(presentDocumentStatus('EXTRACTION_FAILED').tone).toBe('danger');
  });
});

describe('formatExtractedValue', () => {
  it('usa o texto bruto quando o valor está ausente ou vazio', () => {
    expect(formatExtractedValue(null, '12/2026')).toBe('12/2026');
    expect(formatExtractedValue('  ', 'bruto')).toBe('bruto');
    expect(formatExtractedValue(undefined, null)).toBe('-');
  });

  it('formata números, booleanos e objetos sem "[object Object]"', () => {
    expect(formatExtractedValue(42)).toBe('42');
    expect(formatExtractedValue(false)).toBe('false');
    expect(formatExtractedValue({ uf: 'DF' })).toBe('{"uf":"DF"}');
    expect(formatExtractedValue(['a', 'b'])).toBe('["a","b"]');
  });
});

describe('formatConfidence', () => {
  it('mostra a confiança só quando é menor que 100%', () => {
    expect(formatConfidence(0.734)).toBe('Confiança 73%');
    expect(formatConfidence(0)).toBe('Confiança 0%');
    expect(formatConfidence(1)).toBeNull();
  });

  it('ignora valores ausentes ou fora de [0, 1]', () => {
    expect(formatConfidence(undefined)).toBeNull();
    expect(formatConfidence(null)).toBeNull();
    expect(formatConfidence(Number.NaN)).toBeNull();
    expect(formatConfidence(-0.1)).toBeNull();
    expect(formatConfidence(1.5)).toBeNull();
  });
});
