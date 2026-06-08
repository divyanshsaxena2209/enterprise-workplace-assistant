"use client";

import React, { useState } from "react";
import { Upload, Search, Filter, MoreHorizontal, FileText, Sparkles, CheckCircle2 } from "lucide-react";

export default function ResumeScreeningPage() {
  const [activeTab, setActiveTab] = useState("candidates");

  return (
    <div className="space-y-8 pb-10">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-foreground flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-foreground animate-pulse" />
            Candidate Suitability Screening
          </h1>
          <p className="text-sm text-muted-foreground mt-1">Review AI suitability scores, match factors, and rank candidates across active requisitions.</p>
        </div>
        <div className="flex p-1 bg-secondary rounded-xl border border-border/50">
          <button
            onClick={() => setActiveTab("candidates")}
            className={`px-4 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wider transition-all cursor-pointer ${activeTab === "candidates" ? "bg-card shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground"}`}
          >
            Evaluated Personnel
          </button>
          <button
            onClick={() => setActiveTab("upload")}
            className={`px-4 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wider transition-all cursor-pointer ${activeTab === "upload" ? "bg-card shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground"}`}
          >
            Ingest Resumes
          </button>
        </div>
      </div>

      {activeTab === "upload" ? <ResumeUploadFlow /> : <CandidateDashboard />}
    </div>
  );
}

function ResumeUploadFlow() {
  return (
    <div className="bg-card border border-border rounded-2xl p-10 flex flex-col items-center justify-center text-center min-h-[400px] border-dashed shadow-sm">
      <div className="w-16 h-16 bg-secondary rounded-full flex items-center justify-center text-foreground mb-5 border border-border/50 shadow-sm">
        <Upload size={24} />
      </div>
      <h3 className="text-lg font-bold tracking-tight mb-2 text-foreground">Ingest Candidate Resumes</h3>
      <p className="text-sm text-muted-foreground mb-8 max-w-sm leading-relaxed">
        Upload resumes in PDF or DOCX format. The parser pipeline will extract skills, experience, and score suitability against requisitions.
      </p>
      <button className="bg-foreground hover:bg-foreground/90 text-background px-6 py-3 rounded-lg text-xs font-bold uppercase tracking-wider transition-all shadow-sm flex items-center gap-2 cursor-pointer">
        <FileText size={14} />
        Select Files for Ingestion
      </button>
    </div>
  );
}

function CandidateDashboard() {
  const candidates = [
    { id: 1, name: "Alice Johnson", role: "Senior Frontend Engineer", match: 96, status: "Shortlisted", time: "2h ago" },
    { id: 2, name: "Bob Smith", role: "Senior Frontend Engineer", match: 84, status: "Reviewing", time: "5h ago" },
    { id: 3, name: "Charlie Davis", role: "Product Manager", match: 91, status: "Interview Panel", time: "1d ago" },
    { id: 4, name: "Diana Prince", role: "UX Architect", match: 72, status: "Registered", time: "2d ago" },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
      
      {/* Sidebar Filters */}
      <div className="md:col-span-1 space-y-4">
        <div className="flex items-center gap-2 text-muted-foreground mb-2">
          <Filter size={14} />
          <span className="font-bold text-[10px] uppercase tracking-wider">Active Filters</span>
        </div>
        <div className="p-5 bg-card border border-border rounded-2xl space-y-5 shadow-sm">
          <div>
            <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider mb-2 block">Job Requisition</label>
            <select className="w-full text-xs border border-border bg-background rounded-lg px-3 py-2.5 focus:ring-1 focus:ring-ring focus:border-ring outline-none font-medium cursor-pointer">
              <option>All Active Roles</option>
              <option>Senior Frontend Engineer</option>
              <option>Product Manager</option>
              <option>UX Architect</option>
            </select>
          </div>
          <div>
            <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider mb-2 block">Workflow Stage</label>
            <select className="w-full text-xs border border-border bg-background rounded-lg px-3 py-2.5 focus:ring-1 focus:ring-ring focus:border-ring outline-none font-medium cursor-pointer">
              <option>All Stages</option>
              <option>Registered</option>
              <option>Reviewing</option>
              <option>Shortlisted</option>
              <option>Interview Panel</option>
            </select>
          </div>
        </div>
      </div>

      {/* Candidates List */}
      <div className="md:col-span-3 space-y-3">
        <div className="flex items-center justify-between mb-2">
          <div className="relative w-full max-w-sm">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" size={14} />
            <input
              type="text"
              placeholder="Search evaluated records..."
              className="w-full pl-10 pr-4 py-2 rounded-lg border border-border bg-card text-xs font-semibold focus:outline-none focus:ring-1 focus:ring-ring shadow-sm"
            />
          </div>
          <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">{candidates.length} Profiles Listed</span>
        </div>

        {candidates.map((c) => (
          <div key={c.id} className="p-5 bg-card border border-border rounded-2xl hover:border-foreground/20 hover:shadow-sm cursor-pointer transition-all flex items-center justify-between group">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-xl bg-secondary flex items-center justify-center text-muted-foreground group-hover:text-foreground transition-colors border border-border/50">
                <FileText size={18} />
              </div>
              <div>
                <h4 className="font-bold text-sm text-foreground tracking-tight">{c.name}</h4>
                <p className="text-xs text-muted-foreground mt-0.5">{c.role} • Registered {c.time}</p>
              </div>
            </div>
            <div className="flex items-center gap-6">
              <div className="text-right">
                <div className="text-[9px] uppercase tracking-wider text-muted-foreground font-bold mb-1">Match Index</div>
                <div className="flex items-center justify-end gap-2">
                  <div className="w-16 h-1.5 bg-secondary rounded-full overflow-hidden">
                    <div
                      className={`h-full ${c.match >= 90 ? 'bg-foreground' : 'bg-muted-foreground'}`}
                      style={{ width: `${c.match}%` }}
                    ></div>
                  </div>
                  <span className="font-bold text-xs text-foreground w-8">{c.match}%</span>
                </div>
              </div>
              <span className="px-2.5 py-1 bg-secondary border border-border/50 text-[10px] uppercase font-bold tracking-wider rounded-md text-foreground w-28 text-center shadow-sm">
                {c.status}
              </span>
              <button className="text-muted-foreground hover:text-foreground p-1 rounded-lg hover:bg-secondary transition-colors">
                <MoreHorizontal size={18} />
              </button>
            </div>
          </div>
        ))}
      </div>

    </div>
  );
}
