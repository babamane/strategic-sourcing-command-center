# Phase 1E — React Dashboard Frontend, Chatbot Integration, and Write Trigger UI

**Version:** v2 · **Audit Date:** 2026-05-01 · **Session:** Phase 1E Spec  
**Depends on:** Phase 1D complete · 161 tests passing · FastAPI on :8000 · MCP server ready  
**Prepared for:** Frontend implementation handoff  
**Backend additions:** `api/routers/triggers.py` (3 endpoints) · `api/routers/mail.py` (1 endpoint) · `services/mail_service.py` · new MCP tool `send_churn_notification`

---

## Changes from v1 (do not implement v1)

| # | Location | Fix |
|---|---|---|
| 1 | `InsightBanner` interface | Added `secondaryAction?` — was silently dropped |
| 2 | Zustand `pendingConfirm` | Added `type` discriminator — `ConfirmModal` couldn't pick endpoint |
| 3 | `useTrigger.js` | Added try/catch — network errors left `loading` stuck at `true` |
| 4 | `triggerClient.js` | Added full specification — was referenced but never defined |
| 5 | Build order step 17 | Fixed "Anthropic" → "LLM server" |
| 6 | `DEFAULT_CFG` | Defined once in env-vars section; ChatPanel section removed duplicate |
| 7 | `InsightBanner` | Removed `useTrigger` hook call — display components don't call hooks; sets `pendingConfirm` directly |
| 8 | `buildParams()` | Added code definition — agent would have guessed the "All" omit logic wrong |
| 9 | `OverviewView` | Added `useGhostDetail` call for dept breakdown chart |
| 10 | `UtilizationView` | Fixed field names: `active_usage_rate` from API, `idle_pct` derived in component |
| 11 | CORS (critical) | LLM calls now proxied through Vite `/llm` → `:11434`; direct browser→Ollama is blocked by CORS |
| 12 | Trigger type naming | Standardised to `"reclamation"` everywhere — was mixed `"reclamation_csv"` vs `"reclamation"` |
| 13 | `RenewalView` alert cards | Spec now uses a `TwoActionBanner` variant; `InsightBanner` only handles one action |
| + | **New** Chat guardrails | MAX_TURNS, timeout, loop prevention, input validation on action fields |
| + | **New** Mailing service | `services/mail_service.py`, MCP tool, `api/routers/mail.py`, env vars, frontend integration |

---

## What This Phase Is

Phase 1E builds the React dashboard that surfaces every processor output the
backend already computes. It adds a sliding AI chatbot panel backed by the
local LLM server already running for the CLI demo, a filter-driven agentic
insight banner that generates a context-specific recommendation whenever the
vendor or view changes, and a two-step confirmation flow for write triggers
(ghost ticket, reclamation CSV, rightsizing email, churn notification email).

Two thin backend additions: a `/triggers/*` router so the frontend talks to a
single FastAPI origin instead of the MCP server directly, and a `/mail/*` router
backed by a new `services/mail_service.py` for churn notifications.

This phase makes the platform usable by a non-technical SaaS operations manager
without touching a CLI.

---

## What This Phase Is Not

- Authentication, login, or multi-tenant access control
- Real-time websocket updates or push notifications
- Email reply-tracking UI (Phase 2)
- Execution agent status tracker (Phase 2)
- Mobile-responsive layout (desktop-first V1 only)
- Dark/light theme toggle (dark theme only V1)
- Contract creation or expansion flows (Phase 2)
- Saved filters, user preferences, or session persistence

---

## Architecture

### Layer map

```
Browser
  └── React App (Vite, :5173 dev / :4173 preview)
        ├── /api  proxy ─────────────────────────→ FastAPI (:8000)
        │     read:  GET /ghost, /reclamation, …        (Phase 1D)
        │     write: POST /triggers/*                   (Phase 1E)
        │     mail:  POST /mail/churn-notification      (Phase 1E)
        └── /llm  proxy ─────────────────────────→ local LLM server (:11434)
              planning turn:  POST /llm/api/chat  format:"json"
              answer turn:    POST /llm/api/chat  (plain text)
```

The MCP server is **not** called from the browser. Both trigger and mail
endpoints in FastAPI call the corresponding service/action layers internally,
keeping one trusted origin for the frontend and avoiding all CORS issues.

The `/llm` proxy in Vite rewrites to the local LLM server — this solves the
CORS problem. `chat.js` always uses `/llm/api/chat`, never a raw `:11434` URL.

### Frontend layers

```
src/
  store/         Global state (Zustand)
  api/           HTTP layer — Axios + fetch wrappers
  hooks/         React Query hooks — one file per domain
  engine/        Insight engine — pure function, no side effects
  components/    Reusable atoms + chat subsystem
  views/         One file per nav item
  App.jsx        View routing (hash-based, no library)
```

---

## Backend Additions

### 1. `services/mail_service.py` (new file)

Standalone SMTP service. No FastAPI dependency. Called by the MCP tool and
the FastAPI router. Uses standard library `smtplib` only — no new pip install.

```python
# services/mail_service.py

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

def _get_smtp_cfg() -> dict:
    return {
        "host":     os.environ["SMTP_HOST"],
        "port":     int(os.environ.get("SMTP_PORT", "587")),
        "user":     os.environ["SMTP_USER"],
        "password": os.environ["SMTP_PASSWORD"],
    }

def build_churn_email_body(
    vendor: str,
    department: Optional[str],
    candidates: list[dict],
    dollar_impact: float,
) -> str:
    """Returns an HTML string for the churn notification email."""
    dept_label = f" / {department}" if department else ""
    rows = "".join(
        f"{c.get('license_id','')}{c.get('employee','')}"
        f"{c.get('department','')}{c.get('last_login','')}"
        f"${c.get('annual_value', 0):,.0f}"
        for c in candidates
    )
    return f"""

[SaaS Spend] Churn Notification — {vendor}{dept_label}
The following {len(candidates)} licenses have been identified as
inactive. Total recoverable annual value: ${dollar_impact:,.0f}.

  
    License IDEmployeeDepartment
    Last LoginAnnual Value
  
  {rows}


  Generated by SaaS Spend Management Platform · Phase 1E


""".strip()

def send_churn_notification(
    vendor: str,
    department: Optional[str],
    candidates: list[dict],
    dollar_impact: float,
    preview_only: bool = True,
) -> dict:
    """
    If preview_only=True: return subject + body + recipient without sending.
    If preview_only=False: send via SMTP and return confirmation.
    Recipient is always read from CHURN_NOTIFICATION_RECIPIENT env var.
    """
    recipient = os.environ["CHURN_NOTIFICATION_RECIPIENT"]
    dept_label = f" / {department}" if department else ""
    subject    = f"[SaaS Spend] Churn notification — {vendor}{dept_label}"
    body_html  = build_churn_email_body(vendor, department, candidates, dollar_impact)

    if preview_only:
        return {
            "preview":          True,
            "recipient":        recipient,
            "subject":          subject,
            "body_preview":     body_html[:400] + "…",
            "candidate_count":  len(candidates),
            "dollar_impact":    dollar_impact,
        }

    cfg = _get_smtp_cfg()
    msg = MIMEMultipart("alternative")
    msg["From"]    = cfg["user"]
    msg["To"]      = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(body_html, "html"))

    with smtplib.SMTP(cfg["host"], cfg["port"]) as server:
        server.ehlo()
        server.starttls()
        server.login(cfg["user"], cfg["password"])
        server.sendmail(cfg["user"], recipient, msg.as_string())

    return {
        "preview":         False,
        "sent":            True,
        "recipient":       recipient,
        "subject":         subject,
        "candidate_count": len(candidates),
        "dollar_impact":   dollar_impact,
    }
```

