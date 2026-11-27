import React from 'react';
import { FileText, UploadCloud, ShieldCheck, RefreshCw, AlertTriangle, Clock } from 'lucide-react';
import { DocumentItem, ComplianceReport } from '../services/api';
import { PollingSnapshot } from '../services/polling';
import { presentDocumentStatus, TONE_CLASSES } from '../services/presentation';
import { ComplianceReportPanel } from './ComplianceReportPanel';

interface DocumentUploadTabProps {
  documents: DocumentItem[];
  loadingDocs: boolean;
  uploading: boolean;
  verifyingId: string | null;
  activeReport: ComplianceReport | null;
  apiKeyLabel: string | null;
  pollingState?: PollingSnapshot | null;
  onFileUpload: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onRefreshDocuments: () => void;
  onVerifyCompliance: (docId: string, filename: string) => void;
  onOpenApiKeyModal: () => void;
  onCloseReport: () => void;
}

export function DocumentUploadTab({
  documents,
  loadingDocs,
  uploading,
  verifyingId,
  activeReport,
  apiKeyLabel,
  pollingState,
  onFileUpload,
  onRefreshDocuments,
  onVerifyCompliance,
  onOpenApiKeyModal,
  onCloseReport,
}: DocumentUploadTabProps) {
  return (
    <div className="space-y-8">
      {/* Área de Ingestão de Documentos */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
        <div className="max-w-2xl mx-auto text-center">
          <div className="w-16 h-16 bg-emerald-50 text-emerald-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <FileText className="w-8 h-8" />
          </div>
          <h3 className="text-lg font-semibold text-slate-900 mb-1">
            Ingestão Inteligente de Documentos PDF
          </h3>
          <p className="text-sm text-slate-500 mb-6">
            Faça o upload de certidões, balanços ou certidões de regularidade para OCR, extração e avaliação.
          </p>

          <label className="inline-flex items-center px-5 py-2.5 rounded-lg shadow-sm text-sm font-medium text-white bg-emerald-600 hover:bg-emerald-700 cursor-pointer transition-colors">
            <UploadCloud className="w-4 h-4 mr-2" />
            {uploading ? 'Processando Documento...' : 'Selecionar Arquivo PDF'}
            <input
              type="file"
              accept=".pdf"
              className="hidden"
              disabled={uploading}
              onChange={onFileUpload}
            />
          </label>
          <div className="mt-2 text-xs text-slate-400">
            Suporte a OCR Tesseract (PT-BR) e extração tabular nativa
          </div>
        </div>
      </div>

      {/* Lista de Documentos Ingeridos */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="p-5 border-b border-slate-200 flex justify-between items-center bg-slate-50/50">
          <div>
            <h4 className="font-semibold text-slate-900">Documentos em Fila / Processados</h4>
            <p className="text-xs text-slate-500">Documentos prontos para laudo de conformidade</p>
          </div>
          <button
            onClick={onRefreshDocuments}
            className="p-2 text-slate-500 hover:text-slate-800 transition-colors"
            title="Atualizar lista"
          >
            <RefreshCw className={`w-4 h-4 ${loadingDocs ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {pollingState?.exhausted && (
          <div
            role="status"
            aria-live="polite"
            className="px-5 py-3 bg-amber-50 border-b border-amber-200 text-amber-900 text-xs flex flex-wrap items-center justify-between gap-2"
          >
            <div className="flex items-center space-x-2">
              <Clock className="w-4 h-4 text-amber-600 shrink-0" />
              <span>
                O processamento está demorando mais que o esperado. A atualização automática foi pausada após{' '}
                {pollingState.maxAttempts} tentativas.
                {pollingState.consecutiveErrors >= 2 && (
                  <>
                    {' '}As últimas {pollingState.consecutiveErrors} consultas de status falharam.
                  </>
                )}
              </span>
            </div>
            <button
              type="button"
              onClick={onRefreshDocuments}
              className="px-3 py-1 rounded-md font-semibold bg-amber-600 hover:bg-amber-700 text-white transition-colors"
            >
              Atualizar manualmente
            </button>
          </div>
        )}

        {pollingState && !pollingState.exhausted && pollingState.consecutiveErrors >= 2 && (
          <div
            role="status"
            aria-live="polite"
            className="px-5 py-3 bg-rose-50 border-b border-rose-200 text-rose-800 text-xs flex flex-wrap items-center justify-between gap-2"
          >
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>
                Falha ao atualizar o status automaticamente ({pollingState.consecutiveErrors} tentativas
                consecutivas falharam). Nova tentativa em andamento ou atualize manualmente.
              </span>
            </div>
            <button
              type="button"
              onClick={onRefreshDocuments}
              className="px-3 py-1 rounded-md font-semibold bg-rose-600 hover:bg-rose-700 text-white transition-colors"
            >
              Atualizar manualmente
            </button>
          </div>
        )}

        {documents.length === 0 ? (
          <div className="p-8 text-center text-slate-400 text-sm">
            Nenhum documento ingerido até o momento.
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {documents.map((doc) => {
              const statusInfo = presentDocumentStatus(doc.status);
              const isCompleted = doc.status === 'COMPLETED';
              return (
                <div
                  key={doc.id}
                  className="p-5 flex flex-wrap items-center justify-between gap-4 hover:bg-slate-50/80 transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <div className="p-2 rounded bg-slate-100 text-slate-600">
                      <FileText className="w-5 h-5" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-slate-900">{doc.original_filename}</p>
                      <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500 mt-1">
                        <span>Tamanho: {(doc.file_size / 1024).toFixed(1)} KB</span>
                        <span>•</span>
                        <span>Páginas: {doc.total_pages || 1}</span>
                        <span>•</span>
                        <span
                          className={`px-2 py-0.5 rounded-full text-[11px] font-semibold ${TONE_CLASSES[statusInfo.tone]}`}
                        >
                          {statusInfo.label}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-3">
                    <button
                      onClick={() => onVerifyCompliance(doc.id, doc.original_filename)}
                      disabled={!isCompleted || verifyingId === doc.id}
                      title={
                        isCompleted
                          ? 'Executar ou abrir laudo de conformidade'
                          : 'Aguarde a conclusão do processamento para verificar a conformidade'
                      }
                      className="px-4 py-2 rounded-lg text-xs font-semibold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 flex items-center space-x-1.5 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {verifyingId === doc.id ? (
                        <>
                          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                          <span>Avaliando Regras...</span>
                        </>
                      ) : (
                        <>
                          <ShieldCheck className="w-3.5 h-3.5" />
                          <span>Verificar Conformidade</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Painel do Relatório de Conformidade Selecionado */}
      {activeReport && (
        <ComplianceReportPanel
          key={activeReport.document_id}
          report={activeReport}
          apiKeyLabel={apiKeyLabel}
          onOpenApiKeyModal={onOpenApiKeyModal}
          onClose={onCloseReport}
        />
      )}
    </div>
  );
}
