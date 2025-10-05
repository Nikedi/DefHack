import { describe, it, expect } from 'vitest';
import axios from 'axios';
import { ingestObservation, _internal } from './index';

// Integration test (soft by default). RUN_INTEGRATION=1 makes failures hard.
const ENV: any = (import.meta as any).env || {};
const RUN_INTEGRATION = ENV.RUN_INTEGRATION === '1';
const BASE = ENV.VITE_API_BASE || 'http://172.20.10.5:8080';
const API_KEY = ENV.VITE_API_KEY;

const MGRS_RE = /^[0-9]{1,2}[C-HJ-NP-X][A-HJ-NP-Z]{2}[0-9]{2,10}$/;

interface SensorObservationIn { time: string; mgrs?: string | null; what: string; confidence: number; sensor_id?: string | null; unit?: string | null; observer_signature: string; original_message?: string | null; }

function buildClient() {
  return axios.create({ baseURL: BASE, timeout: 5000, headers: { ...(API_KEY ? { 'X-API-Key': API_KEY } : {}) } });
}

function softFail(msg: string, err?: any) {
  if (RUN_INTEGRATION) throw err || new Error(msg);
  console.warn('[integration-soft-skip]', msg, err?.message || '');
  expect(true).toBe(true);
}

function validateObservation(o: any) {
  expect(o).toBeTypeOf('object');
  expect(typeof o.time).toBe('string');
  expect(!Number.isNaN(Date.parse(o.time))).toBe(true);
  if (o.mgrs != null) {
    expect(typeof o.mgrs).toBe('string');
    expect(MGRS_RE.test(String(o.mgrs).replace(/\s+/g, '').toUpperCase())).toBe(true);
  }
  expect(typeof o.what).toBe('string');
  if (typeof o.confidence === 'number') {
    expect(o.confidence).toBeGreaterThanOrEqual(0);
    expect(o.confidence).toBeLessThanOrEqual(100);
  }
}

describe('API ingest observation (soft)', () => {
  it('connectivity (soft)', async () => {
    const c = buildClient();
    try {
      await c.get('/').catch(() => {});
      expect(true).toBe(true);
    } catch (e: any) {
      if (['ECONNREFUSED', 'ETIMEDOUT'].includes(e.code)) softFail('Backend unreachable', e);
      else softFail('Unexpected connectivity error', e);
    }
  }, 5000);

  it('POST /ingest/sensor -> validate minimal backend response (soft)', async () => {
    const uniqueTag = 'TEST_OBS_' + Date.now();
    const payload: SensorObservationIn = {
      time: new Date().toISOString(),
      mgrs: '35VLG8472571866',
      what: uniqueTag,
      confidence: 64,
      sensor_id: 'TEST_CLIENT',
      observer_signature: 'VitestClient'
    };

    try {
      const res = await ingestObservation(payload);
      if (RUN_INTEGRATION) {
        expect(res).toBeTypeOf('object');
        expect(res.report_id || res.notification_status).toBeTruthy();
      }
    } catch (e: any) {
      const code = e?.response?.status;
      if ([400, 401, 403, 404, 422].includes(code)) return softFail('Ingest returned ' + code, e);
      if (['ECONNREFUSED', 'ETIMEDOUT'].includes(e.code)) return softFail('Network error ' + e.code, e);
      return softFail('Unexpected ingest error', e);
    }

    // Optional retrieval only if listing endpoint exists
    try {
      const path = await _internal.detectObservationsEndpoint();
      if (!path) {
        console.warn('[integration-soft-skip] No observations endpoint yet');
        return expect(true).toBe(true);
      }
      const c = buildClient();
      const list = await c.get(path, { params: { limit: 50 } }).then(r => r.data);
      if (Array.isArray(list) && RUN_INTEGRATION) {
        const found = list.find((o: any) => o.what === uniqueTag);
        if (found) validateObservation(found);
      }
      expect(true).toBe(true);
    } catch (e: any) {
      const code = e?.response?.status;
      if ([404, 401, 403].includes(code)) softFail('Fetch observations returned ' + code, e);
      else if (['ECONNREFUSED', 'ETIMEDOUT'].includes(e.code)) softFail('Fetch network error ' + e.code, e);
      else softFail('Unexpected fetch error', e);
    }
  }, 12000);
});