**Error handling contract:** `smtplib.SMTPException` propagates up to the
caller (FastAPI router or MCP tool), which catches it and returns a structured
error dict. Do not swallow the exception inside `mail_service.py`.

### 2. `api/routers/triggers.py` (new file)

New file only. `api/main.py` gains one line: `app.include_router(triggers.router)`.

#### Endpoints

```
POST /triggers/ghost-ticket
POST /triggers/reclamation
POST /triggers/rightsizing
```

#### Schemas — `api/schemas/triggers.py` (new file)

```python
from pydantic import BaseModel
from typing import Optional

class TriggerRequest(BaseModel):
    vendor: str
    department: Optional[str] = None
    confirmed: bool = False

class TriggerResponse(BaseModel):
    preview: bool
    vendor: str
    department: Optional[str]
    count: int
    dollar_impact: float
    message: str
    status: Optional[str] = None           # "dispatched" when confirmed=True
    integration: Optional[str] = None      # "jira" | "slack" | "csv"
    ticket_id: Optional[str] = None
    recommendation_id: Optional[str] = None
    db_status: Optional[str] = None        # "pending"
```

#### Implementation pattern

```python
# api/routers/triggers.py

from fastapi import APIRouter
from api.schemas.triggers import TriggerRequest, TriggerResponse
from processing.context_builder import build_context
from processing.ghost_processor import get_ghost_summary
from mcp_server.actions import dispatch_jira
from db.recommendations_table import insert_recommendation

router = APIRouter(prefix="/triggers", tags=["triggers"])

@router.post("/ghost-ticket", response_model=TriggerResponse)
def ghost_ticket(req: TriggerRequest):
    ctx = build_context(vendor=req.vendor)
    rows = get_ghost_summary(ctx)
    # Filter by department if supplied; sum counts and dollar impacts
    if req.department:
        rows = [r for r in rows if r.get("department") == req.department]
    ghost_count   = sum(r.get("ghost_count", 0) for r in rows)
    dollar_impact = sum(r.get("annual_waste", 0.0) for r in rows)

    if not req.confirmed:
        return TriggerResponse(
            preview=True,
            vendor=req.vendor, department=req.department,
            count=ghost_count, dollar_impact=dollar_impact,
            message=(f"Found {ghost_count} ghost licenses worth "
                     f"${dollar_impact:,.0f}/yr. "
                     "Call again with confirmed=true to create Jira ticket."),
        )

    result = dispatch_jira({
        "vendor": req.vendor, "ghost_count": ghost_count,
        "dollar_impact": dollar_impact, "department": req.department,
    })
    rec_id = insert_recommendation({
        "type": "ghost_ticket", "vendor": req.vendor,
        "department": req.department, "affected_records": [],
        "dollar_impact": dollar_impact,
    })
    return TriggerResponse(
        preview=False,
        vendor=req.vendor, department=req.department,
        count=ghost_count, dollar_impact=dollar_impact,
        message=result.get("message", "Dispatched."),
        status="dispatched", integration=result.get("integration"),
        ticket_id=result.get("ticket_id"),
        recommendation_id=rec_id, db_status="pending",
    )
```

Reclamation and rightsizing endpoints follow the same pattern, calling
`dispatch_csv` and `dispatch_slack` respectively.

#### Test gate

`tests/test_api_triggers.py` — 6 tests:
- `POST /triggers/ghost-ticket` `confirmed=false` → `preview: true`, `count > 0`
- `POST /triggers/ghost-ticket` `confirmed=true`  → `status: "dispatched"`, `recommendation_id` not None
- Same two for `/triggers/reclamation` and `/triggers/rightsizing`
- Full suite: **167 passed** (161 existing + 6 new)

### 3. `api/routers/mail.py` (new file)

`api/main.py` gains: `app.include_router(mail.router)`.

#### Endpoint

```
POST /mail/churn-notification
```

#### Schemas — `api/schemas/mail.py` (new file)

```python
from pydantic import BaseModel
from typing import Optional

class ChurnMailRequest(BaseModel):
    vendor: str
    department: Optional[str] = None
    confirmed: bool = False

class ChurnMailResponse(BaseModel):
    preview: bool
    recipient: str
    subject: str
    body_preview: Optional[str] = None    # first 400 chars of HTML when preview=True
    candidate_count: int
    dollar_impact: float
    sent: Optional[bool] = None           # True when preview=False and send succeeded
    recommendation_id: Optional[str] = None
    error: Optional[str] = None           # set if SMTP fails
```

#### Implementation

```python
# api/routers/mail.py

from fastapi import APIRouter
from api.schemas.mail import ChurnMailRequest, ChurnMailResponse
from processing.context_builder import build_context
from processing.reclamation_processor import get_reclamation_candidates
from services.mail_service import send_churn_notification
from db.recommendations_table import insert_recommendation
import smtplib

router = APIRouter(prefix="/mail", tags=["mail"])

@router.post("/churn-notification", response_model=ChurnMailResponse)
def churn_notification(req: ChurnMailRequest):
    ctx        = build_context(vendor=req.vendor)
    candidates = get_reclamation_candidates(ctx)
    if req.department:
        candidates = [c for c in candidates if c.get("department") == req.department]
    dollar_impact = sum(c.get("annual_value", 0.0) for c in candidates)

    try:
        result = send_churn_notification(
            vendor=req.vendor,
            department=req.department,
            candidates=candidates,
            dollar_impact=dollar_impact,
            preview_only=(not req.confirmed),
        )
    except smtplib.SMTPException as exc:
        return ChurnMailResponse(
            preview=False, recipient="", subject="", candidate_count=0,
            dollar_impact=0, sent=False, error=str(exc),
        )

    rec_id = None
    if req.confirmed and result.get("sent"):
        rec_id = insert_recommendation({
            "type": "churn_mail", "vendor": req.vendor,
            "department": req.department, "affected_records": candidates,
            "dollar_impact": dollar_impact,
        })

    return ChurnMailResponse(
        preview=result["preview"],
        recipient=result["recipient"],
        subject=result["subject"],
        body_preview=result.get("body_preview"),
        candidate_count=result["candidate_count"],
        dollar_impact=result["dollar_impact"],
        sent=result.get("sent"),
        recommendation_id=rec_id,
    )
```

#### Test gate

`tests/test_mail_service.py` — 2 tests (monkeypatch `smtplib.SMTP`):
- `send_churn_notification(..., preview_only=True)` → `preview: True`, no SMTP call made
- `send_churn_notification(..., preview_only=False)` → `sent: True`, `sendmail` called once

`tests/test_api_mail.py` — 2 tests:
- `POST /mail/churn-notification` `confirmed=false` → `preview: true`
- `POST /mail/churn-notification` `confirmed=true` (SMTP mocked) → `sent: true`, `recommendation_id` not None

Full suite after both: **171 passed** (167 + 4 new mail tests).

### 4. New MCP tool — `send_churn_notification` in `mcp_server/tools.py`

Add alongside the existing write tools. Delegates to `mail_service`.

