"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  BookOpen,
  Send,
  UploadCloud,
  FileText,
  User,
  Bot,
  Link2,
  ChevronRight,
  Info,
  Sparkles,
  Plus,
  ArrowUpRight,
  Search,
  CheckCircle,
  HelpCircle
} from "lucide-react";

interface DocumentMeta {
  id: string;
  title: string;
  category: string;
  fileType: string;
  fileSize: string;
  uploadedAt: string;
}

interface ChatReference {
  document_title: string;
  file_path: string;
  matched_text: string;
}

interface ChatMessage {
  id: string;
  sender: "USER" | "AI";
  text: string;
  timestamp: string;
  references?: ChatReference[];
}

export default function KnowledgeAssistant() {
  // 1. Initial State for documents catalog
  const [documents, setDocuments] = useState<DocumentMeta[]>([
    {
      id: "doc-1",
      title: "Employee Code of Conduct & Ethics Manual",
      category: "HR & Policies",
      fileType: "PDF",
      fileSize: "1.2 MB",
      uploadedAt: "2026-05-20"
    },
    {
      id: "doc-2",
      title: "Annual Leave & Workplace Wellness SOP",
      category: "Benefits",
      fileType: "PDF",
      fileSize: "850 KB",
      uploadedAt: "2026-05-22"
    },
    {
      id: "doc-3",
      title: "IT Equipment Security & Access Policy",
      category: "Information Security",
      fileType: "PDF",
      fileSize: "520 KB",
      uploadedAt: "2026-05-24"
    }
  ]);

  // 2. Chat history initial state
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "msg-1",
      sender: "AI",
      text: "Hello! I am your Enterprise Knowledge Assistant. I can help you search, summarize, and understand company policies, SOPs, and employee manuals. What question can I help you with today?",
      timestamp: "17:45"
    }
  ]);

  const [inputText, setInputText] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [newDocTitle, setNewDocTitle] = useState("");
  const [newDocCategory, setNewDocCategory] = useState("HR & Policies");
  const [uploadFileName, setUploadFileName] = useState("");
  const [activeReference, setActiveReference] = useState<ChatReference | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom of chat log
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      sender: "USER",
      text: inputText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    setInputText("");
    setIsTyping(true);

    // Simulate RAG endpoint search & response
    setTimeout(() => {
      let aiResponseText = "";
      let aiRefs: ChatReference[] = [];

      const queryLower = userMsg.text.toLowerCase();

      if (queryLower.includes("leave") || queryLower.includes("vacation") || queryLower.includes("holiday")) {
        aiResponseText = "According to Section 4.2 of the **Annual Leave & Workplace Wellness SOP**, full-time employees are allocated **25 standard leaves per calendar year**. These accrue monthly at a rate of 2.08 days. Unused leaves up to 10 days can be rolled over to the subsequent year. All vacation leaves exceeding 3 consecutive days must be requested in the system at least two weeks in advance for manager approval.";
        aiRefs = [
          {
            document_title: "Annual Leave & Workplace Wellness SOP",
            file_path: "annual_leave_policy.pdf",
            matched_text: "Section 4.2: Standard Leave Allocation. Full-time employees accrue 2.08 days of paid annual leave per month, culminating in a total of 25 days per calendar year. Rollover of unused leave balance is strictly capped at a maximum of 10 working days annually."
          }
        ];
      } else if (queryLower.includes("laptop") || queryLower.includes("password") || queryLower.includes("security") || queryLower.includes("device")) {
        aiResponseText = "As per the **IT Equipment Security & Access Policy**, employees are issued enterprise-managed laptops and are fully responsible for asset protection. Laptops must not be left unattended in public zones. Password changes are mandated every 90 days, requiring at least 12 characters including digits and special symbols. Connecting personal USB storage devices is prohibited without IT security approval.";
        aiRefs = [
          {
            document_title: "IT Equipment Security & Access Policy",
            file_path: "it_security_policy.pdf",
            matched_text: "Section 2.1: Device Security. Issued hardware is property of the company. Connecting unauthorized personal storage media or peripheral equipment is strictly forbidden under corporate information defense regulations."
          }
        ];
      } else {
        aiResponseText = "Based on our indexed company documents, I found guidelines on general compliance. Employees must act in compliance with the **Employee Code of Conduct & Ethics Manual**. If you have a specific question about benefits, office access, or travel expenses, please specify so I can run a vector search in ChromaDB and locate the exact policy clause.";
        aiRefs = [
          {
            document_title: "Employee Code of Conduct & Ethics Manual",
            file_path: "ethics_code.pdf",
            matched_text: "Section 1.1: General Conduct. All employees of Sopra Steria must perform duties with professionalism, integrity, and absolute adherence to local state laws and standard corporate policies."
          }
        ];
      }

      const aiMsg: ChatMessage = {
        id: `msg-${Date.now() + 1}`,
        sender: "AI",
        text: aiResponseText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        references: aiRefs
      };

      setMessages(prev => [...prev, aiMsg]);
      setIsTyping(false);
    }, 2000);
  };

  const handleCreateDocument = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDocTitle || !uploadFileName) return;

    const newDoc: DocumentMeta = {
      id: `doc-${Date.now()}`,
      title: newDocTitle,
      category: newDocCategory,
      fileType: "PDF",
      fileSize: "1.1 MB",
      uploadedAt: new Date().toISOString().split("T")[0]
    };

    setDocuments([newDoc, ...documents]);
    setShowUploadModal(false);
    
    // Reset states
    setNewDocTitle("");
    setUploadFileName("");

    // Show a success message in chat simulation
    setMessages(prev => [
      ...prev,
      {
        id: `msg-success-${Date.now()}`,
        sender: "AI",
        text: `Success! I have chunked and vectorized **"${newDoc.title}"** into ChromaDB. Its content is now fully searchable for RAG-based context querying.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ]);
  };

  return (
    <div className="space-y-6">
      {/* Overview Intro */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Enterprise Knowledge Assistant (RAG)</h2>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
            Search policies, manuals, and SOPs in plain natural language. Get cited references instantly using ChromaDB semantic search.
          </p>
        </div>
        <button
          onClick={() => setShowUploadModal(true)}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2.5 rounded-lg text-sm font-semibold transition-all shadow cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>Upload Policy Manual</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 h-[calc(100vh-230px)] min-h-[500px]">
        {/* Left 1/4 Column: Documents Catalog */}
        <div className="lg:col-span-1 bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-xl p-4 flex flex-col h-full overflow-hidden">
          <h3 className="font-bold text-sm text-slate-700 dark:text-slate-300 mb-3 flex items-center gap-2 flex-shrink-0">
            <BookOpen className="w-4.5 h-4.5 text-blue-600" />
            <span>Document Repository</span>
          </h3>

          {/* Simple search bar */}
          <div className="relative mb-3 flex-shrink-0">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search indexed manuals..."
              className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs focus:outline-none focus:border-blue-600"
            />
          </div>

          {/* Document list */}
          <div className="flex-1 overflow-y-auto space-y-2 pr-1">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="p-3 border border-slate-100 dark:border-slate-850 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors space-y-1.5"
              >
                <div className="flex gap-2 items-start">
                  <FileText className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
                  <span className="font-semibold text-xs leading-snug text-slate-800 dark:text-slate-200 line-clamp-2">
                    {doc.title}
                  </span>
                </div>
                <div className="flex justify-between items-center text-[10px] text-slate-400">
                  <span className="bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded text-slate-500 uppercase tracking-wider font-semibold">
                    {doc.category}
                  </span>
                  <span>{doc.uploadedAt}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right 3/4 Column: RAG Conversation Window */}
        <div className="lg:col-span-3 bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-xl flex flex-col h-full overflow-hidden relative">
          
          {/* Chat header */}
          <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center bg-slate-50/50 dark:bg-[#111827] flex-shrink-0">
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></div>
              <span className="font-bold text-xs uppercase tracking-widest text-slate-400 flex items-center gap-1">
                <Sparkles className="w-3.5 h-3.5 text-blue-500" />
                <span>RAG AI System Online</span>
              </span>
            </div>
            <span className="text-xs text-slate-400">Model: GPT-4o + ChromaDB</span>
          </div>

          {/* Conversation list log */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-4 max-w-[85%] ${msg.sender === "USER" ? "ml-auto flex-row-reverse" : ""}`}
              >
                {/* Avatar */}
                <div className={`h-8 w-8 rounded-full flex-shrink-0 flex items-center justify-center ${
                  msg.sender === "USER" 
                    ? "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300"
                    : "bg-blue-100 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400"
                }`}>
                  {msg.sender === "USER" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </div>

                {/* Message block */}
                <div className="space-y-1.5">
                  <div className={`p-4 rounded-2xl text-sm leading-relaxed ${
                    msg.sender === "USER"
                      ? "bg-blue-600 text-white rounded-tr-none"
                      : "bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-tl-none text-slate-800 dark:text-slate-200"
                  }`}>
                    {msg.text}
                  </div>

                  {/* Render citations references */}
                  {msg.references && msg.references.length > 0 && (
                    <div className="flex flex-wrap gap-2 items-center text-xs text-slate-400 pt-1 pl-1">
                      <span className="flex items-center gap-1 font-semibold text-[10px] text-slate-400 uppercase tracking-widest">
                        <Link2 className="w-3 h-3 text-blue-500" />
                        <span>Sources:</span>
                      </span>
                      {msg.references.map((ref, idx) => (
                        <button
                          key={idx}
                          onClick={() => setActiveReference(ref)}
                          className="flex items-center gap-1 bg-slate-50 dark:bg-slate-900 border border-slate-150 dark:border-slate-800 px-2 py-0.5 rounded text-[11px] text-blue-600 dark:text-blue-400 hover:border-blue-300 hover:bg-blue-50/20 transition-all cursor-pointer font-semibold"
                        >
                          <span>{ref.document_title}</span>
                          <ArrowUpRight className="w-3 h-3" />
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Simulated typing bubble */}
            {isTyping && (
              <div className="flex gap-4 max-w-[80%]">
                <div className="h-8 w-8 rounded-full bg-blue-100 dark:bg-blue-950/40 text-blue-600 flex items-center justify-center flex-shrink-0">
                  <Bot className="w-4 h-4" />
                </div>
                <div className="bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 p-4 rounded-2xl rounded-tl-none flex items-center gap-1">
                  <span className="h-2 w-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></span>
                  <span className="h-2 w-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></span>
                  <span className="h-2 w-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></span>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Form message input */}
          <form onSubmit={handleSendMessage} className="p-4 border-t border-slate-200 dark:border-slate-800 flex-shrink-0 bg-white dark:bg-[#111827]">
            <div className="flex gap-3 items-center">
              <input
                type="text"
                required
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Ask leaves allowance, IT security codes, emergency rules..."
                className="flex-1 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-blue-600"
              />
              <button
                type="submit"
                disabled={isTyping}
                className="h-10 w-10 bg-blue-600 hover:bg-blue-700 text-white rounded-xl flex items-center justify-center shadow-md shadow-blue-500/10 cursor-pointer disabled:opacity-50 transition-all flex-shrink-0"
              >
                <Send className="w-4.5 h-4.5" />
              </button>
            </div>
          </form>

          {/* Reference Side Drawer panel overlay */}
          {activeReference && (
            <div className="absolute top-0 right-0 w-80 h-full bg-white dark:bg-[#111827] border-l border-slate-200 dark:border-slate-800 z-30 shadow-2xl flex flex-col animate-fade-in">
              <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center bg-slate-50/50 dark:bg-[#111827]">
                <span className="text-[10px] font-bold text-blue-600 dark:text-blue-400 uppercase tracking-widest">Document Citation Details</span>
                <button
                  onClick={() => setActiveReference(null)}
                  className="p-1 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full cursor-pointer text-xs font-bold"
                >
                  Close
                </button>
              </div>
              <div className="p-5 flex-1 overflow-y-auto space-y-4">
                <div className="flex items-start gap-2">
                  <FileText className="w-5 h-5 text-blue-500 mt-0.5 flex-shrink-0" />
                  <div>
                    <h4 className="font-bold text-sm leading-snug">{activeReference.document_title}</h4>
                    <p className="text-[10px] text-slate-400 mt-0.5">File: {activeReference.file_path}</p>
                  </div>
                </div>
                
                <div className="space-y-1.5 pt-4 border-t border-slate-150 dark:border-slate-800">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Semantic Match Excerpt</span>
                  <div className="bg-slate-50 dark:bg-slate-900 p-4 border border-slate-150 dark:border-slate-800 rounded-lg text-xs leading-relaxed text-slate-600 dark:text-slate-350 italic">
                    "{activeReference.matched_text}"
                  </div>
                </div>

                <div className="pt-2 flex items-center gap-1.5 text-[10px] text-slate-400 leading-snug">
                  <Info className="w-3.5 h-3.5 text-blue-500" />
                  <span>This document snippet was fetched via cosine similarity embeddings matches in ChromaDB.</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* UPLOAD MANUAL MODAL */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 w-full max-w-md rounded-xl overflow-hidden shadow-2xl animate-fade-in">
            <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center">
              <h3 className="font-bold text-lg">Upload Knowledge Manual</h3>
              <button onClick={() => setShowUploadModal(false)} className="p-1 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full cursor-pointer">
                <X className="w-4 h-4 text-slate-400" />
              </button>
            </div>

            <form onSubmit={handleCreateDocument} className="p-5 space-y-4">
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-400 uppercase">Manual Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Travel & Entertainment Expense Policy"
                  value={newDocTitle}
                  onChange={(e) => setNewDocTitle(e.target.value)}
                  className="w-full bg-transparent border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-blue-600"
                />
              </div>

              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-400 uppercase">Category</label>
                <select
                  value={newDocCategory}
                  onChange={(e) => setNewDocCategory(e.target.value)}
                  className="w-full bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-2 text-xs focus:outline-none"
                >
                  <option value="HR & Policies">HR & Policies</option>
                  <option value="Benefits">Benefits</option>
                  <option value="Information Security">Information Security</option>
                  <option value="Corporate Operations">Corporate Operations</option>
                </select>
              </div>

              <div className="border-2 border-dashed border-slate-200 dark:border-slate-800 hover:border-blue-500 rounded-lg p-6 text-center transition-colors relative cursor-pointer group">
                <input
                  type="file"
                  required
                  accept=".pdf,.docx,.txt"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) setUploadFileName(file.name);
                  }}
                  className="absolute inset-0 opacity-0 cursor-pointer"
                />
                <UploadCloud className="w-8 h-8 text-slate-400 group-hover:text-blue-500 mx-auto transition-colors" />
                <p className="text-xs font-bold text-slate-600 mt-2">
                  {uploadFileName ? uploadFileName : "Select policy PDF or document file"}
                </p>
                <p className="text-[10px] text-slate-400 mt-0.5">PDF, DOCX, TXT files up to 20MB</p>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-850">
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="px-4 py-2 border border-slate-200 dark:border-slate-800 rounded-lg text-xs font-semibold hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold cursor-pointer"
                >
                  Chunk & Index Document
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
