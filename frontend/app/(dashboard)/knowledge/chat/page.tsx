"use client";

import React, { useState, useRef, useEffect } from "react";
import { Send, Sparkles, Loader2, FileText, ArrowLeft, Copy, Check, MessageSquare, Plus, Trash2, AlertCircle, Edit2, X } from "lucide-react";
import Link from "next/link";
import { useUser } from "@/lib/context/UserContext";
import { 
  queryKnowledgeBase, 
  getChatSessions, 
  createChatSession, 
  getChatSessionMessages, 
  deleteChatSession,
  renameChatSession
} from "@/lib/api/knowledge";

interface Message {
  id: number | string;
  role: "assistant" | "user";
  content: string;
  sources?: Array<{ file: string; page: number }>;
}

export default function KnowledgeChat() {
  const { profile, loading } = useUser();
  const [sessions, setSessions] = useState<any[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<number | string | null>(null);
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const loadSessions = async () => {
    try {
      const data = await getChatSessions();
      setSessions(data || []);
      
      const savedSession = sessionStorage.getItem("currentChatSessionId");
      if (savedSession && data?.some((s: any) => s.id === savedSession)) {
        selectSession(savedSession);
      } else {
        startNewChat();
      }
    } catch (error) {
      console.error(error);
      startNewChat();
    }
  };

  useEffect(() => {
    if (!loading) {
      loadSessions();
    }
  }, [loading]);

  const handleCopy = (text: string, id: number | string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const startNewChat = () => {
    setCurrentSessionId(null);
    sessionStorage.removeItem("currentChatSessionId");
    setMessages([
      { 
        id: 1, 
        role: "assistant", 
        content: "Welcome to the Knowledge Base! I can help you find information from any uploaded documents. Ask me a question." 
      }
    ]);
  };

  const selectSession = async (id: string) => {
    setCurrentSessionId(id);
    sessionStorage.setItem("currentChatSessionId", id);
    setIsLoading(true);
    try {
      const msgs = await getChatSessionMessages(id);
      if (msgs && msgs.length > 0) {
        setMessages(msgs.map((m: any) => ({
          id: m.id,
          role: m.role,
          content: m.content,
          sources: m.sources
        })));
      } else {
        setMessages([{ 
          id: 1, 
          role: "assistant", 
          content: "Welcome back! How can I help you today?" 
        }]);
      }
    } catch (e) {
      console.warn("Could not load session messages:", e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteSession = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    try {
      await deleteChatSession(id);
      if (currentSessionId === id) {
        startNewChat();
      }
      loadSessions();
    } catch(e) {
      console.error(e);
    }
  };

  const handleRenameSubmit = async (e: React.FormEvent, id: string) => {
    e.preventDefault();
    e.stopPropagation();
    if (!editingTitle.trim()) {
      setEditingSessionId(null);
      return;
    }
    try {
      await renameChatSession(id, editingTitle.trim());
      setSessions(sessions.map(s => s.id === id ? { ...s, title: editingTitle.trim() } : s));
      setEditingSessionId(null);
    } catch (e) {
      console.error(e);
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    
    const userQuery = input.trim();
    const newMsg: Message = { id: Date.now(), role: "user", content: userQuery };
    setMessages(prev => [...prev, newMsg]);
    setInput("");
    setIsLoading(true);
    
    abortControllerRef.current = new AbortController();
    
    let activeSessionId = currentSessionId;
    try {
      if (!activeSessionId) {
        const newSession = await createChatSession(
          userQuery.substring(0, 30) + (userQuery.length > 30 ? "..." : ""),
          abortControllerRef.current?.signal
        );
        activeSessionId = newSession.id;
        setCurrentSessionId(activeSessionId);
        sessionStorage.setItem("currentChatSessionId", activeSessionId as string);
        setSessions(prev => [newSession, ...prev]);
      }

      const savedSearches = parseInt(localStorage.getItem('knowledge_searches') || '0', 10);
      localStorage.setItem('knowledge_searches', (savedSearches + 1).toString());

      const response = await queryKnowledgeBase(userQuery, activeSessionId || undefined, abortControllerRef.current?.signal);
      
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: "assistant",
        content: response.answer,
        sources: response.sources
      }]);
    } catch (error: any) {
      if (error.name === 'AbortError') {
        setMessages(prev => [...prev, {
          id: Date.now() + 1,
          role: "assistant",
          content: "Generation stopped."
        }]);
      }
      // Silently handle other network errors as requested
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <div className="flex-1 flex gap-4 h-full">
        {/* Sidebar */}
        <div className="w-64 flex flex-col bg-card border border-border rounded-2xl shadow-sm overflow-hidden">
          <div className="p-4 border-b border-border bg-secondary/30">
            <button 
              suppressHydrationWarning
              onClick={startNewChat}
              className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg font-medium transition-colors shadow-sm text-sm"
            >
              <Plus size={16} />
              New Chat
            </button>
          </div>
          <div className="flex-1 overflow-y-auto chatbot-scrollbar p-3 space-y-1">
            {sessions.map(session => (
              <div 
                key={session.id}
                onClick={() => {
                  if (editingSessionId !== session.id) selectSession(session.id);
                }}
                className={`group flex items-center justify-between p-3 rounded-xl cursor-pointer transition-colors border ${
                  currentSessionId === session.id 
                  ? "bg-secondary/80 border-border/80" 
                  : "bg-transparent border-transparent hover:bg-secondary/40"
                }`}
              >
                <div className="flex items-center gap-3 overflow-hidden flex-1">
                  <MessageSquare size={16} className={currentSessionId === session.id ? "text-blue-500 shrink-0" : "text-muted-foreground shrink-0"} />
                  
                  {editingSessionId === session.id ? (
                    <form 
                      onSubmit={(e) => handleRenameSubmit(e, session.id)} 
                      className="flex-1 flex items-center gap-1 min-w-0"
                      onClick={e => e.stopPropagation()}
                    >
                      <input
                        autoFocus
                        value={editingTitle}
                        onChange={e => setEditingTitle(e.target.value)}
                        className="flex-1 bg-background text-foreground text-sm px-2 py-1 rounded border border-border focus:outline-none focus:border-blue-500 w-full min-w-0"
                      />
                      <button type="submit" className="text-green-500 hover:bg-green-500/10 p-1 rounded shrink-0"><Check size={14} /></button>
                      <button type="button" onClick={() => setEditingSessionId(null)} className="text-red-500 hover:bg-red-500/10 p-1 rounded shrink-0"><X size={14} /></button>
                    </form>
                  ) : (
                    <span className="text-sm truncate font-medium">{session.title}</span>
                  )}
                </div>
                
                {editingSessionId !== session.id && (
                  <div className="opacity-0 group-hover:opacity-100 flex items-center transition-all shrink-0 ml-2">
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        setEditingSessionId(session.id);
                        setEditingTitle(session.title);
                      }}
                      className="p-1.5 text-muted-foreground hover:text-blue-500 hover:bg-blue-500/10 rounded-md"
                      title="Rename chat"
                    >
                      <Edit2 size={14} />
                    </button>
                    <button 
                      onClick={(e) => handleDeleteSession(e, session.id)}
                      className="p-1.5 text-muted-foreground hover:text-red-500 hover:bg-red-500/10 rounded-md"
                      title="Delete chat"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                )}
              </div>
            ))}
            {sessions.length === 0 && (
              <div className="text-center p-4 text-xs text-muted-foreground mt-4">
                No chat history found.
              </div>
            )}
          </div>
        </div>

        {/* Chat Area */}
        <div className="flex-1 bg-card border border-border rounded-2xl flex flex-col shadow-sm overflow-hidden h-full">
          {/* Header */}
          <div className="h-16 border-b border-border flex items-center px-6 gap-3 bg-secondary/30 justify-between shrink-0">
            <div className="flex items-center gap-3">
              <Link 
                href="/knowledge" 
                className="w-8 h-8 rounded-lg hover:bg-secondary/80 flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors"
              >
                <ArrowLeft size={16} />
              </Link>
              <div className="w-8 h-8 rounded-lg bg-secondary border border-border/50 text-foreground flex items-center justify-center ml-1">
                <Sparkles size={14} />
              </div>
              <div>
                <h2 className="font-bold text-sm tracking-tight text-foreground">Organizational Intelligence Engine</h2>
                <p className="text-[9px] text-muted-foreground font-semibold uppercase tracking-wider">Semantic Document Discovery</p>
              </div>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto chatbot-scrollbar p-6 space-y-6">
            {messages.map(msg => (
              <div key={msg.id} className={`flex gap-4 max-w-3xl group ${msg.role === "user" ? "ml-auto flex-row-reverse" : ""}`}>
                <img 
                  src={msg.role === "user" 
                    ? (profile?.avatar_url || `https://api.dicebear.com/7.x/adventurer/svg?seed=${encodeURIComponent(profile?.full_name || "User")}`)
                    : "https://api.dicebear.com/7.x/bottts/svg?seed=Enterprise"
                  }
                  alt={msg.role} 
                  className="w-8 h-8 rounded-lg border border-border object-cover bg-secondary flex-shrink-0 mt-1"
                />
                <div className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"} max-w-[calc(100%-3rem)]`}>
                  <div className={`px-5 py-4 rounded-2xl text-sm leading-relaxed ${
                    msg.role === "user" 
                    ? "bg-foreground text-background rounded-tr-sm border border-foreground" 
                    : "bg-secondary/50 border border-border text-foreground rounded-tl-sm"
                  }`}>
                    <div className="whitespace-pre-wrap">{msg.content}</div>
                    
                    {msg.role === "assistant" && msg.sources && msg.sources.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-border/50">
                        <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest block mb-2">Referenced Records</span>
                        <div className="flex flex-wrap gap-2">
                          {msg.sources.map((source, idx) => (
                            <div key={idx} className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-secondary border border-border/50 rounded-lg text-[10px] font-semibold text-foreground">
                              <FileText size={10} className="text-muted-foreground" />
                              <span className="truncate max-w-[150px]">{source.file ? source.file.split(/[/\\]/).pop() : "Unknown"}</span>
                              <span className="text-muted-foreground opacity-70">Pg {source.page}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                  <div className={`mt-1.5 opacity-0 group-hover:opacity-100 transition-opacity flex gap-2 ${msg.role === "user" ? "mr-1" : "ml-1"}`}>
                    <button 
                      onClick={() => handleCopy(msg.content, msg.id)}
                      className="flex items-center gap-1.5 p-1.5 rounded-md text-[11px] font-medium text-muted-foreground hover:text-foreground hover:bg-secondary/50 transition-colors"
                      title="Copy text"
                    >
                      {copiedId === msg.id ? <Check size={12} className="text-green-500" /> : <Copy size={12} />}
                      {copiedId === msg.id ? "Copied" : "Copy"}
                    </button>
                  </div>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex gap-4 max-w-3xl">
                <img 
                  src="https://api.dicebear.com/7.x/bottts/svg?seed=Enterprise"
                  alt="assistant" 
                  className="w-8 h-8 rounded-lg border border-border object-cover bg-secondary flex-shrink-0"
                />
                <div className="flex items-center gap-1.5 pt-3 pl-2">
                  <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="p-4 border-t border-border bg-card shrink-0">
            <form onSubmit={handleSend} className="relative max-w-4xl mx-auto flex gap-2">
              <input 
                suppressHydrationWarning
                type="text" 
                value={input}
                onChange={e => setInput(e.target.value)}
                disabled={isLoading}
                placeholder="Enter operational query..."
                className="w-full pl-4 pr-12 py-3 rounded-xl border border-border bg-secondary/30 text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-ring focus:border-ring transition-all placeholder:text-muted-foreground shadow-sm disabled:opacity-50"
              />
              {isLoading ? (
                <button 
                  type="button"
                  onClick={() => abortControllerRef.current?.abort()}
                  className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 bg-red-500 hover:bg-red-600 text-white active:scale-95 rounded-lg flex items-center justify-center transition-all duration-200 cursor-pointer shadow-md"
                  title="Stop generating"
                >
                  <div className="w-2.5 h-2.5 bg-white rounded-[2px]"></div>
                </button>
              ) : (
                <button 
                  type="submit"
                  disabled={!input.trim()}
                  className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 bg-blue-600 text-white hover:scale-110 hover:shadow-lg hover:shadow-blue-600/20 active:scale-95 disabled:opacity-50 disabled:hover:scale-100 disabled:shadow-none rounded-lg flex items-center justify-center transition-all duration-200 cursor-pointer"
                >
                  <Send size={14} />
                </button>
              )}
            </form>
            <div className="text-center mt-3">
              <span className="text-[9px] font-bold uppercase tracking-widest text-muted-foreground">
                <AlertCircle size={10} className="inline mr-1 mb-0.5" />
                Operational records are indexed dynamically. Validate responses against cited manuals.
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
