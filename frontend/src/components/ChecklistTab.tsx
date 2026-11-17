import { RefreshCw } from 'lucide-react';
import { ComplianceRule } from '../services/api';

interface ChecklistTabProps {
  rules: ComplianceRule[];
  loadingRules: boolean;
  onRefreshRules: () => void;
}

export function ChecklistTab({ rules, loadingRules, onRefreshRules }: ChecklistTabProps) {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-bold text-slate-900">Checklist Declarativo de Conformidade</h3>
          <p className="text-sm text-slate-500">
            Regras normativas configuradas conforme o edital da Consulta Pública BNDES nº 01/2025.
          </p>
        </div>
        <button
          onClick={onRefreshRules}
          className="px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-medium text-slate-600 hover:bg-slate-100 flex items-center space-x-1"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loadingRules ? 'animate-spin' : ''}`} />
          <span>Atualizar Catálogo</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {rules.map((rule) => (
          <div
            key={rule.id}
            className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 flex flex-col justify-between hover:shadow-md transition-shadow"
          >
            <div>
              <div className="flex justify-between items-start mb-3">
                <span className="px-2 py-0.5 text-xs font-mono font-bold rounded bg-slate-100 text-slate-700">
                  {rule.code}
                </span>
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                  {rule.type}
                </span>
              </div>
              <h4 className="text-sm font-bold text-slate-900 mb-2">{rule.title}</h4>
              <p className="text-xs text-slate-500 leading-relaxed mb-4">{rule.failure_message}</p>
            </div>
            <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400">
              <span className="font-semibold text-slate-600">Categoria: {rule.category}</span>
              <span className="font-mono">{rule.id}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
