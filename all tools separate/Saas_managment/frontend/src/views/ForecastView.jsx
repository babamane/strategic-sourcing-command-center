import { useMemo, useState } from "react";
import { Area, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useActiveDemandSeries, useForecast } from "../hooks/useForecast.js";
import { useAppStore } from "../store/useAppStore.js";
import { DataTable } from "../components/shared/DataTable.jsx";
import { EmptyState } from "../components/shared/EmptyState.jsx";
import { filterBySkuSeat, seriesLabel } from "../utils/deriveFilters.js";
import { monthLabel } from "../utils/fmt.js";

const grainClass = {
  dept_level: "text-success",
  dept_only: "text-amber",
  portfolio: "text-danger",
};

const palette = [
  "#F59E0B",
  "#10B981",
  "#60A5FA",
  "#A78BFA",
  "#F472B6",
  "#34D399",
  "#F87171",
  "#22D3EE",
  "#FBBF24",
  "#818CF8",
];

function seriesKey(row) {
  return `${row.vendor}|${row.sku}|${row.seat_type}`;
}

function addMonths(month, count) {
  const [year, value] = month.split("-").map(Number);
  const next = new Date(Date.UTC(year, value - 1 + count, 1));
  const nextYear = next.getUTCFullYear();
  const nextMonth = String(next.getUTCMonth() + 1).padStart(2, "0");
  return `${nextYear}-${nextMonth}`;
}

function collapseRows(rows, vendor, selectedSku) {
  if (!rows?.length) return rows;

  // All vendors → collapse to one series per vendor
  if (!vendor || vendor === "All") {
    const byVendorMonth = {};
    rows.forEach(r => {
      const key = `${r.vendor}|${r.month}`;
      byVendorMonth[key] ??= {
        ...r,
        sku: r.vendor,
        seat_type: "all",
        vendor: r.vendor,
        productive_active: 0,
        projected_active: 0,
        contracted_capacity: 0,
        projected_over_capacity: 0,
        _count: 0,
      };
      byVendorMonth[key].productive_active += r.productive_active ?? 0;
      byVendorMonth[key].projected_active += r.projected_active ?? 0;
      byVendorMonth[key].contracted_capacity += r.contracted_capacity ?? 0;
      byVendorMonth[key].projected_over_capacity += r.projected_over_capacity ?? 0;
      byVendorMonth[key]._count += 1;
    });
    return Object.values(byVendorMonth);
  }

  // Single vendor, no SKU filter → collapse to one series per SKU
  if (!selectedSku || selectedSku === "All") {
    const bySkuMonth = {};
    rows.forEach(r => {
      const key = `${r.sku}|${r.month}`;
      bySkuMonth[key] ??= {
        ...r,
        seat_type: "all",
        productive_active: 0,
        projected_active: 0,
        contracted_capacity: 0,
        projected_over_capacity: 0,
      };
      bySkuMonth[key].productive_active += r.productive_active ?? 0;
      bySkuMonth[key].projected_active += r.projected_active ?? 0;
      bySkuMonth[key].contracted_capacity += r.contracted_capacity ?? 0;
      bySkuMonth[key].projected_over_capacity += r.projected_over_capacity ?? 0;
    });
    return Object.values(bySkuMonth);
  }

  // Single vendor + specific SKU → show per seat type (original behavior)
  return rows;
}