```python
@mcp.tool()
async def send_churn_notification(
    vendor: str,
    department: Optional[str] = None,
    confirmed: bool = False,
) -> dict:
    """Send a churn notification email to the configured recipient listing
    inactive license holders for a vendor (and optionally a department).

    Use confirmed=False to preview email content without sending.
    Use confirmed=True to dispatch the email via SMTP.
    Recipient address is configured server-side — never passed by the caller.
    """
    from services.mail_service import send_churn_notification as _send
    from processing.context_builder import build_context
    from processing.reclamation_processor import get_reclamation_candidates
    from db.recommendations_table import insert_recommendation

    ctx        = build_context(vendor=vendor)
    candidates = get_reclamation_candidates(ctx)
    if department:
        candidates = [c for c in candidates if c.get("department") == department]
    dollar_impact = sum(c.get("annual_value", 0.0) for c in candidates)

    result = _send(vendor=vendor, department=department, candidates=candidates,
                   dollar_impact=dollar_impact, preview_only=(not confirmed))

    if confirmed and result.get("sent"):
        insert_recommendation({
            "type": "churn_mail", "vendor": vendor,
            "department": department, "affected_records": candidates,
            "dollar_impact": dollar_impact,
        })

    return result
```

---

## Frontend Tech Stack

| Concern | Library | Version |
|---|---|---|
| Build | Vite | 5.x |
| UI framework | React | 18.x |
| Styling | Tailwind CSS | 3.x |
| Server state | TanStack React Query | 5.x |
| Global state | Zustand | 4.x |
| HTTP | Axios | 1.x |
| Charts | Recharts | 2.x |
| Icons | Lucide React | latest |
| Class merging | clsx + tailwind-merge | latest |

No component library — all UI is hand-built against the dark industrial design
tokens defined below.

### Design tokens — `tailwind.config.js`

```js
// extend.colors
{
  bg:              "#080A0F",
  surface:         "#0E1118",
  "surface-hover": "#141822",
  border:          "#1C2232",
  "border-accent": "#2A3044",
  amber:           "#F59E0B",
  "amber-dim":     "#92610A",
  danger:          "#EF4444",
  "danger-dim":    "#7F1D1D",
  success:         "#22D3A5",
  "success-dim":   "#064E3B",
  info:            "#60A5FA",
  "info-dim":      "#1E3A5F",
  "text-primary":  "#E8ECFF",
  "text-secondary":"#6B7499",
  "text-dim":      "#2D3458",
}

// extend.fontFamily
{
  display: ["Syne", "sans-serif"],
  mono:    ["JetBrains Mono", "monospace"],
  sans:    ["Plus Jakarta Sans", "sans-serif"],
}
```

Google Fonts URL in `index.html`:
```
https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800
  &family=JetBrains+Mono:wght@400;500
  &family=Plus+Jakarta+Sans:wght@300;400;500;600
  &display=swap
```

---

## File Index — Complete

### Backend additions

```
services/
└── mail_service.py              ← SMTP sender, preview/send, reads env vars

api/
├── main.py                      ← +2 lines: include triggers.router, mail.router
├── routers/
│   ├── triggers.py              ← POST /triggers/ghost-ticket|reclamation|rightsizing
│   └── mail.py                  ← POST /mail/churn-notification
└── schemas/
    ├── triggers.py              ← TriggerRequest, TriggerResponse
    └── mail.py                  ← ChurnMailRequest, ChurnMailResponse

mcp_server/
└── tools.py                     ← +1 tool: send_churn_notification

tests/
├── test_api_triggers.py         ← 6 tests
├── test_api_mail.py             ← 2 tests
└── test_mail_service.py         ← 2 tests
```

### Frontend root

```
frontend/
├── index.html                   ← Google Fonts link + #root mount
├── vite.config.js               ← /api proxy → :8000, /llm proxy → :11434
├── tailwind.config.js           ← tokens + content globs
├── postcss.config.js
└── package.json
```

### `src/`

```
src/
├── main.jsx                     ← ReactDOM.createRoot, QueryClientProvider
├── App.jsx                      ← AppShell + view routing (object map, no library)
│
├── api/
│   ├── client.js                ← Axios instance, baseURL=/api, error interceptor
│   ├── endpoints.js             ← typed async function per GET endpoint
│   ├── triggerClient.js         ← postTrigger(type, req) — maps type → path
│   ├── mailClient.js            ← postChurnMail(req)
│   └── chat.js                  ← sendMessage(), buildPlannerSystem(), DEFAULT_CFG
│                                   two-step LLM call + full guardrails
│
├── store/
│   └── useAppStore.js           ← vendor, department, activeView,
│                                   chatOpen, pendingConfirm, dispatchedRecs
│
├── hooks/
│   ├── useHealth.js
│   ├── useGhost.js              ← exports useGhostSummary + useGhostDetail
│   ├── useReclamation.js
│   ├── useUtilization.js
│   ├── useRenewal.js
│   ├── useForecast.js           ← Promise.all for demand + momentum
│   ├── useTrueUp.js
│   └── useTrigger.js            ← preview/confirm state machine with error handling
│
├── engine/
│   └── insightEngine.js         ← pure: (vendor, view, liveData) → InsightConfig
│
├── components/
│   ├── layout/
│   │   ├── AppShell.jsx
│   │   ├── Sidebar.jsx
│   │   └── TopBar.jsx
│   ├── shared/
│   │   ├── KPICard.jsx
│   │   ├── InsightBanner.jsx    ← single-action banner
│   │   ├── TwoActionBanner.jsx  ← two-action variant (RenewalView expired cards)
│   │   ├── ConfirmModal.jsx
│   │   ├── StatusBadge.jsx
│   │   ├── DataTable.jsx
│   │   ├── SkeletonRow.jsx
│   │   └── EmptyState.jsx
│   └── chat/
│       ├── ChatPanel.jsx
│       ├── ChatMessage.jsx
│       ├── ActionCard.jsx
│       └── QuickPrompts.jsx
│
└── views/
    ├── OverviewView.jsx
    ├── GhostView.jsx
    ├── ReclamationView.jsx      ← includes "Send Churn Mail" button
    ├── UtilizationView.jsx
    ├── RenewalView.jsx
    ├── ForecastView.jsx
    └── RecommendationsView.jsx
```

---

## Component Specifications

### `AppShell.jsx`

Outer flex row: `Sidebar (220px) | main (flex-1, overflow-y-auto) | ChatPanel (380px fixed right, z-50)`.

`margin-right` on the main area shifts by 380px when `chatOpen=true`.
CSS `transition: margin-right 0.3s ease`.

View component is selected by a plain `const VIEWS = { overview: OverviewView, ... }` map.
`const ViewComponent = VIEWS[activeView]`. No router library.

### `Sidebar.jsx`

Props: none (reads Zustand).

| id | label | icon (Lucide) | badge |
|---|---|---|---|
| `overview` | Overview | `LayoutDashboard` | — |
| `ghost` | Ghost Licenses | `Ghost` | ghost total, danger |
| `reclamation` | Reclamation | `RefreshCw` | candidate count, amber |
| `utilization` | Utilization | `PieChart` | — |
| `renewal` | Renewal Pressure | `Zap` | expired count, danger |
| `forecast` | Demand Forecast | `TrendingUp` | — |
| `recommendations` | Recommendations | `Sparkles` | pending count, amber |

Active: `border-l-2 border-amber bg-amber/10 text-amber`.
Inactive: `text-text-secondary hover:text-text-primary`.

Bottom: `audit_date` + `fetched_at` from health query. Green/red dot on health status.

### `TopBar.jsx`

Left: page title | divider | vendor `<select>` (from `active_vendors` + "All") | department `<select>` (hardcoded set).  
Right: "AI Assistant" toggle (`bg-amber text-black` when open, else bordered).

