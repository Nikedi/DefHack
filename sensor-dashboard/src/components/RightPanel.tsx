import React from "react";

/* Right-side intel panel: cards, mini map and activity placeholder */
export default function RightPanel({ analytics }: any) {
  return (
    <aside style={{ width: 360 }} className="ml-4">
      <div className="mil-panel mb-4">
        <div className="flex items-center justify-between">
          <div className="font-bold">Key Findings</div>
          <div className="mil-muted text-xs">Updated 00:00:30</div>
        </div>
        <ul className="mt-3 space-y-2">
          <li className="p-2 bg-black/10 border border-black/10">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-bold">Foot movement detected</div>
                <div className="mil-muted text-xs">GRID 12K • 5 units</div>
              </div>
              <div className="text-sm font-bold" style={{ color: "var(--mil-sand)" }}>91%</div>
            </div>
          </li>
          <li className="p-2 bg-black/10 border border-black/10">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-bold">Sensor latency</div>
                <div className="mil-muted text-xs">Sensor S3 lag &gt; 30s</div>
              </div>
              <div className="text-sm font-bold" style={{ color: "var(--mil-accent)" }}>73%</div>
            </div>
          </li>
        </ul>
      </div>

      <div className="mil-panel mb-4">
        <div className="mil-muted text-sm mb-2">Mini Map</div>
        <div style={{ height: 180 }} className="bg-black/30 border border-black/15" />
      </div>

      <div className="mil-panel mb-4">
        <div className="mil-muted text-sm mb-2">Activity (last hour)</div>
        <div style={{ height: 120 }} className="bg-black/20 border border-black/12 flex items-center justify-center mil-muted">Activity graph</div>
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