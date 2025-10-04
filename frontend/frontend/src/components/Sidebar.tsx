// src/components/Sidebar.tsx
import React from "react";

export default function Sidebar({ filters, setFilters }: any) {
  return (
    <aside className="space-y-4 mil-panel">
      <div>
        <label className="block mb-1 text-xs mil-muted">Date Range</label>
        <input className="w-full p-2 border bg-black/10 border-black/12" type="date" onChange={e => setFilters((f: any) => ({ ...f, from: e.target.value }))} />
        <input className="w-full p-2 mt-2 border bg-black/10 border-black/12" type="date" onChange={e => setFilters((f: any) => ({ ...f, to: e.target.value }))} />
      </div>
      <div>
        <label className="block mb-1 text-xs mil-muted">Type</label>
        <select className="w-full p-2 border bg-black/10 border-black/12" onChange={e => setFilters((f: any) => ({ ...f, what: e.target.value }))}>
          <option value="">All</option>
          <option value="vehicle">Vehicle</option>
          <option value="person">Person</option>
        </select>
      </div>
      <div>
        <label className="block mb-1 text-xs mil-muted">Sensor ID</label>
        <input className="w-full p-2 border bg-black/10 border-black/12" type="text" onChange={e => setFilters((f: any) => ({ ...f, sensor_id: e.target.value }))} />
      </div>
      <div>
        <label className="block mb-1 text-xs mil-muted">Confidence</label>
        <input className="w-full" type="range" min={0} max={100} value={filters.confidence ?? 0}
          onChange={e => setFilters((f: any) => ({ ...f, confidence: Number(e.target.value) }))} />
        <div className="mt-1 text-xs mil-muted">{filters.confidence ?? 0}</div>
      </div>
      <div className="flex gap-2">
        <button className="btn-mil" onClick={() => setFilters({})}>Reset</button>
        <button className="btn-mil">Apply</button>
      </div>
    </aside>
  );
}