### `KPICard.jsx`

```ts
interface KPICardProps {
  title: string;
  value: string;          // caller pre-formats
  sub?: string;
  trend?: number;         // positive = worse (danger), negative = better (success)
  accentColor: "amber" | "danger" | "success" | "info";
  onClick?: () => void;
}
```

`border-l-[3px]` in accent color. Title: `font-mono text-[11px] uppercase tracking-widest text-text-secondary`. Value: `font-mono text-2xl text-text-primary`.

### `InsightBanner.jsx` — single primary action

```ts
interface InsightBannerProps {
  level:  "critical" | "warning" | "info";
  icon:   string;
  title:  string;
  body:   string;
  primaryAction?: {
    label: string;
    // null = navigate only, no trigger
    triggerType: "ghost_ticket" | "reclamation" | "rightsizing" | "churn_mail" | null;
    data: { vendor?: string; department?: string };
  };
  secondaryAction?: {
    label: string;
    triggerType: "ghost_ticket" | "reclamation" | "rightsizing" | "churn_mail" | null;
    data: { vendor?: string; department?: string };
  };
}
```

Level colors: `critical → danger`, `warning → amber`, `info → info`.
Background `bg-{color}/[0.07]`, left border `border-l-2 border-{color}`.

Both `primaryAction` and `secondaryAction` buttons, when clicked, call:
```js
useAppStore.getState().setPendingConfirm({
  type: action.triggerType,
  vendor: action.data.vendor,
  department: action.data.department ?? null,
});
```

`InsightBanner` does **not** import or call `useTrigger`. It sets `pendingConfirm`
in the Zustand store, which causes `ConfirmModal` (always mounted in `AppShell`)
to open. This is the same pattern used by `ActionCard`.

### `TwoActionBanner.jsx`

Used only in `RenewalView` for expired contract alert cards. Same visual as
`InsightBanner` but always `level="critical"` and always has exactly two
action buttons side-by-side. Props are narrower:

```ts
interface TwoActionBannerProps {
  title:    string;
  body:     string;
  actions:  [
    { label: string; triggerType: string; data: object },
    { label: string; triggerType: string; data: object },
  ];
}
```

### `ConfirmModal.jsx`

Always mounted in `AppShell`, visibility driven by `pendingConfirm !== null`.

**Frontend-side `PendingConfirm` shape** (distinct from Python `TriggerRequest`):

```ts
interface PendingConfirm {
  type:        "ghost_ticket" | "reclamation" | "rightsizing" | "churn_mail";
  vendor:      string;
  department?: string | null;
}
```

The `type` field is what `ConfirmModal` uses to select which client function
to call (`triggerClient.postTrigger` vs `mailClient.postChurnMail`).

Lifecycle:
1. On mount (when `pendingConfirm` becomes non-null): call the appropriate
   client with `confirmed: false` → render preview grid.
2. "Cancel": `clearConfirm()`.
3. "Dispatch →": call with `confirmed: true`.
4. Success: show `recommendation_id` + "Done" button → `clearConfirm()` + `addDispatchedRec(result)`.
5. Error: red error text + "Retry" button (re-runs step 3).

### `DataTable.jsx`

```ts
interface Column {
  key:       string;
  label:     string;
  width?:    string;
  render?:   (value: any, row: object) => ReactNode;
  sortable?: boolean;
}

interface DataTableProps {
  columns:       Column[];
  rows:          object[];
  loading?:      boolean;     // shows SkeletonRow × 5
  emptyMessage?: string;
}
```

Sort state is local (`useState`). Click header → toggle asc/desc. No API call.

### `ChatPanel.jsx`

Fixed right drawer, 380px, `z-[100]`. Slide: `right: chatOpen ? "0" : "-400px"`.

```jsx
// ChatPanel.jsx — sendMessage handler

const handleSend = async () => {
  if (!input.trim() || loading) return;
  const userText = input.trim();
  setInput("");
  setMessages(prev => [...prev, { role: "user", content: userText, action: null }]);
  setLoading(true);

  const liveData = assembleLiveData();   // reads current React Query cache
  try {
    const { text, action } = await sendMessage(
      [...messages, { role: "user", content: userText }],
      liveData,
    );
    setMessages(prev => [...prev, { role: "assistant", content: text, action }]);
  } catch (err) {
    setMessages(prev => [...prev, {
      role: "assistant",
      content: `Connection error: ${err.message}. Is the LLM server running?`,
      action: null,
    }]);
  } finally {
    setLoading(false);
  }
};
```

`assembleLiveData()` is a local helper that reads from the React Query
`queryClient` cache. It does **not** trigger new network requests.

### `ActionCard.jsx`

Rendered below an assistant message when `message.action !== null`.

"Confirm & Dispatch →" button:
```js
useAppStore.getState().setPendingConfirm(message.action);
```

Does not call `useTrigger` or any API directly.

---

## Chatbot — `src/api/chat.js`

All LLM communication lives in this file. No LLM logic anywhere else in the frontend.

### Guardrails

The two-step call (planning → answer) is the **maximum** per `sendMessage`
invocation. There are no further loops, no retry on unexpected output, no
recursive calls.

```
Turn budget:    MAX 2 LLM calls per sendMessage() — plan turn + optional explain turn
Timeout:        15 000 ms per call (AbortController)
Loop guard:     No call is ever made from within a postChat response handler
Fallback rule:  ANY unexpected JSON shape or parse failure → skip to text fallback
                immediately; do not call the LLM again to recover
Input guard:    Action fields validated before ActionCard renders (see below)
```

### `DEFAULT_CFG`

Defined **once** here. The ChatPanel section references this; it does not
re-define it.

```js
export const DEFAULT_CFG = {
  baseUrl:     import.meta.env.VITE_LLM_BASE_URL ?? "http://127.0.0.1:11434",
  model:       import.meta.env.VITE_LLM_MODEL    ?? "qwen2.5:14b",
  temperature: 0.1,
  num_ctx:     8192,
  num_predict: 1024,
  timeoutMs:   15_000,
};
```

### `postChat(messages, { format, cfg })`

```js
async function postChat(messages, { format, cfg }) {
  const controller = new AbortController();
  const tid = setTimeout(() => controller.abort(), cfg.timeoutMs);

  try {
    const body = {
      model:   cfg.model,
      stream:  false,
      messages,
      options: {
        temperature:  cfg.temperature,
        num_ctx:      cfg.num_ctx,
        num_predict:  cfg.num_predict,
      },
    };
    if (format) body.format = format;

    const res = await fetch("/llm/api/chat", {   // proxied — no CORS issue
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify(body),
      signal:  controller.signal,
    });

    if (!res.ok) throw new Error(`LLM server HTTP ${res.status}`);
    const data = await res.json();
    return data.message?.content ?? "";
  } finally {
    clearTimeout(tid);
  }
}
```

The URL is `/llm/api/chat` — always goes through the Vite proxy. Never
call `:11434` directly from the browser.

### `sendMessage(history, liveData, cfg = DEFAULT_CFG)`

