"use client";

import React, { useState } from "react";
import { ArrowLeft, Play, Pause, FileText, CheckSquare, Target, User, Calendar, Clock } from "lucide-react";
import Link from "next/link";

export default function MeetingDetailPage() {
  const [isPlaying, setIsPlaying] = useState(false);

  const meeting = {
    title: "Q3 Engineering Roadmap",
    date: "Oct 12, 2026 • 10:00 AM",
    duration: "45 min",
    organizer: "Alice Johnson",
    executive_summary: "The team discussed the upcoming Q3 engineering priorities, finalizing the decision to migrate to Next.js 15. The new RAG pipeline was approved for immediate implementation. Security audits are scheduled for next month.",
    decisions: [
      "Migrate entirely to Next.js 15 app router.",
      "Use ChromaDB for the vector store instead of Pinecone.",
      "Delay the mobile app rewrite to Q4."
    ],
    action_items: [
      { id: 1, title: "Initialize Next.js 15 monorepo", assignee: "Bob Smith", priority: "High", deadline: "Oct 15" },
      { id: 2, title: "Set up ChromaDB container", assignee: "Charlie Davis", priority: "Medium", deadline: "Oct 18" },
      { id: 3, title: "Draft security audit RFP", assignee: "Alice Johnson", priority: "Critical", deadline: "Oct 20" }
    ],
    transcript: [
      { time: "00:00", speaker: "Alice", text: "Alright, let's get started. Today we need to finalize our Q3 engineering roadmap." },
      { time: "00:15", speaker: "Bob", text: "I've been looking at Next.js 15. The new app router caching improvements are exactly what we need." },
      { time: "00:28", speaker: "Alice", text: "Agreed. Let's make the decision to migrate entirely to Next.js 15." },
      { time: "00:40", speaker: "Charlie", text: "What about the vector database for the RAG pipeline? Are we sticking with Pinecone?" },
      { time: "00:55", speaker: "Alice", text: "Actually, let's use ChromaDB. Charlie, can you set up the container by the 18th?" },
      { time: "01:05", speaker: "Charlie", text: "Sure, I'll get that done." }
    ]
  };

  return (
    <div className="space-y-6 h-[calc(100vh-8rem)] flex flex-col">
      {/* Header */}
      <div className="shrink-0">
        <Link href="/meetings" className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-900 dark:hover:text-gray-100 transition mb-4">
          <ArrowLeft size={16} /> Back to Meetings
        </Link>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold">{meeting.title}</h1>
            <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
              <span className="flex items-center gap-1"><Calendar size={14} /> {meeting.date}</span>
              <span className="flex items-center gap-1"><Clock size={14} /> {meeting.duration}</span>
              <span className="flex items-center gap-1"><User size={14} /> {meeting.organizer}</span>
            </div>
          </div>
          <div className="flex items-center gap-3 bg-white dark:bg-gray-950 px-4 py-2 rounded-full border border-gray-200 dark:border-gray-800 shadow-sm">
            <button onClick={() => setIsPlaying(!isPlaying)} className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center hover:bg-blue-700 transition">
              {isPlaying ? <Pause size={16} /> : <Play size={16} className="ml-0.5" />}
            </button>
            <div className="w-48 h-1 bg-gray-200 dark:bg-gray-800 rounded-full overflow-hidden">
              <div className="h-full bg-blue-600 w-1/3"></div>
            </div>
            <span className="text-xs font-medium text-gray-500">15:20 / 45:00</span>
          </div>
        </div>
      </div>

      <div className="flex-1 flex gap-6 min-h-0">
        {/* Left: Transcript */}
        <div className="w-1/2 bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-800 rounded-2xl flex flex-col shadow-sm overflow-hidden">
          <div className="p-4 border-b border-gray-100 dark:border-gray-800 shrink-0">
            <h3 className="font-semibold flex items-center gap-2">
              <FileText size={18} className="text-gray-400" /> Full Transcript
            </h3>
          </div>
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {meeting.transcript.map((line, i) => (
              <div key={i} className="flex gap-4 group">
                <div className="w-12 pt-1 text-xs font-medium text-gray-400 text-right shrink-0 group-hover:text-blue-500 transition cursor-pointer">
                  {line.time}
                </div>
                <div>
                  <span className="font-semibold text-sm mb-1 block">{line.speaker}</span>
                  <p className="text-gray-700 dark:text-gray-300 text-sm leading-relaxed">{line.text}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: AI Intelligence */}
        <div className="w-1/2 flex flex-col gap-6 min-h-0 overflow-y-auto">
          {/* Summary */}
          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-950/20 dark:to-indigo-950/20 border border-blue-100 dark:border-blue-900/30 rounded-2xl p-6 shadow-sm shrink-0">
            <h3 className="font-semibold flex items-center gap-2 text-blue-900 dark:text-blue-100 mb-3">
              <Target size={18} /> Executive Summary
            </h3>
            <p className="text-sm text-blue-900/80 dark:text-blue-100/80 leading-relaxed">
              {meeting.executive_summary}
            </p>
          </div>

          {/* Action Items */}
          <div className="bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-800 rounded-2xl p-6 shadow-sm shrink-0">
            <h3 className="font-semibold flex items-center gap-2 mb-4">
              <CheckSquare size={18} className="text-green-500" /> Action Items
            </h3>
            <div className="space-y-3">
              {meeting.action_items.map(task => (
                <div key={task.id} className="p-3 border border-gray-100 dark:border-gray-800 rounded-xl hover:border-gray-200 dark:hover:border-gray-700 transition flex items-center justify-between">
                  <div>
                    <h4 className="font-medium text-sm">{task.title}</h4>
                    <p className="text-xs text-gray-500 mt-1">Assigned to {task.assignee}</p>
                  </div>
                  <div className="text-right">
                    <span className={`px-2 py-0.5 text-[10px] uppercase tracking-wider font-bold rounded-sm mb-1 inline-block ${
                      task.priority === 'Critical' ? 'bg-red-100 text-red-700' :
                      task.priority === 'High' ? 'bg-orange-100 text-orange-700' :
                      'bg-blue-100 text-blue-700'
                    }`}>
                      {task.priority}
                    </span>
                    <p className="text-xs font-medium text-gray-500">Due {task.deadline}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Decisions */}
          <div className="bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-800 rounded-2xl p-6 shadow-sm shrink-0">
            <h3 className="font-semibold flex items-center gap-2 mb-4">
              <Target size={18} className="text-purple-500" /> Decisions Made
            </h3>
            <ul className="space-y-2">
              {meeting.decisions.map((decision, i) => (
                <li key={i} className="text-sm flex items-start gap-2 text-gray-700 dark:text-gray-300">
                  <div className="w-1.5 h-1.5 rounded-full bg-purple-500 shrink-0 mt-1.5" />
                  {decision}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
