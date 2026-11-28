import { RefreshCw } from 'lucide-react';
import { ComplianceRule } from '../services/api';
import { presentRuleType } from '../services/presentation';

interface ChecklistTabProps {
  rules: ComplianceRule[];
  loadingRules: boolean;
  onRefreshRules: () => void;
}

export function ChecklistTab({ rules, loadingRules, onRefreshRules }: ChecklistTabProps) {
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap justify-between items-center gap-4">
        <div>
          <h3 className="text-lg font-bold text-bndes-blue tracking-tight">
            Checklist Declarativo de Conformidade
          </h3>
          <p className="text-sm text-bndes-ink-secondary">
            Regras normativas configuradas conforme o edital da Consulta Pública BNDES nº 01/2025.
          </p>
        </div>
        <button
          type="button"
          onClick={onRefreshRules}
          className="px-3.5 py-2 rounded border border-bndes-border-strong bg-white text-xs font-semibold text-bndes-blue hover:bg-bndes-blue-tint hover:border-bndes-blue flex items-center space-x-1.5 transition-colors cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loadingRules ? 'animate-spin' : ''}`} />
          <span>Atualizar Catálogo</span>
        </button>
      </div>

      {loadingRules && rules.length === 0 ? (
        <div className="bg-white rounded-md shadow-(--shadow-bndes-card) border border-bndes-border p-8 text-center text-bndes-ink-muted text-sm">
          Carregando regras normativas...
        </div>
      ) : rules.length === 0 ? (
        <div className="bg-white rounded-md shadow-(--shadow-bndes-card) border border-bndes-border p-8 text-center text-bndes-ink-muted text-sm">
          Nenhuma regra normativa carregada.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {rules.map((rule) => (
            <div
              key={rule.id}
              className="bg-white rounded-md shadow-(--shadow-bndes-card) border border-bndes-border border-t-2 border-t-bndes-blue p-5 flex flex-col justify-between hover:shadow-(--shadow-bndes-elevated) transition-shadow"
            >
              <div>
                <div className="flex justify-between items-start mb-3">
                  <span className="px-2 py-0.5 text-xs font-mono font-bold rounded bg-bndes-blue-tint text-bndes-blue border border-bndes-blue-border">
                    {rule.code}
                  </span>
                  <span
                    className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded border ${
                      rule.type === 'HYBRID'
                        ? 'bg-bndes-purple-tint text-bndes-purple-ink border-bndes-purple-border'
                        : 'bg-bndes-green-tint text-bndes-green-ink border-bndes-green-border'
                    }`}
                  >
                    {presentRuleType(rule.type)}
                  </span>
                </div>
                <h4 className="text-sm font-bold text-bndes-ink mb-2">{rule.title}</h4>
                <p className="text-xs text-bndes-ink-secondary leading-relaxed mb-4">{rule.failure_message}</p>
              </div>
              <div className="pt-3 border-t border-bndes-border flex items-center justify-between text-xs text-bndes-ink-muted">
                <span className="font-semibold text-bndes-ink-secondary">Categoria: {rule.category}</span>
                <span className="font-mono">{rule.id}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
