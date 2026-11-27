import { useState } from 'react';
import { FileSearch, Quote, ChevronDown, ChevronUp } from 'lucide-react';
import { ExtractionResult } from '../services/api';
import {
  formatConfidence,
  formatExtractedValue,
  presentExtractedFieldName,
} from '../services/presentation';

interface PageEvidencesSectionProps {
  extraction: ExtractionResult | null | undefined;
  loading: boolean;
  error: string | null;
}

export function PageEvidencesSection({
  extraction,
  loading,
  error,
}: PageEvidencesSectionProps) {
  const [expanded, setExpanded] = useState<boolean>(true);
  const fields = extraction ? Object.values(extraction.fields || {}) : [];
  const evidences = extraction?.evidences || [];

  return (
    <div className="border-t border-bndes-border pt-5 space-y-4">
      <button
        type="button"
        onClick={() => setExpanded((prev) => !prev)}
        aria-expanded={expanded}
        aria-controls="page-evidences-content"
        className="w-full flex flex-wrap items-center justify-between gap-2 text-left py-1.5 px-2 -mx-2 rounded hover:bg-bndes-surface-muted/70 transition-colors cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-bndes-blue-2"
      >
        <div className="flex items-center space-x-2">
          <FileSearch className="w-4 h-4 text-bndes-blue shrink-0" aria-hidden="true" />
          <span className="text-sm font-bold text-bndes-blue">
            Evidências e Campos Extraídos por Página
            {extraction ? ` (${evidences.length})` : ''}
          </span>
        </div>
        <div className="flex items-center space-x-3">
          {extraction && (
            <span className="text-xs text-bndes-ink-muted font-medium">
              {extraction.total_pages} página(s) analisada(s)
            </span>
          )}
          <span className="inline-flex items-center space-x-1 text-xs font-semibold text-bndes-ink-secondary">
            <span>{expanded ? 'Recolher' : 'Expandir'}</span>
            {expanded ? (
              <ChevronUp className="w-4 h-4" aria-hidden="true" />
            ) : (
              <ChevronDown className="w-4 h-4" aria-hidden="true" />
            )}
          </span>
        </div>
      </button>

      {expanded && (
        <div id="page-evidences-content" className="space-y-4">

      {loading && (
        <div className="p-4 rounded-md bg-bndes-bg border border-bndes-border text-xs text-bndes-ink-muted">
          Carregando evidências extraídas do documento...
        </div>
      )}

      {!loading && error && (
        <div className="p-3 rounded-md bg-bndes-orange-tint border border-bndes-orange-border border-l-4 border-l-bndes-orange text-xs text-bndes-orange-ink font-medium">
          {error}
        </div>
      )}

      {!loading && !error && !extraction && (
        <div className="p-4 rounded-md bg-bndes-bg border border-bndes-border text-xs text-bndes-ink-muted">
          Nenhuma extração detalhada disponível para este documento.
        </div>
      )}

      {!loading && !error && extraction && (
        <div className="space-y-4">
          {fields.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {fields.map((field) => (
                <div
                  key={field.name}
                  className="p-3 rounded-md bg-bndes-bg border border-bndes-border space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-semibold uppercase text-bndes-ink-secondary">
                      {presentExtractedFieldName(field.name)}
                    </span>
                    {field.evidence?.page && (
                      <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-bndes-blue-tint text-bndes-blue border border-bndes-blue-border">
                        Pág. {field.evidence.page}
                      </span>
                    )}
                  </div>
                  <p className="text-xs font-semibold text-bndes-ink break-words">
                    {formatExtractedValue(field.value, field.raw_value)}
                  </p>
                  {formatConfidence(field.evidence?.confidence ?? field.confidence) && (
                    <p className="text-[10px] font-medium text-amber-700">
                      {formatConfidence(field.evidence?.confidence ?? field.confidence)}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}

          {evidences.length > 0 ? (
            <div className="space-y-2">
              <p className="text-xs font-semibold text-bndes-ink-secondary">
                Trechos literais localizados ({evidences.length})
              </p>
              <div className="divide-y divide-bndes-border border border-bndes-border rounded-md overflow-hidden bg-white">
                {evidences.map((ev, index) => (
                  <div key={`${ev.page}-${index}`} className="p-3 flex items-start justify-between gap-3">
                    <div className="flex items-start space-x-2 min-w-0">
                      <Quote className="w-3.5 h-3.5 text-bndes-green mt-0.5 shrink-0" />
                      <p className="text-xs font-mono text-bndes-ink break-words">{ev.text}</p>
                    </div>
                    <div className="shrink-0 flex flex-col items-end gap-1">
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-bndes-green-tint text-bndes-green-ink border border-bndes-green-border">
                        Pág. {ev.page}
                      </span>
                      {formatConfidence(ev.confidence) && (
                        <span className="text-[10px] font-medium text-amber-700">
                          {formatConfidence(ev.confidence)}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="p-3 rounded-md bg-bndes-bg border border-bndes-border text-xs text-bndes-ink-muted">
              Nenhum trecho literal de evidência foi registrado na extração.
            </div>
          )}
        </div>
      )}
        </div>
      )}
    </div>
  );
}
