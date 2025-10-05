import { describe, test, expect } from 'vitest';
import axios from 'axios';
import { fetchObservations, ingestObservation, _internal } from './index';

/* Diagnostic STRICT test to debug fetching observations
   Steps:
   1. Detect observations endpoint (logs every step)
   2. Ingest a unique observation directly via wrapper AND (optionally) raw axios
   3. Retry fetchObservations with filtering until the new observation is visible
   4. If detection failed, attempt manual direct GET /observations fallback

   Run with (adjust IP/key):
   VITE_API_BASE=http://10.3.35.148:8080 VITE_API_KEY=YOUR_KEY npx vitest run src/api/fetchDebug.test.ts
*/

const ENV: any = (import.meta as any).env || {};
const BASE = ENV.VITE_API_BASE || 'http://10.3.35.148:8080';
const API_KEY = ENV.VITE_API_KEY;
if (!API_KEY) console.warn('[fetchDebug] Warning: VITE_API_KEY missing (may 401)');

const rawClient = axios.create({ baseURL: BASE, timeout: 10000, headers: { 'Content-Type': 'application/json', ...(API_KEY ? { 'X-API-Key': API_KEY } : {}) } });

async function delay(ms: number) { return new Promise(r => setTimeout(r, ms)); }

async function directIngest(tag: string) {
  const payload = {
    time: new Date().toISOString(),
    mgrs: '35VLG8472571866',
    what: tag,
    confidence: 90,
    sensor_id: 'FETCH_DEBUG',
    observer_signature: 'FetchDebugTest'
  };
  const res = await rawClient.post('/ingest/sensor', payload).catch(e => {
    console.error('[fetchDebug] direct ingest error status', e?.response?.status, e?.response?.data);
    throw e;
  });
  return { res, payload };
}

function validateObservation(o: any) {
  expect(o).toBeTypeOf('object');
  expect(typeof o.time).toBe('string');
  expect(typeof o.what).toBe('string');
}

describe('FETCH DEBUG observations', () => {
  test('detect + ingest + fetch', async () => {
    const tag = 'FETCH_DEBUG_OBS_' + Date.now();

    // 1. Attempt endpoint detection via internal logic
    const detected = await _internal.detectObservationsEndpoint();
    console.log('[fetchDebug] detected endpoint:', detected);

    // 2. Ingest via wrapper first (tests wrapper path & headers)
    try {
      const wrapRes: any = await ingestObservation({
        time: new Date().toISOString(),
        mgrs: '35VLG8472571866',
        what: tag,
        confidence: 85,
        sensor_id: 'FETCH_DEBUG_WRAPPER',
        observer_signature: 'FetchDebugWrapper'
      });
      console.log('[fetchDebug] wrapper ingest response keys:', Object.keys(wrapRes || {}));
    } catch (e: any) {
      console.error('[fetchDebug] wrapper ingest failed status:', e?.response?.status, e?.response?.data);
      throw e;
    }

    // 2b. Direct ingest (ensures at least one entry even if wrapper mutated later)
    await directIngest(tag);

    // 3. Retry fetching using exported fetchObservations (which itself calls detection)
    let fetched: any[] = [];
    let found: any = null;
    const maxAttempts = 12;
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        fetched = await fetchObservations({ what: tag, limit: 20 });
        console.log(`[fetchDebug] attempt ${attempt} got ${fetched.length} items`);
        if (Array.isArray(fetched)) {
          found = fetched.find(o => o.what === tag);
          if (found) break;
        }
      } catch (e: any) {
        console.warn('[fetchDebug] fetchObservations error attempt', attempt, e?.response?.status, e?.code);
      }
      await delay(750);
    }

    if (!found && !detected) {
      // 4. Manual fallback probe if internal detection failed (try hard-coded /observations)
      try {
        const manual = await rawClient.get('/observations', { params: { what: tag, limit: 20 } }).then(r => r.data);
        console.log('[fetchDebug] manual /observations length', Array.isArray(manual) ? manual.length : 'non-array');
        if (Array.isArray(manual)) found = manual.find(o => o.what === tag);
      } catch (e: any) {
        console.error('[fetchDebug] manual /observations error status', e?.response?.status);
      }
    }

    expect(found, 'Ingested observation not returned by listing').toBeTruthy();
    validateObservation(found);
  }, 45000);

  test('basic list sanity (limit=5)', async () => {
    const list = await fetchObservations({ limit: 5 });
    expect(Array.isArray(list)).toBe(true);
    expect(list.length <= 5).toBe(true);
    list.forEach(o => validateObservation(o));
  }, 10000);
});

export {};
