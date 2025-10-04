import React from "react";

type Observation = any;

export default function DataTable({ data = [] }: { data?: Observation[] }) {
  if (!Array.isArray(data)) data = [];
  return (
    <div className="mil-panel">
      <div className="flex justify-between items-center mb-2">
        <h2 className="text-lg font-bold">Observations</h2>
        <div className="flex items-center gap-3">
          <span className="status-dot status-ok blink" title="Live feed" />
          <button className="btn-mil">Refresh</button>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm mil-table">
          <thead>
            <tr>
              <th className="p-3">ID</th>
              <th className="p-3">Time</th>
              <th className="p-3">MGRS</th>
              <th className="p-3">What</th>
              <th className="p-3">Confidence</th>
            </tr>
          </thead>
          <tbody>
            {data.slice(0, 50).map((r: any) => (
              <tr key={r.id ?? Math.random()} className="hover:bg-black/10 transition-colors">
                <td className="p-3">{r.id}</td>
                <td className="p-3">{r.time}</td>
                <td className="p-3">{r.mgrs}</td>
                <td className="p-3">{r.what}</td>
                <td className="p-3">{r.confidence ?? ""}</td>
              </tr>
            ))}
            {data.length === 0 && (
              <tr>
                <td className="p-4 mil-muted" colSpan={5}>No observations</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}