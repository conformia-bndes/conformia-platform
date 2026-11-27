import { useEffect, useState, useCallback } from 'react';
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  MinusCircle,
  X,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import {
  apiService,
  ComplianceReport,
  ExtractionResult,
  ReviewStateResponse,
} from '../services/api';
import {
  describeApiError,
  formatRuleEvidenceEntries,
  presentDocumentType,
  presentStatus,
  StatusTone,
  TONE_CLASSES,
} from '../services/presentation';
import { PageEvidencesSection } from './PageEvidencesSection';
import { HumanReviewPanel } from './HumanReviewPanel';

interface ComplianceReportPanelProps {
  report: ComplianceReport;
  apiKeyLabel: string | null;
  onOpenApiKeyModal: () => void;
  onClose: () => void;
}

function renderRuleEvidenceSummary(evidence: Record<string, unknown> | null | undefined) {
  const entries = formatRuleEvidenceEntries(evidence);
  if (entries.length === 0) return null;

  return (
    <div className="mt-2 flex flex-wrap gap-1.5">
      {entries.map((entry) => (
        <span
          key={entry.key}
          className="inline-flex items-center px-2 py-0.5 rounded bg-bndes-surface-muted border border-bndes-border text-[11px] font-mono text-bndes-ink-secondary"
        >
          {entry.label}: {entry.displayValue}
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
  const [checksExpanded, setChecksExpanded] = useState<boolean>(true);

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
            className="text-bndes-ink-muted hover:text-bndes-ink text-sm ml-2 p-1 rounded cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-bndes-blue-2"
            title="Fechar Relatório"
            aria-label="Fechar laudo de conformidade"
          >
            <X className="w-4 h-4" aria-hidden="true" />
          </button>
        </div>
      </div>

      {/* Resumo com Métricas */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 rounded-md bg-bndes-bg border border-bndes-border">
          <p className="text-xs text-bndes-ink-secondary font-medium">Score de Conformidade</p>
          <p
            className={`text-2xl font-bold mt-1 ${
              (
                {
                  success: 'text-bndes-green-ink',
                  danger: 'text-bndes-orange-ink',
                  warning: 'text-bndes-ochre-ink',
                  neutral: 'text-bndes-ink-secondary',
                } as Record<StatusTone, string>
              )[presentStatus(report.overall_status).tone]
            }`}
          >
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
            {presentDocumentType(report.document_type)}
          </p>
        </div>
      </div>

      {/* Itens Verificados */}
      <div className="space-y-3">
        <button
          type="button"
          onClick={() => setChecksExpanded((prev) => !prev)}
          aria-expanded={checksExpanded}
          aria-controls="report-checks-list"
          className="w-full flex items-center justify-between gap-2 text-left py-1.5 px-2 -mx-2 rounded hover:bg-bndes-surface-muted/70 transition-colors cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-bndes-blue-2"
        >
          <span className="text-sm font-bold text-bndes-blue">
            Detalhamento dos Critérios BNDES ({report.checks.length})
          </span>
          <span className="inline-flex items-center space-x-1 text-xs font-semibold text-bndes-ink-secondary">
            <span>{checksExpanded ? 'Recolher' : 'Expandir'}</span>
            {checksExpanded ? (
              <ChevronUp className="w-4 h-4" aria-hidden="true" />
            ) : (
              <ChevronDown className="w-4 h-4" aria-hidden="true" />
            )}
          </span>
        </button>

        {checksExpanded && (
          <div
            id="report-checks-list"
            className="divide-y divide-bndes-border border border-bndes-border rounded-md overflow-hidden"
          >
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
                    <CheckCircle2 className="w-4 h-4" aria-hidden="true" />
                  ) : c.status === 'NON_COMPLIANT' ? (
                    <XCircle className="w-4 h-4" aria-hidden="true" />
                  ) : c.status === 'MANUAL_REVIEW_REQUIRED' ? (
                    <AlertTriangle className="w-4 h-4" aria-hidden="true" />
                  ) : (
                    <MinusCircle className="w-4 h-4" aria-hidden="true" />
                  )}
                  <span>{presentStatus(c.status).label}</span>
                </span>
              </div>
              </div>
            ))}
          </div>
        )}
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
