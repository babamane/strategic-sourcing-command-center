import { useEffect } from "react";
import { useAppStore } from "../../store/useAppStore.js";
import { useTrigger } from "../../hooks/useTrigger.js";

export function ConfirmModal() {
  const pendingConfirm = useAppStore(s => s.pendingConfirm);
  const clearConfirm = useAppStore(s => s.clearConfirm);
  const { preview, result, loading, error, fetchPreview, dispatch, reset } = useTrigger();

  useEffect(() => {
    reset();
    if (pendingConfirm) {
      fetchPreview(pendingConfirm.type, {
        vendor: pendingConfirm.vendor,
        department: pendingConfirm.department ?? null,
      });
    }
  }, [pendingConfirm]);

  if (!pendingConfirm) return null;

  const payload = {
    vendor: pendingConfirm.vendor,
    department: pendingConfirm.department ?? null,
  };

  return (
    <div className="fixed inset-0 z-[120] flex items-center justify-center bg-black/70">
      <div className="w-[520px] rounded-md border border-border bg-surface p-6 shadow-2xl">
        <div className="font-display text-xl text-text-primary">Confirm action</div>
        <div className="mt-1 text-sm text-text-secondary">{pendingConfirm.type} for {pendingConfirm.vendor}</div>

        <div className="mt-5 rounded-md border border-border bg-bg p-4">
          {loading && <div className="text-text-secondary">Loading...</div>}
          {error && <div className="text-danger">{error}</div>}
          {preview && !result && (
            <div className="space-y-2 text-sm">
              <div>Count: <span className="font-mono">{preview.count ?? preview.candidate_count ?? 0}</span></div>
              <div>Impact: <span className="font-mono">${Number(preview.dollar_impact ?? 0).toLocaleString()}</span></div>
              <div className="text-text-secondary">{preview.message ?? preview.subject}</div>
              {preview.body_preview && <div className="max-h-28 overflow-auto text-xs text-text-secondary">{preview.body_preview}</div>}
            </div>
          )}
          {result && (
            <div className="space-y-2 text-sm">
              <div className="text-success">Dispatched successfully.</div>
              <div>Recommendation: <span className="font-mono">{result.recommendation_id ?? "n/a"}</span></div>
            </div>
          )}
        </div>

        <div className="mt-5 flex justify-end gap-2">
          <button className="rounded-md border border-border px-4 py-2 text-text-secondary" onClick={clearConfirm}>Cancel</button>
          {result ? (
            <button className="rounded-md bg-amber px-4 py-2 text-black" onClick={clearConfirm}>Done</button>
          ) : (
            <button
              className="rounded-md bg-amber px-4 py-2 text-black disabled:opacity-40"
              disabled={loading}
              onClick={() => dispatch(pendingConfirm.type, payload)}
            >
              Dispatch
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
