import React from "react";
import { Upload, FileCheck, AlertCircle, Loader2 } from "lucide-react";
import axios from "axios";

export function UploadZone({ table, label, onUploadSuccess }) {
  const [dragActive, setDragActive] = React.useState(false);
  const [status, setStatus] = React.useState("idle"); // idle | uploading | success | error
  const [error, setError] = React.useState("");
  const [fileInfo, setFileInfo] = React.useState(null);

  const handleDrag = e => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = async e => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await uploadFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = async e => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      await uploadFile(e.target.files[0]);
    }
  };

  const uploadFile = async file => {
    if (!file.name.endsWith(".csv")) {
      setStatus("error");
      setError("Only CSV files are allowed");
      return;
    }

    setStatus("uploading");
    setError("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post("/api/v1/pipeline/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setStatus("success");
      setFileInfo(response.data);
      onUploadSuccess?.(response.data);
    } catch (err) {
      setStatus("error");
      setError(err.response?.data?.detail || "Upload failed");
    }
  };

  return (
    <div
      className={`relative group p-6 border-2 border-dashed rounded-2xl transition-all ${
        dragActive ? "border-indigo-500 bg-indigo-50/50" : "border-slate-200 hover:border-slate-300 bg-white"
      } ${status === "success" ? "border-emerald-500 bg-emerald-50/20" : ""}`}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
    >
      <input
        type="file"
        id={`upload-${table}`}
        className="hidden"
        accept=".csv"
        onChange={handleChange}
      />
      
      <div className="flex flex-col items-center text-center gap-3">
        {status === "idle" && (
          <>
            <div className="p-3 bg-slate-50 rounded-full group-hover:bg-slate-100 transition-colors">
              <Upload className="w-6 h-6 text-slate-400" />
            </div>
            <div>
              <p className="font-semibold text-slate-900">{label}</p>
              <p className="text-sm text-slate-500 mt-1">
                Drag and drop or <label htmlFor={`upload-${table}`} className="text-indigo-600 font-medium cursor-pointer hover:underline">browse</label>
              </p>
            </div>
          </>
        )}

        {status === "uploading" && (
          <>
            <Loader2 className="w-10 h-10 text-indigo-500 animate-spin" />
            <p className="font-medium text-slate-700">Uploading {fileInfo?.filename}...</p>
          </>
        )}

        {status === "success" && (
          <>
            <div className="p-3 bg-emerald-50 rounded-full">
              <FileCheck className="w-6 h-6 text-emerald-500" />
            </div>
            <div>
              <p className="font-semibold text-slate-900">{label} Ready</p>
              <p className="text-sm text-emerald-600 mt-1">{fileInfo?.filename}</p>
            </div>
            <button 
              onClick={() => setStatus("idle")}
              className="text-xs text-slate-400 hover:text-slate-600 underline mt-2"
            >
              Replace file
            </button>
          </>
        )}

        {status === "error" && (
          <>
            <div className="p-3 bg-rose-50 rounded-full">
              <AlertCircle className="w-6 h-6 text-rose-500" />
            </div>
            <div>
              <p className="font-semibold text-slate-900">Upload Failed</p>
              <p className="text-sm text-rose-600 mt-1">{error}</p>
            </div>
            <button 
              onClick={() => setStatus("idle")}
              className="text-xs text-slate-400 hover:text-slate-600 underline mt-2"
            >
              Try again
            </button>
          </>
        )}
      </div>
    </div>
  );
}
