"use client";

import React from "react";
import { ArrowLeft, UserCircle, CheckCircle, FileText, Bot } from "lucide-react";
import Link from "next/link";

export default function CandidateDetailPage() {
  const candidate = {
    name: "Alice Johnson",
    role: "Senior Frontend Engineer",
    email: "alice.j@example.com",
    match: 92,
    status: "Shortlisted",
    aiSummary: "Alice is an exceptionally strong match for the Senior Frontend Engineer role. She possesses 6 years of deep React experience and has previously migrated large codebases to Next.js. She also demonstrates strong leadership traits.",
    strengths: ["React Performance Optimization", "Next.js 14/15", "Team Leadership", "TypeScript Mastery"],
    weaknesses: ["No explicit mention of GraphQL experience (nice-to-have)"],
    recommendation: "Strongly Recommend Interview",
  };

  return (
    <div className="space-y-8 pb-10">
      <Link href="/resume-screening" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground font-medium transition-colors">
        <ArrowLeft size={16} />
        Back to Candidates
      </Link>

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Left Column: Profile & Resume Preview */}
        <div className="lg:w-1/2 space-y-6">
          <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
            <div className="flex items-start justify-between">
              <div className="flex gap-5">
                <UserCircle size={64} className="text-muted-foreground stroke-[1.5]" />
                <div>
                  <h1 className="text-2xl font-bold tracking-tight text-foreground">{candidate.name}</h1>
                  <p className="text-sm font-medium text-muted-foreground mt-0.5">{candidate.role}</p>
                  <p className="text-xs text-muted-foreground mt-1 bg-secondary inline-block px-2 py-0.5 rounded border border-border/50">{candidate.email}</p>
                </div>
              </div>
              <span className="px-3 py-1 bg-foreground text-background text-xs uppercase tracking-wider rounded-md font-semibold">
                {candidate.status}
              </span>
            </div>
          </div>

          <div className="bg-card border border-border rounded-xl p-6 flex-1 min-h-[500px] flex flex-col shadow-sm">
            <h3 className="font-semibold text-sm uppercase tracking-wide text-foreground mb-4 flex items-center gap-2">
              <FileText size={16} className="text-muted-foreground" /> Original Resume
            </h3>
            <div className="flex-1 bg-secondary/50 rounded-lg border border-border flex items-center justify-center text-muted-foreground text-sm font-medium border-dashed">
              [PDF Viewer Component Integration Here]
            </div>
          </div>
        </div>

        {/* Right Column: AI Match & Insights */}
        <div className="lg:w-1/2 space-y-6">
          <div className="bg-card border border-border rounded-xl p-6 shadow-sm relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-foreground/5 rounded-bl-full -z-10"></div>
            <div className="flex items-center justify-between mb-6">
              <h3 className="font-semibold flex items-center gap-2 text-foreground tracking-tight">
                <div className="p-1.5 bg-foreground text-background rounded-md">
                  <Bot size={16} />
                </div>
                AI Evaluation
              </h3>
              <div className="text-right flex items-center gap-3">
                <div className="text-right">
                  <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold block mb-0.5">Match Score</span>
                  <div className="flex items-center justify-end gap-2">
                    <div className="w-20 h-1.5 bg-secondary rounded-full overflow-hidden">
                      <div className="h-full bg-foreground" style={{ width: `${candidate.match}%` }}></div>
                    </div>
                  </div>
                </div>
                <span className="text-2xl font-bold tracking-tight text-foreground">{candidate.match}%</span>
              </div>
            </div>
            
            <div className="bg-secondary/50 border border-border rounded-lg p-4 mb-6">
              <p className="text-sm text-muted-foreground leading-relaxed">
                {candidate.aiSummary}
              </p>
            </div>
            
            <div className="space-y-6 mt-6">
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-foreground mb-3 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-foreground"></span>
                  Strengths
                </h4>
                <ul className="space-y-2.5">
                  {candidate.strengths.map((s, i) => (
                    <li key={i} className="text-sm text-muted-foreground flex items-start gap-3">
                      <CheckCircle size={16} className="text-foreground shrink-0 mt-0.5" />
                      {s}
                    </li>
                  ))}
                </ul>
              </div>
              
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-foreground mb-3 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-muted-foreground"></span>
                  Missing / Weaknesses
                </h4>
                <ul className="space-y-2.5">
                  {candidate.weaknesses.map((w, i) => (
                    <li key={i} className="text-sm text-muted-foreground flex items-start gap-3">
                      <div className="w-1.5 h-1.5 rounded-full bg-muted-foreground shrink-0 mt-2 ml-1" />
                      {w}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
            
            <div className="mt-8 pt-6 border-t border-border">
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Recommendation</span>
                <span className="px-4 py-1.5 bg-foreground text-background text-xs uppercase tracking-wider rounded-md font-semibold">
                  {candidate.recommendation}
                </span>
              </div>
            </div>
          </div>
          
          <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
            <h3 className="font-semibold text-sm uppercase tracking-wide text-foreground mb-4">Recruiter Actions</h3>
            <div className="flex flex-col sm:flex-row gap-3">
              <button className="flex-1 bg-foreground hover:bg-foreground/90 text-background py-2.5 rounded-md text-sm font-semibold transition-all shadow-sm">
                Schedule Interview
              </button>
              <button className="flex-1 bg-secondary hover:bg-secondary/80 text-foreground border border-border py-2.5 rounded-md text-sm font-semibold transition-all">
                Reject Candidate
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
