// src/components/Sidebar.tsx
import React from "react";

export default function Sidebar({ filters, setFilters }: any) {
  return (
    <aside className="mil-panel space-y-4">
      <div>
        <label className="mil-muted text-xs block mb-1">Date Range</label>
        <input className="w-full p-2 bg-black/10 border border-black/12" type="date" onChange={e => setFilters((f: any) => ({ ...f, from: e.target.value }))} />
        <input className="w-full p-2 mt-2 bg-black/10 border border-black/12" type="date" onChange={e => setFilters((f: any) => ({ ...f, to: e.target.value }))} />
      </div>
      <div>
        <label className="mil-muted text-xs block mb-1">Type</label>
        <select className="w-full p-2 bg-black/10 border border-black/12" onChange={e => setFilters((f: any) => ({ ...f, what: e.target.value }))}>
          <option value="">All</option>
          <option value="vehicle">Vehicle</option>
          <option value="person">Person</option>
        </select>
      </div>
      <div>
        <label className="mil-muted text-xs block mb-1">Sensor ID</label>
        <input className="w-full p-2 bg-black/10 border border-black/12" type="text" onChange={e => setFilters((f: any) => ({ ...f, sensor_id: e.target.value }))} />
      </div>
      <div>
        <label className="mil-muted text-xs block mb-1">Confidence</label>
        <input className="w-full" type="range" min={0} max={100} value={filters.confidence ?? 0}
          onChange={e => setFilters((f: any) => ({ ...f, confidence: Number(e.target.value) }))} />
        <div className="mil-muted text-xs mt-1">{filters.confidence ?? 0}</div>
      </div>
      <div className="flex gap-2">
        <button className="btn-mil" onClick={() => setFilters({})}>Reset</button>
        <button className="btn-mil">Apply</button>
      </div>
    </aside>
  );
}