import { useMemo } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { buildInsight } from "../engine/insightEngine.js";
import { useGhostDetail, useGhostSummary } from "../hooks/useGhost.js";
import { useRenewal } from "../hooks/useRenewal.js";
import { useTrueUp } from "../hooks/useTrueUp.js";
import { useUtilization } from "../hooks/useUtilization.js";
import { useAppStore } from "../store/useAppStore.js";
import { DataTable } from "../components/shared/DataTable.jsx";
import { InsightBanner } from "../components/shared/InsightBanner.jsx";
import { KPICard } from "../components/shared/KPICard.jsx";
import { StatusBadge } from "../components/shared/StatusBadge.jsx";
import { filterBySkuSeat, seriesLabel } from "../utils/deriveFilters.js";

const money = n => `$${Number(n ?? 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
const pct = n => `${Math.round(Number(n ?? 0) * 100)}%`;

export function OverviewView() {
  const vendor = useAppStore(s => s.vendor);
  const selectedSku = useAppStore(s => s.selectedSku);
  const selectedSeatType = useAppStore(s => s.selectedSeatType);
  const ghost = useGhostSummary(vendor);
  const ghostDetail = useGhostDetail(vendor, null);
  const trueup = useTrueUp(vendor);
  const utilization = useUtilization(vendor);
  const renewal = useRenewal(vendor);

  const filteredUtil = useMemo(
    () => filterBySkuSeat(utilization.data, selectedSku, selectedSeatType),
    [utilization.data, selectedSku, selectedSeatType],
  );
  const filteredRenewal = useMemo(
    () => filterBySkuSeat(renewal.data, selectedSku, selectedSeatType),
    [renewal.data, selectedSku, selectedSeatType],
  );
  const filteredGhostDetail = useMemo(
    () => filterBySkuSeat(ghostDetail.data, selectedSku, selectedSeatType),
    [ghostDetail.data, selectedSku, selectedSeatType],
  );

  const ghostTotal = filteredGhostDetail.length || (ghost.data ?? []).reduce((sum, row) => sum + row.ghost_license_count, 0);
  const ghostWaste = filteredGhostDetail.reduce((sum, row) => sum + (row.annual_cost ?? 0), 0)
    || (ghost.data ?? []).reduce((sum, row) => sum + row.total_cost_at_risk_annual, 0);
  const filteredTrueup = filterBySkuSeat(trueup.data, selectedSku, selectedSeatType);
  const exposure = filteredTrueup.reduce((sum, row) => sum + row.exposure_amount_annual, 0);
  const avgRate = filteredUtil.reduce((sum, row) => sum + (row.active_rate ?? row.active_usage_rate ?? 0), 0)
    / Math.max(filteredUtil.length, 1);
  const expired = filteredRenewal.filter(row => row.renewal_urgency === "expired");

  const deptRows = Object.values(filteredGhostDetail.reduce((acc, row) => {
    acc[row.department] ??= { department: row.department, count: 0 };
    acc[row.department].count += 1;
    return acc;
  }, {}));

  const utilRows = useMemo(() => {
    const rows = filteredUtil.map(row => {
      const rate = row.active_rate ?? row.active_usage_rate ?? 0;
      const usedPct = Math.round(rate * 100);
      return {
        ...row,
        chartLabel: seriesLabel(row, vendor),
        usedPct,
        idlePct: 100 - usedPct,
      };
    });

    // All vendors → one bar per vendor
    if (!vendor || vendor === "All") {
      const byVendor = {};
      rows.forEach(r => {
        byVendor[r.vendor] ??= { vendor: r.vendor, usedPct: 0, count: 0 };
        byVendor[r.vendor].usedPct += r.usedPct;
        byVendor[r.vendor].count += 1;
      });
      return Object.values(byVendor).map(v => ({
        ...v,
        chartLabel: v.vendor,
        usedPct: Math.round(v.usedPct / v.count),
        idlePct: 100 - Math.round(v.usedPct / v.count),
      }));
    }

    // Single vendor, no SKU filter → one bar per SKU (collapsed across seat types)
    if (!selectedSku || selectedSku === "All") {
      const bySku = {};
      rows.forEach(r => {
        bySku[r.sku] ??= { sku: r.sku, usedPct: 0, count: 0 };
        bySku[r.sku].usedPct += r.usedPct;
        bySku[r.sku].count += 1;
      });
      return Object.values(bySku).map(s => ({
        ...s,
        chartLabel: s.sku,
        usedPct: Math.round(s.usedPct / s.count),
        idlePct: 100 - Math.round(s.usedPct / s.count),
      }));
    }

    // Single vendor + specific SKU selected → one bar per seat type
    return rows.map(r => ({ ...r, chartLabel: r.seat_type }));
  }, [filteredUtil, vendor, selectedSku]);

  // With this:
  const ghostKeyed = useMemo(() => {
    const rows = ghost.data ?? [];
    const result = {};
    rows.forEach(row => {
      result[row.vendor] = {
        total: row.ghost_license_count,
        annual_waste: row.total_cost_at_risk_annual,
      };
    });
    result.All = {
      total: rows.reduce((s, r) => s + r.ghost_license_count, 0),
      annual_waste: rows.reduce((s, r) => s + r.total_cost_at_risk_annual, 0),
    };
    return result;
  }, [ghost.data]);

  const trueupKeyed = useMemo(() => {
    const rows = trueup.data ?? [];
    const result = {};
    rows.forEach(row => {
      result[row.vendor] ??= { exposure: 0 };
      result[row.vendor].exposure += row.exposure_amount_annual ?? 0;
    });
    result.All = { exposure: rows.reduce((s, r) => s + (r.exposure_amount_annual ?? 0), 0) };
    return result;
  }, [trueup.data]);

  const utilizationKeyed = useMemo(() => {
    const rows = utilization.data ?? [];
    const vendors = [...new Set(rows.map(r => r.vendor))];
    const result = {};
    vendors.forEach(v => {
      const vRows = rows.filter(r => r.vendor === v);
      const avg = vRows.reduce((s, r) => s + (r.active_rate ?? 0), 0) / Math.max(vRows.length, 1);
      result[v] = avg;
    });
    const allAvg = rows.reduce((s, r) => s + (r.active_rate ?? 0), 0) / Math.max(rows.length, 1);
    result.All = allAvg;
    return result;
  }, [utilization.data]);

  const renewalKeyed = useMemo(() => {
    const rows = renewal.data ?? [];
    const result = { All: rows };
    rows.forEach(row => {
      result[row.vendor] ??= [];
      result[row.vendor].push(row);
    });
    return result;
  }, [renewal.data]);

  const insight = buildInsight(vendor, "overview", {
    ghost:       ghostKeyed,
    trueup:      trueupKeyed,
    utilization: utilizationKeyed,
    renewal:     renewalKeyed,
  });

  return (
    <div className="space-y-6">
      <InsightBanner {...insight} />
      <div className="grid grid-cols-4 gap-4">
        <KPICard title="Ghost Licenses" value={ghostTotal.toLocaleString()} sub={money(ghostWaste)} accentColor="danger" />
        <KPICard title="True-Up Exposure" value={money(exposure)} accentColor="amber" />
        <KPICard title="Utilization Rate" value={pct(avgRate)} accentColor={avgRate > 0.7 ? "success" : "amber"} />
        <KPICard title="Expired Contracts" value={expired.length.toLocaleString()} accentColor={expired.length ? "danger" : "success"} />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="rounded-md border border-border bg-surface p-4">
          <div className="mb-3 font-display text-lg">Ghost by Dept</div>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={deptRows}>
              <XAxis dataKey="department" tickFormatter={v => v.slice(0, 4)} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#EF4444" />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="rounded-md border border-border bg-surface p-4">
          <div className="mb-3 font-display text-lg">Seat Utilization</div>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={utilRows}>
              <XAxis dataKey="chartLabel" interval={0} tick={{ fontSize: 10 }} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="usedPct" fill="#10B981" name="Used %" />
              <Bar dataKey="idlePct" fill="#EF4444" opacity={0.5} name="Idle %" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      <DataTable rows={filteredRenewal} columns={[
        { key: "vendor", label: "Vendor" },
        { key: "sku", label: "SKU" },
        { key: "seat_type", label: "Seat Type" },
        { key: "renewal_urgency", label: "Status", render: v => <StatusBadge value={v} /> },
        { key: "contract_expiry", label: "Expiry" },
        { key: "effective_total_seats", label: "Seats" },
        { key: "hires_before_deadline", label: "Projected Active at Deadline" },
      ]} />
    </div>
  );
}
