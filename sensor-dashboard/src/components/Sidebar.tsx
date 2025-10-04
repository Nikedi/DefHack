// src/components/Sidebar.tsx
import React from "react";

export default function Sidebar({ filters, setFilters }: any) {
  return (
    <aside className="w-64 bg-gray-100 p-4 space-y-4">
      <div>
        <label>Date Range</label>
        <input type="date" onChange={e => setFilters((f: any) => ({ ...f, from: e.target.value }))} />
        <input type="date" onChange={e => setFilters((f: any) => ({ ...f, to: e.target.value }))} />
      </div>
      <div>
        <label>Type</label>
        <select onChange={e => setFilters((f: any) => ({ ...f, what: e.target.value }))}>
          <option value="">All</option>
          <option value="vehicle">Vehicle</option>
          <option value="person">Person</option>
        </select>
      </div>
      <div>
        <label>Sensor ID</label>
        <input type="text" onChange={e => setFilters((f: any) => ({ ...f, sensor_id: e.target.value }))} />
      </div>
      <div>
        <label>Confidence</label>
        <input type="range" min={0} max={100} value={filters.confidence ?? 0}
          onChange={e => setFilters((f: any) => ({ ...f, confidence: Number(e.target.value) }))} />
        <span>{filters.confidence ?? 0}</span>
      </div>
      <button className="btn btn-primary" onClick={() => setFilters({})}>Reset Filters</button>
    </aside>
  );
}