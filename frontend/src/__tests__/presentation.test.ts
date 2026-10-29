import { describe, it, expect } from 'vitest';
import { AxiosError, AxiosHeaders } from 'axios';
import { describeApiError, presentStatus } from '../services/presentation';

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
