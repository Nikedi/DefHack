import { describe, test, expect } from 'vitest';
import { fetchObservations, ingestObservation, _internal } from './index';

/* STRICT test for wrapper format of GET /observations
   Backend returns: { total, limit, offset, observations: [...] }
   Client fetchObservations now normalizes to plain array.
*/

const ENV: any = (import.meta as any).env || {};
const API_KEY = ENV.VITE_API_KEY;
if (!API_KEY) console.warn('[fetchWrapperStrict] Missing VITE_API_KEY – may fail');

function validateObservation(o: any) {
  expect(o).toBeTypeOf('object');
  expect(typeof o.time).toBe('string');
  expect(typeof o.what).toBe('string');
  if (typeof o.confidence === 'number') {
    expect(o.confidence).toBeGreaterThanOrEqual(0);
    expect(o.confidence).toBeLessThanOrEqual(100);
  }
}

describe('STRICT wrapper observations fetch', () => {
  test('detect endpoint', async () => {
    const ep = await _internal.detectObservationsEndpoint();
    if (!ep) throw new Error('Observations endpoint missing');
    expect(['/observations','/sensor/observations']).toContain(ep);
  });

  test('ingest + verify listing unwrap', async () => {
    const tag = 'WRAP_FETCH_' + Date.now();
    await ingestObservation({
      time: new Date().toISOString(),
      mgrs: '35VLG8472571866',
      what: tag,
      confidence: 77,
      sensor_id: 'WRAP_CLIENT',
      observer_signature: 'WrapStrict'
    });

    let found: any = null;
    for (let i = 0; i < 8; i++) {
      const list = await fetchObservations({ what: tag, limit: 25 });
      expect(Array.isArray(list)).toBe(true);
      found = list.find(o => o.what === tag);
      if (found) break;
      await new Promise(r => setTimeout(r, 500));
    }
    expect(found, 'Ingested observation not found after retries').toBeTruthy();
    validateObservation(found);
  }, 20000);

  test('limit mechanics still respected with wrapper', async () => {
    const list = await fetchObservations({ limit: 3 });
    expect(Array.isArray(list)).toBe(true);
    expect(list.length <= 3).toBe(true);
    list.forEach(validateObservation);
  });
});

export {};
