import { useMemo, useState } from "react";
import { useReclamation } from "../hooks/useReclamation.js";
import { useAppStore } from "../store/useAppStore.js";
import { DataTable } from "../components/shared/DataTable.jsx";
import { KPICard } from "../components/shared/KPICard.jsx";
import { filterBySkuSeat } from "../utils/deriveFilters.js";

const money = n => `$${Number(n ?? 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;

const ACTIVE_ONLY = new Set(["active", "over_tier"]);

function filterReclamationRows(rows, minScore) {
  const threshold = Number(minScore);
  return (rows ?? []).filter(row => {
    if (!ACTIVE_ONLY.has(row.license_status)) return false;
    return Number(row.reclamation_score) >= threshold - 1e-9;
  });
}

export function ReclamationView() {
  const vendor = useAppStore(s => s.vendor);
  const department = useAppStore(s => s.department);
  const selectedSku = useAppStore(s => s.selectedSku);
  const selectedSeatType = useAppStore(s => s.selectedSeatType);
  const [minScore, setMinScore] = useState(0.45);
  const rec = useReclamation(vendor, department, minScore);
  const rows = useMemo(() => {
    const scored = filterReclamationRows(rec.data, minScore);
    return filterBySkuSeat(scored, selectedSku, selectedSeatType);
  }, [rec.data, minScore, selectedSku, selectedSeatType]);

  const scores = rows.map(row => Number(row.reclamation_score));
  const minShown = scores.length ? Math.min(...scores) : 0;
  const maxShown = scores.length ? Math.max(...scores) : 0;
  const value = rows.reduce((sum, row) => sum + row.annual_cost, 0);
  const avgScore = scores.reduce((sum, s) => sum + s, 0) / Math.max(scores.length, 1);
  const triggerVendor = vendor === "All" ? "Atlassify" : vendor;
  const triggerDept = department === "All" ? null : department;

  const open = type => useAppStore.getState().setPendingConfirm({ type, vendor: triggerVendor, department: triggerDept });

  return (
    <div className="space-y-6">
      <p className="text-sm text-text-secondary">
        Active licenses with low utilization — rightsizing candidates. Ghost licenses belong on the Ghost Licenses tab.
      </p>
      <div className="grid grid-cols-4 gap-4">
        <KPICard title="Candidates" value={rows.length.toLocaleString()} accentColor="amber" />
        <KPICard title="Recoverable Value" value={money(value)} accentColor="success" />
        <KPICard title="Avg Score" value={avgScore.toFixed(2)} accentColor="info" />
        <KPICard
          title="Score range"
          value={scores.length ? `${minShown.toFixed(2)} – ${maxShown.toFixed(2)}` : "—"}
          sub="Active / over-tier only"
          accentColor="info"
        />
      </div>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <label className="text-sm text-text-secondary">
          Min score (show ≥)
          <input
            className="ml-2 w-40 accent-amber"
            type="range"
            min="0.45"
            max="1"
            step="0.05"
            value={minScore}
            onChange={e => setMinScore(Number(e.target.value))}
          />
          <span className="ml-1 font-mono text-text-primary">{minScore.toFixed(2)}</span>
        </label>
        <div className="flex flex-wrap gap-2">
          <button className="rounded-md border border-amber px-3 py-2 text-amber" onClick={() => open("reclamation")}>Export CSV</button>
          <button className="rounded-md bg-amber px-3 py-2 text-black" onClick={() => open("reclamation_review")}>Raise Jira Review</button>
          <button className="rounded-md bg-success px-3 py-2 text-black" onClick={() => open("rightsizing")}>Send Confirmation Emails</button>
          <button className="rounded-md border border-info px-3 py-2 text-info" onClick={() => open("churn_mail")}>Send Churn Notification</button>
        </div>
      </div>
      <DataTable
        loading={rec.isLoading}
        rows={rows}
        emptyMessage={`No active low-utilization candidates with score ≥ ${minScore.toFixed(2)}.`}
        columns={[
          { key: "license_id", label: "License ID" },
          { key: "vendor", label: "Vendor" },
          { key: "sku", label: "SKU" },
          { key: "seat_type", label: "Seat Type" },
          { key: "usage_tier", label: "Usage" },
          { key: "email", label: "Employee" },
          { key: "department", label: "Dept" },
          {
            key: "reclamation_score",
            label: "Score",
            render: v => (
              <span className={v >= 0.9 ? "text-danger" : v >= 0.8 ? "text-amber" : ""}>
                {Number(v).toFixed(2)}
              </span>
            ),
          },
          { key: "annual_cost", label: "Annual Value", render: money },
          { key: "days_since_last_active", label: "Days Idle" },
        ]}
      />
    </div>
  );
}
