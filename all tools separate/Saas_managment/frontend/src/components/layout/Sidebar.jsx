import { BarChart2, Database, Ghost, LayoutDashboard, PieChart, RefreshCw, Sparkles, TrendingUp, Zap } from "lucide-react";
import { useHealth } from "../../hooks/useHealth.js";
import { useGhostSummary } from "../../hooks/useGhost.js";
import { useReclamation } from "../../hooks/useReclamation.js";
import { useRenewal } from "../../hooks/useRenewal.js";
import { useAppStore } from "../../store/useAppStore.js";

const items = [
  ["overview", "Overview", LayoutDashboard],
  ["ghost", "Ghost Licenses", Ghost],
  ["reclamation", "Reclamation", RefreshCw],
  ["trueup", "True-Up Exposure", BarChart2],
  ["utilization", "Utilization", PieChart],
  ["renewal", "Renewal Pressure", Zap],
  ["forecast", "Demand Forecast", TrendingUp],
  ["recommendations", "Recommendations", Sparkles],
];

export function Sidebar() {
  const activeView = useAppStore(s => s.activeView);
  const setView = useAppStore(s => s.setView);
  const setEnterDashboard = useAppStore(s => s.setEnterDashboard);
  const vendor = useAppStore(s => s.vendor);
  const health = useHealth();
  const ghost = useGhostSummary(vendor, "All");
  const reclamation = useReclamation(vendor, "All", 0.5);
  const renewal = useRenewal(vendor);
  const ghostTotal = (ghost.data ?? []).reduce((sum, row) => sum + row.ghost_license_count, 0);
  const candidateCount = (reclamation.data ?? []).length;
  const expiredCount = (renewal.data ?? []).filter(row => row.renewal_urgency === "expired").length;

  const badges = {
    ghost: ghostTotal,
    reclamation: candidateCount,
    renewal: expiredCount,
  };

  return (
    <aside className="flex w-[220px] shrink-0 flex-col border-r border-border bg-surface">
      <div className="border-b border-border p-4">
        <div className="font-display text-xl">SaaS Spend</div>
        <div className="font-mono text-xs text-text-secondary">Phase 1E</div>
      </div>
      <nav className="flex-1 p-2">
        {items.map(([id, label, Icon]) => (
          <button
            key={id}
            className={`mb-1 flex w-full items-center gap-3 rounded-sm px-3 py-2 text-left text-sm ${activeView === id ? "border-l-2 border-amber bg-amber/10 text-amber" : "text-text-secondary hover:text-text-primary"}`}
            onClick={() => setView(id)}
          >
            <Icon className="h-4 w-4" />
            <span className="flex-1">{label}</span>
            {badges[id] > 0 && (
              <span className="rounded-full bg-danger/20 px-2 py-0.5 font-mono text-[10px] text-danger">
                {badges[id]}
              </span>
            )}
          </button>
        ))}
      </nav>
      <div className="border-t border-border p-4 text-xs text-text-secondary">
        <div className="flex items-center gap-2">
          <span className={`h-2 w-2 rounded-full ${health.isSuccess ? "bg-success" : "bg-danger"}`} />
          API {health.isSuccess ? "online" : "offline"}
        </div>
        <div className="mt-2">Audit: {health.data?.audit_date ?? "-"}</div>
        <button
          onClick={() => setEnterDashboard(false)}
          className="mt-3 flex w-full items-center gap-2 rounded-lg border border-border bg-surface-hover px-3 py-2 text-left font-medium transition-colors hover:bg-border"
        >
          <Database className="h-3 w-3" />
          <span>Re-run pipeline</span>
        </button>
      </div>
    </aside>
  );
}
