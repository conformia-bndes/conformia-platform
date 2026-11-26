import { describe, it, expect } from 'vitest';
import { AxiosError, AxiosHeaders } from 'axios';
import {
  describeApiError,
  formatRuleEvidenceEntries,
  presentAuditAction,
  presentDocumentStatus,
  presentDocumentType,
  presentExtractedFieldName,
  presentReviewDecision,
  presentReviewEventType,
  presentReviewState,
  presentReviewSummary,
  presentRuleType,
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

  it('formats rule evidence in Portuguese without [object Object]', () => {
    const entries = formatRuleEvidenceEntries({
      matched_keywords: ['CERTIDÃO NEGATIVA', 'RFB'],
      missing_keywords: [],
      validity_date: '15/05/2027',
      hallucination_detected: false,
      nested_detail: { page: 1 },
    });

    expect(entries).toEqual([
      {
        key: 'matched_keywords',
        label: 'Palavras-chave encontradas',
        displayValue: 'CERTIDÃO NEGATIVA, RFB',
      },
      {
        key: 'validity_date',
        label: 'Validade extraída',
        displayValue: '15/05/2027',
      },
      {
        key: 'hallucination_detected',
        label: 'Inconsistência detectada',
        displayValue: 'Não',
      },
      {
        key: 'nested_detail',
        label: 'nested_detail',
        displayValue: '{"page":1}',
      },
    ]);
  });

  it('uses semantic tones for final review summary based on final decision', () => {
    expect(presentReviewSummary('FINAL', 'APPROVE').tone).toBe('success');
    expect(presentReviewSummary('FINAL', 'REJECT')).toEqual({
      label: 'Revisão Concluída • Reprovar Laudo',
      tone: 'danger',
    });
    expect(presentReviewSummary('FINAL', 'EXCEPTION').tone).toBe('warning');
    expect(presentReviewSummary('PENDING_CHECK', null).tone).toBe('warning');
  });

  it('translates review events, rule types, document types, fields and audit actions', () => {
    expect(presentReviewEventType('PROPOSED')).toEqual({ label: 'Proposta', tone: 'neutral' });
    expect(presentReviewEventType('CONFIRMED')).toEqual({ label: 'Confirmada', tone: 'success' });
    expect(presentReviewEventType('RETURNED')).toEqual({ label: 'Devolvida', tone: 'danger' });

    expect(presentRuleType('DETERMINISTIC')).toBe('Determinística');
    expect(presentRuleType('HYBRID')).toBe('Híbrida (IA + Regras)');

    expect(presentDocumentType('CND_FEDERAL')).toBe('CND Federal (RFB / PGFN)');
    expect(presentDocumentType(null)).toBe('Não identificada (revisão manual)');

    expect(presentExtractedFieldName('data_validade')).toBe('Data de Validade');
    expect(presentAuditAction('DOCUMENT_UPLOADED')).toBe('Documento Enviado');
  });
});
