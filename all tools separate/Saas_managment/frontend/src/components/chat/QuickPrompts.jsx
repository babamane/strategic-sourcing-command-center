const prompts = {
  overview: ["Portfolio waste summary", "Which contracts expired?", "Top savings opportunity","Brief planning agent"],
  ghost: ["Ghost breakdown by department", "Raise Jira for Engineering ghosts", "How much can we reclaim?"],
  reclamation: ["Show top candidates", "Export CSV for Nexaflow", "Send churn email for Atlassify"],
  trueup: [
    "Show true-up exposure by SKU",
    "Which SKUs are over contracted capacity?",
    "Total shelfware cost across vendors",
  ],
  utilization: ["Which vendor has worst utilization?", "Seats we can cut right now"],
  renewal: ["Which contracts need renewal?", "Nexaflow renewal risk", "Cloudora options"],
  forecast: ["When will Atlassify hit capacity?", "Forecast for next 6 months"],
  recommendations: ["What's still pending?", "Show dispatched tickets", "Total impact if all actioned"],
};

export function QuickPrompts({ view, onPick }) {
  return (
    <div className="flex flex-wrap gap-2">
      {(prompts[view] ?? prompts.overview).map(prompt => (
        <button key={prompt} className="rounded-full border border-border px-3 py-1 text-xs text-text-secondary hover:text-text-primary" onClick={() => onPick(prompt)}>
          {prompt}
        </button>
      ))}
    </div>
  );
}
