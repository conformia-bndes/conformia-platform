import React, { useState, useEffect } from 'react';
import {
  FileText,
  CheckCircle2,
  XCircle,
  UploadCloud,
  ShieldCheck,
  History,
  ListFilter,
  RefreshCw,
  X,
  BookOpen,
  Search,
} from 'lucide-react';
import {
  apiService,
  HealthResponse,
  DocumentItem,
  ComplianceRule,
  ComplianceReport,
  AuditLogItem,
  PageEvidence,
  ExtractedField,
  ExtractionResult,
} from './services/api';
import { describeApiError, presentStatus, TONE_CLASSES, formatExtractedValue, hasEvidence, hasNonEmptyEvidence, getFieldEvidenceOrEmpty } from './services/presentation';
import { EvidenceCard, EvidenceEmptyState } from './components/EvidenceCard';

export default function App() {
  const [activeTab, setActiveTab] = useState<'upload' | 'checklist' | 'audit'>('upload');
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthLoading, setHealthLoading] = useState<boolean>(true);
  const [healthError, setHealthError] = useState<boolean>(false);

  // Estados dos MÃ³dulos
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loadingDocs, setLoadingDocs] = useState<boolean>(false);
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);

  const [rules, setRules] = useState<ComplianceRule[]>([]);
  const [loadingRules, setLoadingRules] = useState<boolean>(false);

  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);
  const [loadingAudit, setLoadingAudit] = useState<boolean>(false);

  const [activeReport, setActiveReport] = useState<ComplianceReport | null>(null);
  const [activeExtraction, setActiveExtraction] = useState<ExtractionResult | null>(null);
  const [verifyingId, setVerifyingId] = useState<string | null>(null);

  // Falhas sao exibidas como erro; a interface nunca substitui a resposta da API por dados simulados.
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Checagem de SaÃºde do Backend
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
      setErrorMessage(describeApiError(error, 'NÃ£o foi possÃ­vel carregar os documentos.'));
    } finally {
      setLoadingDocs(false);
    }
  };

  useEffect(() => {
    let isMounted = true;

    apiService.getHealth()
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

    apiService.listDocuments()
      .then((res) => {
        if (isMounted) setDocuments(res.items || []);
      })
      .catch((error) => {
        if (isMounted) {
          setErrorMessage(describeApiError(error, 'NÃ£o foi possÃ­vel carregar os documentos.'));
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
      setErrorMessage(describeApiError(error, 'NÃ£o foi possÃ­vel carregar o checklist de regras.'));
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
      setErrorMessage(describeApiError(error, 'NÃ£o foi possÃ­vel carregar a trilha de auditoria.'));
    } finally {
      setLoadingAudit(false);
    }
  };

  const handleTabChange = (tab: 'upload' | 'checklist' | 'audit') => {
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
      setErrorMessage(describeApiError(error, `NÃ£o foi possÃ­vel avaliar a conformidade de ${filename}.`));
    } finally {
      setVerifyingId(null);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-800">
      {/* CabeÃ§alho Institucional Conform.IA BNDES */}
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
                  Consulta PÃºblica nÂº 01/2025 â€¢ VerificaÃ§Ã£o Inteligente de Conformidade
                </p>
              </div>
            </div>

            {/* Indicador de Status da API */}
            <div className="flex items-center space-x-4">
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
                  onClick={checkHealthStatus}
                  title="Atualizar Status"
                  className="text-slate-400 hover:text-white transition-colors ml-1"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${healthLoading ? 'animate-spin' : ''}`} />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Abas de NavegaÃ§Ã£o */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8 -mb-px">
            <button
              onClick={() => handleTabChange('upload')}
              className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 transition-colors ${
                activeTab === 'upload'
                  ? 'border-emerald-500 text-emerald-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700'
              }`}
            >
              <UploadCloud className="w-4 h-4" />
              <span>IngestÃ£o Documental (IDP)</span>
            </button>

            <button
              onClick={() => handleTabChange('checklist')}
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
              onClick={() => handleTabChange('audit')}
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

      {/* ConteÃºdo Principal */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* NotificaÃ§Ãµes / Toasts */}
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

        {/* ================= ABA 1: UPLOAD & INGESTÃƒO ================= */}
        {activeTab === 'upload' && (
          <div className="space-y-8">
            {/* Ãrea de IngestÃ£o de Documentos */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
              <div className="max-w-2xl mx-auto text-center">
                <div className="w-16 h-16 bg-emerald-50 text-emerald-600 rounded-full flex items-center justify-center mx-auto mb-4">
                  <FileText className="w-8 h-8" />
                </div>
                <h3 className="text-lg font-semibold text-slate-900 mb-1">
                  IngestÃ£o Inteligente de Documentos PDF
                </h3>
                <p className="text-sm text-slate-500 mb-6">
                  FaÃ§a o upload de certidÃµes, balanÃ§os ou certidÃµes de regularidade para OCR, extraÃ§Ã£o e avaliaÃ§Ã£o.
                </p>

                <label className="inline-flex items-center px-5 py-2.5 rounded-lg shadow-sm text-sm font-medium text-white bg-emerald-600 hover:bg-emerald-700 cursor-pointer transition-colors">
                  <UploadCloud className="w-4 h-4 mr-2" />
                  {uploading ? 'Processando Documento...' : 'Selecionar Arquivo PDF'}
                  <input
                    type="file"
                    accept=".pdf"
                    className="hidden"
                    disabled={uploading}
                    onChange={handleFileUpload}
                  />
                </label>
                <div className="mt-2 text-xs text-slate-400">Suporte a OCR Tesseract (PT-BR) e extraÃ§Ã£o tabular nativa</div>
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
                  onClick={loadDocuments}
                  className="p-2 text-slate-500 hover:text-slate-800 transition-colors"
                  title="Atualizar lista"
                >
                  <RefreshCw className={`w-4 h-4 ${loadingDocs ? 'animate-spin' : ''}`} />
                </button>
              </div>

              {documents.length === 0 ? (
                <div className="p-8 text-center text-slate-400 text-sm">
                  Nenhum documento ingerido atÃ© o momento.
                </div>
              ) : (
                <div className="divide-y divide-slate-100">
                  {documents.map((doc) => (
                    <div key={doc.id} className="p-5 flex items-center justify-between hover:bg-slate-50/80 transition-colors">
                      <div className="flex items-center space-x-3">
                        <div className="p-2 rounded bg-slate-100 text-slate-600">
                          <FileText className="w-5 h-5" />
                        </div>
                        <div>
                          <p className="text-sm font-semibold text-slate-900">{doc.original_filename}</p>
                          <div className="flex items-center space-x-3 text-xs text-slate-500 mt-1">
                            <span>Tamanho: {(doc.file_size / 1024).toFixed(1)} KB</span>
                            <span>â€¢</span>
                            <span>PÃ¡ginas: {doc.total_pages || 1}</span>
                            <span>â€¢</span>
                            <span className="text-emerald-700 font-medium">Status: {doc.status}</span>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center space-x-3">
                        <button
                          onClick={() => handleVerifyCompliance(doc.id, doc.original_filename)}
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

            {/* Painel do RelatÃ³rio de Conformidade Selecionado */}
            {activeReport && (
              <div className="bg-white rounded-xl shadow-md border border-slate-200 p-6 space-y-6">
                <div className="flex justify-between items-start border-b border-slate-100 pb-4">
                  <div>
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                      Resultado da AvaliaÃ§Ã£o
                    </span>
                    <h3 className="text-lg font-bold text-slate-900 flex items-center space-x-2 mt-1">
                      <span>Laudo de Conformidade: {activeReport.document_filename}</span>
                    </h3>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
                      TONE_CLASSES[presentStatus(activeReport.overall_status).tone]
                    }`}>
                      {presentStatus(activeReport.overall_status).label}
                    </span>
                    <button
                      onClick={() => setActiveReport(null)}
                      className="text-slate-400 hover:text-slate-600 text-sm ml-2"
                      title="Fechar RelatÃ³rio"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Resumo com MÃ©tricas */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
                    <p className="text-xs text-slate-500 font-medium">Score de Conformidade</p>
                    <p className="text-2xl font-bold text-emerald-600 mt-1">
                      {(activeReport.compliance_score * 100).toFixed(0)}%
                    </p>
                  </div>
                  <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
                    <p className="text-xs text-slate-500 font-medium">Regras Conformes / AplicÃ¡veis</p>
                    <p className="text-2xl font-bold text-slate-800 mt-1">
                      {activeReport.compliant_rules} / {activeReport.evaluated_rules}
                    </p>
                  </div>
                  <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
                    <p className="text-xs text-slate-500 font-medium">Tipologia Identificada</p>
                    <p className="text-sm font-semibold text-slate-700 mt-2">
                      {activeReport.document_type ?? 'NÃ£o identificada (revisÃ£o manual)'}
                    </p>
                  </div>
                </div>

                {/* Itens Verificados */}
                <div className="space-y-3">
                  <h4 className="text-sm font-semibold text-slate-800">Detalhamento dos CritÃ©rios BNDES</h4>
                  <div className="divide-y divide-slate-100 border border-slate-200 rounded-lg overflow-hidden">
                    {activeReport.checks.map((c) => (
                      <div key={c.rule_id} className="p-4 flex items-start justify-between bg-white hover:bg-slate-50">
                        <div className="space-y-1">
                          <div className="flex items-center space-x-2">
                            <span className="text-xs font-mono font-bold text-slate-500">{c.rule_id}</span>
                            <span className="text-sm font-semibold text-slate-900">{c.rule_title}</span>
                            <span className="text-[10px] px-2 py-0.5 rounded bg-slate-100 font-semibold text-slate-600 uppercase">
                              {c.category}
                            </span>
                          </div>
                          <p className="text-xs text-slate-600">{c.findings}</p>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span
                            className={`flex items-center text-xs font-semibold px-2 py-1 rounded space-x-1 ${
                              TONE_CLASSES[presentStatus(c.status).tone]
                            }`}
                          >
                            {c.status === 'COMPLIANT' ? (
                              <CheckCircle2 className="w-4 h-4" />
                            ) : (
                              <XCircle className="w-4 h-4" />
                            )}
                            <span>{presentStatus(c.status).label}</span>
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

              </div>
            )}
          </div>
        )}

        {/* ================= SEÇÃO: EVIDÊNCIAS POR REGRA ================= */}
        {activeReport.checks.length > 0 && (
          <div className="pt-4 border-t border-slate-100">
            <h4 className="text-sm font-semibold text-slate-800 mb-3 flex items-center space-x-2">
              <BookOpen className="w-4 h-4 text-emerald-600" />
              <span>Evidências de Apoio por Critério</span>
            </h4>
            <div className="space-y-3">
              {activeReport.checks.map((c) => {
                const matchedEvidence = activeExtraction?.evidences?.find(ev => {
                  if (!c.evidence || typeof c.evidence !== 'object') return false;
                  const evObj = c.evidence as Record<string, unknown>;
                  const matchedKeywords = evObj.matched_keywords as string[] | undefined;
                  if (!matchedKeywords) return false;
                  return matchedKeywords.some(kw => {
                    const kwStr = String(kw).toUpperCase();
                    return ev.text.toUpperCase().includes(kwStr);
                  });
                }) ?? null;

                const hasRuleEvidence = matchedEvidence !== null;

                return (
                  <div key={c.rule_id} className="bg-slate-50 rounded-lg border border-slate-200 px-4 py-3">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <p className="text-xs font-mono font-bold text-slate-500">{c.rule_id}</p>
                        <p className="text-sm font-semibold text-slate-900 truncate">{c.rule_title}</p>
                      </div>
                      <span
                        className={lex items-center text-xs font-semibold px-2 py-1 rounded space-x-1 flex-shrink-0 }
                      >
                        {c.status === 'COMPLIANT' ? (
                          <CheckCircle2 className="w-4 h-4" />
                        ) : (
                          <XCircle className="w-4 h-4" />
                        )}
                        <span>{presentStatus(c.status).label}</span>
                      </span>
                    </div>
                    {hasRuleEvidence ? (
                      <div className="mt-2 pt-2 border-t border-slate-200">
                        <p className="text-xs text-slate-600 mb-1">Trecho literal:</p>
                        <blockquote className="border-l-2 border-slate-300 pl-3 text-sm text-slate-600 italic">
                          "{matchedEvidence.text}"
                        </blockquote>
                        <p className="text-xs text-slate-500 mt-1 font-mono">
                          &larr; Página {matchedEvidence.page}
                        </p>
                      </div>
                    ) : (
                      <div className="mt-2 pt-2 border-t border-slate-200 bg-slate-50 rounded px-3 py-3 text-xs text-slate-500">
                        <p className="font-medium text-slate-600">Sem evidência textual disponível</p>
                        <p className="text-slate-400 mt-0.5">Aguarde o processamento IDP ou reflita sobre o documento.</p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ================= SEÇÃO: EXTRAÇÃO DE CAMPO COM EVIDÊNCIA ================= */}
        {activeExtraction && activeExtraction.fields && Object.keys(activeExtraction.fields).length > 0 && (
          <div className="pt-4 border-t border-slate-100">
            <h4 className="text-sm font-semibold text-slate-800 mb-3 flex items-center space-x-2">
              <Search className="w-4 h-4 text-emerald-600" />
              <span>Extração de Campos (IDP)</span>
            </h4>
            <div className="space-y-3">
              {(Object.entries(activeExtraction.fields) as [string, ExtractedField][]).map(([fieldName, field]) => {
                const hasFieldEvidence = hasEvidence(field);
                const fieldEvidence = hasFieldEvidence ? field.evidence! : null;

                return (
                  <div key={fieldName} className="bg-white rounded-lg border border-slate-200 p-4 shadow-sm">
                    <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-3">
                      <div>
                        <span className="text-xs font-mono font-bold text-slate-500">{fieldName}</span>
                        <p className="text-sm font-semibold text-slate-900 mt-0.5">
                          {formatExtractedValue(field.value, field.raw_value)}
                        </p>
                        <p className="text-xs text-slate-500 mt-1">
                          Confiança: {(field.confidence * 100).toFixed(0)}%
                        </p>
                      </div>
                      <div className="flex shrink-0 items-center space-x-2">
                        <span className={px-2 py-0.5 rounded text-xs font-semibold }>
                          {hasFieldEvidence ? 'Com evidência' : 'Sem evidência'}
                        </span>
                      </div>
                    </div>
                    {hasFieldEvidence ? (
                      <div className="mt-3 pt-3 border-t border-slate-100">
                        <EvidenceCard evidence={fieldEvidence} label="Evidência do campo" />
                      </div>
                    ) : (
                      <div className="mt-3 pt-3 border-t border-slate-100">
                        <div className="bg-slate-50 rounded px-3 py-2 text-xs text-slate-500">
                          <p className="font-medium text-slate-600">Nenhum trecho extraído como fundamento</p>
                          <p className="text-slate-400 mt-0.5">O campo foi extraído mas não possui ancoragem em página</p>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Estado vazio quando não há evidência nem extração */}
        {!activeExtraction && activeReport.checks.length > 0 && (
          <div className="bg-slate-50 rounded-lg border border-dashed border-slate-300 px-4 py-6 text-center">
            <p className="text-sm text-slate-500">
              <svg className="w-5 h-5 mx-auto mb-1 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M12 2a10 10 0 100 20 10 10 0 000-20z" />
              </svg>
              Nenhuma evidência de apoio disponível para este documento ainda.
            </p>
            <p className="text-xs text-slate-400 mt-1">Aguarde o término do processamento IDP ou reflita sobre o documento.</p>
          </div>
        )}

        {/* ================= ABA 2: CHECKLIST DE REGRAS ================= */}
        {activeTab === 'checklist' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-lg font-bold text-slate-900">Checklist Declarativo de Conformidade</h3>
                <p className="text-sm text-slate-500">
                  Regras normativas configuradas conforme o edital da Consulta PÃºblica BNDES nÂº 01/2025.
                </p>
              </div>
              <button
                onClick={loadRules}
                className="px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-medium text-slate-600 hover:bg-slate-100 flex items-center space-x-1"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loadingRules ? 'animate-spin' : ''}`} />
                <span>Atualizar CatÃ¡logo</span>
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {rules.map((rule) => (
                <div key={rule.id} className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 flex flex-col justify-between hover:shadow-md transition-shadow">
                  <div>
                    <div className="flex justify-between items-start mb-3">
                      <span className="px-2 py-0.5 text-xs font-mono font-bold rounded bg-slate-100 text-slate-700">
                        {rule.code}
                      </span>
                      <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                        {rule.type}
                      </span>
                    </div>
                    <h4 className="text-sm font-bold text-slate-900 mb-2">{rule.title}</h4>
                    <p className="text-xs text-slate-500 leading-relaxed mb-4">{rule.failure_message}</p>
                  </div>
                  <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400">
                    <span className="font-semibold text-slate-600">Categoria: {rule.category}</span>
                    <span className="font-mono">{rule.id}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ================= ABA 3: TRILHA DE AUDITORIA ================= */}
        {activeTab === 'audit' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-lg font-bold text-slate-900">Trilha de Auditoria ImutÃ¡vel</h3>
                <p className="text-sm text-slate-500">
                  Registro cronolÃ³gico de todas as decisÃµes automatizadas, avaliaÃ§Ãµes Maker-Checker e uploads.
                </p>
              </div>
              <button
                onClick={loadAuditLogs}
                className="px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-medium text-slate-600 hover:bg-slate-100 flex items-center space-x-1"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loadingAudit ? 'animate-spin' : ''}`} />
                <span>Atualizar Logs</span>
              </button>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
              <table className="w-full text-left text-sm text-slate-600">
                <thead className="bg-slate-50 text-xs font-semibold uppercase text-slate-500 border-b border-slate-200">
                  <tr>
                    <th className="px-6 py-4">Data / Hora</th>
                    <th className="px-6 py-4">AÃ§Ã£o</th>
                    <th className="px-6 py-4">Entidade</th>
                    <th className="px-6 py-4">Agente ResponsÃ¡vel</th>
                    <th className="px-6 py-4">Detalhes</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {auditLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-50/60">
                      <td className="px-6 py-4 text-xs font-mono text-slate-500">
                        {new Date(log.timestamp).toLocaleString('pt-BR')}
                      </td>
                      <td className="px-6 py-4">
                        <span className="px-2 py-0.5 rounded text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
                          {log.action}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-xs font-mono font-medium text-slate-700">
                        {log.entity_type}: {log.entity_id}
                      </td>
                      <td className="px-6 py-4 text-xs text-slate-600">
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
          </div>
        )}
      </main>

      {/* RodapÃ© Institucional */}
      <footer className="bg-white border-t border-slate-200 py-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row justify-between items-center gap-2">
          <p>Â© 2026 Conform.IA BNDES Platform â€¢ Consulta PÃºblica BNDES nÂº 01/2025</p>
          <div className="flex space-x-4">
            <span className="hover:text-slate-700">Harness Engineering Standard</span>
            <span>â€¢</span>
            <span className="hover:text-slate-700">Maker-Checker Protocol</span>
          </div>
        </div>
      </footer>
    </div>
  );
}





