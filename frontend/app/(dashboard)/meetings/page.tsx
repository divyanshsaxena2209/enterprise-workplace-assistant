"use client";

import React, { useState } from "react";
import { Video, Calendar, UploadCloud, ChevronRight, Mic, CheckCircle } from "lucide-react";
import Link from "next/link";

export default function MeetingsDashboard() {
  const [meetings] = useState([
    { id: 1, title: "Q3 Engineering Roadmap", dept: "Engineering", date: "Today, 10:00 AM", status: "Completed", tasks: 4 },
    { id: 2, title: "Marketing Campaign Kickoff", dept: "Marketing", date: "Yesterday", status: "Completed", tasks: 12 },
    { id: 3, title: "Weekly Sync - Sales", dept: "Sales", date: "2 days ago", status: "Transcribing", tasks: 0 },
  ]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Meeting Intelligence</h1>
          <p className="text-gray-500">Transcribe, summarize, and extract action items automatically.</p>
        </div>
        <Link href="/meetings/upload" className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors">
          <UploadCloud size={18} />
          Upload Recording
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-800 rounded-2xl shadow-sm">
          <h3 className="text-gray-500 text-sm font-medium mb-1">Total Meetings Indexed</h3>
          <p className="text-3xl font-bold">142</p>
        </div>
        <div className="p-6 bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-800 rounded-2xl shadow-sm">
          <h3 className="text-gray-500 text-sm font-medium mb-1">Action Items Generated</h3>
          <p className="text-3xl font-bold text-blue-600">894</p>
        </div>
        <div className="p-6 bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-800 rounded-2xl shadow-sm">
          <h3 className="text-gray-500 text-sm font-medium mb-1">Hours Saved</h3>
          <p className="text-3xl font-bold text-green-600">284h</p>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-800 rounded-2xl shadow-sm overflow-hidden">
        <div className="p-6 border-b border-gray-100 dark:border-gray-800 flex justify-between items-center">
          <h3 className="font-semibold text-lg">Recent Meetings</h3>
        </div>
        <div className="divide-y divide-gray-100 dark:divide-gray-800">
          {meetings.map(meeting => (
            <Link href={`/meetings/${meeting.id}`} key={meeting.id} className="p-5 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-900/50 transition cursor-pointer">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-full bg-blue-50 text-blue-600 dark:bg-blue-900/30 flex items-center justify-center shrink-0">
                  <Video size={20} />
                </div>
                <div>
                  <h4 className="font-semibold">{meeting.title}</h4>
                  <div className="flex items-center gap-3 text-xs text-gray-500 mt-1">
                    <span className="flex items-center gap-1"><Calendar size={12} /> {meeting.date}</span>
                    <span className="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 rounded-full">{meeting.dept}</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-6">
                <div className="text-right hidden md:block">
                  <span className={`text-xs font-medium px-2 py-1 rounded-full ${meeting.status === "Completed" ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400" : "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400"}`}>
                    {meeting.status === "Transcribing" ? <Mic size={12} className="inline mr-1 animate-pulse" /> : <CheckCircle size={12} className="inline mr-1" />}
                    {meeting.status}
                  </span>
                </div>
                {meeting.status === "Completed" && (
                  <div className="text-sm font-medium text-blue-600 hidden md:block">
                    {meeting.tasks} Tasks
                  </div>
                )}
                <ChevronRight className="text-gray-400" size={20} />
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
