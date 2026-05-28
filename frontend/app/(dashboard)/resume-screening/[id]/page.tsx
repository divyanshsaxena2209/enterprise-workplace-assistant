"use client";

import React from "react";
import { ArrowLeft, UserCircle, Briefcase, GraduationCap, Code, CheckCircle, FileText, Bot } from "lucide-react";
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
    <div className="space-y-6">
      <Link href="/resume-screening" className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-900 dark:hover:text-gray-100 transition">
        <ArrowLeft size={16} />
        Back to Candidates
      </Link>

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Left Column: Profile & Resume Preview */}
        <div className="lg:w-1/2 space-y-6">
          <div className="bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-800 rounded-2xl p-6">
            <div className="flex items-start justify-between">
              <div className="flex gap-4">
                <UserCircle size={64} className="text-gray-400" />
                <div>
                  <h1 className="text-2xl font-bold">{candidate.name}</h1>
                  <p className="text-gray-500">{candidate.role}</p>
                  <p className="text-sm text-gray-400 mt-1">{candidate.email}</p>
                </div>
              </div>
              <span className="px-3 py-1 bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 text-sm rounded-full font-medium">
                {candidate.status}
              </span>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-800 rounded-2xl p-6 flex-1 min-h-[500px] flex flex-col">
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              <FileText size={18} /> Original Resume
            </h3>
            <div className="flex-1 bg-gray-50 dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 flex items-center justify-center text-gray-500">
              [PDF Viewer Component Integration Here]
            </div>
          </div>
        </div>

        {/* Right Column: AI Match & Insights */}
        <div className="lg:w-1/2 space-y-6">
          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-950/20 dark:to-indigo-950/20 border border-blue-100 dark:border-blue-900/30 rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold flex items-center gap-2 text-blue-900 dark:text-blue-100">
                <Bot size={20} /> AI Evaluation
              </h3>
              <div className="text-right">
                <span className="text-3xl font-bold text-blue-600 dark:text-blue-400">{candidate.match}%</span>
                <span className="text-sm text-blue-800/70 dark:text-blue-200/70 block">Match Score</span>
              </div>
            </div>
            <p className="text-sm text-blue-900/80 dark:text-blue-100/80 leading-relaxed mb-4">
              {candidate.aiSummary}
            </p>
            
            <div className="space-y-4 mt-6">
              <div>
                <h4 className="text-sm font-semibold text-green-700 dark:text-green-400 mb-2">Strengths</h4>
                <ul className="space-y-1">
                  {candidate.strengths.map((s, i) => (
                    <li key={i} className="text-sm flex items-start gap-2">
                      <CheckCircle size={16} className="text-green-500 shrink-0 mt-0.5" />
                      {s}
                    </li>
                  ))}
                </ul>
              </div>
              
              <div>
                <h4 className="text-sm font-semibold text-red-700 dark:text-red-400 mb-2">Missing / Weaknesses</h4>
                <ul className="space-y-1">
                  {candidate.weaknesses.map((w, i) => (
                    <li key={i} className="text-sm flex items-start gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-red-500 shrink-0 mt-1.5 ml-1" />
                      {w}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
            
            <div className="mt-6 pt-6 border-t border-blue-200/50 dark:border-blue-800/50">
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold">Recommendation</span>
                <span className="px-3 py-1 bg-green-500 text-white text-sm rounded-full font-medium">
                  {candidate.recommendation}
                </span>
              </div>
            </div>
          </div>
          
          <div className="bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-800 rounded-2xl p-6">
            <h3 className="font-semibold mb-4">Recruiter Actions</h3>
            <div className="flex gap-3">
              <button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg font-medium transition">
                Schedule Interview
              </button>
              <button className="flex-1 bg-white hover:bg-gray-50 text-gray-700 border border-gray-200 dark:bg-gray-900 dark:text-gray-300 dark:border-gray-800 py-2 rounded-lg font-medium transition">
                Reject Candidate
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
