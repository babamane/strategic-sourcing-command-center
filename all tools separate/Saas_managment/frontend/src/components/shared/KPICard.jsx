const color = {
  amber: "border-amber",
  danger: "border-danger",
  success: "border-success",
  info: "border-info",
};

export function KPICard({ title, value, sub, trend, accentColor = "info", onClick }) {
  return (
    <button onClick={onClick} className={`w-full rounded-md border border-border bg-surface p-4 text-left ${color[accentColor]} border-l-[3px]`}>
      <div className="font-mono text-[11px] uppercase tracking-widest text-text-secondary">{title}</div>
      <div className="mt-2 font-mono text-2xl text-text-primary">{value}</div>
      <div className="mt-1 text-sm text-text-secondary">{sub}</div>
      {trend != null && <div className={trend > 0 ? "mt-2 text-xs text-danger" : "mt-2 text-xs text-success"}>{trend > 0 ? "+" : ""}{trend}%</div>}
    </button>
  );
}
