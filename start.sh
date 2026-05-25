#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
#  Strategic Sourcing Command Center — Unified Launcher
#  Run: & "$env:LOCALAPPDATA\Programs\Git\bin\bash.exe" start.sh
# ═══════════════════════════════════════════════════════════════════════════════

# NO set -e — grep/netstat return non-zero when nothing found; don't exit on that
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLS="$REPO/all tools separate"
LOGS="$REPO/.logs"
mkdir -p "$LOGS"

# ── Colours ───────────────────────────────────────────────────────────────────
CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
RED='\033[0;31m'; GRAY='\033[0;37m'; BOLD='\033[1m'; NC='\033[0m'

banner() { echo -e "\n${CYAN}${BOLD}  $*${NC}"; }
ok()     { echo -e "  ${GREEN}✔${NC}  $*"; }
warn()   { echo -e "  ${YELLOW}⚠${NC}  $*"; }
info()   { echo -e "  ${GRAY}→${NC}  $*"; }

# ── Python resolver ───────────────────────────────────────────────────────────
resolve_python() {
  local dir="$1" venv="${2:-}"
  if [[ -n "$venv" && -x "$dir/$venv/Scripts/python.exe" ]]; then
    echo "$dir/$venv/Scripts/python.exe"
  elif [[ -x "$dir/venv/Scripts/python.exe" ]]; then
    echo "$dir/venv/Scripts/python.exe"
  elif command -v python3 &>/dev/null; then
    echo "python3"
  else
    echo "python"
  fi
}

# ── Kill port (|| true so grep non-match never aborts script) ─────────────────
kill_port() {
  local port="$1"
  local pids
  pids=$(netstat -ano 2>/dev/null | grep ":${port}[[:space:]].*LISTENING" | awk '{print $NF}' | sort -u || true)
  for pid in $pids; do
    [[ "$pid" =~ ^[0-9]+$ ]] && taskkill //F //PID "$pid" &>/dev/null || true
  done
}

# ── Wait for TCP port ─────────────────────────────────────────────────────────
wait_port() {
  local port="$1" label="$2" timeout="${3:-60}"
  local elapsed=0
  while (( elapsed < timeout )); do
    if bash -c "echo >/dev/tcp/127.0.0.1/$port" 2>/dev/null; then
      ok "$label  →  http://localhost:$port"
      return 0
    fi
    sleep 1; (( elapsed++ ))
  done
  warn "$label not ready after ${timeout}s — check .logs/"
  return 1
}

# ── Start background service ──────────────────────────────────────────────────
start_service() {
  local name="$1" dir="$2"; shift 2
  local log="$LOGS/${name}.log"
  info "Starting $name…"
  (cd "$dir" && "$@" >> "$log" 2>&1) &
  echo $! > "$LOGS/${name}.pid"
}

