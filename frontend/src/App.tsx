import React, { useState, useEffect, useRef } from 'react';
import { CheckCircle2, XCircle, X } from 'lucide-react';
import {
  apiService,
  setApiKey,
  getApiKeyLabel,
  HealthResponse,
  DocumentItem,
  ComplianceRule,
  ComplianceReport,
  AuditLogItem,
} from './services/api';
import { describeApiError } from './services/presentation';
import { createDocumentPoller, PollingSnapshot } from './services/polling';
import { Header, ActiveTab } from './components/Header';
import { Footer } from './components/Footer';
import { DocumentUploadTab } from './components/DocumentUploadTab';
import { ChecklistTab } from './components/ChecklistTab';
import { AuditTrailTab } from './components/AuditTrailTab';
import { ApiKeyModal } from './components/ApiKeyModal';

export default function App() {
  const [activeTab, setActiveTab] = useState<ActiveTab>('upload');
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthLoading, setHealthLoading] = useState<boolean>(true);
  const [healthError, setHealthError] = useState<boolean>(false);

  // Estados dos Módulos
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loadingDocs, setLoadingDocs] = useState<boolean>(false);
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);

  const [rules, setRules] = useState<ComplianceRule[]>([]);
  const [loadingRules, setLoadingRules] = useState<boolean>(false);

  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);
  const [loadingAudit, setLoadingAudit] = useState<boolean>(false);

  const [activeReport, setActiveReport] = useState<ComplianceReport | null>(null);
  const [verifyingId, setVerifyingId] = useState<string | null>(null);

  // Chave pessoal do analista mantida apenas em memória na sessão.
  const [sessionKey, setSessionKey] = useState<string | null>(null);
  const [apiKeyModalOpen, setApiKeyModalOpen] = useState<boolean>(false);

  // Falhas sao exibidas como erro; a interface nunca substitui a resposta da API por dados simulados.
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [pollingState, setPollingState] = useState<PollingSnapshot | null>(null);
  const [pollingResetCount, setPollingResetCount] = useState<number>(0);
  const uploadTimerRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (uploadTimerRef.current !== null) {
        window.clearTimeout(uploadTimerRef.current);
      }
    };
  }, []);

  const hasProcessingDocs = documents.some(
    (doc) => doc.status === 'PENDING' || doc.status === 'PROCESSING',
  );

  useEffect(() => {
    if (!hasProcessingDocs) return;

    const poller = createDocumentPoller({
      poll: () => apiService.listDocuments(),
      onSuccess: (res) => {
        setDocuments(res.items || []);
      },
      onStateChange: (snapshot) => {
        setPollingState(snapshot);
      },
    });

    const onVisibilityChange = () => poller.handleVisibilityChange();
    document.addEventListener('visibilitychange', onVisibilityChange);
    poller.start();

    return () => {
      document.removeEventListener('visibilitychange', onVisibilityChange);
      poller.stop();
      setPollingState(null);
    };
  }, [hasProcessingDocs, pollingResetCount]);

  const handleSaveApiKey = (newKey: string | null) => {
    setApiKey(newKey);
    setSessionKey(newKey);
    setErrorMessage(null);
    if (activeTab === 'upload') loadDocuments();
    if (activeTab === 'checklist') loadRules();
    if (activeTab === 'audit') loadAuditLogs();
  };

  // Checagem de Saúde do Backend
  const checkHealthStatus = async () => {
    try {
      setHealthLoading(true);
      const data = await apiService.getHealth();
      setHealth(data);
      setHealthError(false);
    } catch {
      setHealthError(true);
      setHealth(null);
    } finally {
      setHealthLoading(false);
    }
  };

  const loadDocuments = async () => {
    try {
      setLoadingDocs(true);
      const res = await apiService.listDocuments();
      setDocuments(res.items || []);
      setErrorMessage(null);
    } catch (error) {
      setErrorMessage(describeApiError(error, 'Não foi possível carregar os documentos.'));
    } finally {
      setLoadingDocs(false);
    }
  };

  const handleManualRefreshDocuments = async () => {
    setPollingState(null);
    setPollingResetCount((prev) => prev + 1);
    await loadDocuments();
  };

  useEffect(() => {
    let isMounted = true;

    apiService
      .getHealth()
      .then((data) => {
        if (isMounted) {
          setHealth(data);
          setHealthError(false);
        }
      })
      .catch(() => {
        if (isMounted) {
          setHealthError(true);
          setHealth(null);
        }
      })
      .finally(() => {
        if (isMounted) setHealthLoading(false);
      });

    apiService
      .listDocuments()
      .then((res) => {
        if (isMounted) setDocuments(res.items || []);
      })
      .catch((error) => {
        if (isMounted) {
          setErrorMessage(describeApiError(error, 'Não foi possível carregar os documentos.'));
        }
      })
      .finally(() => {
        if (isMounted) setLoadingDocs(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const loadRules = async () => {
    try {
      setLoadingRules(true);
      const res = await apiService.getRules();
      setRules(res.rules || []);
      setErrorMessage(null);
    } catch (error) {
      setRules([]);
      setErrorMessage(describeApiError(error, 'Não foi possível carregar o checklist de regras.'));
    } finally {
      setLoadingRules(false);
    }
  };

  const loadAuditLogs = async () => {
    try {
      setLoadingAudit(true);
      const res = await apiService.getAuditTrail();
      setAuditLogs(res.items || []);
      setErrorMessage(null);
    } catch (error) {
      setAuditLogs([]);
      setErrorMessage(describeApiError(error, 'Não foi possível carregar a trilha de auditoria.'));
    } finally {
      setLoadingAudit(false);
    }
  };

  const handleTabChange = (tab: ActiveTab) => {
    setActiveTab(tab);
    if (tab === 'upload') loadDocuments();
    if (tab === 'checklist') loadRules();
    if (tab === 'audit') loadAuditLogs();
  };

  const uploadPdfFile = async (file: File) => {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setErrorMessage('Selecione um arquivo no formato PDF.');
      return;
    }

    if (file.size === 0) {
      setErrorMessage('O arquivo PDF selecionado está vazio.');
      return;
    }

    const MAX_PDF_BYTES = 50 * 1024 * 1024;
    if (file.size > MAX_PDF_BYTES) {
      setErrorMessage('O arquivo excede o limite máximo de 50 MB.');
      return;
    }

    if (uploadTimerRef.current !== null) {
      window.clearTimeout(uploadTimerRef.current);
      uploadTimerRef.current = null;
    }

    try {
      setUploading(true);
      setErrorMessage(null);
      setUploadMessage('Enviando documento para a fila de processamento OCR/IDP...');
      await apiService.uploadDocument(file);
      setUploadMessage('Documento recebido e enviado para processamento. O status será atualizado automaticamente.');
      setPollingResetCount((prev) => prev + 1);
      await loadDocuments();
      uploadTimerRef.current = window.setTimeout(() => {
        setUploadMessage(null);
        uploadTimerRef.current = null;
      }, 4000);
    } catch (error) {
      setUploadMessage(null);
      setErrorMessage(describeApiError(error, 'Falha no envio do documento.'));
    } finally {
      setUploading(false);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      await uploadPdfFile(file);
    } finally {
      // Permite reenviar o mesmo arquivo apos uma falha.
      event.target.value = '';
    }
  };

  const handleVerifyCompliance = async (docId: string, filename: string) => {
    try {
      setVerifyingId(docId);
      setErrorMessage(null);
      const report = await apiService.verifyCompliance(docId);
      setActiveReport(report);
    } catch (error) {
      // Sem laudo real nao ha laudo: nunca exibir resultado de conformidade simulado.
      setActiveReport(null);
      setErrorMessage(describeApiError(error, `Não foi possível avaliar a conformidade de ${filename}.`));
    } finally {
      setVerifyingId(null);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-bndes-bg text-bndes-ink">
      <Header
        activeTab={activeTab}
        onTabChange={handleTabChange}
        health={health}
        healthLoading={healthLoading}
        healthError={healthError}
        onRefreshHealth={checkHealthStatus}
        apiKeyLabel={getApiKeyLabel(sessionKey)}
        onOpenApiKeyModal={() => setApiKeyModalOpen(true)}
      />

      {apiKeyModalOpen && (
        <ApiKeyModal
          isOpen={apiKeyModalOpen}
          currentKey={sessionKey}
          onSave={handleSaveApiKey}
          onClose={() => setApiKeyModalOpen(false)}
        />
      )}

      {/* Conteúdo Principal */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Notificações / Toasts */}
        {errorMessage && (
          <div
            role="alert"
            className="mb-6 p-4 rounded-md bg-bndes-orange-tint border border-bndes-orange-border border-l-4 border-l-bndes-orange text-bndes-orange-ink text-sm flex items-center justify-between shadow-(--shadow-bndes-card)"
          >
            <div className="flex items-center space-x-2.5">
              <XCircle className="w-5 h-5 text-bndes-orange shrink-0" aria-hidden="true" />
              <span className="font-medium">{errorMessage}</span>
            </div>
            <button
              type="button"
              onClick={() => setErrorMessage(null)}
              className="text-bndes-orange-ink/80 hover:text-bndes-orange-ink p-1 rounded transition-colors cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-bndes-blue-2"
              title="Fechar"
              aria-label="Fechar aviso de erro"
            >
              <X className="w-4 h-4" aria-hidden="true" />
            </button>
          </div>
        )}
        {uploadMessage && (
          <div
            role="status"
            aria-live="polite"
            className="mb-6 p-4 rounded-md bg-bndes-green-tint border border-bndes-green-border border-l-4 border-l-bndes-green text-bndes-green-ink text-sm flex items-center justify-between shadow-(--shadow-bndes-card)"
          >
            <div className="flex items-center space-x-2.5">
              <CheckCircle2 className="w-5 h-5 text-bndes-green shrink-0" aria-hidden="true" />
              <span className="font-medium">{uploadMessage}</span>
            </div>
            <button
              type="button"
              onClick={() => setUploadMessage(null)}
              className="text-bndes-green-ink/80 hover:text-bndes-green-ink p-1 rounded transition-colors cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-bndes-blue-2"
              title="Fechar"
              aria-label="Fechar aviso de envio"
            >
              <X className="w-4 h-4" aria-hidden="true" />
            </button>
          </div>
        )}

        {activeTab === 'upload' && (
          <div id="panel-upload" role="tabpanel" aria-labelledby="tab-upload">
            <DocumentUploadTab
              documents={documents}
              loadingDocs={loadingDocs}
              uploading={uploading}
              verifyingId={verifyingId}
              activeReport={activeReport}
              apiKeyLabel={getApiKeyLabel(sessionKey)}
              pollingState={hasProcessingDocs ? pollingState : null}
              onFileUpload={handleFileUpload}
              onFileDrop={uploadPdfFile}
              onRefreshDocuments={handleManualRefreshDocuments}
              onVerifyCompliance={handleVerifyCompliance}
              onOpenApiKeyModal={() => setApiKeyModalOpen(true)}
              onCloseReport={() => setActiveReport(null)}
            />
          </div>
        )}

        {activeTab === 'checklist' && (
          <div id="panel-checklist" role="tabpanel" aria-labelledby="tab-checklist">
            <ChecklistTab
              rules={rules}
              loadingRules={loadingRules}
              onRefreshRules={loadRules}
            />
          </div>
        )}

        {activeTab === 'audit' && (
          <div id="panel-audit" role="tabpanel" aria-labelledby="tab-audit">
            <AuditTrailTab
              auditLogs={auditLogs}
              loadingAudit={loadingAudit}
              onRefreshAudit={loadAuditLogs}
            />
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
}
