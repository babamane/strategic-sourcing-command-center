import { useMemo } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useAppStore } from "../store/useAppStore.js";
import { useGhostDetail, useGhostSummary } from "../hooks/useGhost.js";
import { DataTable } from "../components/shared/DataTable.jsx";
import { EmptyState } from "../components/shared/EmptyState.jsx";
import { KPICard } from "../components/shared/KPICard.jsx";
import { filterBySkuSeat } from "../utils/deriveFilters.js";
import { buildAccumulationSeries, fmtMoney } from "../utils/fmt.js";

export function GhostView() {
  const vendor = useAppStore(s => s.vendor);
  const department = useAppStore(s => s.department);
  const selectedYear = useAppStore(s => s.selectedYear);
  const selectedSku = useAppStore(s => s.selectedSku);
  const selectedSeatType = useAppStore(s => s.selectedSeatType);
  const summary = useGhostSummary(vendor, department);
  const detail = useGhostDetail(vendor, department);
  const detailRows = useMemo(
    () => filterBySkuSeat(detail.data, selectedSku, selectedSeatType),
    [detail.data, selectedSku, selectedSeatType],
  );
  const total = detailRows.length || (summary.data ?? []).reduce((sum, row) => sum + row.ghost_license_count, 0);
  const annual = detailRows.reduce((sum, row) => sum + (row.annual_cost ?? 0), 0)
    || (summary.data ?? []).reduce((sum, row) => sum + row.total_cost_at_risk_annual, 0);
  const series = useMemo(
    () => buildAccumulationSeries(detailRows, selectedYear, selectedSku, selectedSeatType),
    [detailRows, selectedYear, selectedSku, selectedSeatType],
  );
  const deptRows = Object.values(detailRows.reduce((acc, row) => {
    acc[row.department] ??= { department: row.department, ghost_count: 0, annual_waste: 0 };
    acc[row.department].ghost_count += 1;
    acc[row.department].annual_waste += row.annual_cost;
    return acc;
  }, {})).map(row => ({ ...row, avg: row.annual_waste / Math.max(row.ghost_count, 1) }));

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-3 gap-4">
        <KPICard title="Total Ghost" value={total.toLocaleString()} accentColor="danger" />
        <KPICard title="Annual Waste" value={fmtMoney(annual)} accentColor="danger" />
        <KPICard title="Monthly Burn" value={fmtMoney(annual / 12)} accentColor="amber" />
      </div>
      <div className="rounded-md border border-border bg-surface p-4">
        <div className="mb-3 font-display text-lg">Ghost accumulation</div>
        {detail.isLoading ? (
          <EmptyState title="Loading ghost detail" body="" />
        ) : series.length === 0 ? (
          <EmptyState title="No dated ghost records" body="No exit dates match the current vendor and filter selection." />
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={series}>
              <CartesianGrid stroke="#E5E7EB" />
              <XAxis dataKey="label" tick={{ fontSize: 11 }} />
              <YAxis />
              <Tooltip />
              <Line dataKey="cumulative" stroke="#EF4444" strokeWidth={2} dot={false} name="Cumulative ghosts" />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
      <div className="flex justify-end">
        <button
          className="rounded-md bg-amber px-4 py-2 text-black"
          onClick={() => useAppStore.getState().setPendingConfirm({
            type: "ghost_ticket",
            vendor: vendor === "All" ? "Atlassify" : vendor,
            department: department === "All" ? null : department,
          })}
        >
          Raise Jira Ticket
        </button>
      </div>
      <DataTable loading={detail.isLoading} rows={deptRows} columns={[
        { key: "department", label: "Department" },
        { key: "ghost_count", label: "Ghost Count" },
        { key: "annual_waste", label: "Annual Waste", render: fmtMoney },
        { key: "avg", label: "Avg per License", render: fmtMoney },
      ]} />
    </div>
  );
}