# ── Cleanup on Ctrl+C ─────────────────────────────────────────────────────────
cleanup() {
  echo ""
  banner "Stopping all services…"
  for pidfile in "$LOGS"/*.pid; do
    [[ -f "$pidfile" ]] && kill "$(cat "$pidfile")" 2>/dev/null || true
    rm -f "$pidfile"
  done
  ok "All services stopped."
}
trap cleanup EXIT INT TERM

# ═══════════════════════════════════════════════════════════════════════════════
banner "Strategic Sourcing Command Center"
echo -e "  ${GRAY}Repo: $REPO${NC}\n"

info "Clearing ports…"
for p in 3000 5000 5173 5174 7860 8000 8010 8020 8090 8501 8503 9001; do
  kill_port "$p"
done
echo ""

# ── 1. Vendor Onboarding (8090) ───────────────────────────────────────────────
ONBOARD_DIR="$REPO/onboarding"
ONBOARD_PY="$(resolve_python "$ONBOARD_DIR")"
info "[1] DB migration…"
(cd "$ONBOARD_DIR" && "$ONBOARD_PY" migrations/init_db.py >> "$LOGS/onboarding_migration.log" 2>&1) || true
start_service "onboarding" "$ONBOARD_DIR" \
  "$ONBOARD_PY" -m uvicorn backend.main:app --host 0.0.0.0 --port 8090

# ── 2. CRA Workflow (8000 + 8501) ────────────────────────────────────────────
CRA_DIR="$TOOLS/cra_workflow"
CRA_PY="$(resolve_python "$CRA_DIR" "cra_env")"
start_service "cra_backend"   "$CRA_DIR" "$CRA_PY" -m uvicorn main:app --host 0.0.0.0 --port 8000
start_service "cra_dashboard" "$CRA_DIR" "$CRA_PY" -m streamlit run app_v8.py \
  --server.port 8501 --server.headless true

# ── 3. SAFE (7860) ────────────────────────────────────────────────────────────
SAFE_DIR="$TOOLS/safe_new_case"
SAFE_PY="$(resolve_python "$SAFE_DIR" "safe")"
start_service "safe" "$SAFE_DIR" "$SAFE_PY" app_v3.py

# ── 4. Vendor Risk (5000) ─────────────────────────────────────────────────────
RISK_DIR="$TOOLS/vendor-risk-analyze"
RISK_PY="$(resolve_python "$TOOLS" "sourcing_tool")"
[[ "$RISK_PY" == *"sourcing_tool"* ]] || RISK_PY="$(resolve_python "$RISK_DIR")"
start_service "vendor_risk" "$RISK_DIR" "$RISK_PY" backend.py

# ── 5. VIBE (9001 + 5173) ────────────────────────────────────────────────────
VIBE_DIR="$TOOLS/vibe-main"
VIBE_PY="$(resolve_python "$VIBE_DIR" "vibe_env")"
start_service "vibe_backend"  "$VIBE_DIR"          "$VIBE_PY" -m uvicorn backend_api:app --host 0.0.0.0 --port 9001
start_service "vibe_frontend" "$VIBE_DIR/frontend"  npm run dev -- --port 5173

# ── 6. SaaS Management (8010 + 5174) ─────────────────────────────────────────
SAAS_DIR="$TOOLS/Saas_managment"
SAAS_PY="$(resolve_python "$SAAS_DIR")"
start_service "saas_api"      "$SAAS_DIR"          "$SAAS_PY" -m uvicorn api.main:app --host 127.0.0.1 --port 8010
start_service "saas_frontend" "$SAAS_DIR/frontend"  npm run dev -- --port 5174

# ── 7. Risk Intelligence (8020 + 8503) ───────────────────────────────────────
INTEL_DIR="$TOOLS/risk-intelligence-platform"
INTEL_PY="$(resolve_python "$INTEL_DIR")"
start_service "riskintel_api"       "$INTEL_DIR/backend"      "$INTEL_PY" -m uvicorn main:app --host 0.0.0.0 --port 8020
start_service "riskintel_streamlit" "$INTEL_DIR/streamlit_app" "$INTEL_PY" -m streamlit run app.py \
  --server.port 8503 --server.headless true

# ── 8. Main Dashboard (3000) ──────────────────────────────────────────────────
start_service "dashboard" "$REPO/frontend" npm run dev -- --port 3000

# ── Wait for all services ─────────────────────────────────────────────────────
echo ""
banner "Waiting for services…"
echo ""

wait_port 8090 "Vendor Onboarding API    " 60
wait_port 8000 "CRA Backend              " 45
wait_port 8501 "CRA Dashboard            " 60
wait_port 7860 "SAFE App                 " 60
wait_port 5000 "Vendor Risk Analyzer     " 45
wait_port 9001 "VIBE Backend             " 45
wait_port 5173 "VIBE Frontend            " 60
wait_port 8010 "SaaS Management API      " 45
wait_port 5174 "SaaS Management Frontend " 60
wait_port 8020 "Risk Intelligence API    " 45
wait_port 8503 "Risk Intelligence UI     " 60
wait_port 3000 "Main Dashboard           " 60

# ── Open browser once dashboard is ready ─────────────────────────────────────
start "http://localhost:3000" 2>/dev/null || true

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}${BOLD}  ╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}${BOLD}  ║       STRATEGIC SOURCING COMMAND CENTER — LIVE           ║${NC}"
echo -e "${CYAN}${BOLD}  ╠══════════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}  ║${NC}  ${BOLD}Main Dashboard${NC}            http://localhost:3000          ${CYAN}║${NC}"
echo -e "${CYAN}  ╠══════════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}  ║${NC}  Vendor Onboarding API     http://localhost:8090/docs     ${CYAN}║${NC}"
echo -e "${CYAN}  ║${NC}  CRA Backend               http://localhost:8000/docs     ${CYAN}║${NC}"
echo -e "${CYAN}  ║${NC}  CRA Dashboard             http://localhost:8501          ${CYAN}║${NC}"
echo -e "${CYAN}  ║${NC}  SAFE Forecasting          http://localhost:7860          ${CYAN}║${NC}"
echo -e "${CYAN}  ║${NC}  Vendor Risk Analyzer      http://localhost:5000          ${CYAN}║${NC}"
echo -e "${CYAN}  ║${NC}  VIBE Backend              http://localhost:9001/docs     ${CYAN}║${NC}"
echo -e "${CYAN}  ║${NC}  VIBE Frontend             http://localhost:5173          ${CYAN}║${NC}"
echo -e "${CYAN}  ║${NC}  SaaS Management API       http://localhost:8010/docs     ${CYAN}║${NC}"
echo -e "${CYAN}  ║${NC}  SaaS Management Frontend  http://localhost:5174          ${CYAN}║${NC}"
echo -e "${CYAN}  ║${NC}  Risk Intelligence API     http://localhost:8020/docs     ${CYAN}║${NC}"
echo -e "${CYAN}  ║${NC}  Risk Intelligence UI      http://localhost:8503          ${CYAN}║${NC}"
echo -e "${CYAN}  ╠══════════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}  ║${NC}  ${GRAY}Logs → $REPO/.logs/${NC}              ${CYAN}║${NC}"
echo -e "${CYAN}${BOLD}  ╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${GRAY}Press Ctrl+C to stop all services.${NC}\n"

wait
