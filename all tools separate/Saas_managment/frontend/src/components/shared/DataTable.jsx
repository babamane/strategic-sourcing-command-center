import { useMemo, useState } from "react";
import { SkeletonRow } from "./SkeletonRow.jsx";

export function DataTable({ columns, rows, loading = false, emptyMessage = "No rows." }) {
  const [sort, setSort] = useState(null);
  const sortedRows = useMemo(() => {
    if (!sort) return rows ?? [];
    return [...(rows ?? [])].sort((a, b) => {
      const av = a[sort.key];
      const bv = b[sort.key];
      if (av === bv) return 0;
      return (av > bv ? 1 : -1) * (sort.dir === "asc" ? 1 : -1);
    });
  }, [rows, sort]);

  if (loading) return <div className="space-y-2"><SkeletonRow /><SkeletonRow /><SkeletonRow /><SkeletonRow /><SkeletonRow /></div>;
  if (!sortedRows.length) return <div className="rounded-md border border-border bg-surface p-6 text-text-secondary">{emptyMessage}</div>;

  return (
    <div className="overflow-hidden rounded-md border border-border bg-surface">
      <table className="w-full border-collapse text-sm">
        <thead className="bg-surface-hover text-left font-mono text-[11px] uppercase text-text-secondary">
          <tr>
            {columns.map(column => (
              <th key={column.key} style={{ width: column.width }} className="cursor-pointer px-3 py-3" onClick={() => column.sortable !== false && setSort(s => ({ key: column.key, dir: s?.key === column.key && s.dir === "asc" ? "desc" : "asc" }))}>
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sortedRows.map((row, idx) => (
            <tr key={row.id ?? row.license_id ?? `${row.vendor}-${idx}`} className="border-t border-border">
              {columns.map(column => (
                <td key={column.key} className="px-3 py-3 text-text-primary">
                  {column.render ? column.render(row[column.key], row) : String(row[column.key] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
