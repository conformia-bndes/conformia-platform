import { FileSearch, Quote } from 'lucide-react';
import { ExtractionResult } from '../services/api';
import { formatConfidence, formatExtractedValue } from '../services/presentation';

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
  const fields = extraction ? Object.values(extraction.fields || {}) : [];
  const evidences = extraction?.evidences || [];

  return (
    <div className="border-t border-slate-200 pt-5 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <FileSearch className="w-4 h-4 text-emerald-600" />
          <h4 className="text-sm font-semibold text-slate-800">
            Evidências e Campos Extraídos por Página
          </h4>
        </div>
        {extraction && (
          <span className="text-xs text-slate-500">
            {extraction.total_pages} página(s) analisada(s)
          </span>
        )}
      </div>

      {loading && (
        <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-500">
          Carregando evidências extraídas do documento...
        </div>
      )}

      {!loading && error && (
        <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-700">
          {error}
        </div>
      )}

      {!loading && !error && !extraction && (
        <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-500">
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
                  className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-mono font-semibold uppercase text-slate-500">
                      {field.name}
                    </span>
                    {field.evidence?.page && (
                      <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-slate-200 text-slate-700">
                        Pág. {field.evidence.page}
                      </span>
                    )}
                  </div>
                  <p className="text-xs font-semibold text-slate-900 break-words">
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
              <p className="text-xs font-medium text-slate-600">
                Trechos literais localizados ({evidences.length})
              </p>
              <div className="divide-y divide-slate-100 border border-slate-200 rounded-lg overflow-hidden bg-white">
                {evidences.map((ev, index) => (
                  <div key={`${ev.page}-${index}`} className="p-3 flex items-start justify-between gap-3">
                    <div className="flex items-start space-x-2 min-w-0">
                      <Quote className="w-3.5 h-3.5 text-emerald-600 mt-0.5 shrink-0" />
                      <p className="text-xs font-mono text-slate-700 break-words">{ev.text}</p>
                    </div>
                    <div className="shrink-0 flex flex-col items-end gap-1">
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
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
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-500">
              Nenhum trecho literal de evidência foi registrado na extração.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
