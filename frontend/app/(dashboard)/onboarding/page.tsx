"use client";

import React, { useState } from "react";
import { CheckCircle, Clock, FileText, Bot, ArrowRight, BookOpen, ShieldCheck } from "lucide-react";
import Link from "next/link";

export default function OnboardingDashboard() {
  const [tasks] = useState([
    { id: 1, title: "Sign Employment Contract", type: "Document", status: "Completed", due: "Yesterday" },
    { id: 2, title: "Upload ID Proof", type: "Document", status: "Pending", due: "Tomorrow" },
    { id: 3, title: "Read IT Security Policy", type: "Reading", status: "Pending", due: "In 3 days" },
    { id: 4, title: "Setup Developer Environment", type: "Task", status: "Pending", due: "In 5 days" },
  ]);

  const completionPercentage = 25;

  return (
    <div className="space-y-6">
      {/* Header Area */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-2xl p-8 text-white shadow-sm flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2">Welcome to the team, Divya! 🎉</h1>
          <p className="text-blue-100 max-w-lg">We are thrilled to have you join as a Software Engineer. Complete the checklist below to get fully set up.</p>
        </div>
        <div className="hidden md:block">
          <div className="w-24 h-24 rounded-full border-4 border-white/20 flex items-center justify-center relative">
            <svg className="w-full h-full absolute inset-0 -rotate-90" viewBox="0 0 36 36">
              <path className="text-white/20" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="3" />
              <path className="text-white" strokeDasharray={`${completionPercentage}, 100`} d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="3" />
            </svg>
            <span className="text-xl font-bold">{completionPercentage}%</span>
          </div>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Left: Checklist */}
        <div className="lg:w-2/3 space-y-6">
          <div className="bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-800 rounded-2xl shadow-sm overflow-hidden">
            <div className="p-6 border-b border-gray-100 dark:border-gray-800">
              <h2 className="text-lg font-semibold">Your Onboarding Checklist</h2>
            </div>
            <div className="divide-y divide-gray-100 dark:divide-gray-800">
              {tasks.map((task) => (
                <div key={task.id} className="p-5 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-900/50 transition">
                  <div className="flex items-start gap-4">
                    <div className={`mt-0.5 ${task.status === 'Completed' ? 'text-green-500' : 'text-gray-300 dark:text-gray-700'}`}>
                      {task.status === 'Completed' ? <CheckCircle size={20} /> : <div className="w-5 h-5 rounded-full border-2 border-current" />}
                    </div>
                    <div>
                      <h4 className={`font-medium ${task.status === 'Completed' ? 'text-gray-500 line-through' : 'text-gray-900 dark:text-gray-100'}`}>
                        {task.title}
                      </h4>
                      <div className="flex items-center gap-3 text-xs text-gray-500 mt-1">
                        <span className="flex items-center gap-1"><Clock size={12} /> Due {task.due}</span>
                        <span className="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 rounded-full">{task.type}</span>
                      </div>
                    </div>
                  </div>
                  {task.status !== 'Completed' && (
                    <button className="px-4 py-2 bg-gray-900 hover:bg-gray-800 dark:bg-white dark:hover:bg-gray-100 dark:text-gray-900 text-white text-sm font-medium rounded-lg transition">
                      Complete
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right: AI Copilot & Resources */}
        <div className="lg:w-1/3 space-y-6">
          {/* AI Onboarding Assistant Widget */}
          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-950/20 dark:to-indigo-950/20 border border-blue-100 dark:border-blue-900/30 rounded-2xl p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-blue-600 text-white rounded-full flex items-center justify-center">
                <Bot size={20} />
              </div>
              <div>
                <h3 className="font-semibold text-blue-900 dark:text-blue-100">AI Onboarding Guide</h3>
                <p className="text-xs text-blue-700 dark:text-blue-300">Ask me anything about policies or setup</p>
              </div>
            </div>
            
            <div className="bg-white dark:bg-gray-900 border border-blue-100 dark:border-blue-800 rounded-xl p-4 mb-4 text-sm text-gray-700 dark:text-gray-300 shadow-sm">
              <p>Hi Divya! Since you're a Software Engineer, make sure to check out the Engineering Handbook in the Knowledge Hub. Need help setting up your dev environment?</p>
            </div>
            
            <Link href="/onboarding/chat" className="flex items-center justify-center gap-2 w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg text-sm font-medium transition">
              Open Chat <ArrowRight size={16} />
            </Link>
          </div>

          {/* Quick Links */}
          <div className="bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-800 rounded-2xl p-6 shadow-sm">
            <h3 className="font-semibold mb-4">Quick Resources</h3>
            <div className="space-y-3">
              <Link href="/knowledge" className="flex items-center gap-3 p-3 border border-gray-100 dark:border-gray-800 rounded-xl hover:border-blue-500 transition group">
                <BookOpen size={18} className="text-gray-400 group-hover:text-blue-500" />
                <span className="text-sm font-medium">Company Handbook</span>
              </Link>
              <Link href="/knowledge" className="flex items-center gap-3 p-3 border border-gray-100 dark:border-gray-800 rounded-xl hover:border-blue-500 transition group">
                <ShieldCheck size={18} className="text-gray-400 group-hover:text-blue-500" />
                <span className="text-sm font-medium">IT Security Policies</span>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
