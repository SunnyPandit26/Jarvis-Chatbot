import { useState, useEffect } from "react";
import ChatBox from "../components/ChatBox";
import InputBox from "../components/InputBox";

export default function Home() {
  const [chats, setChats] = useState([]);
  const [currentChatId, setCurrentChatId] = useState(null);
  const [messages, setMessages] = useState([
    { role: "bot", text: "Hello, I am Jarvis. How can I assist you?" }
  ]);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [hoveredChatId, setHoveredChatId] = useState(null);

  useEffect(() => {
    try {
      const savedChats = localStorage.getItem("jarvis-chats");
      if (savedChats) {
        const parsedChats = JSON.parse(savedChats);
        setChats(parsedChats);
        if (parsedChats.length > 0) {
          setCurrentChatId(parsedChats[0].id);
          setMessages(parsedChats[0].messages || [{ role: "bot", text: "Hello, I am Jarvis!" }]);
        }
      }
    } catch (e) {
      console.log("No saved chats found");
    }
  }, []);

  useEffect(() => {
    if (chats.length > 0) {
      try {
        localStorage.setItem("jarvis-chats", JSON.stringify(chats));
      } catch (e) {
        console.log("Error saving chats");
      }
    }
  }, [chats]);

  const deleteChat = (chatId) => {
    if (window.confirm("Are you sure you want to delete this chat?")) {
      const newChats = chats.filter(chat => chat.id !== chatId);
      setChats(newChats);
      
      if (currentChatId === chatId) {
        if (newChats.length > 0) {
          setCurrentChatId(newChats[0].id);
          setMessages(newChats[0].messages || [{ role: "bot", text: "Hello, I am Jarvis. How can I assist you?" }]);
        } else {
          setCurrentChatId(null);
          setMessages([{ role: "bot", text: "Hello, I am Jarvis. How can I assist you?" }]);
        }
      }
    }
  };

  const loadChat = (chatId) => {
    const chat = chats.find(c => c.id === chatId);
    if (chat) {
      setMessages(chat.messages.map(msg => ({ ...msg, skipTyping: true })));
      setCurrentChatId(chatId);
      setSidebarOpen(false);
    }
  };

  const createNewChat = () => {
    const newChat = {
      id: Date.now().toString(),
      title: "New Chat",
      messages: [{ role: "bot", text: "Hello, I am Jarvis. How can I assist you?" }]
    };
    setChats([newChat, ...chats]);
    setMessages(newChat.messages);
    setCurrentChatId(newChat.id);
    setSidebarOpen(false);
  };

  const speak = (text) => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const speech = new SpeechSynthesisUtterance(text);
      speech.lang = "en-IN";
      speech.rate = 1;
      speech.pitch = 1;
      window.speechSynthesis.speak(speech);
    }
  };

  const sendMessage = async (text, isVoice = false) => {
    const userMsg = { role: "user", text };
    const loadingMsg = { role: "bot", loading: true };
    setMessages(prev => [...prev, userMsg, loadingMsg]);

    try {
      const res = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text })
      });

      const data = await res.json();

      setMessages(prev => {
        const updated = [...prev];
        updated.pop();
        updated.push({ role: "bot", text: data.text || data.message || "No response" });
        return updated;
      });

      setTimeout(() => {
        setChats(prevChats => {
          return prevChats.map(chat => 
            chat.id === currentChatId 
              ? { 
                  ...chat, 
                  messages: [...messages, userMsg, { role: "bot", text: data.text || data.message || "No response" }],
                  title: chat.messages.length === 1 ? text.slice(0, 30) + "..." : chat.title
                }
              : chat
          );
        });
      }, 100);

      if (isVoice) speak(data.text || data.message);

    } catch (err) {
      console.error("Chat error:", err);
      setMessages(prev => {
        const updated = [...prev];
        updated.pop();
        updated.push({ role: "bot", text: "Sorry, something went wrong! Please try again." });
        return updated;
      });
    }
  };

  const currentChat = chats.find(c => c.id === currentChatId);

  return (
    <div className="h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-cyan-900 flex">
      {/* Sidebar */}
      <div className={`
        w-80 bg-slate-900/95 backdrop-blur-lg border-r border-slate-800
        flex flex-col transition-all duration-300
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        lg:w-72
      `}>
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-200">Chats</h2>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-1 rounded-lg hover:bg-slate-800 text-slate-300 hover:text-white"
          >
            ✕
          </button>
        </div>

        <button
          onClick={createNewChat}
          className="mx-3 mt-3 px-4 py-2 bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-200 rounded-xl font-medium transition-all flex items-center gap-2"
        >
          ➕ New Chat
        </button>

        <div className="flex-1 overflow-y-auto py-2 space-y-1 px-2">
          {chats.length === 0 ? (
            <div className="text-center text-slate-500 py-8 text-sm">
              No chats yet. Create a new chat!
            </div>
          ) : (
            chats.map((chat) => {
              const isHovered = hoveredChatId === chat.id;
              const isCurrent = currentChatId === chat.id;
              
              return (
                <div 
                  key={chat.id}
                  className="relative"
                  onMouseEnter={() => setHoveredChatId(chat.id)}
                  onMouseLeave={() => setHoveredChatId(null)}
                >
                  {/* ✅ FIXED POSITION: Delete button INSIDE chat item */}
                  {isHovered && !isCurrent && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteChat(chat.id);
                      }}
                      className="absolute right-2 top-2 bg-red-500/90 hover:bg-red-600 text-white p-1.5 rounded-full text-xs transition-all duration-200 shadow-lg z-20 w-6 h-6 flex items-center justify-center"
                      title="Delete chat"
                    >
                      🗑️
                    </button>
                  )}
                  
                  <button
                    onClick={() => loadChat(chat.id)}
                    className={`
                      w-full text-left p-3 rounded-lg transition-all text-sm relative
                      ${isHovered ? 'pr-10 pl-10' : 'pr-4'} 
                      ${isCurrent
                        ? 'bg-cyan-500/20 border-r-4 border-cyan-400 text-white' 
                        : 'hover:bg-slate-800 text-slate-300 hover:text-white'
                      }
                    `}
                  >
                    <div className="font-medium truncate">{chat.title}</div>
                    <div className="text-xs text-slate-500 truncate mt-1">
                      {chat.messages[chat.messages.length - 1]?.text?.slice(0, 50)}...
                    </div>
                  </button>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col max-w-6xl mx-auto w-full">
        <button
          onClick={() => setSidebarOpen(true)}
          className="lg:hidden p-4 bg-slate-900/50 border-b border-slate-800"
        >
          <svg className="w-6 h-6 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        <div className="p-6 border-b border-slate-800 flex items-center gap-3 bg-slate-900/50">
          <div className="w-3 h-3 bg-cyan-400 rounded-full animate-pulse"></div>
          <h1 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
            Jarvis AI
          </h1>
          {currentChat && (
            <div className="text-sm text-slate-400 ml-auto truncate max-w-[200px]">
              {currentChat.title}
            </div>
          )}
        </div>

        <div className="flex-1 overflow-hidden flex flex-col">
          <div className="flex-1 overflow-y-auto px-6 py-4 bg-slate-950/50">
            <ChatBox messages={messages} />
          </div>
          <InputBox onSend={sendMessage} />
        </div>
      </div>
    </div>
  );
}