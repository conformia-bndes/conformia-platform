import { describe, it, expect } from 'vitest';
import { apiClient } from '../services/api';

describe('API Service Client Configuration', () => {
  it('should initialize apiClient with proper defaults', () => {
    expect(apiClient).toBeDefined();
    expect(apiClient.defaults.timeout).toBe(30000);
    expect(apiClient.defaults.headers['Content-Type']).toBe('application/json');
  });

  it('should have valid base URL configured', () => {
    expect(apiClient.defaults.baseURL).toBeDefined();
    expect(typeof apiClient.defaults.baseURL).toBe('string');
  });
});
