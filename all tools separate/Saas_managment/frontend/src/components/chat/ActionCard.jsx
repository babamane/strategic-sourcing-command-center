import { useState } from "react";
import { postTrigger } from "../../api/triggerClient.js";
import { useAppStore } from "../../store/useAppStore.js";

export function ActionCard({ action }) {
  if (!action) return null;
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleConfirm = async () => {
    setLoading(true);
    setError(null);
    try {
      const preview = await postTrigger(action.type, {
        vendor: action.vendor,
        department: action.department ?? null,
        confirmed: false,
      });
      useAppStore.getState().setPendingConfirm({
        type: action.type,
        vendor: preview.vendor,
        department: preview.department,
        count: preview.count,
        impact: preview.dollar_impact,
        message: preview.message,
      });
    } catch (err) {
      setError("Preview failed: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mt-3 rounded-md border border-amber bg-amber/10 p-3">
      <div className="font-mono text-xs uppercase text-amber">{action.type}</div>
      <div className="mt-1 text-sm text-text-primary">
        {action.vendor}{action.department ? ` / ${action.department}` : ""}
      </div>
      <div className="mt-1 text-xs text-text-secondary">{action.message}</div>
      {error && <div className="mt-1 text-xs text-red-500">{error}</div>}
      <button
        className="mt-3 rounded-md bg-amber px-3 py-2 text-sm text-black disabled:opacity-50"
        onClick={handleConfirm}
        disabled={loading}
      >
        {loading ? "Loading preview…" : "Confirm & Dispatch"}
      </button>
    </div>
  );
}