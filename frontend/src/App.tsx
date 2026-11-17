import React, { useState, useEffect } from 'react';
import { CheckCircle2, XCircle, X } from 'lucide-react';
import {
  apiService,
  HealthResponse,
  DocumentItem,
  ComplianceRule,
  ComplianceReport,
  AuditLogItem,
} from './services/api';
import { describeApiError } from './services/presentation';
import { Header, ActiveTab } from './components/Header';
import { Footer } from './components/Footer';
import { DocumentUploadTab } from './components/DocumentUploadTab';
import { ChecklistTab } from './components/ChecklistTab';
import { AuditTrailTab } from './components/AuditTrailTab';

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

  // Falhas sao exibidas como erro; a interface nunca substitui a resposta da API por dados simulados.
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

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
    } catch (error) {
      setErrorMessage(describeApiError(error, 'Não foi possível carregar os documentos.'));
    } finally {
      setLoadingDocs(false);
    }
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

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      alert('Selecione um arquivo no formato PDF.');
      return;
    }

    try {
      setUploading(true);
      setErrorMessage(null);
      setUploadMessage('Enviando documento para a fila de processamento OCR/IDP...');
      await apiService.uploadDocument(file);
      setUploadMessage('Documento recebido e enviado para processamento. Atualize a lista para acompanhar o status.');
      await loadDocuments();
      setTimeout(() => setUploadMessage(null), 4000);
    } catch (error) {
      setUploadMessage(null);
      setErrorMessage(describeApiError(error, 'Falha no envio do documento.'));
    } finally {
      // Permite reenviar o mesmo arquivo apos uma falha.
      event.target.value = '';
      setUploading(false);
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
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-800">
      <Header
        activeTab={activeTab}
        onTabChange={handleTabChange}
        health={health}
        healthLoading={healthLoading}
        healthError={healthError}
        onRefreshHealth={checkHealthStatus}
      />

      {/* Conteúdo Principal */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Notificações / Toasts */}
        {errorMessage && (
          <div
            role="alert"
            className="mb-6 p-4 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-sm flex items-center justify-between shadow-sm"
          >
            <div className="flex items-center space-x-2">
              <XCircle className="w-5 h-5 text-rose-600" />
              <span>{errorMessage}</span>
            </div>
            <button onClick={() => setErrorMessage(null)} className="text-rose-600 hover:text-rose-800" title="Fechar">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}
        {uploadMessage && (
          <div className="mb-6 p-4 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm flex items-center justify-between shadow-sm">
            <div className="flex items-center space-x-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              <span>{uploadMessage}</span>
            </div>
            <button onClick={() => setUploadMessage(null)} className="text-emerald-600 hover:text-emerald-800" title="Fechar">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {activeTab === 'upload' && (
          <DocumentUploadTab
            documents={documents}
            loadingDocs={loadingDocs}
            uploading={uploading}
            verifyingId={verifyingId}
            activeReport={activeReport}
            onFileUpload={handleFileUpload}
            onRefreshDocuments={loadDocuments}
            onVerifyCompliance={handleVerifyCompliance}
            onCloseReport={() => setActiveReport(null)}
          />
        )}

        {activeTab === 'checklist' && (
          <ChecklistTab
            rules={rules}
            loadingRules={loadingRules}
            onRefreshRules={loadRules}
          />
        )}

        {activeTab === 'audit' && (
          <AuditTrailTab
            auditLogs={auditLogs}
            loadingAudit={loadingAudit}
            onRefreshAudit={loadAuditLogs}
          />
        )}
      </main>

      <Footer />
    </div>
  );
}
