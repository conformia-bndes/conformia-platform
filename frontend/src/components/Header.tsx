import {
  ShieldCheck,
  RefreshCw,
  UploadCloud,
  ListFilter,
  History,
  KeyRound,
} from 'lucide-react';
import { HealthResponse } from '../services/api';

export type ActiveTab = 'upload' | 'checklist' | 'audit';

interface HeaderProps {
  activeTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
  health: HealthResponse | null;
  healthLoading: boolean;
  healthError: boolean;
  onRefreshHealth: () => void;
  apiKeyLabel: string | null;
  onOpenApiKeyModal: () => void;
}

export function Header({
  activeTab,
  onTabChange,
  health,
  healthLoading,
  healthError,
  onRefreshHealth,
  apiKeyLabel,
  onOpenApiKeyModal,
}: HeaderProps) {
  return (
    <header className="bg-slate-900 border-b border-slate-800 text-white shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-20">
          <div className="flex items-center space-x-4">
            <div className="w-11 h-11 rounded-lg bg-emerald-600 flex items-center justify-center text-white shadow-md">
              <ShieldCheck className="w-7 h-7" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xl font-bold tracking-tight text-white">Conform.IA</span>
                <span className="px-2 py-0.5 text-xs font-semibold rounded bg-emerald-800 text-emerald-200 uppercase">
                  BNDES
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Consulta Pública nº 01/2025 • Verificação Inteligente de Conformidade
              </p>
            </div>
          </div>

          {/* Chave do Analista e Indicador de Status da API */}
          <div className="flex items-center space-x-3">
            <button
              type="button"
              onClick={onOpenApiKeyModal}
              title={
                apiKeyLabel
                  ? `Chave de sessão ativa (${apiKeyLabel}). Clique para alterar ou remover.`
                  : 'Informar chave pessoal (X-API-Key) para operações autenticadas'
              }
              className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-full border text-xs font-medium transition-colors ${
                apiKeyLabel
                  ? 'bg-emerald-950/60 border-emerald-700 text-emerald-200 hover:bg-emerald-900/70'
                  : 'bg-slate-800 border-slate-700 text-slate-300 hover:text-white hover:border-slate-500'
              }`}
            >
              <KeyRound className="w-3.5 h-3.5" />
              <span>{apiKeyLabel ? `Analista: ${apiKeyLabel}` : 'Informar Chave'}</span>
            </button>

            <div className="flex items-center space-x-2 bg-slate-800 px-3.5 py-1.5 rounded-full border border-slate-700">
              <span className="relative flex h-2.5 w-2.5">
                {healthLoading ? (
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
                ) : !healthError ? (
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
                ) : (
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-rose-500"></span>
                )}
              </span>
              <span className="text-xs font-medium text-slate-300">
                {healthLoading
                  ? 'Conectando...'
                  : healthError
                    ? 'API Offline'
                    : health?.status === 'healthy'
                      ? `API Online (v${health.version})`
                      : 'API Degradada'}
              </span>
              <button
                onClick={onRefreshHealth}
                title="Atualizar Status"
                className="text-slate-400 hover:text-white transition-colors ml-1"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${healthLoading ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Abas de Navegação */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <nav className="flex space-x-8 -mb-px">
          <button
            onClick={() => onTabChange('upload')}
            className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 transition-colors ${
              activeTab === 'upload'
                ? 'border-emerald-500 text-emerald-400'
                : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700'
            }`}
          >
            <UploadCloud className="w-4 h-4" />
            <span>Ingestão Documental (IDP)</span>
          </button>

          <button
            onClick={() => onTabChange('checklist')}
            className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 transition-colors ${
              activeTab === 'checklist'
                ? 'border-emerald-500 text-emerald-400'
                : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700'
            }`}
          >
            <ListFilter className="w-4 h-4" />
            <span>Checklist de Conformidade</span>
          </button>

          <button
            onClick={() => onTabChange('audit')}
            className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 transition-colors ${
              activeTab === 'audit'
                ? 'border-emerald-500 text-emerald-400'
                : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700'
            }`}
          >
            <History className="w-4 h-4" />
            <span>Trilha de Auditoria</span>
          </button>
        </nav>
      </div>
    </header>
  );
}
