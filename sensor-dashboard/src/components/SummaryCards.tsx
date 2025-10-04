// src/components/SummaryCards.tsx
export default function SummaryCards({ analytics }: any) {
  const metrics = [
    { id: "total", label: "Total Observations", value: analytics?.total ?? "—" },
    { id: "avg", label: "Avg. Confidence", value: analytics?.avg_confidence ?? "—" },
    { id: "common", label: "Most Common Type", value: analytics?.most_common_what ?? "—" },
    { id: "sensors", label: "Active Sensors", value: analytics?.active_sensors ?? "—" },
  ];
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
      {metrics.map((m) => (
        <div key={m.id} className="mil-panel scanline">
          <div className="mil-muted text-xs">{m.label}</div>
          <div className="text-2xl font-bold" style={{ color: "var(--mil-sand)" }}>{m.value}</div>
        </div>
      ))}
    </div>
  );
}