```js
export async function sendMessage(history, liveData, cfg = DEFAULT_CFG) {
  // ── Turn 1: planning (JSON only) ─────────────────────────────────────────
  const plannerSystem = buildPlannerSystem(liveData);
  const planMessages  = [{ role: "system", content: plannerSystem }, ...history];

  let rawPlan;
  try {
    rawPlan = await postChat(planMessages, { format: "json", cfg });
  } catch (err) {
    // Timeout or network failure on planning turn — surface immediately
    throw err;
  }

  // ── Parse plan — strict fallback, no retry ───────────────────────────────
  let plan;
  try {
    const candidate = JSON.parse(rawPlan);
    // Validate it actually has the shape we expect
    if (typeof candidate?.phase === "string") {
      plan = candidate;
    } else {
      plan = { phase: "answer", text: rawPlan };   // malformed JSON object
    }
  } catch {
    plan = { phase: "answer", text: rawPlan };      // not JSON at all
  }

  // ── Turn 1 result: direct answer ─────────────────────────────────────────
  if (plan.phase === "answer") {
    return { text: plan.text ?? rawPlan, action: null };
  }

  // ── Turn 1 result: action ────────────────────────────────────────────────
  if (plan.phase === "action") {
    // Validate required action fields before proceeding to Turn 2
    const validTypes = ["ghost_ticket", "reclamation", "rightsizing", "churn_mail"];
    const activeVendors = liveData.health?.active_vendors ?? [];

    if (!validTypes.includes(plan.type)) {
      // Model invented an unknown action type — treat as plain answer
      return { text: rawPlan, action: null };
    }
    if (activeVendors.length > 0 && !activeVendors.includes(plan.vendor)) {
      // Model hallucinated a vendor name — return error text, no ActionCard
      return {
        text: `I can't trigger that — "${plan.vendor}" is not a recognised vendor. `
            + `Valid vendors: ${activeVendors.join(", ")}.`,
        action: null,
      };
    }

    // ── Turn 2: plain-language explanation (max 1 sentence) ─────────────
    const actionSummary = JSON.stringify(plan, null, 2);
    const finalMessages = [
      {
        role: "system",
        content:
          "You are the SaaS spend assistant. Write ONE plain-English sentence "
        + "explaining what the action will do and the dollar saving. No JSON.",
      },
      ...history,
      { role: "user", content: `Action planned:\n${actionSummary}\nExplain briefly.` },
    ];

    let explanation = "";
    try {
      explanation = await postChat(finalMessages, { cfg });
    } catch {
      // Turn 2 failure is non-fatal — still show the ActionCard with empty text
      explanation = "Action ready to dispatch.";
    }

    return {
      text: explanation,
      action: {
        type:       plan.type,
        vendor:     plan.vendor,
        department: plan.department ?? null,
        count:      typeof plan.count === "number" ? plan.count : 0,
        impact:     typeof plan.impact === "number" ? plan.impact : 0,
        message:    typeof plan.message === "string" ? plan.message : "",
      },
    };
  }

  // ── Unknown phase — never loop, just return raw text ────────────────────
  return { text: rawPlan, action: null };
}
```

**Loop prevention summary:**
- `postChat` is called at most twice per `sendMessage` invocation (turn 1 + turn 2).
- Neither `postChat` nor its callers call `sendMessage` recursively.
- Turn 2 failure is non-fatal and does not trigger a retry.
- Unknown JSON phases fall through to text, no retry.
- Vendor name validation prevents ActionCards with hallucinated vendor names.

### `buildPlannerSystem(liveData)`

```js
export function buildPlannerSystem(liveData) {
  const { health, ghost, trueup, utilization, renewal } = liveData;
  return `
You are the planning component for a SaaS spend assistant.
Reply with a SINGLE JSON object only — no markdown, no text outside the object.

Schema (pick exactly one):

{"phase":"answer","text":""}
  — use for all data questions (ghost counts, utilization, renewals, forecast).

{"phase":"action","type":"ghost_ticket"|"reclamation"|"rightsizing"|"churn_mail",
 "vendor":"","department":"",
 "count":,"impact":,
 "message":""}
  — use ONLY when the user explicitly asks to raise a ticket, export, reclaim,
    rightsize, or send an email.

Rules:
- Vendor MUST be one of: ${health?.active_vendors?.join(", ") ?? "Atlassify, Nexaflow, Cloudora"}
  Do NOT normalise, correct, spell-check, or infer vendor names.
  If the user types a name not in this list, respond with phase:"answer" explaining
  the valid vendors.
- "churn_mail" sends a notification email to the configured recipient listing
  inactive license holders. Use it when the user asks to notify, email, or alert
  about churn/inactive users.
- For count and impact: use the figures from LIVE DATA below. If unavailable, use 0.
- Lead text answers with dollar impact.

LIVE PORTFOLIO DATA (audit: ${health?.audit_date ?? "unknown"}):

${renderVendorBlock("Atlassify", ghost, trueup, utilization, renewal)}
${renderVendorBlock("Nexaflow",  ghost, trueup, utilization, renewal)}
${renderVendorBlock("Cloudora",  ghost, trueup, utilization, renewal)}

PORTFOLIO TOTALS:
- Ghost licenses: ${ghost?.All?.total ?? "?"} | Annual waste: $${fmtK(ghost?.All?.annual_waste)}
- True-up exposure: $${fmtK(trueup?.All?.exposure)}
- Utilization: ${fmtPct(utilization?.All)}
- Expired contracts: ${(renewal?.All ?? []).filter(r => r.status === "expired")
                        .map(r => r.vendor).join(", ") || "none"}
`.trim();
}
```

`renderVendorBlock(vendor, ghost, trueup, utilization, renewal)` returns three
lines: ghost count + waste, utilization rate, contract status + expiry date.
Returns `""` when data is still loading.

`fmtK(n)` → `n == null ? "?" : (n/1000).toFixed(0) + "K"`.  
`fmtPct(n)` → `n == null ? "?" : (n * 100).toFixed(1) + "%"`.

### Quick Prompts per view

| view | chips |
|---|---|
| `overview` | "Portfolio waste summary", "Which contracts expired?", "Top savings opportunity" |
| `ghost` | "Ghost breakdown by department", "Raise Jira for Engineering ghosts", "How much can we reclaim?" |
| `reclamation` | "Show top candidates", "Export CSV for Nexaflow", "Send churn email for Atlassify" |
| `utilization` | "Which vendor has worst utilization?", "Seats we can cut right now" |
| `renewal` | "Which contracts need renewal?", "Nexaflow renewal risk", "Cloudora options" |
| `forecast` | "When will Atlassify hit capacity?", "Forecast for next 6 months" |
| `recommendations` | "What's still pending?", "Show dispatched tickets", "Total impact if all actioned" |

Clicking a chip sets the input value but does **not** auto-send. User presses Enter.

---

## Insight Engine — `engine/insightEngine.js`

Pure function. No React imports. No side effects.

```ts
interface InsightConfig {
  level:           "critical" | "warning" | "info";
  icon:            string;
  title:           string;
  body:            string;
  primaryAction:   ActionSpec | null;
  secondaryAction: ActionSpec | null;
}

interface ActionSpec {
  label:       string;
  triggerType: "ghost_ticket" | "reclamation" | "rightsizing" | "churn_mail" | null;
  data:        { vendor?: string; department?: string };
}
```

The function must return a valid `InsightConfig` for every `(vendor, view)` pair.
If live data is still loading, return:
```js
{ level:"info", title:"Loading data…", body:"", primaryAction:null, secondaryAction:null }
```

### Decision matrix

```
vendor = "All":
  expired = (renewal.All ?? []).filter(r => r.status === "expired")
  IF expired.length > 0:
    level    = "critical"
    title    = `Portfolio: ${expired.length} expired contracts + ${ghost.All.total} ghost licenses`
    body     = `$${fmtK(ghost.All.annual_waste)}/yr ghost waste · $${fmtK(trueup.All.exposure)} true-up exposure`
    primary  = { label:"Raise Ghost Tickets", triggerType:"ghost_ticket", data:{vendor:"Atlassify"} }
    secondary= { label:"Export Reclamation CSV", triggerType:"reclamation", data:{vendor:"All"} }
  ELSE:
    level    = "warning"
    title    = `Portfolio: $${fmtK(trueup.All.exposure)} true-up exposure across 3 vendors`
    body     = `Ghost waste: $${fmtK(ghost.All.annual_waste)}/yr. Utilization: ${fmtPct(util.All)}.`
    primary  = null,  secondary = null

