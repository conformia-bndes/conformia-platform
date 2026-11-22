import { RefreshCw } from 'lucide-react';
import { AuditLogItem } from '../services/api';

interface AuditTrailTabProps {
  auditLogs: AuditLogItem[];
  loadingAudit: boolean;
  onRefreshAudit: () => void;
}

export function AuditTrailTab({ auditLogs, loadingAudit, onRefreshAudit }: AuditTrailTabProps) {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-bold text-slate-900">Trilha de Auditoria Imutável</h3>
          <p className="text-sm text-slate-500">
            Registro cronológico de todas as decisões automatizadas, avaliações Maker-Checker e uploads.
          </p>
        </div>
        <button
          onClick={onRefreshAudit}
          className="px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-medium text-slate-600 hover:bg-slate-100 flex items-center space-x-1"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loadingAudit ? 'animate-spin' : ''}`} />
          <span>Atualizar Logs</span>
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        {loadingAudit && auditLogs.length === 0 ? (
          <div className="p-8 text-center text-slate-400 text-sm">
            Carregando trilha de auditoria...
          </div>
        ) : auditLogs.length === 0 ? (
          <div className="p-8 text-center text-slate-400 text-sm">
            Nenhum evento de auditoria registrado até o momento.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="bg-slate-50 text-xs font-semibold uppercase text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="px-6 py-4">Data / Hora</th>
                  <th className="px-6 py-4">Ação</th>
                  <th className="px-6 py-4">Entidade</th>
                  <th className="px-6 py-4">Agente Responsável</th>
                  <th className="px-6 py-4">Detalhes</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {auditLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50/60">
                    <td className="px-6 py-4 text-xs font-mono text-slate-500 whitespace-nowrap">
                      {new Date(log.timestamp).toLocaleString('pt-BR')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-0.5 rounded text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
                        {log.action}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-xs font-mono font-medium text-slate-700 whitespace-nowrap">
                      {log.entity_type}: {log.entity_id}
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-600 whitespace-nowrap">
                      {log.performed_by}
                    </td>
                    <td className="px-6 py-4 text-xs font-mono text-slate-500 max-w-xs truncate">
                      {JSON.stringify(log.details)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
