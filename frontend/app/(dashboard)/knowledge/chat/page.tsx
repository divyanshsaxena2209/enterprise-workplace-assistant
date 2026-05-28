"use client";

import React, { useState } from "react";
import { Send, Bot, User, Sparkles } from "lucide-react";

export default function KnowledgeChat() {
  const [messages, setMessages] = useState([
    { id: 1, role: "assistant", content: "Hi there! I'm your Enterprise Knowledge Assistant. You can ask me anything about company policies, engineering documentation, or recent project updates." }
  ]);
  const [input, setInput] = useState("");

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    
    const newMsg = { id: Date.now(), role: "user", content: input };
    setMessages([...messages, newMsg]);
    setInput("");
    
    // Simulate AI streaming response
    setTimeout(() => {
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: "assistant",
        content: "Based on the Q3 Engineering Roadmap (DocID: 2), we are prioritizing the migration to Next.js 15 and implementing the new RAG pipeline for the knowledge assistant module."
      }]);
    }, 1000);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <div className="flex-1 bg-white dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-2xl flex flex-col shadow-sm overflow-hidden">
        
        {/* Header */}
        <div className="h-16 border-b border-gray-100 dark:border-gray-800 flex items-center px-6 gap-3">
          <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 dark:bg-blue-900/30 flex items-center justify-center">
            <Sparkles size={16} />
          </div>
          <div>
            <h2 className="font-semibold">Enterprise Copilot</h2>
            <p className="text-xs text-gray-500">Powered by GPT-4o & ChromaDB</p>
          </div>
        </div>

        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.map(msg => (
            <div key={msg.id} className={`flex gap-4 max-w-3xl ${msg.role === "user" ? "ml-auto flex-row-reverse" : ""}`}>
              <div className={`w-8 h-8 shrink-0 rounded-full flex items-center justify-center ${msg.role === "user" ? "bg-gray-900 text-white dark:bg-gray-100 dark:text-gray-900" : "bg-blue-600 text-white"}`}>
                {msg.role === "user" ? <User size={16} /> : <Bot size={16} />}
              </div>
              <div className={`px-5 py-3 rounded-2xl text-sm leading-relaxed ${
                msg.role === "user" 
                ? "bg-gray-100 dark:bg-gray-800" 
                : "bg-blue-50/50 dark:bg-blue-900/10 border border-blue-100 dark:border-blue-900/30"
              }`}>
                {msg.content}
                {msg.role === "assistant" && msg.id > 1 && (
                  <div className="mt-3 pt-3 border-t border-blue-200/50 dark:border-blue-800/50">
                    <span className="text-xs font-semibold text-gray-500 block mb-1">Sources:</span>
                    <span className="inline-flex items-center gap-1 px-2 py-1 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded text-xs text-blue-600 cursor-pointer hover:bg-gray-50">
                      Q3 Engineering Roadmap
                    </span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-gray-100 dark:border-gray-800">
          <form onSubmit={handleSend} className="relative max-w-4xl mx-auto">
            <input 
              type="text" 
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Ask a question about enterprise knowledge..."
              className="w-full pl-4 pr-12 py-3 rounded-xl border border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 shadow-sm"
            />
            <button 
              type="submit"
              disabled={!input.trim()}
              className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white rounded-lg flex items-center justify-center transition"
            >
              <Send size={16} className="-ml-0.5" />
            </button>
          </form>
          <div className="text-center mt-2">
            <p className="text-xs text-gray-400">AI can make mistakes. Verify important information with cited sources.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
