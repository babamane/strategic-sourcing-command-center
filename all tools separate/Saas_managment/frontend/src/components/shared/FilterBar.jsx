export function FilterBar({ filters }) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      {filters.map(filter => (
        <label key={filter.id} className="text-sm text-text-secondary">
          {filter.label}
          <select
            className="ml-2 rounded-md border border-border bg-surface px-3 py-2 text-sm text-text-primary"
            value={filter.value}
            onChange={e => filter.onChange(e.target.value)}
          >
            {filter.options.map(option => (
              <option key={option} value={option}>
                {option === "All" ? `All ${filter.label}s` : option}
              </option>
            ))}
          </select>
        </label>
      ))}
    </div>
  );
}
