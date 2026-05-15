# Strategic Sourcing Command Center — single-command launcher
# Usage: cd C:\sourcing ; .\start.ps1
# Press Ctrl+C to stop all services.

$ErrorActionPreference = "SilentlyContinue"

Write-Host ""
Write-Host "  Strategic Sourcing Command Center" -ForegroundColor Cyan
Write-Host "  Starting all services..." -ForegroundColor Gray
Write-Host ""

# ── Helpers ───────────────────────────────────────────────────────────────────

function Kill-Port($port) {
    $p = Get-NetTCPConnection -LocalPort $port -State Listen 2>$null | Select-Object -First 1
    if ($p) { Stop-Process -Id (Get-Process -Id $p.OwningProcess).Id -Force 2>$null }
}

function Wait-Port($port, $label, $timeoutSec = 30) {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    while ($sw.Elapsed.TotalSeconds -lt $timeoutSec) {
        try {
            $tcp = New-Object Net.Sockets.TcpClient
            $tcp.Connect("127.0.0.1", $port)
            $tcp.Close()
            Write-Host "  [ok] $label" -ForegroundColor Green
            return $true
        } catch { Start-Sleep -Milliseconds 500 }
    }
    Write-Host "  [warn] $label — took longer than expected, may still be starting" -ForegroundColor Yellow
    return $false
}

# ── Clear ports ───────────────────────────────────────────────────────────────
foreach ($port in @(8090, 3000)) { Kill-Port $port }

# ── 1. DB migration (blocking, fast) ─────────────────────────────────────────
Write-Host "  [1/3] Initialising database..." -ForegroundColor DarkGray
Push-Location "$PSScriptRoot\onboarding"
python migrations\init_db.py 2>&1 | Out-Null
Pop-Location

# ── 2. Onboarding backend — port 8090 ────────────────────────────────────────
Write-Host "  [2/3] Starting onboarding backend (port 8090)..." -ForegroundColor DarkGray
$backend = Start-Job -ScriptBlock {
    Set-Location $using:PSScriptRoot\onboarding
    python -m uvicorn backend.main:app --port 8090 2>&1
}

# ── 3. React dashboard — port 3000 ───────────────────────────────────────────
Write-Host "  [3/3] Starting React dashboard (port 3000)..." -ForegroundColor DarkGray
$frontend = Start-Job -ScriptBlock {
    Set-Location $using:PSScriptRoot\frontend
    npm run dev 2>&1
}

# ── Wait for services ─────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  Waiting for services to come online..." -ForegroundColor Gray
Wait-Port 8090 "Onboarding API    -> http://localhost:8090"
Wait-Port 3000 "React Dashboard   -> http://localhost:3000"

# ── Print links ───────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  ============================================" -ForegroundColor Cyan
Write-Host "   READY — open these in your browser:" -ForegroundColor White
Write-Host ""
Write-Host "   Main Dashboard      http://localhost:3000" -ForegroundColor Cyan
Write-Host "   Onboarding API      http://localhost:8090/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "  ============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Press Ctrl+C to stop all services." -ForegroundColor Gray
Write-Host ""

# ── Stream logs + keep alive ──────────────────────────────────────────────────
try {
    while ($true) {
        # Show any new output from background jobs
        Receive-Job $backend, $frontend 2>$null | ForEach-Object {
            if ($_ -match "error|Error|ERROR|warn|WARN|Traceback") {
                Write-Host "  $_" -ForegroundColor Yellow
            }
        }
        Start-Sleep -Seconds 2
    }
} finally {
    Write-Host ""
    Write-Host "  Stopping all services..." -ForegroundColor Gray
    Stop-Job $backend, $frontend 2>$null
    Remove-Job $backend, $frontend -Force 2>$null
    Write-Host "  Stopped." -ForegroundColor Green
}
