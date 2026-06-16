"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Sparkles,
  ArrowRight,
  Briefcase,
  ClipboardCheck,
  BookOpen,
  ShieldCheck,
  Zap,
  Globe,
  ChevronRight
} from "lucide-react";

export default function Home() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const modules = [
    {
      title: "Talent Acquisition",
      desc: "Perform candidate assessments with automated PDF/DOCX parsing, indexing, and scoring models.",
      icon: Briefcase,
    },
    {
      title: "Workforce Onboarding",
      desc: "Track milestones, secure onboarding documentation, and audit operational tasks for new hires.",
      icon: ClipboardCheck,
    },
    {
      title: "Organizational Intel",
      desc: "Query standard operating procedures and policy compliance records using semantic RAG capabilities.",
      icon: BookOpen,
    }
  ];

  if (!mounted) return null; // Avoid hydration mismatch on initial render

  return (
    <div className="bg-background text-foreground min-h-screen font-sans overflow-x-hidden">
      {/* Abstract Background Glows */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none -z-10">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-indigo-500/10 blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-purple-500/10 blur-[120px]" />
      </div>

      <header className="h-20 max-w-7xl mx-auto px-6 flex items-center justify-end z-50 relative">
        <div className="flex items-center gap-4">
          <Link
            href="/login"
            className="text-xs font-bold uppercase tracking-widest text-muted-foreground hover:text-foreground transition-colors"
          >
            Sign In
          </Link>
          <Link
            href="/signup"
            className="group flex items-center gap-2 glass-panel hover:bg-white/5 px-5 py-2.5 rounded-full text-xs font-bold uppercase tracking-widest transition-all shadow-sm"
          >
            <span>Create Account</span>
            <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative max-w-7xl mx-auto px-6 pt-32 pb-24 md:pt-48 md:pb-32 text-center flex flex-col items-center">
        


        <motion.h1 
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
          className="text-5xl md:text-8xl font-black tracking-tighter max-w-5xl mx-auto leading-[0.95] text-transparent bg-clip-text bg-gradient-to-b from-white to-white/60 mb-6"
        >
          Intelligence for the <br /> Modern Enterprise.
        </motion.h1>

        <motion.p 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
          className="text-muted-foreground text-base md:text-xl max-w-2xl mx-auto leading-relaxed mb-10 font-medium"
        >
          Unify your talent pipeline, automate onboarding operations, and centralize organizational knowledge in one secure environment.
        </motion.p>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
          className="flex flex-col sm:flex-row items-center gap-4 w-full sm:w-auto"
        >
          <Link
            href="/signup"
            className="group relative flex items-center justify-center gap-2 bg-foreground text-background px-8 py-4 rounded-xl text-sm font-bold uppercase tracking-wider transition-all w-full sm:w-auto overflow-hidden"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-[150%] group-hover:translate-x-[150%] transition-transform duration-700" />
            <span>Create Account</span>
            <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </Link>
          <Link
            href="/login"
            className="flex items-center justify-center glass-panel hover:bg-white/5 border border-white/10 px-8 py-4 rounded-xl text-sm font-bold uppercase tracking-wider transition-all w-full sm:w-auto text-foreground"
          >
            Sign In
          </Link>
        </motion.div>
      </section>

      {/* Feature Showcase Grid */}
      <section className="relative max-w-7xl mx-auto px-6 py-24 border-t border-white/5">
        <div className="mb-16">
          <h2 className="text-3xl md:text-5xl font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-white to-white/50 inline-block mb-4">
            Core Infrastructure
          </h2>
          <p className="text-muted-foreground max-w-xl text-lg">
            Purpose-built operational portals tailored for scale.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {modules.map((m, idx) => {
            const Icon = m.icon;
            return (
              <motion.div
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: idx * 0.1, ease: [0.16, 1, 0.3, 1] }}
                key={idx}
                className="group relative bg-secondary/30 backdrop-blur-sm border border-white/10 rounded-3xl p-8 hover:border-white/30 transition-all duration-500 overflow-hidden"
              >
                <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                
                <div className="relative z-10">
                  <div className="h-12 w-12 rounded-2xl border border-white/10 flex items-center justify-center bg-background/50 text-foreground mb-6 group-hover:scale-110 transition-transform duration-500">
                    <Icon className="w-5 h-5" />
                  </div>
                  <h3 className="font-bold text-xl text-foreground tracking-tight mb-3 group-hover:text-white transition-colors">{m.title}</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">{m.desc}</p>
                </div>
              </motion.div>
            );
          })}
        </div>
      </section>

      {/* Technical Specs Bento Box */}
      <section id="architecture" className="max-w-7xl mx-auto px-6 py-24">
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          className="glass-panel rounded-3xl p-8 md:p-16 flex flex-col lg:flex-row items-center gap-12 relative overflow-hidden"
        >
          {/* Subtle mesh background for bento box */}
          <div className="absolute inset-0 opacity-10" style={{ backgroundImage: 'radial-gradient(circle at 2px 2px, white 1px, transparent 0)', backgroundSize: '24px 24px' }}></div>

          <div className="flex-1 space-y-6 relative z-10">
            <div className="inline-flex items-center gap-2 bg-foreground text-background px-3 py-1.5 rounded-full text-[10px] font-bold tracking-widest uppercase">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Enterprise Grade</span>
            </div>
            <h3 className="font-bold text-3xl md:text-5xl leading-[1.1] tracking-tight">Zero-Trust Security & <br/> Infinite Scale.</h3>
            <p className="text-lg text-muted-foreground leading-relaxed max-w-lg">
              Engineered with Type-safe routing, isolated document vectors, and fine-grained row level authorization schemas.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4 w-full lg:w-auto relative z-10">
            <div className="bg-background/80 backdrop-blur-xl border border-white/10 rounded-2xl p-6 text-center flex flex-col items-center justify-center shadow-2xl hover:-translate-y-1 transition-transform duration-300">
              <Zap className="w-6 h-6 text-foreground mb-4" />
              <h4 className="font-semibold text-xs tracking-widest uppercase">Edge Deploy</h4>
            </div>
            <div className="bg-background/80 backdrop-blur-xl border border-white/10 rounded-2xl p-6 text-center flex flex-col items-center justify-center shadow-2xl hover:-translate-y-1 transition-transform duration-300">
              <ShieldCheck className="w-6 h-6 text-foreground mb-4" />
              <h4 className="font-semibold text-xs tracking-widest uppercase">Strict RLS</h4>
            </div>
            <div className="bg-background/80 backdrop-blur-xl border border-white/10 rounded-2xl p-6 text-center flex flex-col items-center justify-center shadow-2xl hover:-translate-y-1 transition-transform duration-300 col-span-2">
              <Globe className="w-6 h-6 text-foreground mb-4" />
              <h4 className="font-semibold text-xs tracking-widest uppercase">Global Distribution</h4>
            </div>
          </div>
        </motion.div>
      </section>

      {/* Minimal Footer */}
      <footer className="max-w-7xl mx-auto px-6 py-10 border-t border-white/5 flex flex-col sm:flex-row justify-between items-center gap-4">
        <div className="flex items-center gap-2 text-muted-foreground">
          <Sparkles className="w-4 h-4" />
          <span className="text-[10px] font-bold uppercase tracking-widest">© 2026 Workforce OS.</span>
        </div>
        <div className="flex gap-6">
          <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest hover:text-foreground transition-colors cursor-pointer">Privacy</span>
          <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest hover:text-foreground transition-colors cursor-pointer">Terms</span>
          <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest hover:text-foreground transition-colors cursor-pointer">System Status</span>
        </div>
      </footer>
    </div>
  );
}
