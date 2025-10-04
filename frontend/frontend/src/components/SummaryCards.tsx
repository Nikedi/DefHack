// src/components/SummaryCards.tsx

export default function SummaryCards({ analytics }: any) {
  const metrics = [
    { id: "total", label: "Total Observations", value: analytics?.total ?? "—" },
    { id: "avg", label: "Avg. Confidence", value: analytics?.avg_confidence ?? "—" },
    { id: "common", label: "Most Common Type", value: analytics?.most_common_what ?? "—" },
    { id: "sensors", label: "Active Sensors", value: analytics?.active_sensors ?? "—" },
  ];
  return (
    <div className="mb-4 summary-cards-grid">
      {metrics.map(m => (
        <div key={m.id} className="mil-panel scanline summary-card">
          <div className="text-xs mil-muted">{m.label}</div>
          <div className="text-2xl font-bold" style={{ color: "var(--mil-sand)" }}>{m.value}</div>
        </div>
      ))}
    </div>
  );
}