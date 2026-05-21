import { Zap } from "lucide-react";
import { useAppStore } from "../../store/useAppStore.js";

export function TwoActionBanner({ title, body, actions }) {
  return (
    <div className="flex items-center justify-between rounded-md border-l-2 border-danger bg-danger/10 p-4">
      <div className="flex gap-3">
        <Zap className="mt-1 h-5 w-5 text-danger" />
        <div>
          <div className="font-display text-lg text-text-primary">{title}</div>
          <div className="text-sm text-text-secondary">{body}</div>
        </div>
      </div>
      <div className="flex gap-2">
        {actions.map(action => (
          <button
            key={action.label}
            className="rounded-md border border-danger px-3 py-2 text-sm text-danger hover:bg-danger/10"
            onClick={() => useAppStore.getState().setPendingConfirm({
              type: action.triggerType,
              vendor: action.data.vendor,
              department: action.data.department ?? null,
            })}
          >
            {action.label}
          </button>
        ))}
      </div>
    </div>
  );
}
