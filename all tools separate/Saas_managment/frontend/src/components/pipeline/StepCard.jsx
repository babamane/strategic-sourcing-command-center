import React from "react";
import { CheckCircle2, XCircle, Loader2, MinusCircle, ChevronDown, ChevronRight } from "lucide-react";

export function StepCard({ step, label, status, message, checks }) {
  const [expanded, setExpanded] = React.useState(false);

  const getStatusIcon = () => {
    switch (status) {
      case "passed":
        return <CheckCircle2 className="w-5 h-5 text-emerald-500" />;
      case "failed":
        return <XCircle className="w-5 h-5 text-rose-500" />;
      case "running":
        return <Loader2 className="w-5 h-5 text-indigo-500 animate-spin" />;
      case "skipped":
        return <MinusCircle className="w-5 h-5 text-slate-400" />;
      default:
        return <MinusCircle className="w-5 h-5 text-slate-200" />;
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case "passed":
        return "border-emerald-100 bg-emerald-50/30";
      case "failed":
        return "border-rose-100 bg-rose-50/30";
      case "running":
        return "border-indigo-100 bg-indigo-50/30";
      default:
        return "border-slate-100 bg-white";
    }
  };

  return (
    <div className={`p-4 border rounded-xl transition-all ${getStatusColor()}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {getStatusIcon()}
          <div>
            <h3 className="font-semibold text-slate-900">{label}</h3>
            {message && <p className="text-sm text-slate-500">{message}</p>}
          </div>
        </div>
        {checks && checks.length > 0 && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-1 rounded-lg hover:bg-slate-100 transition-colors"
          >
            {expanded ? (
              <ChevronDown className="w-5 h-5 text-slate-400" />
            ) : (
              <ChevronRight className="w-5 h-5 text-slate-400" />
            )}
          </button>
        )}
      </div>

      {expanded && checks && (
        <div className="mt-4 space-y-2 border-t pt-4">
          {checks.map((check, i) => (
            <div key={i} className="flex items-start gap-2 text-sm">
              {check.passed ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-500 mt-0.5 shrink-0" />
              ) : (
                <XCircle className="w-4 h-4 text-rose-500 mt-0.5 shrink-0" />
              )}
              <div className="flex-1">
                <span className="font-medium text-slate-700">{check.check_name}: </span>
                <span className="text-slate-600">{check.message}</span>
                {check.detail && (
                  <pre className="mt-1 p-2 bg-slate-900 text-slate-300 rounded text-[10px] overflow-auto max-h-32 leading-tight">
                    {JSON.stringify(check.detail, null, 2)}
                  </pre>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
