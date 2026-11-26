import React, { useState } from 'react';
import {
  UserCheck,
  KeyRound,
  Send,
  CheckCircle2,
  RotateCcw,
  Clock,
  AlertTriangle,
} from 'lucide-react';
import {
  apiService,
  ReviewDecision,
  ReviewStateResponse,
} from '../services/api';
import {
  describeApiError,
  presentReviewDecision,
  presentReviewState,
  TONE_CLASSES,
} from '../services/presentation';

interface HumanReviewPanelProps {
  documentId: string;
  overallStatus: string;
  reviewState: ReviewStateResponse | null;
  loading: boolean;
  loadError: string | null;
  apiKeyLabel: string | null;
  onOpenApiKeyModal: () => void;
  onReviewUpdated: () => Promise<void> | void;
}

export function HumanReviewPanel({
  documentId,
  overallStatus,
  reviewState,
  loading,
  loadError,
  apiKeyLabel,
  onOpenApiKeyModal,
  onReviewUpdated,
}: HumanReviewPanelProps) {
  const isNonCompliant = overallStatus === 'NON_COMPLIANT';
  const [decision, setDecision] = useState<ReviewDecision>(isNonCompliant ? 'REJECT' : 'APPROVE');
  const [justification, setJustification] = useState<string>('');
  const [comment, setComment] = useState<string>('');
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const stateBadge = reviewState ? presentReviewState(reviewState.state) : null;
  const pendingProposal =
    reviewState?.pending_proposal_id && reviewState.events
      ? reviewState.events.find((ev) => ev.id === reviewState.pending_proposal_id) ?? null
      : null;

  const isSameActor = Boolean(
    apiKeyLabel && pendingProposal && apiKeyLabel === pendingProposal.actor_id,
  );

  const canPropose =
    reviewState && (reviewState.state === 'NO_REVIEW' || reviewState.state === 'RETURNED');
  const canResolve = reviewState && reviewState.state === 'PENDING_CHECK';

  const handlePropose = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = justification.trim();
    if (trimmed.length < 20) {
      setActionError('A justificativa técnica deve ter pelo menos 20 caracteres.');
      return;
    }

    try {
      setSubmitting(true);
      setActionError(null);
      await apiService.proposeReview(documentId, decision, trimmed);
      setJustification('');
      await onReviewUpdated();
    } catch (err) {
      setActionError(describeApiError(err, 'Não foi possível registrar a proposta de revisão.'));
    } finally {
      setSubmitting(false);
    }
  };

  const handleResolve = async (action: 'confirm' | 'return') => {
    if (!reviewState?.pending_proposal_id) return;
    const trimmed = comment.trim();
    if (trimmed.length < 10) {
      setActionError('O parecer do segundo analista deve ter pelo menos 10 caracteres.');
      return;
    }

    try {
      setSubmitting(true);
      setActionError(null);
      if (action === 'confirm') {
        await apiService.confirmReview(documentId, reviewState.pending_proposal_id, trimmed);
      } else {
        await apiService.returnReview(documentId, reviewState.pending_proposal_id, trimmed);
      }
      setComment('');
      await onReviewUpdated();
    } catch (err) {
      setActionError(
        describeApiError(
          err,
          action === 'confirm'
            ? 'Não foi possível confirmar a proposta.'
            : 'Não foi possível devolver a proposta.',
        ),
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="border-t border-slate-200 pt-5 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center space-x-2">
          <UserCheck className="w-4 h-4 text-emerald-600" />
          <h4 className="text-sm font-semibold text-slate-800">
            Revisão Humana (Maker-Checker / Quatro Olhos)
          </h4>
        </div>

        {stateBadge && (
          <span
            className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${TONE_CLASSES[stateBadge.tone]}`}
          >
            {stateBadge.label}
            {reviewState?.state === 'FINAL' && reviewState.final_decision
              ? ` • ${presentReviewDecision(reviewState.final_decision)}`
              : ''}
          </span>
        )}
      </div>

      {loading && (
        <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-500">
          Carregando estado da revisão humana...
        </div>
      )}

      {!loading && loadError && (
        <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-700">
          {loadError}
        </div>
      )}

      {!loading && !loadError && reviewState && (
        <div className="space-y-4">
          {!apiKeyLabel && (
            <div className="p-3.5 rounded-lg bg-amber-50 border border-amber-200 flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center space-x-2 text-xs text-amber-900">
                <KeyRound className="w-4 h-4 text-amber-600 shrink-0" />
                <span>
                  Informe sua chave pessoal de <strong>ANALISTA</strong> para propor, confirmar ou devolver decisões.
                </span>
              </div>
              <button
                type="button"
                onClick={onOpenApiKeyModal}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-amber-600 hover:bg-amber-700 text-white transition-colors"
              >
                Informar Chave
              </button>
            </div>
          )}

          {actionError && (
            <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-700">
              {actionError}
            </div>
          )}

          {/* Etapa 1: Propor Decisão (Maker) */}
          {canPropose && (
            <form
              onSubmit={handlePropose}
              className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-3"
            >
              <p className="text-xs font-semibold text-slate-800">
                Propor Decisão sobre o Laudo (1º Analista - Maker)
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                {(['APPROVE', 'REJECT', 'EXCEPTION'] as ReviewDecision[]).map((option) => {
                  const disabled = isNonCompliant && option === 'APPROVE';
                  const selected = decision === option;
                  return (
                    <button
                      key={option}
                      type="button"
                      disabled={disabled || submitting}
                      onClick={() => setDecision(option)}
                      className={`px-3 py-2 rounded-lg text-xs font-semibold border text-left transition-colors ${
                        disabled
                          ? 'bg-slate-100 border-slate-200 text-slate-400 cursor-not-allowed'
                          : selected
                            ? 'bg-emerald-600 border-emerald-600 text-white'
                            : 'bg-white border-slate-300 text-slate-700 hover:bg-slate-100'
                      }`}
                    >
                      {presentReviewDecision(option)}
                    </button>
                  );
                })}
              </div>

              {isNonCompliant && (
                <p className="text-[11px] text-slate-500">
                  Laudos <strong>Não Conformes</strong> não podem ser aprovados diretamente; utilize{' '}
                  <strong>Reprovar Laudo</strong> ou <strong>Aprovar com Exceção Motivada</strong>.
                </p>
              )}

              <div>
                <div className="flex justify-between items-center mb-1">
                  <label htmlFor="review-justification" className="text-xs font-medium text-slate-700">
                    Justificativa Técnica (mínimo 20 caracteres)
                  </label>
                  <span className="text-[11px] text-slate-400">
                    {justification.trim().length}/4000
                  </span>
                </div>
                <textarea
                  id="review-justification"
                  rows={3}
                  value={justification}
                  onChange={(e) => setJustification(e.target.value)}
                  disabled={!apiKeyLabel || submitting}
                  placeholder="Descreva os fundamentos normativos e as evidências observadas..."
                  className="w-full px-3 py-2 text-xs bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 disabled:bg-slate-100"
                />
              </div>

              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={!apiKeyLabel || submitting || justification.trim().length < 20}
                  className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-lg text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>{submitting ? 'Enviando...' : 'Enviar Proposta (Maker)'}</span>
                </button>
              </div>
            </form>
          )}

          {/* Etapa 2: Confirmar ou Devolver Proposta (Checker) */}
          {canResolve && pendingProposal && (
            <div className="p-4 rounded-lg bg-amber-50/70 border border-amber-200 space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="text-xs font-semibold text-amber-900">
                  Proposta Pendente de Verificação (2º Analista - Checker)
                </p>
                <span className="text-[11px] font-mono text-amber-800">
                  Autor: {pendingProposal.actor_id} • {presentReviewDecision(pendingProposal.decision)}
                </span>
              </div>

              <div className="p-3 rounded bg-white border border-amber-200/80 text-xs text-slate-700">
                {pendingProposal.justification}
              </div>

              {isSameActor && (
                <div className="p-2.5 rounded bg-rose-50 border border-rose-200 flex items-center space-x-2 text-xs text-rose-800">
                  <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
                  <span>
                    Segregação de funções: <strong>{apiKeyLabel}</strong> propôs esta decisão. Troque para a chave de outro analista no cabeçalho para confirmar ou devolver.
                  </span>
                </div>
              )}

              <div>
                <div className="flex justify-between items-center mb-1">
                  <label htmlFor="review-comment" className="text-xs font-medium text-slate-700">
                    Parecer do Revisor (mínimo 10 caracteres)
                  </label>
                  <span className="text-[11px] text-slate-400">
                    {comment.trim().length}/4000
                  </span>
                </div>
                <textarea
                  id="review-comment"
                  rows={2}
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  disabled={!apiKeyLabel || isSameActor || submitting}
                  placeholder="Registre seu parecer ao confirmar ou devolver a proposta..."
                  className="w-full px-3 py-2 text-xs bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 disabled:bg-slate-100"
                />
              </div>

              <div className="flex flex-wrap justify-end gap-2">
                <button
                  type="button"
                  disabled={!apiKeyLabel || isSameActor || submitting || comment.trim().length < 10}
                  onClick={() => handleResolve('return')}
                  className="inline-flex items-center space-x-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>Devolver Proposta</span>
                </button>
                <button
                  type="button"
                  disabled={!apiKeyLabel || isSameActor || submitting || comment.trim().length < 10}
                  onClick={() => handleResolve('confirm')}
                  className="inline-flex items-center space-x-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Confirmar Proposta</span>
                </button>
              </div>
            </div>
          )}

          {/* Histórico Imutável de Eventos de Revisão */}
          <div className="space-y-2">
            <div className="flex items-center space-x-1.5 text-xs font-medium text-slate-600">
              <Clock className="w-3.5 h-3.5" />
              <span>Histórico de Revisão ({reviewState.events.length})</span>
            </div>

            {reviewState.events.length === 0 ? (
              <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-500">
                Nenhum evento de revisão registrado para este documento.
              </div>
            ) : (
              <div className="divide-y divide-slate-100 border border-slate-200 rounded-lg overflow-hidden bg-white">
                {reviewState.events.map((ev) => (
                  <div key={ev.id} className="p-3 space-y-1">
                    <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                      <div className="flex items-center space-x-2">
                        <span className="px-2 py-0.5 rounded font-semibold bg-slate-100 text-slate-700">
                          {ev.event_type}
                        </span>
                        {ev.decision && (
                          <span className="font-semibold text-slate-800">
                            {presentReviewDecision(ev.decision)}
                          </span>
                        )}
                        <span className="font-mono text-slate-500">
                          por {ev.actor_id} ({ev.actor_role})
                        </span>
                      </div>
                      <span className="font-mono text-[11px] text-slate-400">
                        {new Date(ev.created_at).toLocaleString('pt-BR')}
                      </span>
                    </div>
                    <p className="text-xs text-slate-600">{ev.justification}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