function buildChartModel(rows, vendor, forecastMonths) {
  if (!rows?.length) {
    return { chartRows: [], seriesMeta: [] };
  }

  const historicalMonths = rows.filter(row => !row.is_forecast).map(row => row.month);
  const lastHistoricalMonth = historicalMonths.length ? historicalMonths[historicalMonths.length - 1] : null;
  const forecastCutoff = lastHistoricalMonth ? addMonths(lastHistoricalMonth, forecastMonths) : null;
  const visibleRows = rows.filter(row => !row.is_forecast || !forecastCutoff || row.month <= forecastCutoff);

  const groups = new Map();
  for (const row of visibleRows) {
    const key = seriesKey(row);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(row);
  }

  const monthMap = new Map();
  for (const row of visibleRows) {
    if (!monthMap.has(row.month)) {
      monthMap.set(row.month, { month: row.month, label: monthLabel(row.month) });
    }
  }

  const seriesMeta = [];
  Array.from(groups.entries())
    .sort(([left], [right]) => left.localeCompare(right))
    .forEach(([key, seriesRows], index) => {
      seriesRows.sort((left, right) => left.month.localeCompare(right.month));
      const sample = seriesRows[0];
      const label = seriesLabel(sample, vendor);
      const color = palette[index % palette.length];
      const actualKey = `${key}__actual`;
      const forecastKey = `${key}__forecast`;
      const capacityKey = `${key}__capacity`;
      const overKey = `${key}__over_capacity`;
      const lastHistorical = [...seriesRows].reverse().find(row => !row.is_forecast);
      let hasOverCapacity = false;

      for (const row of seriesRows) {
        const point = monthMap.get(row.month);
        point[capacityKey] = row.contracted_capacity;

        if (row.projected_over_capacity > 0) {
          point[overKey] = row.projected_over_capacity;
          hasOverCapacity = true;
        }

        if (row.is_forecast) {
          point[forecastKey] = row.projected_active;
        } else {
          point[actualKey] = row.productive_active;
          if (row.month === lastHistorical?.month) {
            point[forecastKey] = row.projected_active;
          }
        }
      }

      seriesMeta.push({
        key,
        label,
        color,
        actualKey,
        forecastKey,
        capacityKey,
        overKey,
        hasOverCapacity,
      });
    });

  const chartRows = Array.from(monthMap.values()).sort((left, right) => left.month.localeCompare(right.month));
  return { chartRows, seriesMeta };
}

