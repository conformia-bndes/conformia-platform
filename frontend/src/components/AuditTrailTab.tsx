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
      <div className="flex flex-wrap justify-between items-center gap-4">
        <div>
          <h3 className="text-lg font-bold text-bndes-blue tracking-tight">Trilha de Auditoria Imutável</h3>
          <p className="text-sm text-bndes-ink-secondary">
            Registro cronológico de todas as decisões automatizadas, avaliações Maker-Checker e uploads.
          </p>
        </div>
        <button
          type="button"
          onClick={onRefreshAudit}
          className="px-3.5 py-2 rounded border border-bndes-border-strong bg-white text-xs font-semibold text-bndes-blue hover:bg-bndes-blue-tint hover:border-bndes-blue flex items-center space-x-1.5 transition-colors cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loadingAudit ? 'animate-spin' : ''}`} />
          <span>Atualizar Logs</span>
        </button>
      </div>

      <div className="bg-white rounded-md shadow-(--shadow-bndes-card) border border-bndes-border overflow-hidden">
        {loadingAudit && auditLogs.length === 0 ? (
          <div className="p-8 text-center text-bndes-ink-muted text-sm">
            Carregando trilha de auditoria...
          </div>
        ) : auditLogs.length === 0 ? (
          <div className="p-8 text-center text-bndes-ink-muted text-sm">
            Nenhum evento de auditoria registrado até o momento.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-bndes-ink-secondary">
              <thead className="bg-bndes-surface-muted text-xs font-bold uppercase tracking-wider text-bndes-blue border-b border-bndes-border">
                <tr>
                  <th className="px-6 py-4">Data / Hora</th>
                  <th className="px-6 py-4">Ação</th>
                  <th className="px-6 py-4">Entidade</th>
                  <th className="px-6 py-4">Agente Responsável</th>
                  <th className="px-6 py-4">Detalhes</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-bndes-border">
                {auditLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-bndes-bg/70 transition-colors">
                    <td className="px-6 py-4 text-xs font-mono text-bndes-ink-muted whitespace-nowrap">
                      {new Date(log.timestamp).toLocaleString('pt-BR')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-0.5 rounded text-xs font-semibold bg-bndes-blue-tint text-bndes-blue border border-bndes-blue-border">
                        {log.action}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-xs font-mono font-medium text-bndes-ink whitespace-nowrap">
                      {log.entity_type}: {log.entity_id}
                    </td>
                    <td className="px-6 py-4 text-xs text-bndes-ink-secondary whitespace-nowrap">
                      {log.performed_by}
                    </td>
                    <td className="px-6 py-4 text-xs font-mono text-bndes-ink-muted max-w-xs truncate">
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
