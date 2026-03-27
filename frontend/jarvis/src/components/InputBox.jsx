import { useState } from "react";

export default function InputBox({ onSend }) {
  const [input, setInput] = useState("");
  const [listening, setListening] = useState(false);

  const handleSend = () => {
    if (!input.trim()) return;
    onSend(input, false);
    setInput("");
  };

  // ✅ NEW: Enter key support (Shift+Enter = new line)
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleVoice = () => {
    const recognition = new window.webkitSpeechRecognition();

    setListening(true);
    recognition.start();

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      onSend(transcript, true);
      setInput("");
    };

    recognition.onend = () => {
      setListening(false);
    };
  };

  return (
    <div className="p-4 border-t border-slate-800 flex gap-2 bg-slate-900 rounded-b-2xl">
      <button
        onClick={handleVoice}
        className="bg-slate-700 hover:bg-slate-600 px-3 rounded-xl"
      >
        🎤
      </button>
      {listening && <p className="text-cyan-400 text-sm">🎤 Listening...</p>}
      
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyPress}  // ✅ ENTER KEY MAGIC!
        placeholder="Ask Jarvis anything... (Press Enter to send)"
        className="flex-1 bg-slate-950 border border-slate-700 rounded-xl px-4 py-2 outline-none focus:ring-2 focus:ring-cyan-500 text-white resize-none"
        rows="1"
      />

      <button
        onClick={handleSend}
        className="bg-cyan-500 hover:bg-cyan-600 px-4 py-2 rounded-xl font-medium flex items-center gap-1"
      >
        Send ➤
      </button>
    </div>
  );
}