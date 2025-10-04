// src/App.tsx
import { useEffect, useRef, useState } from "react";
import Topbar from "./components/Topbar";
import Sidebar from "./components/Sidebar";
import SummaryCards from "./components/SummaryCards";
import { TimeSeriesChart } from "./components/Charts";
import DataTable from "./components/DataTable";
import RightPanel from "./components/RightPanel";
import Reports from "./components/Reports";
import { fetchAnalytics, fetchObservations, _internal } from "./api";
import ErrorBoundary from "./components/ErrorBoundary";
import "./styles/military.css";

function App() {
  const [page, setPage] = useState<"dashboard" | "reports">("dashboard");
  const [analytics, setAnalytics] = useState<any>(null);
  const [observations, setObservations] = useState<any[]>([]);
  const [filters, setFilters] = useState<any>({});
  const [loading, setLoading] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<string | null>(null);
  const [endpointPath, setEndpointPath] = useState<string | null>(null);
  const [listMeta, setListMeta] = useState<any>(null);
  const backoffRef = useRef(2000);
  const refreshTimerRef = useRef<any>(null);
  const abortRef = useRef<boolean>(false);

  const API_BASE = (import.meta as any).env?.VITE_API_BASE;

  const load = async (manual: boolean = false) => {
    if (loading) return; // prevent overlap
    setLoading(true);
    abortRef.current = false;
    try {
      // detect endpoint once (cached internally) – if missing keep trying but slower
      if (!endpointPath) {
        const ep = await _internal.detectObservationsEndpoint();
        if (ep) setEndpointPath(ep);
      }
      const a = await fetchAnalytics().catch(() => null);
      if (!abortRef.current) setAnalytics(a);
      const rows = await fetchObservations(filters).catch(() => []);
      if (manual) {
        // eslint-disable-next-line no-console
        console.log('[manual-refresh] fetched observations count=', rows?.length || 0, rows);
      }
      if (!abortRef.current) setObservations(rows ?? []);
      const meta = _internal.getLastObservationMeta?.();
      if (!abortRef.current) setListMeta(meta);
      setLastRefresh(new Date().toLocaleTimeString());
      backoffRef.current = 5000; // reset to 5s after success
    } catch (err) {
      console.error("refresh cycle error", err);
      backoffRef.current = Math.min(backoffRef.current * 1.75, 30000);
    } finally {
      setLoading(false);
    }
  };

  // adaptive polling
  useEffect(() => {
    function schedule() {
      clearTimeout(refreshTimerRef.current);
      refreshTimerRef.current = setTimeout(async () => {
        await load();
        schedule();
      }, backoffRef.current);
    }
    load(); // immediate on filters change
    schedule();
    return () => clearTimeout(refreshTimerRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters]);

  // manual abort (e.g., page change)
  useEffect(() => () => { abortRef.current = true; }, []);

  useEffect(() => {
    if (!endpointPath) {
      const meta = _internal.getDebugMeta();
      // eslint-disable-next-line no-console
      console.warn('[ui] observations endpoint not detected yet', meta, 'API_BASE=', API_BASE);
    }
  }, [endpointPath, API_BASE]);

  return (
    <div className="mil-root">
      <Topbar />
      <div className="mil-main">
        <aside className="mil-sidebar">
          <div className="mil-panel">
            <Sidebar filters={filters} setFilters={setFilters} />
          </div>
          <div className="mil-panel p-2 mt-4 text-xs mil-muted">
            <div>Endpoint: {endpointPath || 'detecting…'}</div>
            <div>API Base: {API_BASE || 'default ip'}</div>
            <div>Last refresh: {lastRefresh || '—'}</div>
          </div>
        </aside>

        <div className="mil-content">
          <ErrorBoundary>
            <div className="flex items-center gap-3 mb-4">
              <button className={`btn-mil ${page === "dashboard" ? "mil-interactive" : ""}`} onClick={() => setPage("dashboard")}>
                Dashboard
              </button>
              <button className={`btn-mil ${page === "reports" ? "mil-interactive" : ""}`} onClick={() => setPage("reports")}>
                Reports
              </button>
              <button className="btn-mil" onClick={() => load(true)} disabled={loading}>
                Refresh Now
              </button>
              <div className="ml-auto flex items-center gap-3">
                <div className="text-xs mil-muted">{loading ? "Refreshing…" : `Updated ${lastRefresh || '—'}`}</div>
                <span className={`status-dot ${endpointPath ? 'status-ok' : 'status-warn'}`} title={endpointPath ? 'Observations endpoint active' : 'Endpoint not detected'} />
              </div>
            </div>

            {page === "dashboard" && (
              <>
                {/* 2x2 Summary Metric Grid */}
                <SummaryCards analytics={analytics} observations={observations} listMeta={listMeta} />

                {/* Observations Table moved ABOVE map */}
                <div className="mb-4 mil-panel mil-table-wrap">
                  <DataTable data={observations} onRefresh={() => load(true)} />
                  {observations.length === 0 && (
                    <div className="mt-2 p-2 text-xs mil-muted border-t border-black/30 flex flex-col gap-1">
                      <div>No observations returned.</div>
                      <div>Endpoint cache: {endpointPath || 'n/a'}</div>
                      <div>Detection meta: {JSON.stringify(_internal.getDebugMeta())}</div>
                      <div>Ensure backend exposes /observations or /sensor/observations and API key is valid.</div>
                    </div>
                  )}
                </div>

                {/* Map + Alerts side by side */}
                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div className="col-span-2 mil-panel scanline">
                    <div className="mb-2 text-sm mil-muted">Map / Feed</div>
                    <div className="mil-map-large" />
                  </div>
                  <div className="mil-panel mil-alerts">
                    <div className="text-sm mil-muted">Alerts</div>
                    <ul className="mt-3 space-y-2">
                      <li className="flex items-start gap-3">
                        <span className="status-dot status-warn" />
                        <div>
                          <div className="font-bold">Sensor latency</div>
                          <div className="text-xs mil-muted">Sensor S3 not responding</div>
                        </div>
                      </li>
                    </ul>
                  </div>
                </div>

                {/* Timeseries / other charts */}
                <div className="mb-4 mil-panel">
                  <TimeSeriesChart data={analytics?.timeseries ?? []} />
                </div>
              </>
            )}

            {page === "reports" && (
              <div className="flex gap-4">
                <div className="flex-1 flex flex-col">
                  <Reports observations={observations} />
                </div>
                <RightPanel mode="reports" analytics={analytics} />
              </div>
            )}
          </ErrorBoundary>
        </div>
      </div>
    </div>
  );
}

export default App;