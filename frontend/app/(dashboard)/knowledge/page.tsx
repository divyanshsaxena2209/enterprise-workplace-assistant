"use client";

import React, { useState } from "react";
import { Search, UploadCloud, MessageSquare, FileText, Database } from "lucide-react";
import Link from "next/link";

export default function KnowledgeDashboard() {
  const [documents] = useState([
    { id: 1, title: "Employee Handbook 2026.pdf", dept: "HR", uploaded: "2 days ago", size: "2.4 MB" },
    { id: 2, title: "Q3 Engineering Roadmap.docx", dept: "Engineering", uploaded: "5 days ago", size: "1.1 MB" },
    { id: 3, title: "Sales Playbook v4.pdf", dept: "Sales", uploaded: "1 week ago", size: "3.8 MB" },
  ]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Enterprise Knowledge Hub</h1>
          <p className="text-gray-500">Query company documents using AI or perform semantic searches.</p>
        </div>
        <div className="flex gap-3">
          <Link href="/knowledge/upload" className="flex items-center gap-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300 px-4 py-2 rounded-lg font-medium transition-colors">
            <UploadCloud size={18} />
            Upload
          </Link>
          <Link href="/knowledge/chat" className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors">
            <MessageSquare size={18} />
            Ask AI Assistant
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl shadow-sm text-white flex flex-col justify-between h-40">
          <Database size={24} className="opacity-80" />
          <div>
            <h3 className="text-4xl font-bold">1,204</h3>
            <p className="opacity-90 font-medium text-sm mt-1">Total Indexed Documents</p>
          </div>
        </div>
        <div className="p-6 bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-800 rounded-2xl shadow-sm flex flex-col justify-between h-40">
          <Search size={24} className="text-blue-500" />
          <div>
            <h3 className="text-3xl font-bold">15K+</h3>
            <p className="text-gray-500 font-medium text-sm mt-1">Queries this month</p>
          </div>
        </div>
        <div className="p-6 bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-800 rounded-2xl shadow-sm flex flex-col justify-between h-40">
          <FileText size={24} className="text-green-500" />
          <div>
            <h3 className="text-3xl font-bold">98%</h3>
            <p className="text-gray-500 font-medium text-sm mt-1">Retrieval Accuracy</p>
          </div>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-800 rounded-2xl shadow-sm overflow-hidden">
        <div className="p-6 border-b border-gray-100 dark:border-gray-800 flex justify-between items-center">
          <h3 className="font-semibold text-lg">Recently Indexed</h3>
          <Link href="/knowledge/search" className="text-sm text-blue-600 hover:underline font-medium">View All / Search</Link>
        </div>
        <div className="divide-y divide-gray-100 dark:divide-gray-800">
          {documents.map(doc => (
            <div key={doc.id} className="p-4 px-6 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-900/50 transition">
              <div className="flex items-center gap-4">
                <FileText className="text-red-400" size={24} />
                <div>
                  <h4 className="font-medium text-sm">{doc.title}</h4>
                  <p className="text-xs text-gray-500 mt-0.5">Uploaded {doc.uploaded} • {doc.size}</p>
                </div>
              </div>
              <span className="px-3 py-1 bg-gray-100 dark:bg-gray-800 text-xs rounded-full font-medium text-gray-600 dark:text-gray-400">
                {doc.dept}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
