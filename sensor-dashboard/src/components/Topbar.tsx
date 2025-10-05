// src/components/Topbar.tsx
export default function Topbar() {
  const now = new Date().toLocaleString();
  return (
    <header className="mil-topbar">
      <div className="flex items-center gap-3">
        <div className="mil-radar" aria-hidden />
        <div>
          <div className="text-lg font-bold">Sensor Command Dashboard</div>
          <div className="text-xs mil-muted">Operational | {now}</div>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <div className="text-sm mil-muted">Demo User</div>
        <button className="btn-mil">Sign Out</button>
      </div>
    </header>
  );
}