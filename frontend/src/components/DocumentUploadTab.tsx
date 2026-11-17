import React from 'react';
import { FileText, UploadCloud, ShieldCheck, RefreshCw } from 'lucide-react';
import { DocumentItem, ComplianceReport } from '../services/api';
import { ComplianceReportPanel } from './ComplianceReportPanel';

interface DocumentUploadTabProps {
  documents: DocumentItem[];
  loadingDocs: boolean;
  uploading: boolean;
  verifyingId: string | null;
  activeReport: ComplianceReport | null;
  onFileUpload: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onRefreshDocuments: () => void;
  onVerifyCompliance: (docId: string, filename: string) => void;
  onCloseReport: () => void;
}

export function DocumentUploadTab({
  documents,
  loadingDocs,
  uploading,
  verifyingId,
  activeReport,
  onFileUpload,
  onRefreshDocuments,
  onVerifyCompliance,
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

        {documents.length === 0 ? (
          <div className="p-8 text-center text-slate-400 text-sm">
            Nenhum documento ingerido até o momento.
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="p-5 flex items-center justify-between hover:bg-slate-50/80 transition-colors"
              >
                <div className="flex items-center space-x-3">
                  <div className="p-2 rounded bg-slate-100 text-slate-600">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-900">{doc.original_filename}</p>
                    <div className="flex items-center space-x-3 text-xs text-slate-500 mt-1">
                      <span>Tamanho: {(doc.file_size / 1024).toFixed(1)} KB</span>
                      <span>•</span>
                      <span>Páginas: {doc.total_pages || 1}</span>
                      <span>•</span>
                      <span className="text-emerald-700 font-medium">Status: {doc.status}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  <button
                    onClick={() => onVerifyCompliance(doc.id, doc.original_filename)}
                    disabled={verifyingId === doc.id}
                    className="px-4 py-2 rounded-lg text-xs font-semibold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 flex items-center space-x-1.5 transition-colors disabled:opacity-50"
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
            ))}
          </div>
        )}
      </div>

      {/* Painel do Relatório de Conformidade Selecionado */}
      {activeReport && (
        <ComplianceReportPanel report={activeReport} onClose={onCloseReport} />
      )}
    </div>
  );
}
