import { describe, it, expect, afterEach } from 'vitest';
import { AxiosHeaders } from 'axios';
import { apiClient, setApiKey, getApiKey, getApiKeyLabel } from '../services/api';

describe('API Service Client Configuration', () => {
  afterEach(() => {
    setApiKey(null);
  });

  it('should initialize apiClient with proper defaults', () => {
    expect(apiClient).toBeDefined();
    expect(apiClient.defaults.timeout).toBe(30000);
    expect(apiClient.defaults.headers['Content-Type']).toBe('application/json');
  });

  it('should have valid base URL configured', () => {
    expect(apiClient.defaults.baseURL).toBeDefined();
    expect(typeof apiClient.defaults.baseURL).toBe('string');
  });

  it('stores API key only in memory and extracts analyst label without exposing secret', () => {
    expect(getApiKey()).toBeNull();
    expect(getApiKeyLabel()).toBeNull();

    setApiKey('  analista-1:segredo-super-forte  ');
    expect(getApiKey()).toBe('analista-1:segredo-super-forte');
    expect(getApiKeyLabel()).toBe('analista-1');

    setApiKey('chave-sem-dois-pontos');
    expect(getApiKeyLabel()).toBe('Chave ativa');

    setApiKey('   ');
    expect(getApiKey()).toBeNull();
    expect(getApiKeyLabel()).toBeNull();
  });

  it('injects X-API-Key header on requests when set and removes when cleared', async () => {
    const adapterCalls: Array<Record<string, unknown>> = [];
    const originalAdapter = apiClient.defaults.adapter;

    apiClient.defaults.adapter = async (config) => {
      adapterCalls.push({
        apiKey: config.headers instanceof AxiosHeaders ? config.headers.get('X-API-Key') : undefined,
      });
      return {
        data: {},
        status: 200,
        statusText: 'OK',
        headers: {},
        config,
      };
    };

    try {
      setApiKey('maria:segredo-123');
      await apiClient.get('/api/v1/health');
      expect(adapterCalls[0].apiKey).toBe('maria:segredo-123');

      setApiKey(null);
      await apiClient.get('/api/v1/health');
      expect(adapterCalls[1].apiKey).toBeUndefined();
    } finally {
      apiClient.defaults.adapter = originalAdapter;
    }
  });
});
