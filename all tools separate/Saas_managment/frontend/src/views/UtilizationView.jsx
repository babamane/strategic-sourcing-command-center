import { useMemo } from "react";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useUtilization } from "../hooks/useUtilization.js";
import { useAppStore } from "../store/useAppStore.js";
import { DataTable } from "../components/shared/DataTable.jsx";
import { KPICard } from "../components/shared/KPICard.jsx";
import { filterBySkuSeat, seriesLabel } from "../utils/deriveFilters.js";

export function UtilizationView() {
  const vendor = useAppStore(s => s.vendor);
  const selectedSku = useAppStore(s => s.selectedSku);
  const selectedSeatType = useAppStore(s => s.selectedSeatType);
  const util = useUtilization(vendor);
  const rows = useMemo(() => {
    const filtered = filterBySkuSeat(util.data, selectedSku, selectedSeatType);
    return filtered.map(row => {
      const usedPct = Math.round((row.active_usage_rate ?? row.active_rate ?? 0) * 100);
      const total = row.total_licenses ?? 0;
      const active = Math.round(total * usedPct / 100);
      return {
        ...row,
        chartLabel: seriesLabel(row, vendor),
        usedPct,
        idlePct: 100 - usedPct,
        active_seats: active,
        idle_seats: total - active,
      };
    });
  }, [util.data, selectedSku, selectedSeatType, vendor]);
  const rate = rows.reduce((sum, row) => sum + row.usedPct, 0) / Math.max(rows.length, 1);
  const active = rows.reduce((sum, row) => sum + row.active_seats, 0);
  const total = rows.reduce((sum, row) => sum + row.total_licenses, 0);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-3 gap-4">
        <KPICard title="Overall Rate" value={`${Math.round(rate)}%`} accentColor="success" />
        <KPICard title="Active Seats" value={active.toLocaleString()} accentColor="info" />
        <KPICard title="Idle Seats" value={(total - active).toLocaleString()} accentColor="danger" />
      </div>
      <div className="rounded-md border border-border bg-surface p-4">
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={rows}>
            <XAxis dataKey="chartLabel" interval={0} tick={{ fontSize: 10 }} />
            <YAxis />
            <Tooltip />
            <Bar dataKey="usedPct" fill="#10B981" name="Used %" />
            <Bar dataKey="idlePct" fill="#EF4444" opacity={0.5} name="Idle %" />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <DataTable rows={rows} loading={util.isLoading} columns={[
        { key: "vendor", label: "Vendor" },
        { key: "sku", label: "SKU" },
        { key: "seat_type", label: "Seat Type" },
        { key: "active_seats", label: "Active" },
        { key: "idle_seats", label: "Idle" },
        { key: "total_licenses", label: "Total" },
        { key: "usedPct", label: "Rate", render: v => `${v}%` },
      ]} />
    </div>
  );
}