vendor = "Atlassify":
  level    = "warning"
  title    = "Atlassify — overpaying detected"
  body     = `${ghost.Atlassify.total} ghost licenses ($${fmtK(ghost.Atlassify.annual_waste)}/yr).
              ${fmtPct(util.Atlassify)} utilization + $${fmtK(trueup.Atlassify.exposure)} true-up exposure.`
  primary  = view === "ghost"       ? { label:"Raise Jira Ticket", triggerType:"ghost_ticket",  data:{vendor:"Atlassify"} }
           : view === "reclamation" ? { label:"Export Reclamation CSV", triggerType:"reclamation", data:{vendor:"Atlassify"} }
           :                          null
  secondary= null

vendor = "Nexaflow" OR "Cloudora":
  level    = "critical"
  title    = `${vendor} contract EXPIRED — action required`
  body     = `Contract expired ${renewal[vendor][0].expiry}. ${ghost[vendor].total} ghost licenses
              accumulating $${fmtK(ghost[vendor].annual_waste)}/yr.`
  primary  = { label:"Raise Jira Ticket",      triggerType:"ghost_ticket", data:{vendor} }
  secondary= { label:"Export Reclamation CSV", triggerType:"reclamation",  data:{vendor} }
```

---

## Hooks — Data Fetching

All hooks use `useQuery` (TanStack React Query v5). Stale time: 60 s (matches
the backend context cache TTL). Retry: 2. Errors are handled at the view level.

### `buildParams(vendor, department)`

Used in every hook that accepts vendor/department. Defined once in `api/endpoints.js`,
imported by hooks.

```js
// api/endpoints.js

export function buildParams(vendor, department) {
  const p = {};
  if (vendor     && vendor     !== "All") p.vendor     = vendor;
  if (department && department !== "All") p.department = department;
  return p;
}
```

`"All"` is the UI sentinel meaning "no filter". It must never be sent to the
backend as a query param — it would cause a 422 (vendor validation failure).

### `useHealth.js`

```js
export function useHealth() {
  return useQuery({
    queryKey:  ["health"],
    queryFn:   () => api.get("/health").then(r => r.data),
    staleTime: 60_000,
  });
}
```

### `useGhost.js`

```js
export function useGhostSummary(vendor, department) {
  return useQuery({
    queryKey:  ["ghost", "summary", vendor, department],
    queryFn:   () => api.get("/ghost/summary",
                      { params: buildParams(vendor, department) }).then(r => r.data),
    staleTime: 60_000,
  });
}

export function useGhostDetail(vendor, department) {
  return useQuery({
    queryKey:  ["ghost", "detail", vendor, department],
    queryFn:   () => api.get("/ghost/detail",
                      { params: buildParams(vendor, department) }).then(r => r.data),
    staleTime: 60_000,
  });
}
```

### Pattern for remaining hooks

```
useReclamation(vendor, department, minScore=0.5)
  → GET /reclamation   params: buildParams(vendor,department) + {min_score}

useUtilization(vendor)
  → GET /utilization   params: buildParams(vendor, null)
  NOTE: department param is NOT supported by this endpoint — always omit it

useRenewal(vendor)
  → GET /renewal-pressure   params: buildParams(vendor, null)
  NOTE: department param is NOT supported by this endpoint — always omit it

useForecast(vendor, department, months=12)
  → Promise.all([
      GET /forecast/demand    params: buildParams(vendor,department) + {months},
      GET /forecast/momentum  params: buildParams(vendor, null) + {months},
    ])
  returns { demand, momentum }

useTrueUp(vendor)
  → GET /trueup/exposure   params: buildParams(vendor, null)
```

### `useTrigger.js`

```js
export function useTrigger() {
  const [preview,  setPreview]  = useState(null);
  const [result,   setResult]   = useState(null);
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState(null);

  const fetchPreview = async (type, req) => {
    setLoading(true); setError(null);
    try {
      const data = type === "churn_mail"
        ? await mailClient.postChurnMail({ ...req, confirmed: false })
        : await triggerClient.postTrigger(type, { ...req, confirmed: false });
      setPreview(data);
    } catch (err) {
      setError(err.message ?? "Preview failed.");
    } finally {
      setLoading(false);
    }
  };

  const dispatch = async (type, req) => {
    setLoading(true); setError(null);
    try {
      const data = type === "churn_mail"
        ? await mailClient.postChurnMail({ ...req, confirmed: true })
        : await triggerClient.postTrigger(type, { ...req, confirmed: true });
      setResult(data);
      useAppStore.getState().addDispatchedRec(data);
    } catch (err) {
      setError(err.message ?? "Dispatch failed.");
    } finally {
      setLoading(false);
    }
  };

  const reset = () => { setPreview(null); setResult(null); setError(null); };

  return { preview, result, loading, error, fetchPreview, dispatch, reset };
}
```

`ConfirmModal` owns the single `useTrigger` instance. Views and `ActionCard`
only write to Zustand `pendingConfirm`; they never call `useTrigger` directly.

---

## `api/triggerClient.js`

Maps the frontend `type` string to the correct FastAPI path.

```js
// api/triggerClient.js

import { api } from "./client.js";

const TYPE_TO_PATH = {
  ghost_ticket: "/triggers/ghost-ticket",
  reclamation:  "/triggers/reclamation",
  rightsizing:  "/triggers/rightsizing",
};

export async function postTrigger(type, req) {
  const path = TYPE_TO_PATH[type];
  if (!path) throw new Error(`Unknown trigger type: ${type}`);
  const res = await api.post(path, req);
  return res.data;
}
```

### `api/mailClient.js`

```js
// api/mailClient.js

import { api } from "./client.js";

export async function postChurnMail(req) {
  const res = await api.post("/mail/churn-notification", req);
  return res.data;
}
```

---

## `api/client.js`

```js
import axios from "axios";

export const api = axios.create({
  baseURL: "/api",     // Vite proxy rewrites to http://localhost:8000
  timeout: 30_000,
});

api.interceptors.response.use(
  r => r,
  err => {
    console.error("[API]", err.response?.status, err.config?.url, err.message);
    return Promise.reject(err);
  }
);
```

### `vite.config.js`

```js
export default {
  server: {
    proxy: {
      "/api": {
        target:      "http://localhost:8000",
        changeOrigin: true,
        rewrite:     path => path.replace(/^\/api/, ""),
      },
      "/llm": {
        target:      process.env.VITE_LLM_BASE_URL ?? "http://127.0.0.1:11434",
        changeOrigin: true,
        rewrite:     path => path.replace(/^\/llm/, ""),
      },
    },
  },
};
```

The `/llm` proxy solves the CORS problem. The LLM server at `:11434` does not
set `Access-Control-Allow-Origin` for `localhost:5173`. By routing through Vite,
the browser sees only `localhost:5173` as the origin.

---

## `store/useAppStore.js`

```js
import { create } from "zustand";

