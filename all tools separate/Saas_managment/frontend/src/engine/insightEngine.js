const fmtK = n => (n == null ? "?" : `${(Number(n) / 1000).toFixed(0)}K`);
const fmtPct = n => (n == null ? "?" : `${(Number(n) * 100).toFixed(1)}%`);

export function buildInsight(vendor, view, liveData) {
  const ghost = liveData?.ghost;
  const trueup = liveData?.trueup;
  const utilization = liveData?.utilization;
  const renewal = liveData?.renewal;
  if (!ghost || !trueup || !utilization || !renewal) {
    return { level: "info", icon: "info", title: "Loading data...", body: "", primaryAction: null, secondaryAction: null };
  }

  if (vendor === "All") {
    const expired = (renewal.All ?? []).filter(row => (row.renewal_urgency ?? row.status) === "expired");
    if (expired.length > 0) {
      return {
        level: "critical",
        icon: "zap",
        title: `Portfolio: ${expired.length} expired contracts + ${ghost.All?.total ?? 0} ghost licenses`,
        body: `$${fmtK(ghost.All?.annual_waste)}/yr ghost waste. $${fmtK(trueup.All?.exposure)} true-up exposure.`,
        primaryAction: { label: "Raise Ghost Tickets", triggerType: "ghost_ticket", data: { vendor: "Atlassify" } },
        secondaryAction: { label: "Export Reclamation CSV", triggerType: "reclamation", data: { vendor: "Atlassify" } },
      };
    }
    return {
      level: "warning",
      icon: "alert",
      title: `Portfolio: $${fmtK(trueup.All?.exposure)} true-up exposure`,
      body: `Ghost waste: $${fmtK(ghost.All?.annual_waste)}/yr. Utilization: ${fmtPct(utilization.All)}.`,
      primaryAction: null,
      secondaryAction: null,
    };
  }

  if (vendor === "Atlassify") {
    return {
      level: "warning",
      icon: "alert",
      title: "Atlassify - overpaying detected",
      body: `${ghost.Atlassify?.total ?? 0} ghost licenses ($${fmtK(ghost.Atlassify?.annual_waste)}/yr). ${fmtPct(utilization.Atlassify)} utilization + $${fmtK(trueup.Atlassify?.exposure)} true-up exposure.`,
      primaryAction: view === "ghost"
        ? { label: "Raise Jira Ticket", triggerType: "ghost_ticket", data: { vendor: "Atlassify" } }
        : view === "reclamation"
          ? { label: "Export Reclamation CSV", triggerType: "reclamation", data: { vendor: "Atlassify" } }
          : null,
      secondaryAction: null,
    };
  }

  // Data-driven fallback for all other vendors
  const vendorGhost = ghost[vendor] ?? { total: 0, annual_waste: 0 };
  const vendorTrueup = trueup[vendor] ?? { exposure: 0 };
  const vendorUtil = utilization[vendor] ?? 0;
  const vendorRenewal = renewal[vendor] ?? [];
  const vendorExpired = vendorRenewal.filter(r => (r.renewal_urgency ?? r.status) === "expired");

  if (vendorExpired.length > 0) {
    return {
      level: "critical",
      icon: "zap",
      title: `${vendor} — ${vendorExpired.length} expired contract(s)`,
      body: `${vendorGhost.total} ghost licenses accumulating $${fmtK(vendorGhost.annual_waste)}/yr. $${fmtK(vendorTrueup.exposure)} true-up exposure.`,
      primaryAction: { label: "Raise Jira Ticket", triggerType: "ghost_ticket", data: { vendor } },
      secondaryAction: { label: "Export Reclamation CSV", triggerType: "reclamation", data: { vendor } },
    };
  }

  return {
    level: vendorGhost.total > 0 ? "warning" : "info",
    icon: "alert",
    title: `${vendor} — ${fmtPct(vendorUtil)} utilization`,
    body: `${vendorGhost.total} ghost licenses ($${fmtK(vendorGhost.annual_waste)}/yr). $${fmtK(vendorTrueup.exposure)} true-up exposure.`,
    primaryAction: vendorGhost.total > 0
      ? { label: "Raise Jira Ticket", triggerType: "ghost_ticket", data: { vendor } }
      : null,
    secondaryAction: null,
  };
}