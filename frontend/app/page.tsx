"use client";

import React from "react";
import Link from "next/link";
import {
  Sparkles,
  ArrowRight,
  Briefcase,
  ClipboardCheck,
  BookOpen,
  Video,
  ShieldCheck,
  Zap,
  Check
} from "lucide-react";

export default function Home() {
  const modules = [
    {
      title: "AI Resume Screening & Hiring",
      desc: "Upload candidates resumes in PDF/DOCX. Automatically parse, score, and rank suitability using GPT-4o.",
      icon: Briefcase,
      color: "text-blue-500",
      bg: "bg-blue-500/10"
    },
    {
      title: "Employee Onboarding Automation",
      desc: "Simplify new-hire processes. Enable progress milestone trackers, document upload portals, and HR audits.",
      icon: ClipboardCheck,
      color: "text-emerald-500",
      bg: "bg-emerald-500/10"
    },
    {
      title: "Enterprise Knowledge Assistant",
      desc: "Interact with corporate SOP policies and employee manuals via natural language semantic RAG chat.",
      icon: BookOpen,
      color: "text-purple-500",
      bg: "bg-purple-500/10"
    },
    {
      title: "AI Meeting Minutes & Transcriber",
      desc: "Translate meeting voice files to structured transcripts, markdown summaries, and automated checklist items.",
      icon: Video,
      color: "text-amber-500",
      bg: "bg-amber-500/10"
    }
  ];

  return (
    <div className="bg-[#090d16] text-slate-100 min-h-screen selection:bg-blue-600/30">
      
      {/* 1. Header Navigation */}
      <header className="h-16 max-w-7xl mx-auto px-6 flex items-center justify-between border-b border-slate-800/40">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold text-lg">
            S
          </div>
          <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-blue-500 to-indigo-400 bg-clip-text text-transparent">
            Sopra Assistant
          </span>
        </div>

        <Link
          href="/dashboard"
          className="flex items-center gap-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 px-4 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer"
        >
          <span>Launch Dashboard</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </header>

      {/* 2. Hero Section */}
      <section className="max-w-7xl mx-auto px-6 py-20 md:py-28 text-center space-y-8 relative overflow-hidden">
        {/* Abstract blur background light */}
        <div className="absolute top-10 left-1/2 -translate-x-1/2 w-80 h-80 rounded-full bg-blue-500/10 blur-[100px] -z-10"></div>
        
        <div className="inline-flex items-center gap-2 bg-blue-950/40 border border-blue-900/60 rounded-full px-3.5 py-1 text-xs text-blue-400 font-semibold mb-2">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Next-Generation Enterprise AI Platform</span>
        </div>

        <h1 className="text-4xl md:text-6xl font-black tracking-tight max-w-4xl mx-auto leading-[1.1] bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
          Automate Workplace Workflows With Advanced Intelligence
        </h1>

        <p className="text-slate-400 text-sm md:text-lg max-w-2xl mx-auto leading-relaxed">
          Unify hiring evaluations, new-hire onboarding tracking, company policy semantic search, and speech meeting minute extractions on a single production-grade corporate AI system.
        </p>

        <div className="flex flex-col sm:flex-row justify-center items-center gap-4 pt-4">
          <Link
            href="/dashboard"
            className="flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg text-sm font-semibold transition-all shadow-lg shadow-blue-500/20 w-full sm:w-auto cursor-pointer"
          >
            <span>Enter Workspace Dashboard</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
          <a
            href="#features"
            className="flex items-center justify-center bg-slate-900 hover:bg-slate-800 border border-slate-800 px-6 py-3 rounded-lg text-sm font-semibold transition-all w-full sm:w-auto"
          >
            Explore AI Modules
          </a>
        </div>
      </section>

      {/* 3. Features Module Section Grid */}
      <section id="features" className="max-w-7xl mx-auto px-6 py-16 border-t border-slate-800/40 space-y-12">
        <div className="text-center space-y-2">
          <h2 className="text-2xl md:text-3xl font-bold tracking-tight">Four Powerful Worksite Modules</h2>
          <p className="text-slate-400 text-sm max-w-md mx-auto">
            Each engineered to address critical administrative bottlenecks in today’s modern workplace environments.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {modules.map((m, idx) => {
            const Icon = m.icon;
            return (
              <div
                key={idx}
                className="bg-[#111827]/40 border border-slate-800/80 rounded-2xl p-6 space-y-4 hover:border-slate-700 hover:bg-[#111827]/60 transition-all group"
              >
                <div className={`h-10 w-10 rounded-lg ${m.bg} flex items-center justify-center ${m.color}`}>
                  <Icon className="w-5 h-5" />
                </div>
                <h3 className="font-bold text-lg group-hover:text-blue-400 transition-colors">{m.title}</h3>
                <p className="text-xs md:text-sm text-slate-400 leading-relaxed">{m.desc}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* 4. Enterprise Architecture Summary Banner */}
      <section className="max-w-7xl mx-auto px-6 py-16 border-t border-slate-800/40">
        <div className="bg-gradient-to-r from-blue-950/20 to-slate-900/30 border border-slate-800/80 rounded-2xl p-8 md:p-12 flex flex-col lg:flex-row justify-between items-center gap-8">
          <div className="space-y-4 max-w-lg">
            <div className="inline-flex items-center gap-2 bg-blue-500/10 text-blue-400 px-3 py-1 rounded-full text-xs font-semibold">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Production-Grade Architecture</span>
            </div>
            <h3 className="font-bold text-2xl md:text-3xl leading-tight">Enterprise Infrastructure Specifications</h3>
            <p className="text-xs md:text-sm text-slate-400 leading-relaxed">
              Designed as a highly-sound TS monorepo, powered by Next.js 15 routing models, FastAPI heavy computational backend microservices, Supabase RLS policies and ChromaDB semantic text databases.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4 w-full lg:w-auto">
            <div className="bg-[#111827]/60 border border-slate-800 rounded-xl p-4 text-center">
              <Zap className="w-5 h-5 text-blue-500 mx-auto mb-2" />
              <h4 className="font-bold text-xs">High Scalability</h4>
            </div>
            <div className="bg-[#111827]/60 border border-slate-800 rounded-xl p-4 text-center">
              <ShieldCheck className="w-5 h-5 text-emerald-500 mx-auto mb-2" />
              <h4 className="font-bold text-xs">Strict Security</h4>
            </div>
          </div>
        </div>
      </section>

      {/* 5. Footer */}
      <footer className="max-w-7xl mx-auto px-6 py-8 border-t border-slate-850 text-center text-xs text-slate-500 flex flex-col sm:flex-row justify-between items-center gap-4">
        <span>© 2026 Sopra Steria India - Project Domain: Enterprise AI & Workflow Automation.</span>
        <span>Prepared by: Divyansh Saxena | Submitted To: Mr. Ram Chandar</span>
      </footer>
    </div>
  );
}
