import React, { useState } from 'react';
import { RefreshCw, ChevronDown, ChevronUp } from 'lucide-react';
import { AuditLogItem } from '../services/api';
import { presentAuditAction, presentAuditEntity } from '../services/presentation';

interface AuditTrailTabProps {
  auditLogs: AuditLogItem[];
  loadingAudit: boolean;
  onRefreshAudit: () => void;
}

export function AuditTrailTab({ auditLogs, loadingAudit, onRefreshAudit }: AuditTrailTabProps) {
  const [expandedLogId, setExpandedLogId] = useState<string | null>(null);

  const toggleExpand = (id: string) => {
    setExpandedLogId((prev) => (prev === id ? null : id));
  };

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
          className="w-full sm:w-auto justify-center px-3.5 py-2 rounded border border-bndes-border-strong bg-white text-xs font-semibold text-bndes-blue hover:bg-bndes-blue-tint hover:border-bndes-blue flex items-center space-x-1.5 transition-colors cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-bndes-blue-2"
        >
          <RefreshCw
            className={`w-3.5 h-3.5 ${loadingAudit ? 'animate-spin motion-reduce:animate-none' : ''}`}
            aria-hidden="true"
          />
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
                {auditLogs.map((log) => {
                  const isExpanded = expandedLogId === log.id;
                  return (
                    <React.Fragment key={log.id}>
                      <tr className="hover:bg-bndes-bg/70 transition-colors">
                        <td className="px-6 py-4 text-xs font-mono text-bndes-ink-muted whitespace-nowrap">
                          {new Date(log.timestamp).toLocaleString('pt-BR')}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="px-2 py-0.5 rounded text-xs font-semibold bg-bndes-blue-tint text-bndes-blue border border-bndes-blue-border">
                            {presentAuditAction(log.action)}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-xs font-mono font-medium text-bndes-ink whitespace-nowrap">
                          {presentAuditEntity(log.entity_type)}: {log.entity_id}
                        </td>
                        <td className="px-6 py-4 text-xs text-bndes-ink-secondary whitespace-nowrap">
                          {log.performed_by}
                        </td>
                        <td className="px-6 py-4 text-xs">
                          <button
                            type="button"
                            onClick={() => toggleExpand(log.id)}
                            aria-expanded={isExpanded}
                            className="inline-flex items-center space-x-1 px-2.5 py-1 rounded border border-bndes-border bg-bndes-surface-muted hover:bg-bndes-blue-tint text-bndes-blue font-semibold transition-colors cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-bndes-blue-2"
                          >
                            <span>{isExpanded ? 'Ocultar' : 'Ver detalhes'}</span>
                            {isExpanded ? (
                              <ChevronUp className="w-3.5 h-3.5" aria-hidden="true" />
                            ) : (
                              <ChevronDown className="w-3.5 h-3.5" aria-hidden="true" />
                            )}
                          </button>
                        </td>
                      </tr>
                      {isExpanded && (
                        <tr className="bg-bndes-bg/80">
                          <td colSpan={5} className="px-6 py-4">
                            <pre className="p-3 rounded bg-white border border-bndes-border text-xs font-mono text-bndes-ink overflow-x-auto whitespace-pre-wrap break-all">
                              {JSON.stringify(log.details, null, 2)}
                            </pre>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
