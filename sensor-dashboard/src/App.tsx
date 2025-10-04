// src/App.tsx
import React, { useEffect, useState } from "react";
import Topbar from "./components/Topbar";
import Sidebar from "./components/Sidebar";
import SummaryCards from "./components/SummaryCards";
import { TimeSeriesChart, WhatPieChart } from "./components/Charts";
import DataTable from "./components/DataTable";
import ClarityChat from "./components/ClarityChat";
import RightPanel from "./components/RightPanel";
import { fetchAnalytics, fetchObservations } from "./api";
import ErrorBoundary from "./components/ErrorBoundary";
import "./styles/military.css";

function App() {
  const [page, setPage] = useState<"dashboard" | "reports">("dashboard");
  const [analytics, setAnalytics] = useState<any>(null);
  const [observations, setObservations] = useState<any[]>([]);
  const [filters, setFilters] = useState<any>({});
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const a = await fetchAnalytics();
      setAnalytics(a);
    } catch (err) {
      console.error("fetchAnalytics error", err);
      setAnalytics(null);
    }
    try {
      const rows = await fetchObservations(filters);
      setObservations(rows ?? []);
    } catch (err) {
      console.error("fetchObservations error", err);
      setObservations([]);
    }
    setLoading(false);
  };

  useEffect(() => {
    load();
    const t = setInterval(load, 30000); // poll every 30s
    return () => clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters]);

  return (
    <div className="mil-root">
      <Topbar />
      <div className="mil-main">
        <aside className="mil-sidebar">
          <div className="mil-panel">
            <Sidebar filters={filters} setFilters={setFilters} />
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
              <div className="ml-auto mil-muted">{loading ? "Refreshing…" : "Idle"}</div>
            </div>

            {page === "dashboard" && (
              <>
                <div className="mil-summary-grid mb-4">
                  <SummaryCards analytics={analytics} />
                </div>

                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div className="col-span-2 mil-panel scanline">
                    <div className="mil-muted text-sm mb-2">Map / Feed</div>
                    <div className="mil-map-large" />
                  </div>
                  <div className="mil-panel mil-alerts">
                    <div className="mil-muted text-sm">Alerts</div>
                    <ul className="mt-3 space-y-2">
                      <li className="flex items-start gap-3">
                        <span className="status-dot status-warn" />
                        <div>
                          <div className="font-bold">Sensor latency</div>
                          <div className="mil-muted text-xs">Sensor S3 not responding</div>
                        </div>
                      </li>
                    </ul>
                  </div>
                </div>

                <div className="mil-panel mb-4">
                  <TimeSeriesChart data={analytics?.timeseries ?? []} />
                </div>

                <div className="mil-panel mil-table-wrap">
                  <DataTable data={observations} />
                </div>
              </>
            )}

            {page === "reports" && (
              <div className="flex gap-4">
                <div className="flex-1">
                  <ClarityChat />
                </div>
                <RightPanel analytics={analytics} />
              </div>
            )}
          </ErrorBoundary>
        </div>
      </div>
    </div>
  );
}

export default App;