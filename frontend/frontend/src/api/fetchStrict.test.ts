import { describe, test, expect } from 'vitest';
import { fetchObservations, ingestObservation, _internal } from './index';

/* STRICT observations listing test
   Fails (no soft skips) if:
   - Observations endpoint is missing
   - Ingestion fails
   - Newly ingested observation is not discoverable via filters within retry window

   Requirements:
   - Backend must expose GET /observations OR /sensor/observations and include it in /openapi.json
   - If API requires key, set VITE_API_KEY
*/

const ENV: any = (import.meta as any).env || {};
const API_KEY = ENV.VITE_API_KEY; // may be required by backend

// Helper validation of a returned observation shape
function validateObservation(o: any) {
  expect(o).toBeTypeOf('object');
  expect(typeof o.time).toBe('string');
  expect(!Number.isNaN(Date.parse(o.time))).toBe(true);
  expect(typeof o.what).toBe('string');
  if (o.confidence != null) {
    expect(typeof o.confidence).toBe('number');
    expect(o.confidence).toBeGreaterThanOrEqual(0);
    expect(o.confidence).toBeLessThanOrEqual(100);
  }
}

async function delay(ms: number) { return new Promise(r => setTimeout(r, ms)); }

describe('STRICT fetch observations', () => {
  test('endpoint detection', async () => {
    const path = await _internal.detectObservationsEndpoint();
    expect(path, 'Observations endpoint MUST exist in strict mode').toBeTruthy();
  }, 8000);

  test('ingest + filtered retrieval', async () => {
    if (!API_KEY) {
      throw new Error('VITE_API_KEY missing – strict test assumes authenticated ingest');
    }

    const uniqueTag = 'STRICT_FETCH_OBS_' + Date.now();
    const payload = {
      time: new Date().toISOString(),
      mgrs: '35VLG8472571866',
      what: uniqueTag,
      confidence: 88,
      sensor_id: 'STRICT_FETCH_CLIENT',
      observer_signature: 'FetchStrictVitest'
    };

    const ingestRes: any = await ingestObservation(payload);
    expect(ingestRes).toBeTypeOf('object');

    // Retry fetch with filter until found (eventual consistency / write propagation)
    const maxAttempts = 10;
    let found: any = null;
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      const filtered = await fetchObservations({ what: uniqueTag, limit: 10 });
      expect(Array.isArray(filtered), 'Fetch must return array').toBe(true);
      found = filtered.find(o => o.what === uniqueTag);
      if (found) break;
      await delay(500);
    }
    expect(found, 'Ingested observation not found via what filter').toBeTruthy();
    validateObservation(found);

    // Confidence filter should still return the observation
    const withConfidence = await fetchObservations({ what: uniqueTag, confidence: 50, limit: 10 });
    expect(withConfidence.some(o => o.what === uniqueTag), 'Observation should appear when min_confidence <= confidence').toBe(true);

    // Higher threshold should also match (since we set confidence 88)
    const highConf = await fetchObservations({ what: uniqueTag, confidence: 85, limit: 10 });
    expect(highConf.some(o => o.what === uniqueTag), 'Observation should appear for high min_confidence').toBe(true);

  }, 30000);

  test('basic limit behavior', async () => {
    const list = await fetchObservations({ limit: 5 });
    expect(Array.isArray(list)).toBe(true);
    expect(list.length <= 5).toBe(true);
    list.slice(0, 3).forEach(validateObservation); // spot check first few
  }, 10000);
});

export {};
