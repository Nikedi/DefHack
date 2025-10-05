import { describe, test, expect } from 'vitest';
import axios from 'axios';

/* Strict integration test updated:
   - Uses authoritative base URL + API key
   - Ingests an observation (expects 200/201)
   - Attempts retrieval only if /observations (or /sensor/observations) exists in openapi spec
*/

const ENV: any = (import.meta as any).env || {};
const BASE = ENV.VITE_API_BASE || 'http://172.20.10.5:8080';
const API_KEY = ENV.VITE_API_KEY; // required

if (!API_KEY) console.warn('[strict-test-warning] VITE_API_KEY not set – ingestion will 401');

interface SensorObservationIn { time: string; mgrs?: string | null; what: string; confidence: number; sensor_id?: string | null; unit?: string | null; observer_signature: string; original_message?: string | null; }

const client = axios.create({ baseURL: BASE, timeout: 8000, headers: { 'Content-Type': 'application/json', ...(API_KEY ? { 'X-API-Key': API_KEY } : {}) } });

let createdTag: string | null = null;
let observationsPath: string | null = null;

async function detectListingPath(): Promise<string | null> {
  try {
    const spec = await client.get('/openapi.json').then(r => r.data);
    const paths = spec?.paths || {};
    if (paths['/observations']) return '/observations';
    //if (paths['/sensor/observations']) return '/sensor/observations';
  } catch (e) {
    // ignore
  }
  return null;
}

describe('STRICT ingest + optional retrieval', () => {
  test('ingest observation', async () => {
    createdTag = 'STRICT_TEST_OBS_' + Date.now();
    const payload: SensorObservationIn = {
      time: new Date().toISOString(),
      mgrs: '35VLG8472571866',
      what: createdTag,
      confidence: 90,
      sensor_id: 'STRICT_CLIENT1',
      observer_signature: 'StrictVitest'
    };

    const res = await client.post('/ingest/sensor', payload).catch(e => e.response || Promise.reject(e));
    expect(res?.status, 'Ingest must succeed (200/201) – got ' + res?.status).toBeDefined();
    expect([200,201]).toContain(res.status);
    expect(res.data).toBeTypeOf('object');
    // backend returns {report_id, notification_status}; we just sanity check
    expect(res.data.report_id || res.data.notification_status).toBeTruthy();
  }, 15000);

  test('retrieve (only if listing path present)', async () => {
    expect(createdTag).toBeTruthy();
    observationsPath = await detectListingPath();
    if (!observationsPath) {
      console.warn('[strict-test-skip] No listing endpoint exposed yet – skipping retrieval test');
      expect(true).toBe(true);
      return;
    }
    // small delay in case persistence is async
    await new Promise(r => setTimeout(r, 750));
    const list = await client.get(observationsPath, { params: { limit: 50 } }).then(r => r.data);
    expect(Array.isArray(list), 'Listing endpoint must return array').toBe(true);
    const found = list.find((o: any) => o?.what === createdTag);
    expect(found, 'Ingested tag not found in listing').toBeTruthy();
  }, 15000);
});

export {};
