export function deriveSkus(rows) {
  const skus = [...new Set((rows ?? []).map(row => row.sku).filter(Boolean))].sort();
  return ["All", ...skus];
}

export function deriveSeatTypes(rows) {
  const types = [...new Set((rows ?? []).map(row => row.seat_type).filter(Boolean))].sort();
  return ["All", ...types];
}

export function deriveDepts(summaryRows, vendor) {
  if (!vendor || vendor === "All") {
    const depts = new Set();
    for (const row of summaryRows ?? []) {
      for (const item of row.by_department ?? []) {
        if (item.department) depts.add(item.department);
      }
    }
    return ["All", ...[...depts].sort()];
  }
  const match = (summaryRows ?? []).find(row => row.vendor === vendor);
  const depts = (match?.by_department ?? []).map(item => item.department).filter(Boolean);
  return ["All", ...[...new Set(depts)].sort()];
}

export function deriveYears(rows) {
  const years = new Set();
  for (const row of rows ?? []) {
    if (!row.exit_date) continue;
    const y = new Date(row.exit_date).getUTCFullYear();
    if (!Number.isNaN(y)) years.add(String(y));
  }
  return ["All", ...[...years].sort()];
}

/** Client-side SKU + seat-type filter (never sends "All" to the API). */
export function filterBySkuSeat(rows, sku = "All", seatType = "All") {
  let next = rows ?? [];
  if (sku !== "All") next = next.filter(row => row.sku === sku);
  if (seatType !== "All") next = next.filter(row => row.seat_type === seatType);
  return next;
}

/** Distinct rows for deriving TopBar SKU/seat options. */
export function mergeFilterRows(...sources) {
  const seen = new Set();
  const out = [];
  for (const rows of sources) {
    for (const row of rows ?? []) {
      if (!row?.sku && !row?.seat_type) continue;
      const key = `${row.vendor}|${row.sku}|${row.seat_type}`;
      if (seen.has(key)) continue;
      seen.add(key);
      out.push(row);
    }
  }
  return out;
}

/** Chart / table label: vendor — sku · seat_type (or sku · seat when vendor is fixed). */
export function seriesLabel(row, vendorFilter = "All") {
  const vendor = row.vendor ?? "";
  const sku = row.sku ?? "";
  const seat = row.seat_type ?? "";
  if (vendorFilter && vendorFilter !== "All") {
    return seat ? `${sku} · ${seat}` : sku || vendor;
  }
  if (sku && seat) return `${vendor} — ${sku} · ${seat}`;
  if (sku) return `${vendor} — ${sku}`;
  return vendor;
}
