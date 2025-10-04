import { useEffect, useState } from "react";

interface HistoryItem { id: number; generated_at: string; title: string; summary: string; content: string; }

function loadHistory(): HistoryItem[] {
  try { return JSON.parse(localStorage.getItem('opord_history') || '[]'); } catch { return []; }
}

export default function RightPanel({ mode = 'dashboard' }: any) {
  const [history, setHistory] = useState<HistoryItem[]>([]);

  useEffect(() => {
    if (mode === 'reports') setHistory(loadHistory().slice().reverse());
    const handler = () => { if (mode === 'reports') setHistory(loadHistory().slice().reverse()); };
    window.addEventListener('opord-history-updated', handler);
    return () => window.removeEventListener('opord-history-updated', handler);
  }, [mode]);

  if (mode === 'reports') {
    return (
      <aside style={{ width: 360 }} className="ml-4">
        <div className="mil-panel mb-4">
          <div className="flex items-center justify-between mb-2">
            <div className="font-bold">OPORD History</div>
            <div className="text-xs mil-muted">{history.length} saved</div>
          </div>
          <div className="overflow-y-auto" style={{ maxHeight: 420 }}>
            <table className="text-xs w-full">
              <thead>
                <tr className="text-left">
                  <th className="p-2">Time</th>
                  <th className="p-2">Title</th>
                </tr>
              </thead>
              <tbody>
                {history.map(h => (
                  <tr key={h.id} className="cursor-pointer hover:bg-black/20" onClick={() => window.dispatchEvent(new CustomEvent('opord-load-request', { detail: { id: h.id } }))}>
                    <td className="p-2 align-top whitespace-nowrap">{new Date(h.generated_at).toLocaleTimeString()}</td>
                    <td className="p-2 align-top">
                      <div className="font-semibold truncate" title={h.title}>{h.title}</div>
                      <div className="mil-muted truncate" title={h.summary}>{h.summary}</div>
                    </td>
                  </tr>
                ))}
                {history.length === 0 && (
                  <tr><td className="p-3 mil-muted" colSpan={2}>No reports yet</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </aside>
    );
  }

  /* Dashboard mode (original content) */
  return (
    <aside style={{ width: 360 }} className="ml-4">
      <div className="mb-4 mil-panel">
        <div className="flex items-center justify-between">
          <div className="font-bold">Key Findings</div>
          <div className="text-xs mil-muted">Updated 00:00:30</div>
        </div>
        <ul className="mt-3 space-y-2">
          <li className="p-2 border bg-black/10 border-black/10">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-bold">Foot movement detected</div>
                <div className="text-xs mil-muted">GRID 12K • 5 units</div>
              </div>
              <div className="text-sm font-bold" style={{ color: "var(--mil-sand)" }}>91%</div>
            </div>
          </li>
          <li className="p-2 border bg-black/10 border-black/10">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-bold">Sensor latency</div>
                <div className="text-xs mil-muted">Sensor S3 lag &gt; 30s</div>
              </div>
              <div className="text-sm font-bold" style={{ color: "var(--mil-accent)" }}>73%</div>
            </div>
          </li>
        </ul>
      </div>
      <div className="mb-4 mil-panel">
        <div className="mb-2 text-sm mil-muted">Mini Map</div>
        <div style={{ height: 180 }} className="border bg-black/30 border-black/15" />
      </div>
      <div className="mb-4 mil-panel">
        <div className="mb-2 text-sm mil-muted">Activity (last hour)</div>
        <div style={{ height: 120 }} className="flex items-center justify-center border bg-black/20 border-black/12 mil-muted">
          Activity graph
        </div>
      </div>
      <div className="mil-panel">
        <div className="flex gap-2">
          <button className="btn-mil">Export SITREP</button>
          <button className="btn-mil">Copy to Briefing</button>
        </div>
      </div>
    </aside>
  );
}