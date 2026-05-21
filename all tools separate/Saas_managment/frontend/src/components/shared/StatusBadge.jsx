export function StatusBadge({ value }) {
  const v = String(value ?? "").toLowerCase();
  const cls = v.includes("expired") || v.includes("critical")
    ? "border-danger text-danger"
    : v.includes("pending") || v.includes("warning")
      ? "border-amber text-amber"
      : "border-success text-success";
  return <span className={`rounded border px-2 py-1 font-mono text-xs ${cls}`}>{value}</span>;
}
