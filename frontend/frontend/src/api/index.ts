// src/api/index.ts
import axios from "axios";

// Backend base URL selection logic enhanced: when in browser dev and no explicit VITE_API_BASE, use proxy prefix /api
const runtimeIsBrowser = typeof window !== 'undefined';
const directBase = (import.meta.env.VITE_API_BASE as string | undefined);
const API_BASE = directBase || (runtimeIsBrowser ? '/api' : 'http://172.20.10.5:8080');
const API_KEY = import.meta.env.VITE_API_KEY as string | undefined; // put X-API-Key here (never hardcode)
const FORCE_PATH = import.meta.env.VITE_OBS_FORCE_PATH as string | undefined; // optionally force endpoint
const DETECT_TIMEOUT = parseInt(import.meta.env.VITE_OBS_DETECT_TIMEOUT_MS || '3500', 10);
const DEBUG_OBS = (import.meta.env.VITE_DEBUG_OBS || '').toLowerCase() === '1';

const client = axios.create({ baseURL: API_BASE, timeout: 10000 });
if (API_KEY) client.defaults.headers.common["X-API-Key"] = API_KEY;

const proxyClient = runtimeIsBrowser ? axios.create({ baseURL: '/api', timeout: 10000 }) : null;
if (proxyClient && API_KEY) proxyClient.defaults.headers.common['X-API-Key'] = API_KEY;

function logDebug(...args: any[]) { if (DEBUG_OBS) console.log('[obs-debug]', ...args); }

// ========= Types (align with backend pydantic models) =========
export interface SensorObservation {
  time: string; // ISO 8601
  mgrs: string | null;
  what: string;
  amount?: number | null;
  confidence: number;
  sensor_id?: string | null;
  unit?: string | null;
  observer_signature: string;
  original_message?: string | null;
  // optional id if backend adds one later
  id?: string | number;
}

export interface ObservationFilters {
  limit?: number; // default 200
  from?: string; // ISO date (yyyy-mm-dd) or datetime
  to?: string;
  what?: string;
  sensor_id?: string;
  confidence?: number; // minimum confidence threshold
}

export interface ObservationListMeta {
  total?: number;
  limit?: number;
  offset?: number;
  returned?: number;
}

let lastObservationMeta: ObservationListMeta | null = null;

// Normalize filters into query params accepted by backend
function buildObservationParams(f: ObservationFilters = {}): Record<string, any> {
  const params: Record<string, any> = {};
  if (f.limit) params.limit = f.limit; else params.limit = 200;
  if (f.from) params.from = f.from;
  if (f.to) params.to = f.to;
  if (f.what) params.what = f.what;
  if (f.sensor_id) params.sensor_id = f.sensor_id;
  if (typeof f.confidence === "number" && !Number.isNaN(f.confidence)) params.min_confidence = f.confidence;
  return params;
}

// --- Dynamic observations endpoint detection (robust) ---
let observationsEndpoint: string | null | undefined; // undefined = unknown, null = not present
let lastDetectionError: string | null = null;

function looksLikeWrapped(data: any): boolean {
  return !!(data && typeof data === 'object' && Array.isArray(data.observations));
}

function acceptableListingPayload(data: any): boolean {
  return Array.isArray(data) || looksLikeWrapped(data);
}

async function safeGet(path: string, params?: any, timeoutMs = DETECT_TIMEOUT): Promise<any | null> {
  try {
    const res = await client.get(path, { params, timeout: timeoutMs });
    return res.data;
  } catch (e: any) {
    logDebug('safeGet error primary', path, e?.code || e?.response?.status);
    // Fallback via proxy (browser CORS scenario)
    if (proxyClient) {
      try {
        const res2 = await proxyClient.get(path, { params, timeout: timeoutMs });
        logDebug('safeGet proxy success', path);
        return res2.data;
      } catch (e2: any) {
        logDebug('safeGet proxy error', path, e2?.code || e2?.response?.status);
      }
    }
    return null;
  }
}

