import React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { Database, Play, CheckCircle2, ChevronRight, LayoutDashboard, History, Info, AlertCircle } from "lucide-react";
import { useAppStore } from "../store/useAppStore";
import { UploadZone } from "../components/pipeline/UploadZone";
import { StepCard } from "../components/pipeline/StepCard";
import { getLastPipelineRun, refreshPipeline } from "../api/endpoints";
import { Search, Settings, ShieldCheck, RefreshCw } from "lucide-react";

export default function PipelineView() {
  const queryClient = useQueryClient();
  const setEnterDashboard = useAppStore(state => state.setEnterDashboard);
  const [activeRunId, setActiveRunId] = React.useState(null);
  const [uploads, setUploads] = React.useState({});
  const [activeTab, setActiveTab] = React.useState("ingestion"); // "ingestion" | "discovery"
  const [runMode, setRunMode] = React.useState(null); // "upload" | "refresh"
  const [refreshNotice, setRefreshNotice] = React.useState("");

  // 1. Fetch current promoted versions
  const { data: versions } = useQuery({
    queryKey: ["pipeline", "versions"],
    queryFn: async () => {
      const res = await axios.get("/api/v1/pipeline/versions");
      return res.data;
    },
    refetchInterval: activeRunId ? false : 30000,
  });

  const { data: lastRun } = useQuery({
    queryKey: ["pipeline", "last-run"],
    queryFn: getLastPipelineRun,
    refetchInterval: activeRunId ? false : 30000,
  });

  // 2. Poll for run status
  const { data: runStatus } = useQuery({
    queryKey: ["pipeline", "status", activeRunId],
    queryFn: async () => {
      const res = await axios.get(`/api/v1/pipeline/status/${activeRunId}`);
      return res.data;
    },
    enabled: !!activeRunId,
    refetchInterval: 2000,
  });

  // 3. Mutation to start the pipeline
  const runMutation = useMutation({
    mutationFn: async () => {
      const res = await axios.post("/api/v1/pipeline/run");
      return res.data;
    },
    onSuccess: data => {
      setRunMode("upload");
      setRefreshNotice("");
      setActiveRunId(data.run_id);
    },
  });

  const refreshMutation = useMutation({
    mutationFn: refreshPipeline,
    onMutate: () => {
      setRunMode("refresh");
      setRefreshNotice("");
    },
    onSuccess: data => {
      setActiveRunId(data.run_id);
    },
    onError: error => {
      if (error.response?.status === 409) {
        setRefreshNotice("A pipeline run is already active.");
      } else {
        setRefreshNotice("No existing data found. Please upload CSVs first.");
      }
    },
  });

  // Handle run completion
  React.useEffect(() => {
    if (runStatus?.status === "complete") {
      queryClient.invalidateQueries();
      queryClient.invalidateQueries({ queryKey: ["pipeline", "last-run"] });
      const timer = setTimeout(() => {
        setEnterDashboard(true);
      }, 1500);
      return () => clearTimeout(timer);
    }
  }, [runStatus?.status, setEnterDashboard, queryClient]);

  React.useEffect(() => {
    if (
      runMode === "refresh" &&
      runStatus?.status === "failed" &&
      runStatus.failure_summary?.includes("No existing data found")
    ) {
      setRefreshNotice("No existing data found. Please upload CSVs first.");
    }
  }, [runMode, runStatus?.status, runStatus?.failure_summary]);

  const hasData = Object.keys(versions || {}).length > 0;
  const isRunning = runMutation.isPending || refreshMutation.isPending || runStatus?.status === "running";
  const allUploaded = Object.keys(uploads).length >= 3;
  const lastIngestedLabel = lastRun?.completed_at
    ? new Date(lastRun.completed_at).toLocaleString(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
      })
    : "No completed run yet";

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-6 sm:p-12">
      <div className="max-w-4xl w-full space-y-8">
        
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-indigo-50 text-indigo-700 rounded-full text-xs font-semibold uppercase tracking-wider">
            <Database className="w-3 h-3" />
            Data Pipeline Control Panel
          </div>
          <h1 className="text-4xl font-extrabold text-slate-900 tracking-tight">
            Enterprise Ingestion Pipeline
          </h1>
          <p className="text-lg text-slate-500 max-w-xl mx-auto">
            Upload your dataset to begin a trial run. Our pipeline validates data across 4 layers before promoting to the dashboard.
          </p>
        </div>

        {/* Data Versions Strip */}
        {hasData && (
          <div className="bg-white border rounded-2xl p-4 flex items-center justify-between shadow-sm">
            <div className="flex items-center gap-6 overflow-x-auto no-scrollbar">
              <div className="flex items-center gap-2 text-slate-400 shrink-0">
                <History className="w-4 h-4" />
                <span className="text-xs font-medium uppercase tracking-wider">Current Live Data:</span>
              </div>
              {Object.entries(versions).map(([table, info]) => (
                <div key={table} className="flex flex-col gap-0.5 shrink-0">
                  <span className="text-[10px] text-slate-400 uppercase font-bold tracking-tight">
                    {table.replace(/_/g, ' ')}
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-slate-700">v{info.version}</span>
                    <span className="text-[10px] bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded">
                      {info.row_count.toLocaleString()} rows
                    </span>
                  </div>
                </div>
              ))}
            </div>
            <button
              onClick={() => setEnterDashboard(true)}
              className="ml-6 flex items-center gap-2 px-4 py-2 bg-slate-900 text-white rounded-xl hover:bg-slate-800 transition-all font-medium text-sm whitespace-nowrap shadow-lg shadow-slate-200"
            >
              Enter Dashboard
              <LayoutDashboard className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Tabs */}
        <div className="flex items-center gap-1 bg-slate-200/50 p-1 rounded-2xl w-fit mx-auto shadow-inner border border-slate-200">
          <button
            onClick={() => setActiveTab("ingestion")}
            className={`flex items-center gap-2 px-6 py-2.5 rounded-xl font-bold text-sm transition-all ${
              activeTab === "ingestion"
                ? "bg-white text-indigo-600 shadow-sm"
                : "text-slate-500 hover:text-slate-700 hover:bg-slate-200/50"
            }`}
          >
            <Database className="w-4 h-4" />
            Ingestion Pipeline
          </button>
          <button
            onClick={() => setActiveTab("discovery")}
            className={`flex items-center gap-2 px-6 py-2.5 rounded-xl font-bold text-sm transition-all ${
              activeTab === "discovery"
                ? "bg-white text-indigo-600 shadow-sm"
                : "text-slate-500 hover:text-slate-700 hover:bg-slate-200/50"
            }`}
          >
            <Search className="w-4 h-4" />
            Discovery & Baselines
          </button>
        </div>

        {activeTab === "ingestion" ? (
          <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white rounded-3xl border border-slate-100 shadow-xl p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                    Upload CSVs
                  </h2>
                  <div className="text-xs text-slate-400 font-medium">
                    {Object.keys(uploads).length}/3 CSVs
                  </div>
                </div>
                
                <div className="space-y-4">
                  <UploadZone 
                    table="vendor_overview" 
                    label="Vendor Overview" 
                    onUploadSuccess={data => setUploads(prev => ({ ...prev, vendor_overview: data }))}
                  />
                  <UploadZone 
                    table="hr_headcount" 
                    label="HR Headcount" 
                    onUploadSuccess={data => setUploads(prev => ({ ...prev, hr_headcount: data }))}
                  />
                  <UploadZone 
                    table="license_utilization" 
                    label="License Utilization" 
                    onUploadSuccess={data => setUploads(prev => ({ ...prev, license_utilization: data }))}
                  />
                </div>

                <button
                  disabled={!allUploaded || isRunning}
                  onClick={() => runMutation.mutate()}
                  className={`w-full py-4 rounded-2xl flex items-center justify-center gap-3 font-bold text-lg transition-all shadow-xl ${
                    allUploaded && !isRunning
                      ? "bg-indigo-600 text-white hover:bg-indigo-700 shadow-indigo-100 scale-[1.02]"
                      : "bg-slate-100 text-slate-400 cursor-not-allowed shadow-none"
                  }`}
                >
                  {isRunning && runMode === "upload" ? (
                    <>
                      <Play className="w-5 h-5 fill-current animate-pulse" />
                      Pipeline Running...
                    </>
                  ) : (
                    <>
                      <Play className="w-5 h-5 fill-current" />
                      Run Validation Pipeline
                    </>
                  )}
                </button>
                
                {!allUploaded && !isRunning && (
                  <div className="flex items-center gap-2 p-3 bg-indigo-50/50 rounded-xl text-xs text-indigo-600 font-medium border border-indigo-100">
                    <Info className="w-4 h-4 shrink-0" />
                    Upload all 3 datasets to enable the validation pipeline.
                  </div>
                )}
              </div>

              <div className="bg-white rounded-3xl border border-slate-100 shadow-xl p-6 flex flex-col justify-between gap-6">
                <div className="space-y-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="space-y-2">
                      <h2 className="text-lg font-bold text-slate-900">Refresh from Existing Data</h2>
                      <p className="text-sm text-slate-500 leading-relaxed">
                        Re-runs the pipeline using the last uploaded CSVs. No file selection needed.
                      </p>
                    </div>
                    <div className="p-3 bg-emerald-50 text-emerald-600 rounded-2xl">
                      <RefreshCw className={`w-5 h-5 ${isRunning && runMode === "refresh" ? "animate-spin" : ""}`} />
                    </div>
                  </div>

                  <div className="rounded-2xl border border-slate-100 bg-slate-50/70 p-4">
                    <div className="text-[11px] text-slate-400 font-bold uppercase tracking-widest">
                      Last Ingested
                    </div>
                    <div className="mt-1 text-sm font-semibold text-slate-700">{lastIngestedLabel}</div>
                  </div>

                  {refreshNotice && (
                    <div className="flex items-center gap-2 p-3 bg-amber-50 rounded-xl text-xs text-amber-700 font-medium border border-amber-100">
                      <AlertCircle className="w-4 h-4 shrink-0" />
                      {refreshNotice}
                    </div>
                  )}
                </div>

                <button
                  disabled={isRunning}
                  onClick={() => refreshMutation.mutate()}
                  className={`w-full py-4 rounded-2xl flex items-center justify-center gap-3 font-bold text-lg transition-all shadow-xl ${
                    !isRunning
                      ? "bg-slate-900 text-white hover:bg-slate-800 shadow-slate-200"
                      : "bg-slate-100 text-slate-400 cursor-not-allowed shadow-none"
                  }`}
                >
                  {isRunning && runMode === "refresh" ? (
                    <>
                      <RefreshCw className="w-5 h-5 animate-spin" />
                      Refresh Running...
                    </>
                  ) : (
                    <>
                      <RefreshCw className="w-5 h-5" />
                      Refresh
                    </>
                  )}
                </button>
              </div>
            </div>

            <div className="bg-white rounded-3xl border border-slate-100 shadow-xl p-6 space-y-4">
              <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                Validation Progress
              </h2>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                {(runStatus?.steps || [
                  { step: "ingestion", label: "Ingestion", status: "pending" },
                  { step: "service", label: "Service Layer", status: "pending" },
                  { step: "processing", label: "Processing", status: "pending" },
                  { step: "promotion", label: "Promotion", status: "pending" }
                ]).map(step => (
                  <StepCard key={step.step} {...step} />
                ))}
              </div>

              {runStatus?.status === "failed" && (
                <div className="p-4 bg-rose-50 border border-rose-100 rounded-2xl space-y-2">
                  <h3 className="font-bold text-rose-900 flex items-center gap-2">
                    <AlertCircle className="w-4 h-4" />
                    Pipeline Trial Failed
                  </h3>
                  <p className="text-sm text-rose-700 leading-relaxed">
                    {runStatus.failure_summary}. Changes have been rolled back to maintain data integrity. Please fix the input data and try again.
                  </p>
                </div>
              )}

              {runStatus?.status === "complete" && (
                <div className="p-4 bg-emerald-50 border border-emerald-100 rounded-2xl space-y-2 text-center">
                  <div className="inline-flex p-2 bg-emerald-500 text-white rounded-full mb-1 shadow-lg shadow-emerald-200">
                    <CheckCircle2 className="w-6 h-6" />
                  </div>
                  <h3 className="font-bold text-emerald-900 text-lg">Trial Run Successful</h3>
                  <p className="text-sm text-emerald-700">
                    All validation layers passed. Your data has been promoted. Redirecting to dashboard...
                  </p>
                </div>
              )}
            </div>
          </div>
        ) : (
          <DiscoveryView />
        )}
      </div>
    </div>
  );
}

