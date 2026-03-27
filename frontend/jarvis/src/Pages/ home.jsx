import { useState } from "react";
import ChatBox from "../components/ChatBox";
import InputBox from "../components/InputBox";

export default function Home() {
 
  const [messages, setMessages] = useState([
    { role: "bot", text: "Hello, I am Jarvis. How can I assist you?" }
  ]);

  // 🔊 Text to Speech function
  const speak = (text) => {
    window.speechSynthesis.cancel(); // stop previous speech

    const speech = new SpeechSynthesisUtterance(text);
    speech.lang = "en-IN";
    speech.rate = 1;
    speech.pitch = 1;

    window.speechSynthesis.speak(speech);
  };

  const sendMessage = async (text, isVoice = false) => {
    const userMsg = { role: "user", text };
    const loadingMsg = { role: "bot", loading: true };

    // ✅ Add user + loading together
    setMessages((prev) => [...prev, userMsg, loadingMsg]);

    try {
      const res = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ message: text })
      });

      const data = await res.json();

      // ✅ Replace loading with real response
      setMessages((prev) => {
        const updated = [...prev];
        updated.pop(); // remove loading
        updated.push({ role: "bot", text: data.text });
        return updated;
      });
    // AUTO OPEN WEBSITE
    if (data.action === "open_url") {
      window.open(data.url, "_blank");
    }
      // 🔊 Speak AFTER response comes
      if (isVoice) {
  speak(data.text);
}

    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="h-screen bg-slate-950 flex justify-center items-center">
      <div className="w-full max-w-4xl h-[90vh] bg-slate-900/80 backdrop-blur-lg border border-slate-800 rounded-2xl flex flex-col shadow-2xl">
        
        <div className="p-4 border-b border-slate-800 flex items-center gap-2">
          <div className="w-3 h-3 bg-cyan-400 rounded-full animate-pulse"></div>
          <h1 className="text-lg font-semibold text-slate-200">
            Jarvis AI
          </h1>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-2">
          <ChatBox messages={messages} />
        </div>

        <InputBox onSend={sendMessage} />
      </div>
    </div>
  );
}