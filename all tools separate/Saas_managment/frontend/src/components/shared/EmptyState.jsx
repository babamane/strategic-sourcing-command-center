export function EmptyState({ title = "No data", body = "Nothing matched the current filters." }) {
  return (
    <div className="rounded-md border border-border bg-surface p-8 text-center">
      <div className="font-display text-xl text-text-primary">{title}</div>
      <div className="mt-2 text-sm text-text-secondary">{body}</div>
    </div>
  );
}