export const useAppStore = create((set) => ({
  vendor:          "All",
  department:      "All",
  activeView:      "overview",
  chatOpen:        false,
  pendingConfirm:  null,        // PendingConfirm | null (see ConfirmModal spec)
  dispatchedRecs:  [],

  setVendor:          v => set({ vendor: v }),
  setDepartment:      d => set({ department: d }),
  setView:            v => set({ activeView: v }),
  toggleChat:         () => set(s => ({ chatOpen: !s.chatOpen })),
  setChatOpen:        b => set({ chatOpen: b }),
  setPendingConfirm:  p => set({ pendingConfirm: p }),
  clearConfirm:       () => set({ pendingConfirm: null }),
  addDispatchedRec:   r => set(s => ({ dispatchedRecs: [r, ...s.dispatchedRecs] })),
}));
```

---

## View Specifications

### `OverviewView.jsx`

Hooks: `useHealth`, `useGhostSummary(vendor)`, `useGhostDetail(vendor, null)`,
`useTrueUp(vendor)`, `useUtilization(vendor)`, `useRenewal(vendor)`.

```
Row 1: KPICard × 4
Row 2: Ghost by Dept BarChart (from useGhostDetail) | Seat Utilization BarChart — 50/50
Row 3: Renewal DataTable — full width
```

**Ghost by Dept chart:** `useGhostDetail` returns rows keyed by department.
X-axis: dept name, abbreviated to 4 chars. Y-axis: count. `fill="#EF4444"`.

**Utilization chart:** for each vendor, two bars: `active` and `idle`.
- `active = Math.round(active_usage_rate * 100)`
- `idle   = 100 - active`
- `fill="#22D3A5"` for active, `fill="#EF4444" opacity={0.5}` for idle.

KPI cards:
- Ghost Licenses → `ghostSummary.total`, color=danger
- True-Up Exposure → `trueup.exposure`, color=amber
- Utilization Rate → `utilization.active_usage_rate`, color=`rate>0.7?success:amber`
- Expired Contracts → `renewal.filter(r=>r.status==="expired").length`, color=`n>0?danger:success`

### `GhostView.jsx`

Hooks: `useGhostSummary(vendor)`, `useGhostDetail(vendor, department)`.

KPIs: Total Ghost | Annual Waste | Monthly Burn (`annual_waste / 12`).

DataTable columns: Department | Ghost Count | Annual Waste | Avg per License | Priority bar.

"Raise Jira Ticket" button (top-right of table):
```js
useAppStore.getState().setPendingConfirm({
  type: "ghost_ticket",
  vendor: vendor === "All" ? "Atlassify" : vendor,
  department: department === "All" ? null : department,
});
```

### `ReclamationView.jsx`

Hook: `useReclamation(vendor, department, minScore)`.

KPIs: Candidates | Recoverable Value (sum of `annual_value`) | Avg Score.

Action buttons row (above table):
- `Export CSV` (amber outlined) → `setPendingConfirm({ type:"reclamation", vendor, department })`
- `Send Confirmation Emails` (success filled) → `setPendingConfirm({ type:"rightsizing", vendor, department })`
- `Send Churn Notification` (info outlined) → `setPendingConfirm({ type:"churn_mail", vendor, department })`

DataTable columns: License ID | Vendor | Employee | Dept | Score | Annual Value | Last Login.
Score coloring: ≥0.9=danger, ≥0.8=amber, else text-primary.

### `UtilizationView.jsx`

Hook: `useUtilization(vendor)`.

The API returns `active_usage_rate` (a float 0–1). Derive `idle_pct` in component:

```js
const usedPct = Math.round((data.active_usage_rate ?? 0) * 100);
const idlePct = 100 - usedPct;
```

KPIs: Overall Rate | Active Seats (`active_seats` field) | Idle Seats (`total_seats - active_seats`).

Chart: `BarChart` with two bars per row — `usedPct` and `idlePct`. Same colors as Overview.

Below chart: DataTable with Active / Idle / Total / Rate per vendor.

### `RenewalView.jsx`

Hook: `useRenewal(vendor)`.

For each row where `status === "expired"`, render a `TwoActionBanner`:
```js