export function ForecastView() {
  const vendor = useAppStore(s => s.vendor);
  const department = useAppStore(s => s.department);
  const selectedSku = useAppStore(s => s.selectedSku);
  const selectedSeatType = useAppStore(s => s.selectedSeatType);
  const [months, setMonths] = useState(12);
  const [expandedRows, setExpandedRows] = useState(() => new Set());
  const forecast = useForecast(vendor, department, months);
  const activeDemandSeries = useActiveDemandSeries(vendor);

  const demandRows = useMemo(
    () => filterBySkuSeat(forecast.data, selectedSku, selectedSeatType),
    [forecast.data, selectedSku, selectedSeatType],
  );

  const activeDemandRows = useMemo(
    () => filterBySkuSeat(activeDemandSeries.data, selectedSku, selectedSeatType),
    [activeDemandSeries.data, selectedSku, selectedSeatType],
  );

  const { chartRows, seriesMeta } = useMemo(() => {
    const collapsed = collapseRows(activeDemandRows, vendor, selectedSku);
    return buildChartModel(collapsed, vendor, months);
  }, [activeDemandRows, vendor, selectedSku, months]);

  const toggleExpanded = key => {
    setExpandedRows(prev => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  return (
    <div className="space-y-6">
      <label className="text-sm text-text-secondary">
        Months
        <input
          className="ml-2 accent-amber"
          type="range"
          min="3"
          max="24"
          value={months}
          onChange={event => setMonths(Number(event.target.value))}
        />
        {" "}
        {months}
      </label>
      {activeDemandSeries.isLoading ? (
        <EmptyState title="Loading forecast" body="" />
      ) : chartRows.length === 0 ? (
        <EmptyState title="Forecast unavailable" body="No active demand series rows available." />
      ) : (
        <div className="rounded-md border border-border bg-surface p-4">
          <ResponsiveContainer width="100%" height={380}>
            <ComposedChart data={chartRows}>
              <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.15} />
              <XAxis dataKey="label" minTickGap={28} />
              <YAxis />
              <Tooltip
                labelFormatter={(_, payload) => payload?.[0]?.payload?.label ?? _}
                formatter={(value, name) => [Number(value ?? 0).toFixed(1), name]}
              />
              {seriesMeta.map(meta => (
                meta.hasOverCapacity ? (
                  <Area
                    key={meta.overKey}
                    type="monotone"
                    dataKey={meta.overKey}
                    name={`${meta.label} over capacity`}
                    stroke="none"
                    fill="#F59E0B"
                    fillOpacity={0.12}
                    connectNulls
                  />
                ) : null
              ))}
              {seriesMeta.map(meta => (
                <Line
                  key={meta.capacityKey}
                  type="stepAfter"
                  dataKey={meta.capacityKey}
                  name={`${meta.label} contracted capacity`}
                  stroke="#94A3B8"
                  strokeOpacity={0.75}
                  strokeWidth={1.5}
                  dot={false}
                  connectNulls
                />
              ))}
              {seriesMeta.map(meta => (
                <Line
                  key={meta.actualKey}
                  type="monotone"
                  dataKey={meta.actualKey}
                  name={`${meta.label} (actual)`}
                  stroke={meta.color}
                  strokeWidth={2}
                  dot={false}
                  connectNulls
                />
              ))}
              {seriesMeta.map(meta => (
                <Line
                  key={meta.forecastKey}
                  type="monotone"
                  dataKey={meta.forecastKey}
                  name={`${meta.label} (forecast)`}
                  stroke={meta.color}
                  strokeWidth={2}
                  strokeDasharray="5 3"
                  dot={false}
                  connectNulls
                />
              ))}
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}
      <DataTable
        rows={demandRows}
        loading={forecast.isLoading}
        columns={[
          {
            key: "by_department",
            label: "",
            width: "40px",
            sortable: false,
            render: (depts, row) => {
              if (!depts?.length) return null;
              const key = `${row.vendor}-${row.forecast_month}-${row.sku}-${row.seat_type}`;
              return (
                <button type="button" className="text-text-secondary" onClick={() => toggleExpanded(key)}>
                  {expandedRows.has(key) ? "-" : "+"}
                </button>
              );
            },
          },
          { key: "forecast_month", label: "Month", render: value => monthLabel(value) },
          { key: "vendor", label: "Vendor" },
          { key: "sku", label: "SKU" },
          { key: "seat_type", label: "Seat Type" },
          { key: "expected_new_licenses", label: "Expected Licenses", render: value => Number(value ?? 0).toFixed(1) },
          { key: "baseline_active", label: "Baseline Active" },
          { key: "projected_active", label: "Projected Active", render: value => Number(value ?? 0).toFixed(1) },
          { key: "contracted_capacity", label: "Contracted" },
          {
            key: "projected_over_capacity",
            label: "Over Capacity",
            render: value => {
              const numeric = Number(value ?? 0);
              return numeric > 0 ? <span className="text-amber">{numeric.toFixed(1)}</span> : "-";
            },
          },
          {
            key: "pipeline_data_available",
            label: "Pipeline Data",
            render: value => <span className={value ? "text-success" : "text-text-dim"}>{value ? "Yes" : "No"}</span>,
          },
          {
            key: "rate_grain_applied",
            label: "Rate Grain",
            render: value => <span className={grainClass[value] ?? "text-text-secondary"}>{value}</span>,
          },
        ]}
      />
      {demandRows.map(row => {
        const key = `${row.vendor}-${row.forecast_month}-${row.sku}-${row.seat_type}`;
        if (!expandedRows.has(key) || !(row.by_department?.length)) return null;
        return (
          <div key={key} className="rounded-md border border-border bg-surface p-3">
            <div className="mb-2 font-mono text-xs text-text-secondary">
              {monthLabel(row.forecast_month)} · {row.sku} · {row.seat_type}
            </div>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-text-secondary">
                  <th className="px-2 py-1">Department</th>
                  <th className="px-2 py-1">Expected Licenses</th>
                </tr>
              </thead>
              <tbody>
                {row.by_department.map(item => (
                  <tr key={item.department} className="border-t border-border">
                    <td className="px-2 py-1">{item.department}</td>
                    <td className="px-2 py-1">{Number(item.expected_licenses ?? 0).toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      })}
    </div>
  );
}