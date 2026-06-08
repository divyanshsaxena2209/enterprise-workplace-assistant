"use client";

import React, { useState } from "react";
import { Search, Upload, MessageSquare, FileText, Database, MoreHorizontal, Sparkles } from "lucide-react";
import Link from "next/link";
import { useUser } from "@/lib/context/UserContext";

export default function KnowledgeDashboard() {
  const { profile } = useUser();
  const [documents] = useState([
    { id: 1, title: "Employee Operations Handbook 2026.pdf", dept: "HR Operations", uploaded: "2 days ago", size: "2.4 MB" },
    { id: 2, title: "Q3 System Architecture Roadmap.docx", dept: "Engineering", uploaded: "5 days ago", size: "1.1 MB" },
    { id: 3, title: "Sales Execution & Strategy v4.pdf", dept: "Revenue Operations", uploaded: "1 week ago", size: "3.8 MB" },
  ]);

  return (
    <div className="space-y-8 pb-10">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
        <div>
          <h1 className="text-2xl font-black tracking-tight flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-foreground animate-pulse" />
            Organizational Intelligence Hub
          </h1>
          <p className="text-sm text-muted-foreground mt-1">Execute query pipelines and perform semantic search across corporate indices.</p>
        </div>
        <div className="flex gap-3">
          <Link 
            href="/knowledge/chat" 
            className="flex items-center gap-2 bg-foreground hover:bg-foreground/90 text-background px-4 py-2.5 rounded-lg text-xs font-bold uppercase tracking-wider transition-all shadow-sm"
          >
            <MessageSquare size={14} />
            Query Corporate Intelligence
          </Link>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 bg-foreground rounded-2xl shadow-sm text-background flex flex-col justify-between h-40">
          <Database size={24} className="opacity-80" />
          <div>
            <h3 className="text-4xl font-black tracking-tight">1,204</h3>
            <p className="text-background/80 font-bold text-[10px] uppercase tracking-wider mt-2">Indexed Knowledge Documents</p>
          </div>
        </div>
        <div className="p-6 bg-card border border-border rounded-2xl shadow-sm flex flex-col justify-between h-40">
          <Search size={24} className="text-foreground" />
          <div>
            <h3 className="text-3xl font-bold tracking-tight">15K+</h3>
            <p className="text-muted-foreground font-bold text-[10px] uppercase tracking-wider mt-2">Semantic Searches Run</p>
          </div>
        </div>
        <div className="p-6 bg-card border border-border rounded-2xl shadow-sm flex flex-col justify-between h-40">
          <FileText size={24} className="text-foreground" />
          <div>
            <h3 className="text-3xl font-bold tracking-tight">98%</h3>
            <p className="text-muted-foreground font-bold text-[10px] uppercase tracking-wider mt-2">Vector Retrieval Precision</p>
          </div>
        </div>
      </div>

      {/* Document Records */}
      <div className="bg-card border border-border rounded-2xl shadow-sm overflow-hidden">
        <div className="p-5 border-b border-border/50 flex justify-between items-center bg-secondary/50">
          <h3 className="font-bold text-xs uppercase tracking-wider text-foreground">Recently Indexed Assets</h3>
        </div>
        <div className="divide-y divide-border/50">
          {documents.map(doc => (
            <div key={doc.id} className="p-5 flex items-center justify-between hover:bg-secondary/30 transition-colors group">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-lg border border-border flex items-center justify-center bg-background text-muted-foreground group-hover:text-foreground transition-colors shadow-sm">
                  <FileText size={18} />
                </div>
                <div>
                  <h4 className="font-semibold text-sm text-foreground tracking-tight">{doc.title}</h4>
                  <p className="text-xs text-muted-foreground mt-0.5">Ingested {doc.uploaded} • {doc.size}</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <span className="px-2.5 py-0.5 bg-secondary border border-border/50 text-[9px] uppercase tracking-wider rounded-full font-bold text-muted-foreground">
                  {doc.dept}
                </span>
                <button className="text-muted-foreground hover:text-foreground p-1 rounded-lg hover:bg-secondary transition-colors">
                  <MoreHorizontal size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
