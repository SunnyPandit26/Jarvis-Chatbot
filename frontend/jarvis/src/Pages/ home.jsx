import { useState, useEffect } from "react";
import ChatBox from "../components/ChatBox";
import InputBox from "../components/InputBox";

const API = "http://127.0.0.1:8000";

export default function Home() {
  const [chats, setChats] = useState([]);
  const [currentChatId, setCurrentChatId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [hoveredChatId, setHoveredChatId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  
  // ✅ NEW: ChatGPT-style delete modal
  const [deleteModal, setDeleteModal] = useState({ show: false, chatId: null });

  useEffect(() => {
    fetchChats();
  }, []);

  const fetchChats = async () => {
    try {
      const res = await fetch(`${API}/chats`);
      const data = await res.json();
      setChats(data);

      if (data.length > 0 && !currentChatId) {
        const firstChat = data[0];
        setCurrentChatId(firstChat.id);
        setMessages(
          (firstChat.messages || [{ role: "bot", text: "Hello, I am Jarvis. How can I assist you?" }])
            .map(msg => ({ ...msg, skipTyping: true }))
        );
      }
    } catch (e) {
      console.log("No saved chats found");
      createNewChat();
    }
  };

  // ✅ FIXED: ChatGPT-style delete with beautiful modal
  const showDeleteModal = (chatId) => {
    setDeleteModal({ show: true, chatId });
  };

  const hideDeleteModal = () => {
    setDeleteModal({ show: false, chatId: null });
  };

  const confirmDeleteChat = async () => {
    const chatId = deleteModal.chatId;
    setIsLoading(true);
    try {
      await fetch(`${API}/chats/${chatId}`, {
        method: "DELETE"
      });

      const newChats = chats.filter(chat => chat.id !== chatId);
      setChats(newChats);

      if (currentChatId === chatId) {
        if (newChats.length > 0) {
          const nextChat = newChats[0];
          setCurrentChatId(nextChat.id);
          setMessages(
            (nextChat.messages || [{ role: "bot", text: "Hello, I am Jarvis. How can I assist you?" }])
              .map(msg => ({ ...msg, skipTyping: true }))
          );
        } else {
          setCurrentChatId(null);
          setMessages([]);
          createNewChat();
        }
      }
      
      hideDeleteModal();
    } catch (e) {
      console.log("Delete failed");
      alert("Failed to delete chat");
    } finally {
      setIsLoading(false);
    }
  };

  const loadChat = async (chatId) => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API}/chats/${chatId}`);
      const chat = await res.json();

      setMessages((chat.messages || []).map(msg => ({ ...msg, skipTyping: true })));
      setCurrentChatId(chatId);
      setSidebarOpen(false);
    } catch (e) {
      console.log("Failed to load chat");
    } finally {
      setIsLoading(false);
    }
  };

  const createNewChat = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API}/chats/new`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: "New Chat" })
      });

      const newChat = await res.json();
      setChats([newChat, ...chats]);
      setMessages(newChat.messages.map(msg => ({ ...msg, skipTyping: true })));
      setCurrentChatId(newChat.id);
      setSidebarOpen(false);
    } catch (e) {
      console.log("New chat failed");
    } finally {
      setIsLoading(false);
    }
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
    if (!text.trim() || isLoading) return;

    const userMsg = { role: "user", text, skipTyping: true };
    const loadingMsg = { role: "bot", text: "", loading: true };
    setMessages(prev => [...prev, userMsg, loadingMsg]);
    setIsLoading(true);

    try {
      const res = await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          chat_id: currentChatId
        })
      });

      const data = await res.json();

      setMessages(prev => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "bot", 
          text: data.response || "No response", 
          loading: false,
          skipTyping: isVoice
        };
        return updated;
      });

      if (data.chat) {
        setCurrentChatId(data.chat.id);
        setChats(prevChats => {
          const exists = prevChats.find(chat => chat.id === data.chat.id);
          if (exists) {
            return prevChats.map(chat => chat.id === data.chat.id ? data.chat : chat);
          }
          return [data.chat, ...prevChats];
        });
      }

      if (isVoice && data.response) speak(data.response);

    } catch (err) {
      console.error("Chat error:", err);
      setMessages(prev => {
        const updated = [...prev];
        updated[updated.length - 1] = { 
          role: "bot", 
          text: "Sorry, something went wrong! Please try again.", 
          loading: false 
        };
        return updated;
      });
    } finally {
      setIsLoading(false);
    }
  };

  const currentChat = chats.find(c => c.id === currentChatId);

  return (
    <>
      {/* ✅ NEW: ChatGPT-style Delete Modal */}
      {deleteModal.show && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900/95 backdrop-blur-xl border border-slate-700 rounded-2xl max-w-sm w-full mx-4 max-h-[90vh] overflow-hidden shadow-2xl">
            {/* Header */}
            <div className="p-6 border-b border-slate-800">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 bg-red-400 rounded-full animate-pulse"></div>
                <h3 className="text-xl font-bold text-white">Delete Chat</h3>
              </div>
            </div>

            {/* Body */}
            <div className="p-6">
              <div className="text-slate-300 leading-relaxed">
                Are you sure you want to delete this chat? 
                <span className="font-semibold text-red-400 block mt-1">
                  This action cannot be undone.
                </span>
              </div>
            </div>

            {/* Footer */}
            <div className="p-6 pt-0 border-t border-slate-800 flex gap-3 justify-end">
              <button
                onClick={hideDeleteModal}
                className="px-4 py-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-xl transition-all font-medium"
              >
                Cancel
              </button>
              <button
                onClick={confirmDeleteChat}
                disabled={isLoading}
                className="px-4 py-2 bg-red-500/90 hover:bg-red-600 disabled:opacity-50 text-white rounded-xl transition-all font-medium shadow-lg hover:shadow-xl flex items-center gap-2"
              >
                {isLoading ? "Deleting..." : "Delete chat"}
              </button>
            </div>
          </div>
        </div>
      )}

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
            disabled={isLoading || deleteModal.show}
            className="mx-3 mt-3 px-4 py-2 bg-cyan-500/20 hover:bg-cyan-500/30 disabled:opacity-50 text-cyan-200 rounded-xl font-medium transition-all flex items-center gap-2"
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
                    {/* ✅ FIXED: Delete button triggers beautiful modal */}
                    {isHovered && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          showDeleteModal(chat.id);
                        }}
                        disabled={isLoading}
                        className="absolute right-2 top-2 bg-red-500/90 hover:bg-red-600 disabled:opacity-50 text-white p-1.5 rounded-full text-xs transition-all duration-200 shadow-lg z-20 w-6 h-6 flex items-center justify-center"
                        title="Delete chat"
                      >
                        🗑️
                      </button>
                    )}

                    <button
                      onClick={() => loadChat(chat.id)}
                      disabled={isLoading || deleteModal.show}
                      className={`
                        w-full text-left p-3 rounded-lg transition-all text-sm relative
                        ${isHovered ? 'pr-12 pl-4' : 'pr-4'}
                        ${isCurrent
                          ? 'bg-cyan-500/20 border-r-4 border-cyan-400 text-white'
                          : 'hover:bg-slate-800 text-slate-300 hover:text-white'
                        }
                        ${isLoading || deleteModal.show ? 'opacity-50 cursor-not-allowed' : ''}
                      `}
                    >
                      <div className="font-medium truncate">{chat.title}</div>
                      <div className="text-xs text-slate-500 truncate mt-1">
                        {chat.messages?.[chat.messages.length - 1]?.text?.slice(0, 50) || "No messages"}...
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
            disabled={deleteModal.show}
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
            <InputBox onSend={sendMessage} disabled={isLoading || deleteModal.show} />
          </div>
        </div>
      </div>
    </>
  );
}