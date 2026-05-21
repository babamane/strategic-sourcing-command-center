import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { sendMessage } from "../../api/chat.js";
import { useAppStore } from "../../store/useAppStore.js";
import { ChatMessage } from "./ChatMessage.jsx";
import { QuickPrompts } from "./QuickPrompts.jsx";

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
    ghostDetail:       queryClient.getQueryData(["ghost", "detail", "All", null]),  // FIXED KEY
    utilizationDetail: queryClient.getQueryData(["utilization", "All"]),            // FIXED KEY
  });

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const userText = input.trim();
    setInput("");
    const nextMessages = [...messages, { role: "user", content: userText, action: null }];
    setMessages(nextMessages);
    setLoading(true);
    try {
      const { text, action } = await sendMessage(nextMessages.map(({ role, content }) => ({ role, content })), assembleLiveData());
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
      <div className="mt-4 flex h-[calc(100%-150px)] flex-col gap-3 overflow-y-auto">
        {messages.map((message, idx) => <ChatMessage key={idx} message={message} />)}
        {loading && <div className="text-sm text-text-secondary">Thinking...</div>}
      </div>
      <div className="mt-3 flex gap-2">
        <input className="min-w-0 flex-1 rounded-md border border-border bg-surface px-3 py-2 text-sm text-text-primary" value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === "Enter" && handleSend()} />
        <button className="rounded-md bg-amber px-3 py-2 text-black" onClick={handleSend}>Send</button>
      </div>
    </aside>
  );
}
