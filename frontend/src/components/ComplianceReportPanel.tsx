import { CheckCircle2, XCircle, X } from 'lucide-react';
import { ComplianceReport } from '../services/api';
import { presentStatus, TONE_CLASSES } from '../services/presentation';

interface ComplianceReportPanelProps {
  report: ComplianceReport;
  onClose: () => void;
}

export function ComplianceReportPanel({ report, onClose }: ComplianceReportPanelProps) {
  return (
    <div className="bg-white rounded-xl shadow-md border border-slate-200 p-6 space-y-6">
      <div className="flex justify-between items-start border-b border-slate-100 pb-4">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Resultado da Avaliação
          </span>
          <h3 className="text-lg font-bold text-slate-900 flex items-center space-x-2 mt-1">
            <span>Laudo de Conformidade: {report.document_filename}</span>
          </h3>
        </div>
        <div className="flex items-center space-x-2">
          <span
            className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
              TONE_CLASSES[presentStatus(report.overall_status).tone]
            }`}
          >
            {presentStatus(report.overall_status).label}
          </span>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 text-sm ml-2"
            title="Fechar Relatório"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Resumo com Métricas */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
          <p className="text-xs text-slate-500 font-medium">Score de Conformidade</p>
          <p className="text-2xl font-bold text-emerald-600 mt-1">
            {(report.compliance_score * 100).toFixed(0)}%
          </p>
        </div>
        <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
          <p className="text-xs text-slate-500 font-medium">Regras Conformes / Aplicáveis</p>
          <p className="text-2xl font-bold text-slate-800 mt-1">
            {report.compliant_rules} / {report.evaluated_rules}
          </p>
        </div>
        <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
          <p className="text-xs text-slate-500 font-medium">Tipologia Identificada</p>
          <p className="text-sm font-semibold text-slate-700 mt-2">
            {report.document_type ?? 'Não identificada (revisão manual)'}
          </p>
        </div>
      </div>

      {/* Itens Verificados */}
      <div className="space-y-3">
        <h4 className="text-sm font-semibold text-slate-800">Detalhamento dos Critérios BNDES</h4>
        <div className="divide-y divide-slate-100 border border-slate-200 rounded-lg overflow-hidden">
          {report.checks.map((c) => (
            <div
              key={c.rule_id}
              className="p-4 flex items-start justify-between bg-white hover:bg-slate-50"
            >
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-mono font-bold text-slate-500">{c.rule_id}</span>
                  <span className="text-sm font-semibold text-slate-900">{c.rule_title}</span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-slate-100 font-semibold text-slate-600 uppercase">
                    {c.category}
                  </span>
                </div>
                <p className="text-xs text-slate-600">{c.findings}</p>
              </div>
              <div className="flex items-center space-x-2">
                <span
                  className={`flex items-center text-xs font-semibold px-2 py-1 rounded space-x-1 ${
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
    </div>
  );
}
