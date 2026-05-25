import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { sendMessage } from "../../api/chat.js";
import { api } from "../../api/client.js";
import { useAppStore } from "../../store/useAppStore.js";
import { ChatMessage } from "./ChatMessage.jsx";
import { QuickPrompts } from "./QuickPrompts.jsx";

const PLANNING_AGENT_PROMPT = "Brief planning agent";

function assembleBriefing(liveData) {
  const { health, ghost, trueup, utilization, renewal } = liveData;
  const activeVendors = health?.active_vendors ?? [];

  return {
    generated_at: new Date().toISOString(),
    audit_date: health?.audit_date ?? "2026-05-01",
    active_vendors: activeVendors,
    portfolio_summary: {
      ghost_waste_annual: ghost?.All?.annual_waste ?? 0,
      trueup_exposure: trueup?.All?.exposure ?? 0,
      avg_utilization: utilization?.All ?? 0,
      expired_contracts: (renewal?.All ?? []).filter(r => r.renewal_urgency === "expired").length,
    },
    vendor_signals: activeVendors.map(v => ({
      vendor: v,
      ghost_licenses: ghost?.[v]?.total ?? 0,
      ghost_waste_annual: ghost?.[v]?.annual_waste ?? 0,
      trueup_exposure: trueup?.[v]?.exposure ?? 0,
      utilization_rate: utilization?.[v] ?? 0,
      expired_contracts: (renewal?.[v] ?? []).filter(r => r.renewal_urgency === "expired").length,
    })),
    available_tools: [
      "get_ghost_detail(vendor, department?)",
      "get_reclamation_candidates(vendor, department?, min_score?)",
      "get_trueup_breakdown(vendor, sku?, seat_type?)",
      "get_renewal_pressure(vendor?)",
      "get_license_demand_forecast(vendor?, department?)",
      "trigger_ghost_ticket(vendor, department?, confirmed?)",
      "trigger_reclamation_review(vendor, department?, confirmed?)",
      "trigger_renewal_alert(vendor, days_threshold?, confirmed?)",
      "send_churn_notification(vendor, department?, confirmed?)",
    ],
    confirmed: true, // In a real implementation, this would be set to true only after the user confirms the briefing content and tool access. For this demo, we'll assume it's always confirmed.
  };
}

export function ChatPanel() {
  const queryClient = useQueryClient();
  const chatOpen = useAppStore(s => s.chatOpen);
  const activeView = useAppStore(s => s.activeView);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([{ role: "assistant", content: "Ask about waste, renewals, forecasts, or trigger an action.", action: null }]);
  const [loading, setLoading] = useState(false);

  const assembleLiveData = () => ({
    health:            queryClient.getQueryData(["health"]),
    ghost:             queryClient.getQueryData(["insight", "ghost"]),
    trueup:            queryClient.getQueryData(["insight", "trueup"]),
    utilization:       queryClient.getQueryData(["insight", "utilization"]),
    renewal:           queryClient.getQueryData(["insight", "renewal"]),
    ghostDetail:       queryClient.getQueryData(["ghost", "detail", "All", null]),
    utilizationDetail: queryClient.getQueryData(["utilization", "All"]),
  });

  const handlePlanningAgentBrief = async () => {
    setLoading(true);
    const liveData = assembleLiveData();
    const briefing = assembleBriefing(liveData);

    setMessages(prev => [...prev, { role: "user", content: PLANNING_AGENT_PROMPT, action: null }]);

    try {
      await api.post("/mail/send-planning-brief", briefing);

      const fmtK = n => `$${(Number(n) / 1000).toFixed(0)}K`;
      const fmtPct = n => `${(Number(n) * 100).toFixed(1)}%`;
      const s = briefing.portfolio_summary;

      const summary = [
        `Planning agent briefed successfully.`,
        ``,
        `Portfolio snapshot sent:`,
        `• Ghost waste: ${fmtK(s.ghost_waste_annual)}/yr across ${briefing.active_vendors.length} vendors`,
        `• True-up exposure: ${fmtK(s.trueup_exposure)}`,
        `• Avg utilization: ${fmtPct(s.avg_utilization)}`,
        `• Expired contracts: ${s.expired_contracts}`,
        ``,
        `${briefing.available_tools.length} MCP tools included. The agent can now investigate and trigger actions autonomously.`,
      ].join("\n");

      setMessages(prev => [...prev, { role: "assistant", content: summary, action: null }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: "assistant", content: `Failed to brief planning agent: ${err.message}`, action: null }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const userText = input.trim();
    setInput("");

    if (userText === PLANNING_AGENT_PROMPT) {
      return handlePlanningAgentBrief();
    }

    const nextMessages = [...messages, { role: "user", content: userText, action: null }];
    setMessages(nextMessages);
    setLoading(true);
    try {
      const { text, action } = await sendMessage(
        nextMessages.map(({ role, content }) => ({ role, content })),
        assembleLiveData(),
      );
      setMessages(prev => [...prev, { role: "assistant", content: text, action }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: "assistant", content: `Connection error: ${err.message}. Is the LLM server running?`, action: null }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <aside className="fixed bottom-0 top-0 z-[100] w-[380px] border-l border-border bg-bg p-4 transition-[right] duration-300" style={{ right: chatOpen ? 0 : -400 }}>
      <div className="font-display text-xl">AI Assistant</div>
      <div className="mt-3"><QuickPrompts view={activeView} onPick={setInput} /></div>
      <div className="mt-4 flex h-[calc(100%-200px)] flex-col gap-3 overflow-y-auto">
        {messages.map((message, idx) => <ChatMessage key={idx} message={message} />)}
        {loading && <div className="text-sm text-text-secondary">Thinking...</div>}
      </div>
      <div className="mt-3 flex gap-2">
        <input
          className="min-w-0 flex-1 rounded-md border border-border bg-surface px-3 py-2 text-sm text-text-primary"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && handleSend()}
        />
        <button className="rounded-md bg-amber px-3 py-2 text-black" onClick={handleSend}>Send</button>
      </div>
    </aside>
  );
}