async function detectObservationsEndpoint(): Promise<string | null> {
  if (FORCE_PATH) { observationsEndpoint = FORCE_PATH; return observationsEndpoint; }
  if (observationsEndpoint !== undefined) return observationsEndpoint;
  lastDetectionError = null;
  try {
    // 1. Try openapi.json quickly
    const spec = await safeGet('/openapi.json');
    const paths = spec?.paths || {};
    if (paths['/observations']) { observationsEndpoint = '/observations'; return observationsEndpoint; }
    if (paths['/sensor/observations']) { observationsEndpoint = '/sensor/observations'; return observationsEndpoint; }
  } catch (e: any) {
    lastDetectionError = 'openapi fail:' + (e?.code || e?.response?.status || 'err');
  }
  // 2. Probe likely endpoints (short timeout)
  const candidates = ['/observations', '/sensor/observations'];
  for (const c of candidates) {
    const probe = await safeGet(c, { limit: 1 });
    if (acceptableListingPayload(probe)) { observationsEndpoint = c; return observationsEndpoint; }
  }
  observationsEndpoint = null;
  if (!lastDetectionError) lastDetectionError = 'no endpoints responded with acceptable payload';
  return observationsEndpoint;
}

function resetObservationsEndpointCache() { observationsEndpoint = undefined; }

function captureMetaFromWrapper(data: any, observations: any[]) {
  lastObservationMeta = {
    total: data.total ?? data.pagination?.total,
    limit: data.limit ?? data.pagination?.limit,
    offset: data.offset ?? data.pagination?.offset,
    returned: data.pagination?.returned ?? observations.length
  };
}

function extractList(data: any): SensorObservation[] {
  if (Array.isArray(data)) {
    lastObservationMeta = { total: data.length, limit: data.length, offset: 0, returned: data.length };
    return data as SensorObservation[];
  }
  if (looksLikeWrapped(data)) {
    const arr = Array.isArray(data.observations) ? data.observations : [];
    captureMetaFromWrapper(data, arr);
    return arr as SensorObservation[];
  }
  lastObservationMeta = null;
  return [];
}

// Fetch raw observations from backend with filtering support.
// Tries detected endpoint, returns [] if none available yet.
export const fetchObservations = async (filters: ObservationFilters = {}): Promise<SensorObservation[]> => {
  let ep = await detectObservationsEndpoint();
  const params = buildObservationParams(filters);
  const tryClients: any[] = [client];
  if (proxyClient && client.defaults.baseURL !== proxyClient.defaults.baseURL) tryClients.push(proxyClient);
  // Fallback: if detection failed, try on-the-fly probes every call (uncached) to recover when backend comes up later
  if (!ep) {
    const candidates = ['/observations', '/sensor/observations'];
    for (const c of candidates) {
      for (const cl of tryClients) {
        try {
          const res = await cl.get(c, { params });
          const data = res.data;
          if (Array.isArray(data) || looksLikeWrapped(data)) {
            observationsEndpoint = c;
            return extractList(data);
          }
        } catch { /* ignore */ }
      }
    }
    return [];
  }
  for (const cl of tryClients) {
    try {
      const res = await cl.get(ep, { params });
      const data = res.data;
      if (Array.isArray(data) || looksLikeWrapped(data)) return extractList(data);
    } catch (e: any) {
      logDebug('fetch error client variant', cl.defaults.baseURL, e?.code || e?.response?.status);
      lastDetectionError = 'fetch fail:' + (e?.code || e?.response?.status || 'err');
      // try next client
    }
  }
  try {
    const data = await safeGet(ep, params);
    if (!data) { lastObservationMeta = null; return []; }
    return extractList(data);
  } catch (e) {
    lastObservationMeta = null;
    return [];
  }
};

// Ingest (POST) single observation; backend returns {report_id, notification_status}
export const ingestObservation = async (payload: Partial<SensorObservation> & { time: string; what: string; confidence: number; observer_signature: string; mgrs?: string | null }) => {
  const res = await client.post('/ingest/sensor', payload);
  return res.data;
};

// Placeholder analytics (keep LLM draft for now) or implement a real /analytics
export const fetchAnalytics = () =>
  client.post("/orders/draft", { query: "summary of recent observations", k: 10 }).then(res => res.data);

// backend has intel upload and ingest endpoints — report route doesn't exist.
// Keep fetchReport but map to a backend route or implement a backend /report route.
export const fetchReport = (type: string, query: string) =>
  client.post(`/report/${type}`, { query }).then(res => res.data);

// Utility export (optional) for tests / diagnostics
export const _internal = { detectObservationsEndpoint, resetObservationsEndpointCache, getDebugMeta: () => ({ endpoint: observationsEndpoint, lastDetectionError }), getLastObservationMeta: () => lastObservationMeta };