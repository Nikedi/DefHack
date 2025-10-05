import React from "react";

/* Right-side intel panel: cards, mini map and activity placeholder */
export default function RightPanel({ analytics }: any) {
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