import { useEffect, useRef } from "react";
import Message from "./Message";

export default function ChatBox({ messages }) {
  const bottomRef = useRef(null);

  // scroll on new message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // 🔥 scroll during typing
  useEffect(() => {
    const interval = setInterval(() => {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, 100);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-4">
      {messages.map((msg, index) => (
        <Message
          key={index}
          role={msg.role}
          text={msg.text}
          loading={msg.loading}
        />
      ))}
      <div ref={bottomRef}></div>
    </div>
  );
}