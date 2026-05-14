# Strategic Sourcing Platform - Run All Services Script
# This script opens each service in a new PowerShell window.

Write-Host "🚀 Starting Strategic Sourcing Platform..." -ForegroundColor Cyan

# 1. CRA Workflow Backend
Write-Host "Starting CRA Backend (Port 8000)..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location 'all tools separate\cra_workflow'; .\cra_env\Scripts\python.exe -m uvicorn main:app --port 8000"

# 2. CRA Workflow Dashboard
Write-Host "Starting CRA Dashboard (Port 8501)..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location 'all tools separate\cra_workflow'; .\cra_env\Scripts\python.exe -m streamlit run app_v8.py --server.port 8501"

# 3. SAFE App
Write-Host "Starting SAFE New Case (Port 7860)..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location 'all tools separate\safe_new_case'; .\safe\Scripts\python.exe app_v3.py"

# 4. Vendor Risk Backend
Write-Host "Starting Vendor Risk Backend (Port 5000)..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location 'all tools separate\vendor-risk-analyze'; ..\sourcing_tool\Scripts\python.exe backend.py"

# 5. Vibe Backend
Write-Host "Starting Vibe Backend (Port 9001)..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location 'all tools separate\vibe-main'; .\vibe_env\Scripts\python.exe -m uvicorn backend_api:app --port 9001"

# 6. Vibe Frontend
Write-Host "Starting Vibe Frontend (Port 5173)..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location 'all tools separate\vibe-main\frontend'; npm run dev -- --port 5173"

# 7. Main Dashboard
Write-Host "Starting Main Dashboard (Port 3000)..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location 'frontend'; npm run dev -- --port 3000"

Write-Host "✅ All services requested. Check the separate windows for status." -ForegroundColor Green
