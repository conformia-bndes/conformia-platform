import React from 'react';
import { PageEvidence } from '../services/api';
import { TONE_CLASSES } from '../services/presentation';

export interface EvidenceCardProps {
  evidence: PageEvidence;
  label?: string;
}

/**
 * Componente de exibição de evidência ancorada por página.
 *
 * Critério de aceite:
 * - Mostra o trecho literal (text) que fundamenta o resultado
 * - Mostra a página (page) que fundamenta o resultado
 * - Exibe confiança (confidence) quando disponível
 */
export function EvidenceCard({ evidence, label }: EvidenceCardProps) {
  return (
    <details className="bg-white rounded-lg border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
      <summary className="flex items-center justify-between px-4 py-3 cursor-pointer list-none">
        <div className="flex items-center space-x-2">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          <span className="text-sm font-medium text-slate-700">
            {label ?? 'Evidência de apoio'}
          </span>
        </div>
        <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-500">
          Página {evidence.page}
        </span>
      </summary>
      <div className="px-4 pb-4 space-y-3">
        <blockquote className="border-l-2 border-slate-300 pl-3 text-sm text-slate-600 italic">
          &ldquo;{evidence.text}&rdquo;
        </blockquote>
        {evidence.confidence !== undefined && evidence.confidence < 1.0 && (
          <p className="text-xs text-amber-600">
            Confiança: {(evidence.confidence * 100).toFixed(0)}%
          </p>
        )}
      </div>
    </details>
  );
}

/**
 * Estado vazio explícito quando não há evidência.
 */
export function EvidenceEmptyState({ message = 'Nenhuma evidência disponível para este critério.' }: { message?: string }) {
  return (
    <div className="bg-slate-50 rounded-lg border border-slate-200 px-4 py-3 text-sm text-slate-500">
      <span className="font-medium">Sem evidências:</span> {message}
    </div>
  );
}
