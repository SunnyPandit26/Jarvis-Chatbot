import { useEffect, useState } from "react";

export default function Message({ role, text, loading }) {
  const isUser = role === "user";
  const [displayText, setDisplayText] = useState("");

  useEffect(() => {
    if (loading) return;

    // ✅ user message = instant
    if (isUser) {
      setDisplayText(text);
      return;
    }

    // ✅ bot typing animation
    let i = 0;
    setDisplayText("");

    const interval = setInterval(() => {
      setDisplayText((prev) => prev + text.charAt(i));
      i++;

      if (i >= text.length) {
        clearInterval(interval);
      }
    }, 15);

    return () => clearInterval(interval);
  }, [text, loading, isUser]);

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`
          max-w-[70%] px-4 py-2 rounded-2xl text-sm whitespace-pre-wrap
          ${isUser 
            ? "bg-slate-800 text-white" 
            : "bg-cyan-600 text-white"}
        `}
      >
        {loading ? (
          <div className="flex gap-1">
            <span className="w-2 h-2 bg-white rounded-full animate-bounce"></span>
            <span className="w-2 h-2 bg-white rounded-full animate-bounce delay-150"></span>
            <span className="w-2 h-2 bg-white rounded-full animate-bounce delay-300"></span>
          </div>
        ) : (
          displayText
        )}
      </div>
    </div>
  );
}