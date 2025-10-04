type Observation = any;

export default function DataTable({ data = [], onRefresh }: { data?: Observation[]; onRefresh?: () => void }) {
  if (!Array.isArray(data)) data = [];
  const fmt = (t: string) => {
    try { return new Date(t).toLocaleString(); } catch { return t; }
  };
  return (
    <div className="mil-panel">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-lg font-bold">Observations</h2>
        <div className="flex items-center gap-3">
          <span className="status-dot status-ok blink" title="Live feed" />
          <button className="btn-mil" onClick={onRefresh}>Refresh</button>
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
              <th className="p-3">Sensor</th>
            </tr>
          </thead>
          <tbody>
            {data.slice(0, 50).map((r: any) => {
              const key = r.id ?? `${r.time}|${r.sensor_id||''}|${r.what}`;
              return (
                <tr key={key} className="transition-colors hover:bg-black/10">
                  <td className="p-3">{r.id ?? ''}</td>
                  <td className="p-3 whitespace-nowrap">{fmt(r.time)}</td>
                  <td className="p-3">{r.mgrs}</td>
                  <td className="p-3 max-w-[260px] truncate" title={r.what}>{r.what}</td>
                  <td className="p-3">{typeof r.confidence === 'number' ? `${r.confidence}%` : ''}</td>
                  <td className="p-3">{r.sensor_id || ''}</td>
                </tr>
              );
            })}
            {data.length === 0 && (
              <tr>
                <td className="p-4 mil-muted" colSpan={6}>No observations</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}