function DiscoveryView() {
  const { data: discovery, isLoading: loadingDiscovery, refetch } = useQuery({
    queryKey: ["pipeline", "discovery"],
    queryFn: async () => {
      const res = await axios.get("/api/v1/pipeline/discovery");
      return res.data;
    },
  });

  const { data: baselines } = useQuery({
    queryKey: ["pipeline", "baselines"],
    queryFn: async () => {
      const res = await axios.get("/api/v1/pipeline/baselines");
      return res.data;
    },
  });

  const establishMutation = useMutation({
    mutationFn: async () => {
      const res = await axios.post("/api/v1/pipeline/baselines");
      return res.data;
    },
    onSuccess: () => {
      refetch();
    },
  });

  if (loadingDiscovery) {
    return (
      <div className="flex flex-col items-center justify-center p-12 bg-white rounded-3xl border border-slate-100 shadow-sm animate-pulse">
        <RefreshCw className="w-8 h-8 text-indigo-200 animate-spin mb-4" />
        <span className="text-slate-400 font-medium">Analyzing current portfolio...</span>
      </div>
    );
  }

  const baselineMap = Object.fromEntries(
    (baselines || []).map(b => [b.metric_name, b.baseline_value])
  );

  return (
    <div className="bg-white rounded-3xl border border-slate-100 shadow-xl overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="p-8 border-b border-slate-50 bg-slate-50/50">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">Portfolio Discovery</h2>
            <p className="text-slate-500 text-sm font-medium">
              Establish ground truth baselines from your initial data ingestion.
            </p>
          </div>
          <ShieldCheck className="w-10 h-10 text-indigo-500/20" />
        </div>
      </div>

      <div className="p-8 space-y-8">
        {!discovery?.can_establish ? (
          <div className="flex flex-col items-center justify-center py-12 text-center space-y-4">
            <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center">
              <Info className="w-8 h-8 text-slate-300" />
            </div>
            <div className="space-y-1">
              <h3 className="font-bold text-slate-900">Baseline Unavailable</h3>
              <p className="text-slate-500 text-sm max-w-xs mx-auto">
                {discovery?.message}
              </p>
            </div>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {discovery.metrics.map(metric => {
                const baseline = baselineMap[metric.metric_name];
                const diff = baseline ? ((metric.current_value - baseline) / baseline) * 100 : null;
                
                return (
                  <div key={metric.metric_name} className="p-6 rounded-2xl border bg-white shadow-sm hover:border-indigo-100 transition-colors">
                    <div className="flex items-center justify-between mb-4">
                      <span className="text-xs font-bold uppercase tracking-widest text-slate-400">
                        {metric.label}
                      </span>
                      {baseline && (
                        <div className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          Math.abs(diff) < 10 ? "bg-emerald-50 text-emerald-600" : "bg-rose-50 text-rose-600"
                        }`}>
                          {diff > 0 ? "+" : ""}{diff.toFixed(1)}% vs Baseline
                        </div>
                      )}
                    </div>
                    <div className="flex items-baseline gap-1">
                      <span className="text-3xl font-black text-slate-900">
                        {metric.unit}{metric.current_value.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                      </span>
                    </div>
                    <div className="mt-4 flex items-center justify-between pt-4 border-t border-slate-50">
                      <span className="text-[11px] text-slate-400 font-medium">Established Baseline:</span>
                      <span className="text-[11px] font-bold text-slate-700">
                        {baseline ? `${metric.unit}${baseline.toLocaleString()}` : "Not Set"}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="p-6 bg-indigo-50/50 rounded-2xl border border-indigo-100/50 space-y-4">
              <div className="flex items-start gap-3">
                <Settings className="w-5 h-5 text-indigo-500 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <h4 className="text-sm font-bold text-indigo-900 uppercase tracking-wide">Governance Controls</h4>
                  <p className="text-sm text-indigo-700/80 leading-relaxed">
                    By establishing baselines, you are setting the "Ground Truth" for future validation trials. 
                    Any significant deviation in subsequent uploads will trigger an automatic security rollback.
                  </p>
                </div>
              </div>

              <button
                onClick={() => establishMutation.mutate()}
                disabled={establishMutation.isPending}
                className={`w-full py-3 rounded-xl font-bold transition-all shadow-lg ${
                  establishMutation.isPending
                    ? "bg-indigo-400 text-white cursor-not-allowed"
                    : "bg-indigo-600 text-white hover:bg-indigo-700 shadow-indigo-200"
                }`}
              >
                {establishMutation.isPending ? "Establishing..." : "Establish All Metrics as Baseline"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
