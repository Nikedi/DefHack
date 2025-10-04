// src/api/index.ts
import axios from "axios";

// Backend base URL: takes from env, else falls back to field network IP
// Set VITE_API_BASE in .env.local if you want to override.
const API_BASE = (import.meta.env.VITE_API_BASE as string | undefined) || "http://172.20.10.5:8080";
const API_KEY = import.meta.env.VITE_API_KEY as string | undefined; // put X-API-Key here (never hardcode)

const client = axios.create({ baseURL: API_BASE });
if (API_KEY) client.defaults.headers.common["X-API-Key"] = API_KEY;

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

// --- Dynamic observations endpoint detection (backend currently missing /observations) ---
let observationsEndpoint: string | null | undefined; // undefined = unknown, null = not present
async function detectObservationsEndpoint(): Promise<string | null> {
  if (observationsEndpoint !== undefined) return observationsEndpoint;
  try {
    const spec = await client.get('/openapi.json').then(r => r.data).catch(() => null);
    const p = spec?.paths || {};
    if (p['/observations']) observationsEndpoint = '/observations';
    else if (p['/sensor/observations']) observationsEndpoint = '/sensor/observations';
    else observationsEndpoint = null;
  } catch {
    observationsEndpoint = null;
  }
  return observationsEndpoint;
}

// Fetch raw observations from backend with filtering support.
// Tries detected endpoint, returns [] if none available yet.
export const fetchObservations = async (filters: ObservationFilters = {}): Promise<SensorObservation[]> => {
  const ep = await detectObservationsEndpoint();
  if (!ep) return []; // backend does not expose listing yet
  const params = buildObservationParams(filters);
  const res = await client.get(ep, { params });
  return Array.isArray(res.data) ? res.data : [];
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
export const _internal = { detectObservationsEndpoint };