```

Below alert cards: full renewal DataTable.  
Columns: Vendor | Status | Expiry | Seats | Annual Value | Hires Before Deadline | Days Overdue.  
Days Overdue: `Math.max(0, dayjs().diff(dayjs(row.expiry_date), "day"))`. Use `Date` math, not a library.

### `ForecastView.jsx`

Hook: `useForecast(vendor, department, months)`.

Months slider: local `useState(12)`, range 3–24, rendered above the chart.

`ForecastUnavailableResult` rows (`available: false`) → `EmptyState` with `reason`.
If all momentum rows unavailable → replace chart with `EmptyState`. No throw.

Chart: `ComposedChart` with:
- `Area` for confidence band: `dataKey="upper"`, `fill="#60A5FA"`, `fillOpacity={0.15}`, no stroke
- `Area` for band floor: `dataKey="lower"`, `fill="#080A0F"`, `stroke="none"` (masks the band bottom)
- `Line` for momentum: `dataKey="procurement_momentum_forecast"`, `stroke="#F59E0B"`, `strokeWidth={2}`
- `Line` for capacity: `dataKey="contracted_capacity"`, `stroke="#EF4444"`, `strokeDasharray="5 5"`, `dot={false}`

Below chart: demand DataTable — `forecast_month`, `vendor`, `sku`,
`expected_new_licenses`, `pipeline_data_available`.

### `RecommendationsView.jsx`

Data: `SEED_RECS` (3 hardcoded records from Phase 1D) merged with
`dispatchedRecs` from Zustand. Newest first.

```js
const SEED_RECS = [
  { id:"rec-001", type:"ghost_ticket",    vendor:"Atlassify", dept:"Engineering",
    count:312, impact:18240,  status:"pending",    date:"2026-05-14" },
  { id:"rec-002", type:"reclamation",     vendor:"Nexaflow",  dept:"Marketing",
    count:28,  impact:67200,  status:"pending",    date:"2026-05-14" },
  { id:"rec-003", type:"rightsizing",     vendor:"Cloudora",  dept:"Operations",
    count:15,  impact:54000,  status:"dispatched", date:"2026-05-13" },
];
```

KPIs: Pending | Dispatched | Total Impact.

DataTable: ID | Type | Vendor | Dept | Count | Impact | Status | Date.

`GET /recommendations` is Phase 2 scope — this view is session-only.

---

## Intentional V1 Constraints (not bugs)

1. **No authentication.** Backend is localhost only.

2. **KPICard trend values are static deltas** for V1 (+12%, –3%, etc.). A
   `/trueup/trend` endpoint for real deltas is Phase 2 scope.

3. **RecommendationsView is session-only.** Refresh resets to seed.
   `GET /recommendations` is Phase 2.

4. **Department filter is omitted for `/utilization` and `/renewal-pressure`.**
   `buildParams` already handles this — caller passes `null` for department on
   those hooks.

5. **Forecast months slider is local to `ForecastView`.** Does not affect TopBar.

6. **Chat messages are not persisted.** Session memory only.

7. **LLM server must be running independently.** If unreachable, `ChatPanel`
   catches the error and shows inline text. Dashboard continues working.

8. **Churn mail sends to one recipient only (Phase 1E).** Bulk per-user
   sending is Phase 2 scope. The single recipient is read from `.env` at
   send time — never hardcoded, never passed by the frontend caller.

---

## Build Order

Do not begin step N+1 until step N's gate passes.

| Step | Scope | Gate |
|------|-------|------|
| 1a | `services/mail_service.py` | `tests/test_mail_service.py` — 2 tests pass |
| 1b | `api/schemas/triggers.py` + `api/routers/triggers.py` + register in `main.py` | `tests/test_api_triggers.py` — 6 tests pass · suite: 169 |
| 1c | `api/schemas/mail.py` + `api/routers/mail.py` + register in `main.py` + MCP tool | `tests/test_api_mail.py` — 2 tests pass · suite: **171 passed** |
| 2 | `frontend/` scaffold: Vite 5 + React 18 + Tailwind 3 + all packages | `npm run dev` starts · blank page · no console errors |
| 3 | `tailwind.config.js` tokens + `index.html` font link | All token classes resolve in DevTools |
| 4 | `store/useAppStore.js` + `api/client.js` + `vite.config.js` proxy (both `/api` and `/llm`) | `api.get("/health")` in console returns `{audit_date, active_vendors}` · `/llm/api/tags` returns models list |
| 5 | `AppShell.jsx` + `Sidebar.jsx` + `TopBar.jsx` (static) | Layout renders · sidebar + topbar visible · no data needed |
| 6 | `useHealth.js` → health dot + vendor list | Green dot when backend running · vendor select from API |
| 7 | All read hooks + `buildParams` | Each hook returns data in network tab · "All" sends no vendor param |
| 8 | `KPICard` + `DataTable` + `SkeletonRow` + `StatusBadge` + `EmptyState` | Components render with hardcoded props |
| 9 | `OverviewView.jsx` with all 5 hooks + both charts | Ghost dept chart populated from `useGhostDetail` · utilization bars show `active_usage_rate` derived correctly |
| 10 | `insightEngine.js` + `InsightBanner.jsx` + `TwoActionBanner.jsx` | Banner renders above Overview · changes on vendor switch · secondary action button visible |
| 11 | `api/triggerClient.js` + `api/mailClient.js` + `useTrigger.js` + `ConfirmModal.jsx` | Clicking banner primary action → modal opens with preview · Dispatch → `recommendation_id` shown · error path shows retry button |
| 12 | `GhostView.jsx` | "Raise Jira Ticket" → ConfirmModal · dept table from `useGhostDetail` |
| 13 | `ReclamationView.jsx` | All 3 action buttons open ConfirmModal with correct types including `churn_mail` |
| 14 | `UtilizationView.jsx` + `RenewalView.jsx` | Utilization bars computed from `active_usage_rate` · expired `TwoActionBanner` cards in Renewal |
| 15 | `ForecastView.jsx` | Chart renders for Atlassify · `EmptyState` for expired vendors |
| 16 | `RecommendationsView.jsx` | Seed records + dispatched records from step 11 visible |
| 17 | `chat.js` + `ChatPanel.jsx` + `ChatMessage.jsx` + `QuickPrompts.jsx` | Panel slides open · message sent · LLM server responds · reply appears |
| 18 | `ActionCard.jsx` + chat → ConfirmModal bridge | "Raise Jira for Atlassify Engineering" → ActionCard → ConfirmModal → dispatch → rec ID |
| 19 | Churn mail end-to-end | "Send churn email for Nexaflow" in chat → `churn_mail` ActionCard → ConfirmModal → `POST /mail/churn-notification confirmed=true` → rec ID |
| 20 | Full integration pass | All 7 views · vendor switching · chat action dispatches · `churn_mail` trigger · backend suite **171 passed** |

---

## Environment Variables

### Frontend — `frontend/.env.local`

```
# LLM server — defaults match local dev; override if running on a different host/port
VITE_LLM_BASE_URL=http://127.0.0.1:11434
VITE_LLM_MODEL=qwen2.5:14b
```

Both optional. `DEFAULT_CFG` in `chat.js` reads them at module load.
No auth header is ever sent.

### Backend — `.env`

```
# ── Phase 1D (unchanged) ───────────────────────────────────────────────────
JIRA_BASE_URL=
JIRA_API_TOKEN=
JIRA_PROJECT_KEY=
SLACK_WEBHOOK_URL=
RECOMMENDATION_EXPORT_PATH=./exports
FASTMCP_TRANSPORT=stdio

# ── Phase 1E additions ─────────────────────────────────────────────────────
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=                        # Gmail address used to send (e.g. yourapp@gmail.com)
SMTP_PASSWORD=                    # Gmail App Password (16-char, not account password)
CHURN_NOTIFICATION_RECIPIENT=     # Destination address for churn notifications
```

`SMTP_USER`, `SMTP_PASSWORD`, and `CHURN_NOTIFICATION_RECIPIENT` are
**required at runtime** when any `/mail/*` endpoint or the
`send_churn_notification` MCP tool is called. If missing, `os.environ[...]`
raises `KeyError` and FastAPI returns a 500. The startup log should warn if
these are absent.

`CHURN_NOTIFICATION_RECIPIENT` is never hardcoded anywhere in source. It is
never sent by the frontend caller. The mail router and mail service always
read it from the environment.

---

## Manual Commands

Start backend:
```powershell
py -3 -m uvicorn api.main:app --reload
# Verify: curl http://localhost:8000/health
```

Verify LLM server (must be running before frontend):
```powershell
curl http://127.0.0.1:11434/api/tags
# Expect: JSON with "models" array
```

Start frontend:
```powershell
cd frontend
npm install
npm run dev
# http://localhost:5173
```

Run full backend suite:
```powershell
py -3 -m pytest tests/
# Expected: 171 passed
```

Build for preview:
```powershell
cd frontend && npm run build && npm run preview
# http://localhost:4173
```

---

## Phase 2 Boundary

| Feature | Reason deferred |
|---|---|
| `GET /recommendations` endpoint | Phase 2 async agent writes status transitions |
| Real-time dispatch status updates | Needs websocket / polling on Phase 2 agent |
| Per-user bulk email (one mail per recipient) | Phase 2 — requires user address lookup |
| Reply tracking table | Phase 2 reply aggregator |
| Multi-user / auth | Separate sprint |
| Mobile layout | Post-V1 UI hardening |
| Email composer / template editor | Phase 2 |

Phase 1E sends **one email** per trigger invocation to the single
`CHURN_NOTIFICATION_RECIPIENT`. Per-user personalised mailing is Phase 2.

---

## Changelog

| Version | Date | Notes |
|---|---|---|
| v1 | 2026-05-14 | Initial spec |
| v2 | 2026-05-14 | Fixed 13 bugs (see change table at top). Added chatbot guardrails (MAX_TURNS=2, timeout, loop prevention, vendor validation). Added mailing service: `services/mail_service.py`, MCP tool, `api/routers/mail.py`, `churn_mail` trigger type, ReclamationView button, env vars. Test count: 161→171. Build steps: 19→20. |

---

*Phase 1E Frontend Dashboard, Chatbot Integration, and Write Trigger UI — v2*  
*Audit Date: 2026-05-01 · Depends on: Phase 1D 161 tests passing*  
*React 18 + Vite 5 + Tailwind 3 + Recharts + Zustand + React Query*  
*Backend additions: triggers router (3 endpoints) + mail router (1 endpoint) + mail service + MCP tool*  
*Chatbot: two-step LLM (MAX 2 turns) · timeout 15 s · vendor validation · no loop possible*  
*Mailing: SMTP via Gmail · single recipient from env · preview/confirm pattern · no hardcoding*  
*No auth · No persistence · No mobile · Desktop V1 only*