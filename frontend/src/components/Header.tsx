import {
  RefreshCw,
  UploadCloud,
  ListFilter,
  History,
  KeyRound,
} from 'lucide-react';
import { HealthResponse } from '../services/api';
import logoBndesConformia from '../assets/logo-bndes-conformia.svg';

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
  const statusBadgeClasses = healthLoading
    ? 'bg-bndes-ochre-tint border-bndes-ochre-border text-bndes-ochre-ink'
    : healthError
      ? 'bg-bndes-orange-tint border-bndes-orange-border text-bndes-orange-ink'
      : health?.status === 'healthy'
        ? 'bg-bndes-green-tint border-bndes-green-border text-bndes-green-ink'
        : 'bg-bndes-ochre-tint border-bndes-ochre-border text-bndes-ochre-ink';

  return (
    <header className="bg-white shadow-(--shadow-bndes-card)">
      {/* Faixa institucional do sistema visual BNDES */}
      <div className="h-1 w-full bndes-brand-bar" aria-hidden="true" />

      {/* Barra principal em fundo branco (0% preto - Seção 1.5 do Manual) para máximo contraste da marca em cores */}
      <div className="border-b border-bndes-border bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center min-h-[5.25rem] py-2.5 sm:py-2 gap-3 sm:gap-4">
            <div className="flex items-center justify-between sm:justify-start">
              {/* Área de proteção equivalente à altura da letra "B" (Seção 1.9) sem distorção ou sombra (Seção 1.11) */}
              <div className="py-1 sm:py-2.5 pr-4 sm:pr-6 shrink-0">
                <img
                  src={logoBndesConformia}
                  alt="BNDES Conform.IA"
                  className="h-9 sm:h-11 w-auto object-contain select-none"
                />
              </div>

              <div className="hidden md:flex flex-col justify-center border-l border-bndes-border pl-5 py-1">
                <div className="flex items-center space-x-2">
                  <span className="px-2 py-0.5 text-[11px] font-bold tracking-wider rounded bg-bndes-blue text-white uppercase">
                    BNDES
                  </span>
                  <span className="text-xs font-semibold text-bndes-blue">
                    Plataforma de Conformidade Documental
                  </span>
                </div>
                <p className="text-xs text-bndes-ink-secondary mt-0.5">
                  Consulta Pública nº 01/2025 • Verificação Inteligente de Conformidade
                </p>
              </div>
            </div>

            {/* Chave do Analista e Indicador de Status da API */}
            <div className="flex flex-wrap items-center gap-2 sm:gap-2.5 w-full sm:w-auto justify-between sm:justify-end">
              <button
                type="button"
                onClick={onOpenApiKeyModal}
                title={
                  apiKeyLabel
                    ? `Chave de sessão ativa (${apiKeyLabel}). Clique para alterar ou remover.`
                    : 'Informar chave pessoal (X-API-Key) para operações autenticadas'
                }
                className={`flex items-center space-x-2 px-3.5 py-1.5 rounded border text-xs font-semibold transition-colors cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-bndes-blue-2 ${
                  apiKeyLabel
                    ? 'bg-bndes-green-tint border-bndes-green-border text-bndes-green-ink hover:bg-[#D8EFE2]'
                    : 'bg-bndes-surface-muted border-bndes-border-strong text-bndes-blue hover:bg-bndes-blue-tint hover:border-bndes-blue'
                }`}
              >
                <KeyRound className="w-3.5 h-3.5" aria-hidden="true" />
                <span>{apiKeyLabel ? `Analista: ${apiKeyLabel}` : 'Informar Chave'}</span>
              </button>

              <div
                className={`flex items-center space-x-2 px-3.5 py-1.5 rounded border ${statusBadgeClasses}`}
              >
                <span className="relative flex h-2.5 w-2.5" aria-hidden="true">
                  {healthLoading ? (
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-bndes-ochre opacity-75"></span>
                  ) : !healthError && health?.status === 'healthy' ? (
                    <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-bndes-green"></span>
                  ) : !healthError ? (
                    <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-bndes-ochre"></span>
                  ) : (
                    <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-bndes-orange"></span>
                  )}
                </span>
                <span className="text-xs font-semibold">
                  {healthLoading
                    ? 'Conectando...'
                    : healthError
                      ? 'API Offline'
                      : health?.status === 'healthy'
                        ? `API Online (v${health.version})`
                        : 'API Degradada'}
                </span>
                <button
                  type="button"
                  onClick={onRefreshHealth}
                  title="Atualizar Status"
                  aria-label="Atualizar status da API"
                  className="opacity-75 hover:opacity-100 transition-opacity ml-1 cursor-pointer rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-bndes-blue-2"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${healthLoading ? 'animate-spin motion-reduce:animate-none' : ''}`} aria-hidden="true" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Barra de Navegação Institucional em Azul 1 (#004A8F) */}
      <div className="bg-bndes-blue text-white">
        <div className="max-w-7xl mx-auto px-2 sm:px-6 lg:px-8">
          <div
            role="tablist"
            aria-label="Módulos da plataforma"
            className="grid grid-cols-3 sm:flex sm:space-x-2"
          >
            <button
              id="tab-upload"
              type="button"
              role="tab"
              aria-selected={activeTab === 'upload'}
              aria-controls="panel-upload"
              onClick={() => onTabChange('upload')}
              className={`py-2.5 sm:py-3.5 px-2 sm:px-4 border-b-[3px] text-[11px] sm:text-sm flex flex-col sm:flex-row items-center justify-center sm:justify-start gap-1 sm:gap-2 text-center sm:text-left leading-tight transition-colors cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white ${
                activeTab === 'upload'
                  ? 'border-bndes-green-2 bg-bndes-blue-deep/70 text-white font-semibold'
                  : 'border-transparent text-white/85 hover:text-white hover:bg-bndes-blue-3/70 font-medium'
              }`}
            >
              <UploadCloud className="w-4 h-4 shrink-0" aria-hidden="true" />
              <span>Ingestão Documental</span>
            </button>

            <button
              id="tab-checklist"
              type="button"
              role="tab"
              aria-selected={activeTab === 'checklist'}
              aria-controls="panel-checklist"
              onClick={() => onTabChange('checklist')}
              className={`py-2.5 sm:py-3.5 px-2 sm:px-4 border-b-[3px] text-[11px] sm:text-sm flex flex-col sm:flex-row items-center justify-center sm:justify-start gap-1 sm:gap-2 text-center sm:text-left leading-tight transition-colors cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white ${
                activeTab === 'checklist'
                  ? 'border-bndes-green-2 bg-bndes-blue-deep/70 text-white font-semibold'
                  : 'border-transparent text-white/85 hover:text-white hover:bg-bndes-blue-3/70 font-medium'
              }`}
            >
              <ListFilter className="w-4 h-4 shrink-0" aria-hidden="true" />
              <span>Checklist de Regras</span>
            </button>

            <button
              id="tab-audit"
              type="button"
              role="tab"
              aria-selected={activeTab === 'audit'}
              aria-controls="panel-audit"
              onClick={() => onTabChange('audit')}
              className={`py-2.5 sm:py-3.5 px-2 sm:px-4 border-b-[3px] text-[11px] sm:text-sm flex flex-col sm:flex-row items-center justify-center sm:justify-start gap-1 sm:gap-2 text-center sm:text-left leading-tight transition-colors cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white ${
                activeTab === 'audit'
                  ? 'border-bndes-green-2 bg-bndes-blue-deep/70 text-white font-semibold'
                  : 'border-transparent text-white/85 hover:text-white hover:bg-bndes-blue-3/70 font-medium'
              }`}
            >
              <History className="w-4 h-4 shrink-0" aria-hidden="true" />
              <span>Trilha de Auditoria</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
