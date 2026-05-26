#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
#  Strategic Sourcing Command Center — Unified Launcher
#  Run: & "$env:LOCALAPPDATA\Programs\Git\bin\bash.exe" start.sh
# ═══════════════════════════════════════════════════════════════════════════════

set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLS="$REPO/all tools separate"
LOGS="$REPO/.logs"
mkdir -p "$LOGS"

# Suppress ALL auto-browser-opens from Gradio, Streamlit, Vite, etc.
export BROWSER=
export GRADIO_SERVER_NAME=127.0.0.1
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
export PYTHONWARNINGS=ignore
# Risk Intelligence API requires Tavily key (set placeholder to allow startup)
export TAVILY_API_KEY="${TAVILY_API_KEY:-placeholder}"

# ── Colours ───────────────────────────────────────────────────────────────────
CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
GRAY='\033[0;37m'; BOLD='\033[1m'; NC='\033[0m'

banner() { echo -e "\n${CYAN}${BOLD}  $*${NC}"; }
ok()     { echo -e "  ${GREEN}✔${NC}  $*"; }
warn()   { echo -e "  ${YELLOW}⚠${NC}  $*"; }
info()   { echo -e "  ${GRAY}→${NC}  $*"; }

# ── Find real Python (skip Windows Store stub) ────────────────────────────────
find_python() {
  local candidates=(
    "$HOME/miniconda3/python.exe"
    "$HOME/anaconda3/python.exe"
    "$HOME/AppData/Local/Programs/Python/Python312/python.exe"
    "$HOME/AppData/Local/Programs/Python/Python311/python.exe"
    "$HOME/AppData/Local/Programs/Python/Python310/python.exe"
    "$HOME/AppData/Local/Programs/Python/Python39/python.exe"
    "/c/Python312/python.exe"
    "/c/Python311/python.exe"
  )
  for c in "${candidates[@]}"; do
    if [[ -x "$c" ]]; then
      echo "$c"; return
    fi
  done
  # fall back — but test it's real (not Windows Store stub)
  for cmd in python python3; do
    if command -v "$cmd" &>/dev/null; then
      local ver
      ver=$("$cmd" -c "import sys; print(sys.version)" 2>/dev/null || true)
      if [[ "$ver" == *"."* ]]; then
        echo "$cmd"; return
      fi
    fi
  done
  echo "python"
}

PYTHON="$(find_python)"
ok "Python: $PYTHON"

# ── Python resolver (prefer local venv, fall back to global) ──────────────────
resolve_python() {
  local dir="$1" venv="${2:-}"
  if [[ -n "$venv" && -x "$dir/$venv/Scripts/python.exe" ]]; then
    echo "$dir/$venv/Scripts/python.exe"
  elif [[ -x "$dir/venv/Scripts/python.exe" ]]; then
    echo "$dir/venv/Scripts/python.exe"
  else
    echo "$PYTHON"
  fi
}

# ── Kill port ─────────────────────────────────────────────────────────────────
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
  local port="$1" label="$2" timeout="${3:-90}"
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

