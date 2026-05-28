"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Briefcase,
  ClipboardCheck,
  BookOpen,
  Video,
  ArrowRight,
  TrendingUp,
  Sparkles,
  Users,
  Award,
  Clock,
  ListTodo
} from "lucide-react";

export default function DashboardOverview() {
  // Simple state for quick dashboard activities
  const stats = [
    { name: "Screened Candidates", value: "3", icon: Users, color: "text-blue-500", bg: "bg-blue-500/10" },
    { name: "Onboarding Progress", value: "60%", icon: ClipboardCheck, color: "text-emerald-500", bg: "bg-emerald-500/10" },
    { name: "Indexed Policy Manuals", value: "3", icon: BookOpen, color: "text-purple-500", bg: "bg-purple-500/10" },
    { name: "Transcribed Meetings", value: "1", icon: Video, color: "text-amber-500", bg: "bg-amber-500/10" }
  ];

  const recentCandidates = [
    { name: "Sarah Conner", job: "Senior Full Stack Engineer", score: 94, status: "SHORTLISTED" },
    { name: "Bruce Wayne", job: "AI Systems Architect", score: 88, status: "SHORTLISTED" }
  ];

  const recentTasks = [
    { title: "IT Assets Allocation", assignee: "Bruce Wayne", deadline: "2026-05-28", status: "PENDING" },
    { title: "Resume screening logic setup", assignee: "Sarah Conner", deadline: "2026-06-01", status: "PENDING" }
  ];

  return (
    <div className="space-y-8">
      {/* Upper banner section */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl p-6 md:p-8 text-white relative overflow-hidden shadow-lg shadow-blue-500/10">
        {/* Abstract shapes overlay */}
        <div className="absolute right-0 top-0 w-80 h-full bg-white/5 skew-x-12 -translate-y-6"></div>
        <div className="absolute right-20 bottom-0 w-40 h-40 rounded-full bg-white/5 blur-xl"></div>

        <div className="space-y-4 max-w-2xl relative z-10">
          <div className="inline-flex items-center gap-1.5 bg-white/15 px-3 py-1 rounded-full text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5" />
            <span>AI Platform Engine Online</span>
          </div>
          <h2 className="text-2xl md:text-3xl font-black tracking-tight leading-snug">
            Welcome to Your Enterprise Workplace Suite
          </h2>
          <p className="text-sm text-blue-100 leading-relaxed max-w-xl">
            You have active candidates screening sessions, pending onboarding approvals, and a fully indexed knowledge database vector ready for semantic searches.
          </p>
        </div>
      </div>

      {/* Grid of four main stats metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, idx) => {
          const Icon = stat.icon;
          return (
            <div
              key={idx}
              className="bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 p-5 rounded-xl flex items-center justify-between shadow-sm"
            >
              <div className="space-y-1">
                <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">{stat.name}</span>
                <p className="text-2xl font-bold">{stat.value}</p>
              </div>
              <div className={`h-11 w-11 rounded-lg ${stat.bg} flex items-center justify-center ${stat.color} flex-shrink-0`}>
                <Icon className="w-5.5 h-5.5" />
              </div>
            </div>
          );
        })}
      </div>

      {/* Main split sections: Left 2/3 Dashboard modules, Right 1/3 Recent Updates */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left: Quick Access to all modules */}
        <div className="lg:col-span-2 space-y-6">
          <h3 className="font-bold text-lg text-slate-700 dark:text-slate-300">Platform Modules</h3>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            {/* Module 1 Card */}
            <div className="bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-xl p-5 hover:border-blue-300 dark:hover:border-blue-900 transition-all flex flex-col justify-between h-48 group">
              <div className="space-y-2">
                <div className="h-9 w-9 rounded-lg bg-blue-500/10 text-blue-500 flex items-center justify-center">
                  <Briefcase className="w-5 h-5" />
                </div>
                <h4 className="font-bold text-sm leading-tight group-hover:text-blue-500 transition-colors">Resume Screening</h4>
                <p className="text-xs text-slate-400 leading-normal line-clamp-2">
                  Extract resume details and parse skills scoring candidate fit instantly using OpenAI.
                </p>
              </div>
              <Link
                href="/dashboard/hiring"
                className="text-xs font-semibold text-blue-600 dark:text-blue-400 flex items-center gap-1.5 hover:underline pt-4"
              >
                <span>Open Screenings</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
              </Link>
            </div>

            {/* Module 2 Card */}
            <div className="bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-xl p-5 hover:border-emerald-300 dark:hover:border-emerald-900 transition-all flex flex-col justify-between h-48 group">
              <div className="space-y-2">
                <div className="h-9 w-9 rounded-lg bg-emerald-500/10 text-emerald-500 flex items-center justify-center">
                  <ClipboardCheck className="w-5 h-5" />
                </div>
                <h4 className="font-bold text-sm leading-tight group-hover:text-emerald-500 transition-colors">Onboarding Automation</h4>
                <p className="text-xs text-slate-400 leading-normal line-clamp-2">
                  Coordinate onboarding milestones, upload verification documents and audit progresses.
                </p>
              </div>
              <Link
                href="/dashboard/onboarding"
                className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5 hover:underline pt-4"
              >
                <span>Track Milestones</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
              </Link>
            </div>

            {/* Module 3 Card */}
            <div className="bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-xl p-5 hover:border-purple-300 dark:hover:border-purple-900 transition-all flex flex-col justify-between h-48 group">
              <div className="space-y-2">
                <div className="h-9 w-9 rounded-lg bg-purple-500/10 text-purple-500 flex items-center justify-center">
                  <BookOpen className="w-5 h-5" />
                </div>
                <h4 className="font-bold text-sm leading-tight group-hover:text-purple-500 transition-colors">Knowledge Assistant</h4>
                <p className="text-xs text-slate-400 leading-normal line-clamp-2">
                  Converse with policy guidelines manuals using context-rich vectors and text chunking.
                </p>
              </div>
              <Link
                href="/dashboard/knowledge"
                className="text-xs font-semibold text-purple-600 dark:text-purple-400 flex items-center gap-1.5 hover:underline pt-4"
              >
                <span>Ask Policies</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
              </Link>
            </div>

            {/* Module 4 Card */}
            <div className="bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-xl p-5 hover:border-amber-300 dark:hover:border-amber-900 transition-all flex flex-col justify-between h-48 group">
              <div className="space-y-2">
                <div className="h-9 w-9 rounded-lg bg-amber-500/10 text-amber-500 flex items-center justify-center">
                  <Video className="w-5 h-5" />
                </div>
                <h4 className="font-bold text-sm leading-tight group-hover:text-amber-500 transition-colors">Meeting Transcripts</h4>
                <p className="text-xs text-slate-400 leading-normal line-clamp-2">
                  Translate recorded session speech, structure markdown highlights and extract task checklists.
                </p>
              </div>
              <Link
                href="/dashboard/meetings"
                className="text-xs font-semibold text-amber-600 dark:text-amber-400 flex items-center gap-1.5 hover:underline pt-4"
              >
                <span>Extract Transcripts</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
              </Link>
            </div>
          </div>
        </div>

        {/* Right: Quick Recent Updates Log */}
        <div className="lg:col-span-1 space-y-6">
          <h3 className="font-bold text-lg text-slate-700 dark:text-slate-300">Recent Activities</h3>
          
          <div className="space-y-6 bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
            
            {/* Recent Candidates */}
            <div className="space-y-3">
              <h4 className="font-bold text-xs uppercase tracking-widest text-slate-400 flex items-center gap-1.5">
                <Award className="w-4 h-4 text-blue-500" />
                <span>Recent Candidates Scored</span>
              </h4>
              <div className="space-y-2.5">
                {recentCandidates.map((cand, idx) => (
                  <div key={idx} className="flex justify-between items-center text-xs">
                    <div>
                      <p className="font-bold">{cand.name}</p>
                      <p className="text-[10px] text-slate-400 mt-0.5">{cand.job}</p>
                    </div>
                    <span className="font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/20 px-2 py-0.5 rounded border border-emerald-100 dark:border-emerald-900/50">
                      {cand.score}% Match
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Recent meeting action items */}
            <div className="space-y-3 pt-5 border-t border-slate-100 dark:border-slate-850">
              <h4 className="font-bold text-xs uppercase tracking-widest text-slate-400 flex items-center gap-1.5">
                <ListTodo className="w-4 h-4 text-emerald-500" />
                <span>Pending Action Items</span>
              </h4>
              <div className="space-y-2.5">
                {recentTasks.map((task, idx) => (
                  <div key={idx} className="flex justify-between items-center text-xs">
                    <div>
                      <p className="font-semibold line-clamp-1 max-w-[150px]">{task.title}</p>
                      <p className="text-[9px] text-slate-400 mt-0.5">Assignee: {task.assignee}</p>
                    </div>
                    <span className="text-[9px] font-bold text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/20 px-2 py-0.5 rounded border border-amber-200 dark:border-amber-900/50 flex items-center gap-1">
                      <Clock className="w-2.5 h-2.5" />
                      <span>{task.deadline}</span>
                    </span>
                  </div>
                ))}
              </div>
            </div>

          </div>
        </div>

      </div>
    </div>
  );
}
