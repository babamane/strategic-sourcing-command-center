import { useEffect, useMemo } from "react";
import { Bot } from "lucide-react";
import { useActiveDemandSeries } from "../../hooks/useForecast.js";
import { useHealth } from "../../hooks/useHealth.js";
import { useGhostDetail, useGhostSummary } from "../../hooks/useGhost.js";
import { useUtilization } from "../../hooks/useUtilization.js";
import { useAppStore } from "../../store/useAppStore.js";
import { deriveDepts, deriveSeatTypes, deriveSkus, deriveYears, mergeFilterRows } from "../../utils/deriveFilters.js";

export function TopBar() {
  const health = useHealth();
  const vendor = useAppStore(s => s.vendor);
  const department = useAppStore(s => s.department);
  const selectedYear = useAppStore(s => s.selectedYear);
  const selectedSku = useAppStore(s => s.selectedSku);
  const selectedSeatType = useAppStore(s => s.selectedSeatType);
  const chatOpen = useAppStore(s => s.chatOpen);
  const activeView = useAppStore(s => s.activeView);
  const setVendor = useAppStore(s => s.setVendor);
  const setDepartment = useAppStore(s => s.setDepartment);
  const setYear = useAppStore(s => s.setYear);
  const setSku = useAppStore(s => s.setSku);
  const setSeatType = useAppStore(s => s.setSeatType);
  const toggleChat = useAppStore(s => s.toggleChat);
  const vendors = useMemo(() => ["All", ...(health.data?.active_vendors ?? [])], [health.data?.active_vendors]);
  const summary = useGhostSummary(vendor, "All");
  const detail = useGhostDetail(vendor, "All");
  const utilization = useUtilization(vendor);
  const activeDemandSeries = useActiveDemandSeries(vendor);
  const departments = useMemo(() => deriveDepts(summary.data, vendor), [summary.data, vendor]);
  const availableYears = useMemo(() => deriveYears(detail.data), [detail.data]);
  const filterSource = useMemo(
    () => mergeFilterRows(utilization.data, detail.data, activeDemandSeries.data),
    [utilization.data, detail.data, activeDemandSeries.data],
  );
  const skuOptions = useMemo(() => deriveSkus(filterSource), [filterSource]);
  const seatOptions = useMemo(() => deriveSeatTypes(filterSource), [filterSource]);

  useEffect(() => {
    setDepartment("All");
    setSku("All");
    setSeatType("All");
  }, [vendor, setDepartment, setSku, setSeatType]);

  useEffect(() => {
    if (health.isSuccess && vendor !== "All" && !vendors.includes(vendor)) {
      setVendor("All");
    }
  }, [health.isSuccess, vendor, vendors, setVendor]);

  return (
    <header className="flex items-center justify-between border-b border-border bg-bg/95 px-6 py-4">
      <div className="flex flex-wrap items-center gap-4">
        <h1 className="font-display text-2xl capitalize">{activeView.replaceAll("_", " ")}</h1>
        <div className="h-6 w-px bg-border" />
        <select className="rounded-md border border-border bg-surface px-3 py-2 text-sm" value={vendor} onChange={e => setVendor(e.target.value)}>
          {vendors.map(v => <option key={v}>{v}</option>)}
        </select>
        <select className="rounded-md border border-border bg-surface px-3 py-2 text-sm" value={department} onChange={e => setDepartment(e.target.value)}>
          {departments.map(d => <option key={d}>{d}</option>)}
        </select>
        {skuOptions.length > 1 && (
          <select className="rounded-md border border-border bg-surface px-3 py-2 text-sm" value={selectedSku} onChange={e => setSku(e.target.value)}>
            {skuOptions.map(s => (
              <option key={s} value={s}>{s === "All" ? "All SKUs" : s}</option>
            ))}
          </select>
        )}
        {seatOptions.length > 1 && (
          <select className="rounded-md border border-border bg-surface px-3 py-2 text-sm" value={selectedSeatType} onChange={e => setSeatType(e.target.value)}>
            {seatOptions.map(s => (
              <option key={s} value={s}>{s === "All" ? "All Seat Types" : s}</option>
            ))}
          </select>
        )}
        {availableYears.length > 2 && (
          <select className="rounded-md border border-border bg-surface px-3 py-2 text-sm" value={selectedYear} onChange={e => setYear(e.target.value)}>
            {availableYears.map(y => (
              <option key={y} value={y}>{y === "All" ? "All Years" : y}</option>
            ))}
          </select>
        )}
      </div>
      <button className={`flex items-center gap-2 rounded-md px-3 py-2 text-sm ${chatOpen ? "bg-amber text-black" : "border border-border text-text-primary"}`} onClick={toggleChat}>
        <Bot className="h-4 w-4" />
        AI Assistant
      </button>
    </header>
  );
}
