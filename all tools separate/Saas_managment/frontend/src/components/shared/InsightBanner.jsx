import { AlertTriangle, Info, Zap } from "lucide-react";
import { useAppStore } from "../../store/useAppStore.js";

const levelClass = {
  critical: "border-danger bg-danger/10 text-danger",
  warning: "border-amber bg-amber/10 text-amber",
  info: "border-info bg-info/10 text-info",
};
const icons = { critical: Zap, warning: AlertTriangle, info: Info };

function ActionButton({ action }) {
  if (!action) return null;
  return (
    <button
      className="rounded-md border border-border-accent px-3 py-2 text-sm text-text-primary hover:bg-surface-hover"
      onClick={() => action.triggerType && useAppStore.getState().setPendingConfirm({
        type: action.triggerType,
        vendor: action.data.vendor,
        department: action.data.department ?? null,
      })}
    >
      {action.label}
    </button>
  );
}

export function InsightBanner({ level = "info", title, body, primaryAction, secondaryAction }) {
  const Icon = icons[level] ?? Info;
  return (
    <div className={`flex items-center justify-between rounded-md border-l-2 p-4 ${levelClass[level]}`}>
      <div className="flex gap-3">
        <Icon className="mt-1 h-5 w-5" />
        <div>
          <div className="font-display text-lg text-text-primary">{title}</div>
          <div className="text-sm text-text-secondary">{body}</div>
        </div>
      </div>
      <div className="flex gap-2">
        <ActionButton action={primaryAction} />
        <ActionButton action={secondaryAction} />
      </div>
    </div>
  );
}
