"use client";

import React, { useState, useRef, useEffect } from "react";
import { Send, Sparkles, AlertCircle, Loader2, FileText, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useUser } from "@/lib/context/UserContext";
import { queryKnowledgeBase } from "@/lib/api/knowledge";

interface Message {
  id: number;
  role: "assistant" | "user";
  content: string;
  sources?: Array<{ file: string; page: number }>;
}

export default function KnowledgeChat() {
  const { profile } = useUser();
  const [messages, setMessages] = useState<Message[]>([
    { 
      id: 1, 
      role: "assistant", 
      content: "Welcome to the Organizational Intelligence Console. I can retrieve details from corporate policies, standard operating procedures, and technical documentation. Please upload a PDF or ask a question." 
    }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    
    const userQuery = input.trim();
    const newMsg: Message = { id: Date.now(), role: "user", content: userQuery };
    setMessages(prev => [...prev, newMsg]);
    setInput("");
    setIsLoading(true);
    
    try {
      // Increment organic search counter
      const savedSearches = parseInt(localStorage.getItem('knowledge_searches') || '0', 10);
      localStorage.setItem('knowledge_searches', (savedSearches + 1).toString());

      const response = await queryKnowledgeBase(userQuery);
      
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: "assistant",
        content: response.answer,
        sources: response.sources
      }]);
    } catch (error: any) {
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: "assistant",
        content: `Error: ${error.message || "Failed to process query."}`
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <div className="flex-1 bg-card border border-border rounded-2xl flex flex-col shadow-sm overflow-hidden">
        
        {}
        <div className="h-16 border-b border-border flex items-center px-6 gap-3 bg-secondary/30 justify-between">
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

        {}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.map(msg => (
            <div key={msg.id} className={`flex gap-4 max-w-3xl ${msg.role === "user" ? "ml-auto flex-row-reverse" : ""}`}>
              <img 
                src={msg.role === "user" 
                  ? (profile?.avatar_url || `https://api.dicebear.com/7.x/adventurer/svg?seed=${encodeURIComponent(profile?.full_name || "User")}`)
                  : "https://api.dicebear.com/7.x/bottts/svg?seed=Enterprise"
                }
                alt={msg.role} 
                className="w-8 h-8 rounded-lg border border-border object-cover bg-secondary flex-shrink-0"
              />
              <div className={`px-5 py-3 rounded-2xl text-sm leading-relaxed ${
                msg.role === "user" 
                ? "bg-foreground text-background" 
                : "bg-secondary/50 border border-border text-foreground"
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
            </div>
          ))}
          {isLoading && (
            <div className="flex gap-4 max-w-3xl">
              <img 
                src="https://api.dicebear.com/7.x/bottts/svg?seed=Enterprise"
                alt="assistant" 
                className="w-8 h-8 rounded-lg border border-border object-cover bg-secondary flex-shrink-0"
              />
              <div className="px-5 py-4 rounded-2xl bg-secondary/50 border border-border flex items-center justify-center">
                <Loader2 size={16} className="text-muted-foreground animate-spin" />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {}
        <div className="p-4 border-t border-border bg-card">
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
            <button 
              type="submit"
              disabled={!input.trim() || isLoading}
              className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 bg-foreground hover:opacity-90 disabled:bg-secondary disabled:text-muted-foreground text-background rounded-lg flex items-center justify-center transition cursor-pointer"
            >
              <Send size={14} />
            </button>
          </form>
          <div className="text-center mt-2.5 flex items-center justify-center gap-1.5 text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
            <AlertCircle size={10} />
            <span>Operational records are indexed dynamically. Validate responses against cited manuals.</span>
          </div>
        </div>
      </div>
    </div>
  );
}
