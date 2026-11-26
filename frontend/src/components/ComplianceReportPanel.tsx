import { useEffect, useState, useCallback } from 'react';
import { CheckCircle2, XCircle, X } from 'lucide-react';
import {
  apiService,
  ComplianceReport,
  ExtractionResult,
  ReviewStateResponse,
} from '../services/api';
import { describeApiError, presentStatus, TONE_CLASSES } from '../services/presentation';
import { PageEvidencesSection } from './PageEvidencesSection';
import { HumanReviewPanel } from './HumanReviewPanel';

interface ComplianceReportPanelProps {
  report: ComplianceReport;
  apiKeyLabel: string | null;
  onOpenApiKeyModal: () => void;
  onClose: () => void;
}

function renderRuleEvidenceSummary(evidence: Record<string, unknown> | null | undefined) {
  if (!evidence) return null;
  const entries = Object.entries(evidence).filter(([, value]) => {
    if (value === null || value === undefined) return false;
    if (Array.isArray(value) && value.length === 0) return false;
    return true;
  });
  if (entries.length === 0) return null;

  return (
    <div className="mt-2 flex flex-wrap gap-1.5">
      {entries.map(([key, value]) => (
        <span
          key={key}
          className="inline-flex items-center px-2 py-0.5 rounded bg-bndes-surface-muted border border-bndes-border text-[11px] font-mono text-bndes-ink-secondary"
        >
          {key}: {Array.isArray(value) ? value.join(', ') : String(value)}
        </span>
      ))}
    </div>
  );
}