# ── npm install if node_modules missing OR vite binary missing ────────────────
ensure_npm() {
  local dir="$1" name="$2"
  if [[ ! -d "$dir/node_modules" || ! -f "$dir/node_modules/.bin/vite" ]]; then
    info "npm install → $name…"
    (cd "$dir" && npm install --silent) >> "$LOGS/npm_install_${name}.log" 2>&1 \
      && ok "npm install done: $name" \
      || warn "npm install issues for $name — check .logs/npm_install_${name}.log"
  fi
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
echo -e "  ${GRAY}Repo : $REPO${NC}"
echo -e "  ${GRAY}Python: $PYTHON${NC}\n"

# ── Free ports ────────────────────────────────────────────────────────────────
info "Clearing ports…"
for p in 3000 5000 5173 5174 7860 8000 8010 8020 8090 8501 8503 9001; do
  kill_port "$p"
done
echo ""

# ── npm install for all frontends (once, skipped if already done) ─────────────
banner "Checking frontend dependencies…"
ensure_npm "$REPO/frontend"                                    "dashboard"
ensure_npm "$TOOLS/vibe-main/frontend"                        "vibe"
ensure_npm "$TOOLS/Saas_managment/frontend"                   "saas"
echo ""

# ═══════════════════════════════════════════════════════════════════════════════
banner "Starting services…"

# 1. Vendor Onboarding (8090)
ONBOARD_DIR="$REPO/onboarding"
ONBOARD_PY="$(resolve_python "$ONBOARD_DIR")"
info "[1] DB migration…"
(cd "$ONBOARD_DIR" && "$ONBOARD_PY" migrations/init_db.py >> "$LOGS/onboarding_migration.log" 2>&1) || true
start_service "onboarding" "$ONBOARD_DIR" \
  "$ONBOARD_PY" -m uvicorn backend.main:app --host 0.0.0.0 --port 8090

# 2. SAFE — Spend Analytics / Demand Planning (7860)
SAFE_DIR="$TOOLS/safe_new_case"
SAFE_PY="$(resolve_python "$SAFE_DIR")"
start_service "safe_spend" "$SAFE_DIR" "$SAFE_PY" app_v3.py

# 3. CRA Project — Contract Renewal Agent (8000 + 8501)
CRA_DIR="$TOOLS/CRA_Project"
CRA_PY="$(resolve_python "$CRA_DIR" "cra_env")"
start_service "cra_backend"   "$CRA_DIR" "$CRA_PY" -m uvicorn main:app --host 0.0.0.0 --port 8000
start_service "cra_dashboard" "$CRA_DIR" "$CRA_PY" -m streamlit run app_v9.py \
  --server.port 8501 --server.headless true

RISK_DIR="$TOOLS/vendor-risk-analyze"
RISK_PY="$(resolve_python "$TOOLS" "sourcing_tool")"
[[ "$RISK_PY" == *"sourcing_tool"* ]] || RISK_PY="$(resolve_python "$RISK_DIR")"
start_service "vendor_risk" "$RISK_DIR" "$RISK_PY" backend.py

# 5. VIBE (9001 + 5173)
VIBE_DIR="$TOOLS/vibe-main"
VIBE_PY="$(resolve_python "$VIBE_DIR" "vibe_env")"
start_service "vibe_backend"  "$VIBE_DIR"          "$VIBE_PY" -m uvicorn backend_api:app --host 0.0.0.0 --port 9001
start_service "vibe_frontend" "$VIBE_DIR/frontend"  npm run dev -- --port 5173 --no-open

# 6. SaaS Management (8010 + 5174)
SAAS_DIR="$TOOLS/Saas_managment"
SAAS_PY="$(resolve_python "$SAAS_DIR")"
start_service "saas_api"      "$SAAS_DIR"          "$SAAS_PY" -m uvicorn api.main:app --host 127.0.0.1 --port 8010
start_service "saas_frontend" "$SAAS_DIR/frontend"  npm run dev -- --port 5174 --no-open

# 7. Risk Intelligence (8020 + 8503)
INTEL_DIR="$TOOLS/risk-intelligence-platform"
INTEL_PY="$(resolve_python "$INTEL_DIR")"
# Ensure fpdf2 is installed (required by streamlit app)
"$INTEL_PY" -m pip install fpdf2 --quiet >> "$LOGS/riskintel_deps.log" 2>&1 || true
start_service "riskintel_api"       "$INTEL_DIR/backend"       "$INTEL_PY" -m uvicorn main:app --host 0.0.0.0 --port 8020
start_service "riskintel_streamlit" "$INTEL_DIR/streamlit_app" "$INTEL_PY" -m streamlit run app.py \
  --server.port 8503 --server.headless true

# 8. Main Dashboard (3000)
start_service "dashboard" "$REPO/frontend" npm run dev -- --port 3000 --no-open

# ── Wait for critical services ────────────────────────────────────────────────
echo ""
banner "Waiting for services…"
echo ""

wait_port 8090 "Vendor Onboarding API    " 60
wait_port 7860 "Spend Analytics (SAFE)   " 90
wait_port 8000 "CRA Backend              " 60
wait_port 8501 "CRA Dashboard            " 90
wait_port 5000 "Vendor Risk Analyzer     " 60
wait_port 9001 "VIBE Backend             " 60
wait_port 5173 "VIBE Frontend            " 120
wait_port 8010 "SaaS Management API      " 60
wait_port 5174 "SaaS Management Frontend " 120
wait_port 8020 "Risk Intelligence API    " 60
wait_port 8503 "Risk Intelligence UI     " 90
wait_port 3000 "Main Dashboard           " 120

# ── Open browser ──────────────────────────────────────────────────────────────
start "http://localhost:3000" 2>/dev/null || true

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}${BOLD}  ╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}${BOLD}  ║       STRATEGIC SOURCING COMMAND CENTER — LIVE           ║${NC}"
echo -e "${CYAN}${BOLD}  ╠══════════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}  ║${NC}  ${BOLD}Main Dashboard${NC}            http://localhost:3000          ${CYAN}║${NC}"
echo -e "${CYAN}  ╠══════════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}  ║${NC}  Vendor Onboarding API     http://localhost:8090/docs     ${CYAN}║${NC}"
echo -e "${CYAN}  ║${NC}  Spend Analytics (SAFE)    http://localhost:7860          ${CYAN}║${NC}"
echo -e "${CYAN}  ║${NC}  CRA Backend               http://localhost:8000/docs     ${CYAN}║${NC}"
echo -e "${CYAN}  ║${NC}  CRA Dashboard             http://localhost:8501          ${CYAN}║${NC}"
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
