export const DEFAULT_CFG = {
  baseUrl: import.meta.env.VITE_LLM_BASE_URL ?? "http://127.0.0.1:11434",
  model: import.meta.env.VITE_LLM_MODEL ?? "qwen2.5:14b",
  temperature: 0.1,
  num_ctx: 8192,
  num_predict: 1024,
  timeoutMs: 600_000,
};

async function postChat(messages, { format, cfg }) {
  const controller = new AbortController();
  const tid = setTimeout(() => controller.abort(), cfg.timeoutMs);
  try {
    const body = {
      model: cfg.model,
      stream: false,
      messages,
      options: {
        temperature: cfg.temperature,
        num_ctx: cfg.num_ctx,
        num_predict: cfg.num_predict,
      },
    };
    if (format) body.format = format;
    const res = await fetch("/llm/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    if (!res.ok) throw new Error(`LLM server HTTP ${res.status}`);
    const data = await res.json();
    return data.message?.content ?? "";
  } finally {
    clearTimeout(tid);
  }
}

const fmtK = n => (n == null ? "?" : `${(Number(n) / 1000).toFixed(0)}K`);
const fmtPct = n => (n == null ? "?" : `${(Number(n) * 100).toFixed(1)}%`);

function renderVendorBlock(vendor, ghost, trueup, utilization, renewal, ghostDetail) {
  const g = ghost?.[vendor];
  const t = trueup?.[vendor];
  const u = utilization?.[vendor];
  const r = renewal?.[vendor] ?? [];

  const vendorDetails = (ghostDetail ?? []).filter(d => d.vendor === vendor);

  if (!g && !t && !u && r.length === 0 && vendorDetails.length === 0) return "";

  const lines = [
    `${vendor} [GHOST — use ghost_ticket only]: departed_employee_licenses=${g?.total ?? "?"}, annual_waste=$${fmtK(g?.annual_waste)}`,
    `${vendor} [RECLAMATION — use reclamation/rightsizing only]: utilization=${fmtPct(u)}`,
    `${vendor} [TRUE-UP — use renewal_alert only]: exposure=$${fmtK(t?.exposure)}`,
    `${vendor} [CONTRACTS]: ${r.map(row => `${row.status ?? row.renewal_urgency}:${row.expiry ?? row.contract_expiry}`).join(", ") || "none"}`,
  ];

  if (vendorDetails.length > 0) {
    const skuList = vendorDetails
      .slice(0, 15)
      .map(d => ` - SKU: ${d.sku_name || d.sku} | Dept: ${d.department} | Cost: $${d.monthly_cost || '?'}/mo | Status: ${d.is_ghost ? 'GHOST' : 'ACTIVE'}`)
      .join("\n");

    lines.push(`SKU-LEVEL BREAKDOWN:\n${skuList}`);
    if (vendorDetails.length > 15) lines.push(` (and ${vendorDetails.length - 15} more SKUs...)`);
  }

  return lines.join("\n");
}

// FIX 1: Factual per-action descriptions so the LLM explanation is grounded,
// not guessed from the action name alone.
const ACTION_EXPLANATIONS = {
  ghost_ticket:       "A Jira ticket will be created to deprovision licenses belonging to departed employees, recovering the annual waste cost.",
  reclamation:        "A CSV will be exported listing active employees with low utilization whose licenses should be reclaimed.",
  reclamation_review: "A Jira review ticket will be created to audit active licenses with low utilization for downsizing.",
  rightsizing:        "A Slack alert will be sent to flag active licenses that can be downgraded to a cheaper tier.",
  renewal_alert:      "A Slack alert will be sent for expired or critical contracts that have seats over their contracted entitlement.",
  churn_mail:         "An internal churn-risk email will be sent to YOUR team flagging low utilization on this vendor, to trigger a cost renegotiation or cancellation review. This is NOT a message sent to the vendor.",
};

export function buildPlannerSystem(liveData) {
  const { health, ghost, trueup, utilization, renewal, ghostDetail } = liveData;

  return `
You are a highly analytical SaaS Spend Assistant. 
Reply with a SINGLE JSON object only.

Schemas:
{"phase":"answer","text":""}
{"phase":"action","type":"ghost_ticket"|"reclamation"|"reclamation_review"|"rightsizing"|"renewal_alert"|"churn_mail","vendor":"","department":"","count":0,"impact":0,"message":""}

Strict Rules:
1. DATA PRIORITIZATION: 
   - If the user asks about "True-ups" or "Exposure", you MUST use true-up data (exposure_amount).
   - If the user asks about "Ghost" licenses, departed employees, or deprovision waste, use ghost license data and ghost_ticket — NOT reclamation.
   - If the user asks about "Reclamation", "rightsizing", or reclaiming unused seats on active employees, use reclamation/rightsizing actions only (active licenses with low utilization).
   - If the user asks about "Usage", use utilization percentages.
2. ACTION TRIGGERING RULES (in strict priority order):
   - If the savings figure comes from [GHOST] data (departed employees, deprovisioning), the action MUST be "ghost_ticket". This overrides everything else.
   - If the issue is seats over contract entitlement ([TRUE-UP] / exposure), use "renewal_alert".
   - If the issue is active employees with low utilization ([RECLAMATION]), use "reclamation" or "rightsizing".
   - If the user asks to send a churn email or flag a vendor for cancellation/renegotiation, use "churn_mail". This sends an INTERNAL email to your team — it does NOT contact the vendor.
   - These categories are MUTUALLY EXCLUSIVE. Never use "rightsizing" for ghost data. Never use "ghost_ticket" for utilization data.
3. NUMBERS: The count and impact fields in your action object MUST come from the data category
   that matches the action type:
   - ghost_ticket → count and impact from [GHOST] figures only.
   - reclamation / rightsizing → count and impact from [RECLAMATION] figures only.
   - renewal_alert → count and impact from [TRUE-UP] figures only.
   - churn_mail → count = 0, impact = 0 (no pre-computed figure; backend resolves it).
   Never mix figures across categories.
4. NO HALLUCINATIONS: If the data below doesn't answer a specific SKU or Department question, do not invent data. State clearly what summary data you do have.
5. Lead with the specific dollar impact related to the USER'S QUESTION.
6. SKU ANALYSIS: If "SKU-LEVEL BREAKDOWN" is visible in the LIVE DATA, use those specific names (e.g., "Jira Service Management") in your text response.
7. DO NOT ANSWER QUESTIONS ABOUT VENDORS NOT LISTED IN THE LIVE DATA. If asked about an unlisted vendor, respond with "I don't have data on that vendor."

Available triggers:
- ghost_ticket(vendor, department?) → ghost / departed-employee licenses only ([GHOST] data); NEVER for active employees.
- reclamation / reclamation_review(vendor, department?) → active-employee licenses with low utilization ([RECLAMATION] data) only; NEVER for ghost licenses.
- renewal_alert(vendor) → sends Slack alert for expired/critical contracts ([TRUE-UP] / [CONTRACTS] data).
- churn_mail(vendor) → sends an INTERNAL email to your team flagging low utilization on this vendor for cost renegotiation or cancellation review. This does NOT contact the vendor directly.

LIVE DATA:
${renderVendorBlock("Atlassify", ghost, trueup, utilization, renewal, ghostDetail)}
${renderVendorBlock("Nexaflow", ghost, trueup, utilization, renewal, ghostDetail)}
${renderVendorBlock("Cloudora", ghost, trueup, utilization, renewal, ghostDetail)}
${renderVendorBlock("Databridge", ghost, trueup, utilization, renewal, ghostDetail)}
${renderVendorBlock("Veloxa", ghost, trueup, utilization, renewal, ghostDetail)}
${renderVendorBlock("Prismly", ghost, trueup, utilization, renewal, ghostDetail)}
Summary:
- Portfolio Ghost Waste: $${fmtK(ghost?.All?.annual_waste)}
- Portfolio True-up Exposure: $${fmtK(trueup?.All?.exposure)}
- Portfolio Avg Utilization: ${fmtPct(utilization?.All)}
`.trim();
}

export async function sendMessage(history, liveData, cfg = DEFAULT_CFG) {
  const plannerSystem = buildPlannerSystem(liveData);
  const planMessages = [{ role: "system", content: plannerSystem }, ...history];
  const rawPlan = await postChat(planMessages, { format: "json", cfg });

  let plan;
  try {
    const candidate = JSON.parse(rawPlan);
    plan = typeof candidate?.phase === "string" ? candidate : { phase: "answer", text: rawPlan };
  } catch {
    plan = { phase: "answer", text: rawPlan };
  }

  if (plan.phase === "answer") {
    return { text: plan.text ?? rawPlan, action: null };
  }

  if (plan.phase === "action") {
    const validTypes = ["ghost_ticket", "reclamation", "reclamation_review", "rightsizing", "renewal_alert", "churn_mail"];
    const activeVendors = liveData.health?.active_vendors ?? [];
    if (!validTypes.includes(plan.type)) return { text: rawPlan, action: null };
    if (activeVendors.length > 0 && !activeVendors.includes(plan.vendor)) {
      return {
        text: `I can't trigger that - "${plan.vendor}" is not a recognised vendor. Valid vendors: ${activeVendors.join(", ")}.`,
        action: null,
      };
    }

    // FIX 2: Ground the explanation in a factual action description rather than
    // letting the LLM guess from the action name alone.
    const actionContext = ACTION_EXPLANATIONS[plan.type] ?? "An action will be dispatched.";
    const finalMessages = [
      {
        role: "system",
        content: `You are a SaaS spend assistant. Write ONE plain-English sentence explaining this specific action.
Context: ${actionContext}
Mention the vendor name (${plan.vendor}) in your sentence. No JSON. No extra sentences.`,
      },
      ...history,
      { role: "user", content: `Action planned:\n${JSON.stringify(plan, null, 2)}\nExplain briefly.` },
    ];

    let explanation = "Action ready to dispatch.";
    try {
      explanation = await postChat(finalMessages, { cfg });
    } catch {
      explanation = actionContext;
    }

    return {
      text: explanation,
      action: {
        type: plan.type,
        vendor: plan.vendor,
        department: plan.department ?? null,
        count: typeof plan.count === "number" ? plan.count : 0,
        impact: typeof plan.impact === "number" ? plan.impact : 0,
        message: typeof plan.message === "string" ? plan.message : "",
      },
    };
  }

  return { text: rawPlan, action: null };
}