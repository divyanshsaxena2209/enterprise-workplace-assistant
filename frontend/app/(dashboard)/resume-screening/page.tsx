"use client";

import React, { useState } from "react";
import { UploadCloud, FileText, ChevronRight, UserCircle, Star, AlertCircle } from "lucide-react";

export default function ResumeScreeningPage() {
  const [activeTab, setActiveTab] = useState("candidates");

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">AI Resume Screening</h1>
          <p className="text-gray-500">Evaluate candidates intelligently with AI analysis.</p>
        </div>
        <div className="flex p-1 bg-gray-100 dark:bg-gray-800 rounded-lg">
          <button 
            onClick={() => setActiveTab("candidates")}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition ${activeTab === "candidates" ? "bg-white dark:bg-gray-900 shadow-sm text-gray-900 dark:text-gray-100" : "text-gray-500 hover:text-gray-700"}`}
          >
            Candidates
          </button>
          <button 
            onClick={() => setActiveTab("upload")}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition ${activeTab === "upload" ? "bg-white dark:bg-gray-900 shadow-sm text-gray-900 dark:text-gray-100" : "text-gray-500 hover:text-gray-700"}`}
          >
            Upload Resumes
          </button>
        </div>
      </div>

      {activeTab === "upload" ? <ResumeUploadFlow /> : <CandidateDashboard />}
    </div>
  );
}

function ResumeUploadFlow() {
  return (
    <div className="bg-white dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-2xl p-8 flex flex-col items-center justify-center text-center min-h-[400px] border-dashed">
      <div className="w-16 h-16 bg-blue-50 dark:bg-blue-900/30 rounded-full flex items-center justify-center text-blue-600 mb-4">
        <UploadCloud size={32} />
      </div>
      <h3 className="text-xl font-bold mb-2">Drag & Drop Resumes</h3>
      <p className="text-gray-500 mb-6 max-w-sm">
        Upload PDF or DOCX files. Our AI will automatically parse the resumes and evaluate them against open jobs.
      </p>
      <button className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2.5 rounded-lg font-medium transition-colors">
        Select Files
      </button>
    </div>
  );
}

function CandidateDashboard() {
  const candidates = [
    { id: 1, name: "Alice Johnson", role: "Senior Frontend Engineer", match: 92, status: "Shortlisted", time: "2h ago" },
    { id: 2, name: "Bob Smith", role: "Senior Frontend Engineer", match: 78, status: "Applied", time: "5h ago" },
    { id: 3, name: "Charlie Davis", role: "Product Manager", match: 85, status: "Interview", time: "1d ago" },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
      <div className="md:col-span-1 space-y-2">
        <div className="font-semibold text-sm text-gray-500 uppercase tracking-wider mb-4">Filters</div>
        <div className="p-4 bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-800 rounded-xl space-y-4">
          <div>
            <label className="text-sm font-medium mb-1 block">Job Role</label>
            <select className="w-full text-sm border-gray-200 rounded-lg dark:bg-gray-900 dark:border-gray-800">
              <option>All Roles</option>
              <option>Senior Frontend Engineer</option>
              <option>Product Manager</option>
            </select>
          </div>
          <div>
            <label className="text-sm font-medium mb-1 block">Status</label>
            <select className="w-full text-sm border-gray-200 rounded-lg dark:bg-gray-900 dark:border-gray-800">
              <option>All Statuses</option>
              <option>Applied</option>
              <option>Shortlisted</option>
              <option>Interview</option>
            </select>
          </div>
        </div>
      </div>
      
      <div className="md:col-span-3 space-y-4">
        {candidates.map((c) => (
          <div key={c.id} className="p-4 bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-800 rounded-xl hover:border-blue-500 cursor-pointer transition flex items-center justify-between">
            <div className="flex items-center gap-4">
              <UserCircle size={40} className="text-gray-400" />
              <div>
                <h4 className="font-semibold">{c.name}</h4>
                <p className="text-sm text-gray-500">{c.role} • Applied {c.time}</p>
              </div>
            </div>
            <div className="flex items-center gap-6">
              <div className="text-right">
                <div className="text-sm text-gray-500">AI Match</div>
                <div className={`font-bold ${c.match >= 90 ? 'text-green-600' : c.match >= 80 ? 'text-blue-600' : 'text-yellow-600'}`}>
                  {c.match}%
                </div>
              </div>
              <span className="px-3 py-1 bg-gray-100 dark:bg-gray-800 text-sm rounded-full font-medium">
                {c.status}
              </span>
              <ChevronRight className="text-gray-400" size={20} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
