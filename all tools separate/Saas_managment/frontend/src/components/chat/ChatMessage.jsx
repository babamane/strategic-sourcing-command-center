import { ActionCard } from "./ActionCard.jsx";

export function ChatMessage({ message }) {
  const mine = message.role === "user";
  return (
    <div className={mine ? "ml-8 rounded-md bg-amber p-3 text-black" : "mr-8 rounded-md bg-surface-hover p-3 text-text-primary"}>
      <div className="text-sm">{message.content}</div>
      <ActionCard action={message.action} />
    </div>
  );
}
