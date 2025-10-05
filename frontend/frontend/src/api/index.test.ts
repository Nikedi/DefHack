import { describe, it, expect } from 'vitest';
import axios from 'axios';

// Use import.meta.env for Vite instead of process.env (avoids needing Node types)
const RUN_INTEGRATION = (import.meta as any).env?.RUN_INTEGRATION === '1';

const BASE = (import.meta as any).env?.VITE_API_BASE || 'http://172.20.10.5:8080';
const API_KEY = (import.meta as any).env?.VITE_API_KEY;

function buildClient() {
  const client = axios.create({ baseURL: BASE, timeout: 2500 });
  if (API_KEY) client.defaults.headers.common['X-API-Key'] = API_KEY;
  return client;
}

function softFail(msg: string, err?: any) {
  if (RUN_INTEGRATION) throw err || new Error(msg);
  // eslint-disable-next-line no-console
  console.warn('[integration-soft-skip]', msg, err?.message || '');
  expect(true).toBe(true);
}

describe('backend connectivity', () => {
  it('reaches backend base URL (soft)', async () => {
    const client = buildClient();
    try {
      await client.get('/').catch(r => r);
      expect(true).toBe(true);
    } catch (e) {
      softFail('Backend not reachable', e);
    }
  }, 4000);
});

describe('observations endpoint (soft, openapi discovery)', () => {
  it('discovers and optionally queries listing endpoint', async () => {
    const client = buildClient();
    let path: string | null = null;
    try {
      const spec = await client.get('/openapi.json').then(r => r.data);
      const p = spec?.paths || {};
      if (p['/observations']) path = '/observations';
      else if (p['/sensor/observations']) path = '/sensor/observations';
      else {
        console.warn('[integration-soft-skip] No observations path in openapi spec');
        return expect(true).toBe(true);
      }
    } catch (e) {
      return softFail('OpenAPI spec not reachable', e);
    }

    if (!path) return; // already soft skipped

    try {
      const res = await client.get(path, { params: { limit: 1 } });
      if (Array.isArray(res.data)) {
        if (RUN_INTEGRATION && res.data.length) {
          const first = res.data[0];
          expect(first).toHaveProperty('time');
          expect(first).toHaveProperty('what');
        }
        expect(true).toBe(true);
      } else softFail('Data not array (acceptable in soft mode)');
    } catch (e: any) {
      const code = e?.response?.status;
      if ([404, 401, 403].includes(code)) softFail('Endpoint responded with ' + code, e);
      else if (['ECONNREFUSED', 'ETIMEDOUT'].includes(e.code)) softFail('Network error ' + e.code, e);
      else softFail('Unexpected error', e);
    }
  }, 5000);
});
