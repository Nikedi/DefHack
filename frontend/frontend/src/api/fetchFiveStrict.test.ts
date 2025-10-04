import { test, expect } from 'vitest';
import { fetchObservations, _internal } from './index';

/* Simple STRICT fetch test
   - Requires observations endpoint to exist (fails otherwise)
   - Fetches up to 5 observations
   - Logs them to console
*/

function validateObservation(o: any) {
  expect(o).toBeTypeOf('object');
  expect(typeof o.time).toBe('string');
  expect(typeof o.what).toBe('string');
}

test('strict fetch 5 observations', async () => {
  const ep = await _internal.detectObservationsEndpoint();
  if (!ep) throw new Error('Observations endpoint not detected');

  const list = await fetchObservations({ limit: 5 });
  expect(Array.isArray(list)).toBe(true);
  expect(list.length <= 5).toBe(true);
  list.forEach(validateObservation);
  // Print cleanly
  // eslint-disable-next-line no-console
  console.log('[strict-five] fetched', list.length, 'observations:', JSON.stringify(list, null, 2));
}, 12000);

export {};
