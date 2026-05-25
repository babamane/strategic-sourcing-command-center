import { useAppStore } from "../store/useAppStore.js";
import { DataTable } from "../components/shared/DataTable.jsx";
import { KPICard } from "../components/shared/KPICard.jsx";
import { StatusBadge } from "../components/shared/StatusBadge.jsx";

const SEED_RECS = [
  { id: "rec-001", type: "ghost_ticket", vendor: "Atlassify", dept: "Engineering", count: 312, impact: 18240, status: "pending", date: "2026-05-14" },
  { id: "rec-002", type: "reclamation", vendor: "Nexaflow", dept: "Marketing", count: 28, impact: 67200, status: "pending", date: "2026-05-14" },
  { id: "rec-003", type: "rightsizing", vendor: "Cloudora", dept: "Operations", count: 15, impact: 54000, status: "dispatched", date: "2026-05-13" },
  { id: "rec-004", type: "Contract Renewal", vendor: "Nexaflow", dept: "-", count: "-", impact: 54000, status: "dispatched", date: "2026-05-13" },
];

export function RecommendationsView() {
  const dispatchedRecs = useAppStore(s => s.dispatchedRecs);
  const live = dispatchedRecs.map((row, index) => ({
    id: row.recommendation_id ?? `session-${index}`,
    type: row.preview === false ? "dispatch" : "preview",
    vendor: row.vendor ?? "",
    dept: row.department ?? "",
    count: row.count ?? row.candidate_count ?? 0,
    impact: row.dollar_impact ?? 0,
    status: row.status ?? (row.sent ? "dispatched" : "pending"),
    date: new Date().toISOString().slice(0, 10),
  }));
  const rows = [...live, ...SEED_RECS];
  const pending = rows.filter(row => row.status === "pending").length;
  const dispatched = rows.filter(row => row.status === "dispatched").length;
  const impact = rows.reduce((sum, row) => sum + row.impact, 0);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-3 gap-4">
        <KPICard title="Pending" value={pending.toLocaleString()} accentColor="amber" />
        <KPICard title="Dispatched" value={dispatched.toLocaleString()} accentColor="success" />
       <KPICard title="Total Impact" value={`$${impact.toLocaleString('en-US')}`} accentColor="info" />
      </div>
      <DataTable rows={rows} columns={[
        { key: "id", label: "ID" },
        { key: "type", label: "Type" },
        { key: "vendor", label: "Vendor" },
        { key: "dept", label: "Dept" },
        { key: "count", label: "Count" },
        { key: "impact", label: "Impact", render: v => `$${Number(v).toLocaleString()}` },
        { key: "status", label: "Status", render: v => <StatusBadge value={v} /> },
        { key: "date", label: "Date" },
      ]} />
    </div>
  );
}
