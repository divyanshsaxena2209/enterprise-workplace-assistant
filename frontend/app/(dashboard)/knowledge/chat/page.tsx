"use client";

import React, { useState } from "react";
import { Send, Bot, User, Sparkles, AlertCircle } from "lucide-react";
import { useUser } from "@/lib/context/UserContext";

export default function KnowledgeChat() {
  const { profile } = useUser();
  const [messages, setMessages] = useState([
    { 
      id: 1, 
      role: "assistant", 
      content: "Welcome to the Organizational Intelligence Console. I can retrieve details from corporate policies, standard operating procedures, and technical documentation." 
    }
  ]);
  const [input, setInput] = useState("");

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    
    const newMsg = { id: Date.now(), role: "user", content: input };
    setMessages([...messages, newMsg]);
    setInput("");
    
    // Simulate AI response
    setTimeout(() => {
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: "assistant",
        content: "Based on the Q3 Systems Architecture Roadmap, we are prioritizing the migration to Next.js 15 routing models and implementing a unified vector search pipeline for data discovery."
      }]);
    }, 1000);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <div className="flex-1 bg-card border border-border rounded-2xl flex flex-col shadow-sm overflow-hidden">
        
        {/* Header */}
        <div className="h-16 border-b border-border flex items-center px-6 gap-3 bg-secondary/30">
          <div className="w-8 h-8 rounded-lg bg-secondary border border-border/50 text-foreground flex items-center justify-center">
            <Sparkles size={14} />
          </div>
          <div>
            <h2 className="font-bold text-sm tracking-tight text-foreground">Organizational Intelligence Engine</h2>
            <p className="text-[9px] text-muted-foreground font-semibold uppercase tracking-wider">Semantic Document Discovery</p>
          </div>
        </div>

        {/* Chat Area */}
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
                {msg.content}
                {msg.role === "assistant" && msg.id > 1 && (
                  <div className="mt-3 pt-3 border-t border-border/50">
                    <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest block mb-1.5">Referenced Records</span>
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 bg-secondary border border-border/50 rounded-full text-[10px] font-semibold text-foreground cursor-pointer hover:bg-background transition-colors">
                      Q3 Systems Architecture Roadmap
                    </span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-border bg-card">
          <form onSubmit={handleSend} className="relative max-w-4xl mx-auto flex gap-2">
            <input 
              type="text" 
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Enter operational query..."
              className="w-full pl-4 pr-12 py-3 rounded-xl border border-border bg-secondary/30 text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-ring focus:border-ring transition-all placeholder:text-muted-foreground shadow-sm"
            />
            <button 
              type="submit"
              disabled={!input.trim()}
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
