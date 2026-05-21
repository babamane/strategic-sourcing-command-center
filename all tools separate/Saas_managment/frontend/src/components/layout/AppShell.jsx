import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useAppStore } from "../../store/useAppStore.js";
import { useGhostSummary } from "../../hooks/useGhost.js";
import { useRenewal } from "../../hooks/useRenewal.js";
import { useTrueUp } from "../../hooks/useTrueUp.js";
import { useUtilization } from "../../hooks/useUtilization.js";
import { ChatPanel } from "../chat/ChatPanel.jsx";
import { ConfirmModal } from "../shared/ConfirmModal.jsx";
import { Sidebar } from "./Sidebar.jsx";
import { TopBar } from "./TopBar.jsx";

function indexLiveData(rows, kind) {
  const byVendor = { All: {} };
  if (kind === "ghost") {
    byVendor.All = {
      total: rows.reduce((sum, row) => sum + (row.ghost_license_count ?? 0), 0),
      annual_waste: rows.reduce((sum, row) => sum + (row.total_cost_at_risk_annual ?? 0), 0),
    };
    rows.forEach(row => { byVendor[row.vendor] = { total: row.ghost_license_count, annual_waste: row.total_cost_at_risk_annual }; });
  } else if (kind === "trueup") {
    byVendor.All = { exposure: rows.reduce((sum, row) => sum + (row.exposure_amount_annual ?? 0), 0) };
    rows.forEach(row => { byVendor[row.vendor] = { exposure: (byVendor[row.vendor]?.exposure ?? 0) + row.exposure_amount_annual }; });
  } else if (kind === "utilization") {
    byVendor.All = rows.reduce((sum, row) => sum + (row.active_rate ?? row.active_usage_rate ?? 0), 0) / Math.max(rows.length, 1);
    rows.forEach(row => { byVendor[row.vendor] = row.active_rate ?? row.active_usage_rate ?? 0; });
  } else if (kind === "renewal") {
    byVendor.All = rows;
    rows.forEach(row => { byVendor[row.vendor] = [...(byVendor[row.vendor] ?? []), row]; });
  }
  return byVendor;
}

export function AppShell({ children }) {
  const chatOpen = useAppStore(s => s.chatOpen);
  const queryClient = useQueryClient();
  const ghost = useGhostSummary("All", "All");
  const trueup = useTrueUp("All");
  const utilization = useUtilization("All");
  const renewal = useRenewal("All");

  useEffect(() => {
    if (ghost.data) queryClient.setQueryData(["insight", "ghost"], indexLiveData(ghost.data, "ghost"));
    if (trueup.data) queryClient.setQueryData(["insight", "trueup"], indexLiveData(trueup.data, "trueup"));
    if (utilization.data) queryClient.setQueryData(["insight", "utilization"], indexLiveData(utilization.data, "utilization"));
    if (renewal.data) queryClient.setQueryData(["insight", "renewal"], indexLiveData(renewal.data, "renewal"));
  }, [ghost.data, trueup.data, utilization.data, renewal.data]);

  return (
    <div className="flex h-full bg-bg text-text-primary">
      <Sidebar />
      <main className="min-w-0 flex-1 overflow-y-auto transition-[margin-right] duration-300" style={{ marginRight: chatOpen ? 380 : 0 }}>
        <TopBar />
        <div className="p-6">{children}</div>
      </main>
      <ChatPanel />
      <ConfirmModal />
    </div>
  );
}
