export function fmtMoney(n) {
  return `$${Number(n ?? 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}

export function monthKey(isoDate) {
  if (!isoDate) return null;
  const d = new Date(isoDate);
  if (Number.isNaN(d.getTime())) return null;
  const y = d.getUTCFullYear();
  const m = String(d.getUTCMonth() + 1).padStart(2, "0");
  return `${y}-${m}`;
}

export function monthLabel(key) {
  const [y, m] = key.split("-").map(Number);
  const d = new Date(Date.UTC(y, m - 1, 1));
  return d.toLocaleString("en-US", { month: "short", year: "numeric", timeZone: "UTC" });
}

export function buildAccumulationSeries(rows, selectedYear = "All", sku = "All", seatType = "All") {
  let filtered = (rows ?? []).filter(row => row.exit_date);
  if (selectedYear !== "All") {
    filtered = filtered.filter(row => String(new Date(row.exit_date).getUTCFullYear()) === String(selectedYear));
  }
  if (sku !== "All") filtered = filtered.filter(row => row.sku === sku);
  if (seatType !== "All") filtered = filtered.filter(row => row.seat_type === seatType);

  const counts = {};
  for (const row of filtered) {
    const key = monthKey(row.exit_date);
    if (!key) continue;
    counts[key] = (counts[key] ?? 0) + 1;
  }

  const months = Object.keys(counts).sort();
  let cumulative = 0;
  return months.map(month => {
    cumulative += counts[month];
    return { month, label: monthLabel(month), count: counts[month], cumulative };
  });
}
