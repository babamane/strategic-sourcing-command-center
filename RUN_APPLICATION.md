# 🚀 Strategic Sourcing Platform - Run Guide

This document provides instructions on how to run the entire integrated platform, including all backend tools and the main dashboard.

## 📋 Prerequisites

Ensure you have the following installed:
- **Python 3.9+**
- **Node.js & npm**
- **Ollama** (with `gemma2:9b` and `qwen2:1.5b` models pulled)

---

## ⚡ Option 1: Run Everything Automatically
We have provided a PowerShell script that opens all services in separate terminal windows.

1. Open PowerShell in the root directory.
2. Run the following command:
   ```powershell
   .\run_all.ps1
   ```

---

## 🛠️ Option 2: Run Manually (Step-by-Step)

Open a new terminal for each of the following commands:

### 1. CRA Workflow (Contract Renewal Agent)
**Backend:**
```powershell
cd "all tools separate\cra_workflow"
.\cra_env\Scripts\python.exe -m uvicorn main:app --port 8000
```
**Dashboard:**
```powershell
cd "all tools separate\cra_workflow"
.\cra_env\Scripts\python.exe -m streamlit run app_v8.py --server.port 8501
```

### 2. SAFE (Software Assets Forecasting Engine)
```powershell
cd "all tools separate\safe_new_case"
.\safe\Scripts\python.exe app_v3.py
```

### 3. Vendor Risk Analyzer
```powershell
cd "all tools separate\vendor-risk-analyze"
..\sourcing_tool\Scripts\python.exe backend.py
```

### 4. VIBE (Earnings Call Analyzer)
**Backend:**
```powershell
cd "all tools separate\vibe-main"
.\vibe_env\Scripts\python.exe -m uvicorn backend_api:app --port 9001
```
**Frontend:**
```powershell
cd "all tools separate\vibe-main\frontend"
npm run dev -- --port 5173
```

### 5. Main Dashboard (Command Tower)
```powershell
cd "frontend"
npm run dev -- --port 3000
```

---

## 🌐 Summary of Ports
| Service | URL |
| :--- | :--- |
| **Main Dashboard** | http://localhost:3000 |
| **CRA Backend** | http://localhost:8000 |
| **CRA Dashboard** | http://localhost:8501 |
| **SAFE App** | http://localhost:7860 |
| **Vendor Risk** | http://localhost:5000 |
| **Vibe Backend** | http://localhost:9001 |
| **Vibe Frontend** | http://localhost:5173 |