export function ComplianceReportPanel({
  report,
  apiKeyLabel,
  onOpenApiKeyModal,
  onClose,
}: ComplianceReportPanelProps) {
  const [extraction, setExtraction] = useState<ExtractionResult | null | undefined>(undefined);
  const [loadingExtraction, setLoadingExtraction] = useState<boolean>(true);
  const [extractionError, setExtractionError] = useState<string | null>(null);

  const [reviewState, setReviewState] = useState<ReviewStateResponse | null>(null);
  const [loadingReview, setLoadingReview] = useState<boolean>(true);
  const [reviewError, setReviewError] = useState<string | null>(null);

  const loadReviewState = useCallback(async () => {
    try {
      setLoadingReview(true);
      setReviewError(null);
      const data = await apiService.getReviewState(report.document_id);
      setReviewState(data);
    } catch (error) {
      setReviewState(null);
      setReviewError(describeApiError(error, 'Não foi possível carregar o estado da revisão humana.'));
    } finally {
      setLoadingReview(false);
    }
  }, [report.document_id]);

  useEffect(() => {
    let isMounted = true;

    apiService
      .getProcessingStatus(report.document_id)
      .then((res) => {
        if (isMounted) {
          setExtraction(res.extraction ?? null);
          setExtractionError(null);
        }
      })
      .catch((error) => {
        if (isMounted) {
          setExtraction(null);
          setExtractionError(
            describeApiError(error, 'Não foi possível carregar as evidências por página.'),
          );
        }
      })
      .finally(() => {
        if (isMounted) setLoadingExtraction(false);
      });

    apiService
      .getReviewState(report.document_id)
      .then((data) => {
        if (isMounted) {
          setReviewState(data);
          setReviewError(null);
        }
      })
      .catch((error) => {
        if (isMounted) {
          setReviewState(null);
          setReviewError(
            describeApiError(error, 'Não foi possível carregar o estado da revisão humana.'),
          );
        }
      })
      .finally(() => {
        if (isMounted) setLoadingReview(false);
      });

    return () => {
      isMounted = false;
    };
  }, [report.document_id]);

  return (
    <div className="bg-white rounded-md shadow-(--shadow-bndes-elevated) border border-bndes-border border-t-[3px] border-t-bndes-blue p-6 space-y-6">
      <div className="flex justify-between items-start border-b border-bndes-border pb-4">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-bndes-ink-muted">
            Resultado da Avaliação
          </span>
          <h3 className="text-lg font-bold text-bndes-blue flex items-center space-x-2 mt-1">
            <span>Laudo de Conformidade: {report.document_filename}</span>
          </h3>
        </div>
        <div className="flex items-center space-x-2">
          <span
            className={`px-3 py-1 rounded text-xs font-bold uppercase tracking-wider ${
              TONE_CLASSES[presentStatus(report.overall_status).tone]
            }`}
          >
            {presentStatus(report.overall_status).label}
          </span>
          <button
            type="button"
            onClick={onClose}
            className="text-bndes-ink-muted hover:text-bndes-ink text-sm ml-2 p-1 rounded cursor-pointer"
            title="Fechar Relatório"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Resumo com Métricas */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 rounded-md bg-bndes-bg border border-bndes-border">
          <p className="text-xs text-bndes-ink-secondary font-medium">Score de Conformidade</p>
          <p className="text-2xl font-bold text-bndes-green-ink mt-1">
            {(report.compliance_score * 100).toFixed(0)}%
          </p>
        </div>
        <div className="p-4 rounded-md bg-bndes-bg border border-bndes-border">
          <p className="text-xs text-bndes-ink-secondary font-medium">Regras Conformes / Aplicáveis</p>
          <p className="text-2xl font-bold text-bndes-blue mt-1">
            {report.compliant_rules} / {report.evaluated_rules}
          </p>
        </div>
        <div className="p-4 rounded-md bg-bndes-bg border border-bndes-border">
          <p className="text-xs text-bndes-ink-secondary font-medium">Tipologia Identificada</p>
          <p className="text-sm font-semibold text-bndes-ink mt-2">
            {report.document_type ?? 'Não identificada (revisão manual)'}
          </p>
        </div>
      </div>

      {/* Itens Verificados */}
      <div className="space-y-3">
        <h4 className="text-sm font-bold text-bndes-blue">Detalhamento dos Critérios BNDES</h4>
        <div className="divide-y divide-bndes-border border border-bndes-border rounded-md overflow-hidden">
          {report.checks.map((c) => (
            <div
              key={c.rule_id}
              className="p-4 flex items-start justify-between gap-4 bg-white hover:bg-bndes-bg/70 transition-colors"
            >
              <div className="space-y-1 min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xs font-mono font-bold text-bndes-blue">{c.rule_id}</span>
                  <span className="text-sm font-semibold text-bndes-ink">{c.rule_title}</span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-bndes-surface-muted border border-bndes-border font-semibold text-bndes-ink-secondary uppercase">
                    {c.category}
                  </span>
                </div>
                <p className="text-xs text-bndes-ink-secondary">{c.findings}</p>
                {renderRuleEvidenceSummary(c.evidence)}
              </div>
              <div className="flex items-center space-x-2 shrink-0">
                <span
                  className={`flex items-center text-xs font-semibold px-2.5 py-1 rounded space-x-1 ${
                    TONE_CLASSES[presentStatus(c.status).tone]
                  }`}
                >
                  {c.status === 'COMPLIANT' ? (
                    <CheckCircle2 className="w-4 h-4" />
                  ) : (
                    <XCircle className="w-4 h-4" />
                  )}
                  <span>{presentStatus(c.status).label}</span>
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Evidências e Campos Extraídos por Página */}
      <PageEvidencesSection
        extraction={extraction}
        loading={loadingExtraction}
        error={extractionError}
      />

      {/* Painel de Revisão Humana (Maker-Checker) */}
      <HumanReviewPanel
        key={report.document_id}
        documentId={report.document_id}
        overallStatus={report.overall_status}
        reviewState={reviewState}
        loading={loadingReview}
        loadError={reviewError}
        apiKeyLabel={apiKeyLabel}
        onOpenApiKeyModal={onOpenApiKeyModal}
        onReviewUpdated={loadReviewState}
      />
    </div>
  );
}
