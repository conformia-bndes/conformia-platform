import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
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
}

export interface ComplianceReport {
  document_id: string;
  document_filename: string;
  overall_status: string;
  compliance_score: number;
  total_rules: number;
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
