// src/components/SummaryCards.tsx

export default function SummaryCards({ analytics, observations = [], listMeta }: any) {
  const hasAnalytics = !!analytics;
  // Use server-reported total if available (so it can exceed current page size / limit)
  const total = (listMeta?.total != null ? listMeta.total : observations.length);
  const avgConfidence = hasAnalytics
    ? analytics.avg_confidence
    : (observations.length
        ? (observations.reduce((s: number, o: any) => s + (typeof o.confidence === 'number' ? o.confidence : 0), 0) / observations.length).toFixed(1)
        : '—');
  const mostCommonType = hasAnalytics ? analytics.most_common_what : (() => {
    const counts: Record<string, number> = {};
    for (const o of observations) {
      if (o?.what) counts[o.what] = (counts[o.what] || 0) + 1;
    }
    const entries = Object.entries(counts).sort((a,b) => b[1]-a[1]);
    return entries[0]?.[0] || '—';
  })();
  const activeSensors = hasAnalytics
    ? analytics.active_sensors
    : new Set(observations.filter((o: any) => o?.sensor_id).map((o: any) => o.sensor_id)).size;

  const metrics = [
    { id: "total", label: "Total Observations", value: (total ?? '—') },
    { id: "avg", label: "Avg. Confidence", value: avgConfidence },
    { id: "common", label: "Most Common Type", value: mostCommonType },
    { id: "sensors", label: "Active Sensors", value: activeSensors || (activeSensors === 0 ? 0 : '—') },
  ];
  return (
    <div className="mb-4 summary-cards-grid">
      {metrics.map(m => (
        <div key={m.id} className="mil-panel scanline summary-card">
          <div className="text-xs mil-muted">{m.label}</div>
            <div className="text-2xl font-bold" style={{ color: "var(--mil-sand)" }}>
              {m.value}
              {m.id === 'total' && listMeta?.returned != null && listMeta?.limit
                ? <span className="ml-1 text-[10px] text-gray-400">({listMeta.returned}/{listMeta.limit} page)</span>
                : null}
            </div>
        </div>
      ))}
    </div>
  );
}