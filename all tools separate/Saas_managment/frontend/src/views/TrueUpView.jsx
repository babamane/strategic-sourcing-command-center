import { useMemo } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useTrueUp, useTrueUpBreakdown } from "../hooks/useTrueUp.js";
import { useAppStore } from "../store/useAppStore.js";
import { DataTable } from "../components/shared/DataTable.jsx";
import { EmptyState } from "../components/shared/EmptyState.jsx";
import { KPICard } from "../components/shared/KPICard.jsx";
import { filterBySkuSeat, seriesLabel } from "../utils/deriveFilters.js";
import { fmtMoney } from "../utils/fmt.js";

export function TrueUpView() {
  const vendor = useAppStore(s => s.vendor);
  const selectedSku = useAppStore(s => s.selectedSku);
  const selectedSeatType = useAppStore(s => s.selectedSeatType);
  const exposure = useTrueUp(vendor);
  const breakdown = useTrueUpBreakdown(vendor, selectedSku, selectedSeatType);
  const filtered = useMemo(
    () => filterBySkuSeat(exposure.data, selectedSku, selectedSeatType),
    [exposure.data, selectedSku, selectedSeatType],
  );
  const chartRows = useMemo(
    () => filtered.map(row => ({
      ...row,
      chartLabel: seriesLabel(row, vendor),
      exposure_seats: row.exposure_seats ?? 0,
    })),
    [filtered, vendor],
  );
  const totalExposure = filtered.reduce((sum, row) => sum + (row.exposure_amount_annual ?? 0), 0);
  const totalShelfware = filtered.reduce((sum, row) => sum + (row.shelfware_amount_annual ?? 0), 0);
  const totalSeats = filtered.reduce((sum, row) => sum + (row.exposure_seats ?? 0), 0);
  const breakdownRows = (breakdown.data ?? []).flatMap(row => [
    ...(row.by_department ?? []).map(item => ({
      vendor: row.vendor,
      sku: row.sku,
      seat_type: row.seat_type,
      department: item.department,
      provisioned: item.provisioned,
      exposure_seats: row.exposure_seats,
    })),
  ]);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-3 gap-4">
        <KPICard title="Exposure (Annual)" value={fmtMoney(totalExposure)} accentColor="danger" />
        <KPICard title="Shelfware (Annual)" value={fmtMoney(totalShelfware)} accentColor="amber" />
        <KPICard title="Exposure Seats" value={totalSeats.toLocaleString()} accentColor="info" />
      </div>
      <div className="rounded-md border border-border bg-surface p-4">
        <div className="mb-3 font-display text-lg">Exposure by SKU / seat type</div>
        {exposure.isLoading ? (
          <EmptyState title="Loading true-up data" body="" />
        ) : chartRows.length === 0 ? (
          <EmptyState title="No exposure" body="No SKUs over contracted capacity for this filter." />
        ) : (
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={chartRows}>
              <CartesianGrid stroke="#E5E7EB" />
              <XAxis dataKey="chartLabel" interval={0} tick={{ fontSize: 10 }} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="exposure_seats" fill="#EF4444" name="Exposure seats" />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
      <DataTable
        loading={breakdown.isLoading}
        rows={breakdownRows}
        emptyMessage="No breakdown rows for this filter."
        columns={[
          { key: "vendor", label: "Vendor" },
          { key: "sku", label: "SKU" },
          { key: "seat_type", label: "Seat Type" },
          { key: "department", label: "Department" },
          { key: "provisioned", label: "Provisioned" },
          { key: "exposure_seats", label: "Exposure Seats" },
        ]}
      />
    </div>
  );
}
