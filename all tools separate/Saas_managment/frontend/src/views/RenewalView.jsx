import { useMemo } from "react";
import { useRenewal } from "../hooks/useRenewal.js";
import { useAppStore } from "../store/useAppStore.js";
import { DataTable } from "../components/shared/DataTable.jsx";
import { KPICard } from "../components/shared/KPICard.jsx";
import { StatusBadge } from "../components/shared/StatusBadge.jsx";
import { TwoActionBanner } from "../components/shared/TwoActionBanner.jsx";
import { filterBySkuSeat } from "../utils/deriveFilters.js";

function buildVendorBanners(data) {
  const byVendor = {};
  for (const row of data) {
    const isExpired = row.renewal_urgency === "expired";
    const isCritical = row.pressure_classification === "critical" && row.renewal_urgency !== "expired";
    if (!isExpired && !isCritical) continue;
    if (!byVendor[row.vendor]) {
      byVendor[row.vendor] = {
        vendor: row.vendor,
        isExpired: false,
        totalExposure: 0,
        totalProjectedActive: 0,
        maxPressureScore: 0,
      };
    }
    const entry = byVendor[row.vendor];
    entry.isExpired = entry.isExpired || isExpired;
    entry.totalExposure += row.exposure_seats ?? 0;
    entry.totalProjectedActive += row.hires_before_deadline ?? 0;
    entry.maxPressureScore = Math.max(entry.maxPressureScore, row.pressure_score ?? 0);
  }
  return Object.values(byVendor);
}

export function RenewalView() {
  const vendor = useAppStore(s => s.vendor);
  const selectedSku = useAppStore(s => s.selectedSku);
  const selectedSeatType = useAppStore(s => s.selectedSeatType);
  const rows = useRenewal(vendor);
  const data = rows.data ?? [];
  const filtered = useMemo(
    () => filterBySkuSeat(data, selectedSku, selectedSeatType),
    [data, selectedSku, selectedSeatType],
  );
  const banners = buildVendorBanners(data);
  const expiredCount = filtered.filter(row => row.renewal_urgency === "expired").length;
  const criticalCount = filtered.filter(row => row.pressure_classification === "critical").length;
  const totalExposure = filtered.reduce((sum, row) => sum + (row.exposure_seats ?? 0), 0);
  const totalProjectedActive = filtered.reduce((sum, row) => sum + (row.hires_before_deadline ?? 0), 0);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-4 gap-4">
        <KPICard title="Contracts" value={filtered.length.toLocaleString()} accentColor="info" />
        <KPICard title="Expired" value={expiredCount.toLocaleString()} accentColor="danger" />
        <KPICard title="Critical pressure" value={criticalCount.toLocaleString()} accentColor="amber" />
        <KPICard
          title="Exposure seats"
          value={totalExposure.toLocaleString()}
          sub={`${totalProjectedActive.toFixed(0)} projected active licenses at deadline`}
          accentColor="danger"
        />
      </div>
      {banners.map(item => (
        <TwoActionBanner
          key={item.vendor}
          title={`${item.vendor} - ${item.isExpired ? "contract EXPIRED" : "critical renewal pressure"}`}
          body={`${item.totalExposure} seats over entitlement - ${item.totalProjectedActive.toFixed(0)} projected active licenses at deadline - pressure score ${(item.maxPressureScore * 100).toFixed(0)}%`}
          actions={[
            { label: "Send Slack Alert", triggerType: "renewal_alert", data: { vendor: item.vendor } },
            { label: "Raise Ghost Ticket", triggerType: "ghost_ticket", data: { vendor: item.vendor } },
          ]}
        />
      ))}
      <DataTable
        loading={rows.isLoading}
        rows={filtered}
        columns={[
          { key: "vendor", label: "Vendor" },
          { key: "sku", label: "SKU" },
          { key: "seat_type", label: "Seat Type" },
          { key: "renewal_urgency", label: "Status", render: value => <StatusBadge value={value} /> },
          { key: "contract_expiry", label: "Expiry" },
          { key: "notice_deadline", label: "Notice" },
          { key: "days_until_notice_deadline", label: "Days to Notice" },
          { key: "effective_total_seats", label: "Seats" },
          { key: "exposure_seats", label: "Exposure", render: value => <span className="text-danger">{value}</span> },
          { key: "hires_before_deadline", label: "Projected Active at Deadline" },
          { key: "pressure_score", label: "Pressure", render: value => `${(Number(value) * 100).toFixed(0)}%` },
          { key: "pressure_classification", label: "Class", render: value => <StatusBadge value={value} /> },
          { key: "auto_renewal", label: "Auto Renew", render: value => (value ? "Yes" : "No") },
          { key: "true_down_rights", label: "True Down", render: value => (value ? "Yes" : "No") },
        ]}
      />
    </div>
  );
}
