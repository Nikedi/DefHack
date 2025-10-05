// src/api/index.ts
import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE ?? ""; // leave empty to use Vite proxy (/api -> backend)

const client = axios.create({ baseURL: API_BASE });

// Example: call backend /search (backend expects q parameter)
export const fetchObservations = (params: any) =>
  // if you want a raw search: map params to q/k
  client.get("/search", { params: { q: params?.q ?? "", k: params?.k ?? 100 } }).then(res => res.data);

// No /analyze on backend — use /orders/draft or create an analyze route.
// Example calling draft order endpoint (backend returns generated text)
export const fetchAnalytics = () =>
  client.post("/orders/draft", { query: "summary of recent observations", k: 10 }).then(res => res.data);

// backend has intel upload and ingest endpoints — report route doesn't exist.
// Keep fetchReport but map to a backend route or implement a backend /report route.
export const fetchReport = (type: string, query: string) =>
  client.post(`/report/${type}`, { query }).then(res => res.data);