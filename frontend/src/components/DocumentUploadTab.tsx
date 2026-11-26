import React, { useEffect, useRef, useState } from 'react';
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
  onFileDrop: (file: File) => void;
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
  onFileDrop,
  onRefreshDocuments,
  onVerifyCompliance,
  onOpenApiKeyModal,
  onCloseReport,
}: DocumentUploadTabProps) {
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const reportSectionRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (activeReport?.document_id) {
      reportSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [activeReport?.document_id]);

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    if (!uploading) setIsDragging(true);
  };

  const handleDragLeave = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
    if (uploading) return;
    const droppedFile = event.dataTransfer.files?.[0];
    if (droppedFile) {
      onFileDrop(droppedFile);
    }
  };

  return (
    <div className="space-y-8">
      {/* Área de Ingestão de Documentos */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`rounded-md shadow-(--shadow-bndes-card) border border-t-[3px] border-t-bndes-blue p-8 transition-colors ${
          isDragging
            ? 'bg-bndes-blue-tint/50 border-bndes-blue border-dashed'
            : 'bg-white border-bndes-border'
        }`}
      >
        <div className="max-w-2xl mx-auto text-center">
          <div className="w-14 h-14 bg-bndes-blue-tint text-bndes-blue border border-bndes-blue-border rounded-md flex items-center justify-center mx-auto mb-4">
            <FileText className="w-7 h-7" aria-hidden="true" />
          </div>
          <h3 className="text-lg font-bold text-bndes-blue tracking-tight mb-1.5">
            Ingestão Inteligente de Documentos PDF
          </h3>
          <p className="text-sm text-bndes-ink-secondary mb-6">
            Arraste e solte um PDF aqui ou selecione o arquivo para OCR, extração e avaliação.
          </p>

          <label className="inline-flex items-center px-5 py-2.5 rounded shadow-xs text-sm font-semibold text-white bg-bndes-blue hover:bg-bndes-blue-3 active:bg-bndes-blue-deep focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-bndes-blue-2 cursor-pointer transition-colors">
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
          <div className="mt-2.5 text-xs text-bndes-ink-muted">
            Suporte a OCR Tesseract (PT-BR) e extração tabular nativa
          </div>
        </div>
      </div>

      {/* Lista de Documentos Ingeridos */}
      <div className="bg-white rounded-md shadow-(--shadow-bndes-card) border border-bndes-border overflow-hidden">
        <div className="p-5 border-b border-bndes-border flex justify-between items-center bg-bndes-surface-muted/65">
          <div>
            <h4 className="font-bold text-bndes-blue">Documentos em Fila / Processados</h4>
            <p className="text-xs text-bndes-ink-secondary">Documentos prontos para laudo de conformidade</p>
          </div>
          <button
            type="button"
            onClick={onRefreshDocuments}
            className="p-2 text-bndes-ink-secondary hover:text-bndes-blue rounded hover:bg-bndes-blue-tint transition-colors cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-bndes-blue-2"
            title="Atualizar lista"
            aria-label="Atualizar lista de documentos"
          >
            <RefreshCw className={`w-4 h-4 ${loadingDocs ? 'animate-spin motion-reduce:animate-none' : ''}`} aria-hidden="true" />
          </button>
        </div>

        {pollingState?.exhausted && (
          <div
            role="status"
            aria-live="polite"
            className="px-5 py-3 bg-bndes-ochre-tint border-b border-bndes-ochre-border text-bndes-ochre-ink text-xs flex flex-wrap items-center justify-between gap-2"
          >
            <div className="flex items-center space-x-2">
              <Clock className="w-4 h-4 text-bndes-ochre shrink-0" />
              <span>
                O processamento está demorando mais que o esperado. A atualização automática foi pausada após{' '}
                {pollingState.maxAttempts} tentativas.
              </span>
            </div>
            <button
              type="button"
              onClick={onRefreshDocuments}
              className="px-3 py-1 rounded font-semibold bg-bndes-ochre hover:bg-bndes-ochre-ink text-white transition-colors cursor-pointer"
            >
              Atualizar manualmente
            </button>
          </div>
        )}

        {pollingState && !pollingState.exhausted && pollingState.consecutiveErrors >= 2 && (
          <div
            role="status"
            aria-live="polite"
            className="px-5 py-3 bg-bndes-orange-tint border-b border-bndes-orange-border text-bndes-orange-ink text-xs flex flex-wrap items-center justify-between gap-2"
          >
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-bndes-orange shrink-0" />
              <span>
                Falha ao atualizar o status automaticamente ({pollingState.consecutiveErrors} tentativas
                consecutivas falharam). Nova tentativa em andamento ou atualize manualmente.
              </span>
            </div>
            <button
              type="button"
              onClick={onRefreshDocuments}
              className="px-3 py-1 rounded font-semibold bg-bndes-orange hover:bg-bndes-orange-ink text-white transition-colors cursor-pointer"
            >
              Atualizar manualmente
            </button>
          </div>
        )}

        {documents.length === 0 ? (
          <div className="p-8 text-center text-bndes-ink-muted text-sm">
            Nenhum documento ingerido até o momento.
          </div>
        ) : (
          <div className="divide-y divide-bndes-border">
            {documents.map((doc) => {
              const statusInfo = presentDocumentStatus(doc.status);
              const isCompleted = doc.status === 'COMPLETED';
              const isSelected = activeReport?.document_id === doc.id;
              return (
                <div
                  key={doc.id}
                  className={`p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-colors ${
                    isSelected
                      ? 'bg-bndes-blue-tint/45 border-l-4 border-l-bndes-blue'
                      : 'hover:bg-bndes-bg/70'
                  }`}
                >
                  <div className="flex items-center space-x-3 min-w-0">
                    <div className="p-2 rounded bg-bndes-blue-tint text-bndes-blue border border-bndes-blue-border/60 shrink-0">
                      <FileText className="w-5 h-5" aria-hidden="true" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-bndes-ink truncate">{doc.original_filename}</p>
                      <div className="flex flex-wrap items-center gap-2 text-xs text-bndes-ink-secondary mt-1">
                        <span>Tamanho: {(doc.file_size / 1024).toFixed(1)} KB</span>
                        <span>•</span>
                        <span>Páginas: {doc.total_pages || 1}</span>
                        <span>•</span>
                        <span
                          className={`px-2 py-0.5 rounded text-[11px] font-semibold ${TONE_CLASSES[statusInfo.tone]}`}
                        >
                          {statusInfo.label}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center sm:shrink-0">
                    <button
                      type="button"
                      onClick={() => onVerifyCompliance(doc.id, doc.original_filename)}
                      disabled={!isCompleted || verifyingId === doc.id}
                      title={
                        isCompleted
                          ? 'Executar ou abrir laudo de conformidade'
                          : 'Aguarde a conclusão do processamento para verificar a conformidade'
                      }
                      className="w-full sm:w-auto justify-center px-4 py-2 rounded text-xs font-semibold text-bndes-blue bg-bndes-blue-tint hover:bg-[#DCEAF7] border border-bndes-blue-border flex items-center space-x-1.5 transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-bndes-blue-2"
                    >
                      {verifyingId === doc.id ? (
                        <>
                          <RefreshCw className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" aria-hidden="true" />
                          <span>Avaliando Regras...</span>
                        </>
                      ) : (
                        <>
                          <ShieldCheck className="w-3.5 h-3.5 text-bndes-green" aria-hidden="true" />
                          <span>{isSelected ? 'Laudo Aberto' : 'Verificar Conformidade'}</span>
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
        <div ref={reportSectionRef} className="scroll-mt-6">
          <ComplianceReportPanel
            key={activeReport.document_id}
            report={activeReport}
            apiKeyLabel={apiKeyLabel}
            onOpenApiKeyModal={onOpenApiKeyModal}
            onClose={onCloseReport}
          />
        </div>
      )}
    </div>
  );
}
