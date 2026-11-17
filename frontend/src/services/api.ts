import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Chave pessoal mantida estritamente em memória (nunca em localStorage/sessionStorage).
let sessionApiKey: string | null = null;

export function setApiKey(key: string | null): void {
  const trimmed = key?.trim() ?? '';
  sessionApiKey = trimmed.length > 0 ? trimmed : null;
}

export function getApiKey(): string | null {
  return sessionApiKey;
}

/** Extrai o identificador do analista (prefixo antes de ':') sem expor o segredo. */
export function getApiKeyLabel(key: string | null = sessionApiKey): string | null {
  if (!key) return null;
  const separatorIndex = key.indexOf(':');
  if (separatorIndex > 0) {
    return key.slice(0, separatorIndex);
  }
  return 'Chave ativa';
}

apiClient.interceptors.request.use((config) => {
  if (sessionApiKey) {
    config.headers.set('X-API-Key', sessionApiKey);
  } else {
    config.headers.delete('X-API-Key');
  }
  return config;
});

export interface HealthResponse {
  status: string;
  app_name: string;
  version: string;
  environment: string;
  timestamp: string;
  services: {
    database: string;
    redis: string;
    minio: string;
  };
}

export interface DocumentItem {
  id: string;
  original_filename: string;
  status: string;
  file_size: number;
  created_at: string;
  total_pages: number;
}

export interface PageEvidence {
  text: string;
  page: number;
  confidence?: number;
  bounding_box?: number[] | null;
}

export interface ExtractedField {
  name: string;
  value: unknown;
  raw_value?: string | null;
  confidence: number;
  evidence?: PageEvidence | null;
}

export interface ExtractionResult {
  document_type?: string | null;
  fields: Record<string, ExtractedField>;
  evidences: PageEvidence[];
  total_pages: number;
  tables: unknown[];
  full_text_preview?: string | null;
}

export interface ErrorDetail {
  code: string;
  message: string;
  details?: Record<string, unknown> | null;
  timestamp: string;
}

export interface ProcessingStatusResponse {
  document_id: string;
  filename: string;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'EXTRACTION_FAILED';
  progress: number;
  message: string;
  extraction?: ExtractionResult | null;
  error?: ErrorDetail | null;
  created_at: string;
  updated_at: string;
}

export interface ComplianceRule {
  id: string;
  code: string;
  title: string;
  category: string;
  type: string;
  failure_message: string;
}

export interface ComplianceCheckResult {
  rule_id: string;
  rule_title: string;
  category: string;
  status: 'COMPLIANT' | 'NON_COMPLIANT' | 'MANUAL_REVIEW_REQUIRED' | 'NOT_APPLICABLE';
  confidence_score: number;
  checker_type: string;
  findings: string;
  evidence?: Record<string, unknown> | null;
}

export interface ComplianceReport {
  document_id: string;
  document_filename: string;
  document_type: string | null;
  overall_status: string;
  compliance_score: number;
  total_rules: number;
  evaluated_rules: number;
  compliant_rules: number;
  checks: ComplianceCheckResult[];
}

export interface AuditLogItem {
  id: string;
  entity_type: string;
  entity_id: string;
  action: string;
  performed_by: string;
  details: Record<string, unknown>;
  timestamp: string;
}

export const apiService = {
  // Diagnóstico e Saúde
  async getHealth(): Promise<HealthResponse> {
    const res = await apiClient.get<HealthResponse>('/api/v1/health');
    return res.data;
  },

  // Documentos e Ingestão IDP
  async uploadDocument(file: File): Promise<DocumentItem> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await apiClient.post<DocumentItem>('/api/v1/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },

  async listDocuments(): Promise<{ total: number; items: DocumentItem[] }> {
    const res = await apiClient.get('/api/v1/documents');
    return res.data;
  },

  async getDocument(id: string) {
    const res = await apiClient.get(`/api/v1/documents/${id}`);
    return res.data;
  },

  async getProcessingStatus(id: string): Promise<ProcessingStatusResponse> {
    const res = await apiClient.get<ProcessingStatusResponse>(`/api/v1/documents/${id}/processing`);
    return res.data;
  },

  // Motor de Conformidade e Regras
  async verifyCompliance(documentId: string): Promise<ComplianceReport> {
    const res = await apiClient.post<ComplianceReport>(`/api/v1/compliance/verify/${documentId}`);
    return res.data;
  },

  async getRules(): Promise<{ total_rules: number; rules: ComplianceRule[] }> {
    const res = await apiClient.get('/api/v1/compliance/rules');
    return res.data;
  },

  // Trilha de Auditoria Imutável
  async getAuditTrail(): Promise<{ total: number; items: AuditLogItem[] }> {
    const res = await apiClient.get('/api/v1/compliance/audit-trail');
    return res.data;
  },
};
