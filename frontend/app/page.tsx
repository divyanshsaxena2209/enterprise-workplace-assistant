"use client";

import React from "react";
import Link from "next/link";
import {
  Sparkles,
  ArrowRight,
  Briefcase,
  ClipboardCheck,
  BookOpen,
  ShieldCheck,
  Zap
} from "lucide-react";

export default function Home() {
  const modules = [
    {
      title: "Talent Acquisition Pipeline",
      desc: "Perform candidate assessments with automated PDF/DOCX parsing, indexing, suitability evaluations, and scoring models.",
      icon: Briefcase,
    },
    {
      title: "Workforce Onboarding Operations",
      desc: "Track milestones, secure onboarding documentation, and audit operational tasks for new hires.",
      icon: ClipboardCheck,
    },
    {
      title: "Organizational Intelligence",
      desc: "Query standard operating procedures, manuals, and policy compliance records using semantic RAG capabilities.",
      icon: BookOpen,
    }
  ];

  return (
    <div className="bg-background text-foreground min-h-screen selection:bg-foreground selection:text-background font-sans">
      
      <header className="h-16 max-w-7xl mx-auto px-6 flex items-center justify-between border-b border-border">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-foreground animate-pulse" />
          <span className="font-bold text-sm tracking-wider uppercase text-foreground">Workforce OS</span>
        </div>
        <Link
          href="/login"
          className="flex items-center gap-2 bg-foreground text-background hover:opacity-90 px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-opacity shadow-sm"
        >
          <span>Access Enterprise Portal</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </header>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-6 py-24 md:py-32 text-center space-y-8 relative">
        <div className="inline-flex items-center gap-2 border border-border rounded-full px-4 py-1.5 text-xs font-semibold mb-4 text-muted-foreground shadow-sm bg-card/50">
          <Sparkles className="w-3.5 h-3.5 text-foreground" />
          <span>Organizational Intelligence Platform</span>
        </div>

        <h1 className="text-4xl md:text-7xl font-black tracking-tighter max-w-4xl mx-auto leading-[1.05] text-foreground">
          Unify Corporate Operations & Intelligence
        </h1>

        <p className="text-muted-foreground text-sm md:text-lg max-w-2xl mx-auto leading-relaxed">
          Index talent pipelines, execute structured onboarding programs, and search organizational documents inside a single secure enterprise environment.
        </p>

        <div className="flex flex-col sm:flex-row justify-center items-center gap-4 pt-8">
          <Link
            href="/login"
            className="flex items-center justify-center gap-2 bg-foreground hover:bg-foreground/90 text-background px-8 py-3.5 rounded-lg text-xs font-bold uppercase tracking-wider transition-all w-full sm:w-auto shadow-sm"
          >
            <span>Enter Operations Portal</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
          <a
            href="#features"
            className="flex items-center justify-center bg-card hover:bg-secondary border border-border px-8 py-3.5 rounded-lg text-xs font-bold uppercase tracking-wider transition-all w-full sm:w-auto text-foreground shadow-sm"
          >
            Explore Systems
          </a>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="max-w-7xl mx-auto px-6 py-20 border-t border-border space-y-16">
        <div className="text-center space-y-3">
          <h2 className="text-2xl md:text-4xl font-bold tracking-tight">Core Functional Infrastructure</h2>
          <p className="text-muted-foreground text-sm max-w-md mx-auto">
            Operational portals tailored for modern workforce environments.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {modules.map((m, idx) => {
            const Icon = m.icon;
            return (
              <div
                key={idx}
                className="bg-card border border-border rounded-2xl p-8 space-y-5 hover:border-foreground/20 transition-all group shadow-sm flex flex-col justify-between"
              >
                <div>
                  <div className="h-10 w-10 rounded-lg border border-border flex items-center justify-center bg-secondary text-foreground group-hover:bg-foreground group-hover:text-background transition-colors mb-5">
                    <Icon className="w-5 h-5" />
                  </div>
                  <h3 className="font-bold text-lg text-foreground tracking-tight mb-2">{m.title}</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">{m.desc}</p>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Specs Section */}
      <section className="max-w-7xl mx-auto px-6 py-20 border-t border-border">
        <div className="bg-card border border-border rounded-2xl p-8 md:p-12 flex flex-col lg:flex-row justify-between items-center gap-10 shadow-sm relative overflow-hidden">
          <div className="space-y-5 max-w-xl relative z-10">
            <div className="inline-flex items-center gap-2 bg-secondary text-foreground px-3 py-1 rounded border border-border/50 text-[10px] font-bold tracking-wider uppercase">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Production Infrastructure</span>
            </div>
            <h3 className="font-bold text-2xl md:text-4xl leading-tight tracking-tight">Security & Integration Specifications</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Engineered with Type-safe Next.js App Routing, secure token verification, isolated document databases, and fine-grained authorization schemas.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4 w-full lg:w-auto relative z-10">
            <div className="bg-secondary/50 border border-border/50 rounded-xl p-5 text-center flex flex-col items-center justify-center shadow-sm">
              <Zap className="w-5 h-5 text-foreground mb-3" />
              <h4 className="font-semibold text-xs tracking-wider uppercase">High Scalability</h4>
            </div>
            <div className="bg-secondary/50 border border-border/50 rounded-xl p-5 text-center flex flex-col items-center justify-center shadow-sm">
              <ShieldCheck className="w-5 h-5 text-foreground mb-3" />
              <h4 className="font-semibold text-xs tracking-wider uppercase">Strict RLS Security</h4>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="max-w-7xl mx-auto px-6 py-8 border-t border-border text-center flex flex-col sm:flex-row justify-between items-center gap-4">
        <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">© 2026 Enterprise Workplace. All Rights Reserved.</span>
        <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Production Environment Build</span>
      </footer>
    </div>
  );
}
