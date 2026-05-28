"use client";

import React, { useState } from "react";
import {
  Video,
  Play,
  Pause,
  UploadCloud,
  FileText,
  Calendar,
  Clock,
  CheckSquare,
  Square,
  User,
  CheckCircle,
  Clock3,
  Search,
  Sparkles,
  ArrowLeft,
  ChevronRight,
  ListTodo,
  FileAudio
} from "lucide-react";

interface ActionItem {
  id: string;
  task_description: string;
  assignee_id?: string;
  assignee_fallback_name: string;
  deadline?: string;
  status: "PENDING" | "COMPLETED";
}

interface MeetingDetails {
  id: string;
  title: string;
  date: string;
  duration: string;
  audio_file_path?: string;
  transcript: string;
  summary: string;
  organized_by: string;
  action_items: ActionItem[];
}

export default function MeetingsDashboard() {
  // 1. Preloaded Premium state of meetings
  const [meetings, setMeetings] = useState<MeetingDetails[]>([
    {
      id: "meet-1",
      title: "Sprint Planning & AI Roadmap Sync",
      date: "2026-05-24",
      duration: "14 mins 20 secs",
      transcript: "[00:05] Divyansh Saxena: Good morning everyone, let's start our sprint planning session. Today we are prioritizing the AI Workplace Platform modules.\n\n[02:15] Sarah Conner: I've completed the base PostgreSQL schema designs and configured Row-Level Security for the user profiles and candidates tables. I will start implementing the resume extraction module using PDF parsers tomorrow.\n\n[05:40] Divyansh Saxena: Great job Sarah. Let's make sure the candidate suitability scoring gets saved correctly. Bruce, how is the knowledge base RAG pipeline looking?\n\n[07:10] Bruce Wayne: We decided to go with persistent ChromaDB storage for policy manual chunks. I've set up the sliding-window text chunker and generated embeddings using OpenAI's model. Next step is connecting the front-end chat interface.\n\n[10:30] Sarah Conner: Excellent. I think we need to finish this by next Friday.\n\n[12:15] Divyansh Saxena: Agreed. I will take care of deploying the Next.js shell layout and configuring Supabase cookie authentication, aiming to wrap that up by Monday.",
      summary: "### Executive Sync Summary\n\nThe team aligned on the development priorities for the **AI-Powered Enterprise Workplace Assistant Platform**.\n\n### Key Discussion Points\n- **Database Infrastructure**: Sarah Conner confirmed that the PostgreSQL schemas and RLS security policies are fully configured in Supabase, laying a secure database core.\n- **RAG & Semantic Search**: Bruce Wayne successfully integrated the ChromaDB persistent client, implementing text sliding-window chunking and embedding pipelines.\n- **Authentication & Dashboard UI**: Divyansh Saxena reported that the core Next.js 15 layout structures and Supabase authentication routing are ready.\n\n### Strategic Decisions\n- Persistent local vector directories are chosen for ChromaDB to ensure stable in-memory queries during local testing.\n- Completed Phase 1 modules will serve as the foundation for the subsequent onboarding portal features.",
      organized_by: "Divyansh Saxena",
      action_items: [
        {
          id: "act-1",
          task_description: "Deploy Next.js dashboard shell layout and set up Supabase cookie authentication.",
          assignee_fallback_name: "Divyansh Saxena",
          deadline: "2026-05-26",
          status: "COMPLETED"
        },
        {
          id: "act-2",
          task_description: "Implement resume document text parsing (PDF/DOCX) and configure GPT-4o screening endpoints.",
          assignee_fallback_name: "Sarah Conner",
          deadline: "2026-06-01",
          status: "PENDING"
        },
        {
          id: "act-3",
          task_description: "Connect frontend knowledge base chat components to FastAPI ChromaDB vector query routes.",
          assignee_fallback_name: "Bruce Wayne",
          deadline: "2026-06-03",
          status: "PENDING"
        }
      ]
    }
  ]);

  const [selectedMeetingId, setSelectedMeetingId] = useState<string | null>(null);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadFileName, setUploadFileName] = useState("");
  const [uploadProgress, setUploadProgress] = useState(0);

  const [activeTab, setActiveTab] = useState<"SUMMARY" | "TRANSCRIPT" | "ACTIONS">("SUMMARY");
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioProgress, setAudioProgress] = useState(35); // mock active audio playing

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadFileName(file.name);
    setIsUploading(true);
    setUploadProgress(15);

    // Simulate Whisper speech-to-text + GPT analysis loading
    const timer = setInterval(() => {
      setUploadProgress(p => {
        if (p >= 90) {
          clearInterval(timer);
          return 90;
        }
        return p + 20;
      });
    }, 450);

    setTimeout(() => {
      clearInterval(timer);
      setUploadProgress(100);

      const parsedMeeting: MeetingDetails = {
        id: `meet-${Date.now()}`,
        title: "IT Assets and HR Onboarding Strategy Review",
        date: new Date().toISOString().split("T")[0],
        duration: "3 mins 12 secs",
        transcript: "[00:10] Divyansh Saxena: Let's quickly synchronize on onboarding IT assets. New employees are facing delays in laptop delivery.\n\n[01:05] Bruce Wayne: I've prepared laptop configurations for IT. I will request procurement to dispatch standard hardware profiles within 48 hours of new hire registrations.\n\n[02:30] Sarah Conner: Excellent. I will update the onboarding milestone checklist in the portal so new hires can see real-time updates.",
        summary: "### IT & HR Sync Summary\n\nSynchronized workflow processes between HR onboarding registrations and IT computer inventory dispatches.\n\n### Core Insights\n- **Asset Delays**: Identified latency in laptop delivery. Bruce Wayne will enforce a 48-hour hardware allocation SLA.\n- **Portal Synchronization**: Sarah Conner will implement real-time IT asset milestones on the employee onboarding portal dashboard.",
        organized_by: "Divyansh Saxena",
        action_items: [
          {
            id: `act-${Date.now()}`,
            task_description: "Enforce 48-hour hardware allocation SLA and dispatch laptop profiles to procurement.",
            assignee_fallback_name: "Bruce Wayne",
            deadline: "2026-05-28",
            status: "PENDING"
          },
          {
            id: `act-${Date.now() + 1}`,
            task_description: "Synchronize IT hardware milestone updates inside the employee onboarding timeline.",
            assignee_fallback_name: "Sarah Conner",
            deadline: "2026-05-29",
            status: "PENDING"
          }
        ]
      };

      setMeetings([parsedMeeting, ...meetings]);
      setIsUploading(false);
      setShowUploadModal(false);
      setSelectedMeetingId(parsedMeeting.id); // View details immediately
    }, 2800);
  };

  const toggleActionItem = (meetingId: string, actionId: string) => {
    setMeetings(prev =>
      prev.map(m => {
        if (m.id === meetingId) {
          const updatedActions = m.action_items.map(a =>
            a.id === actionId ? { ...a, status: (a.status === "PENDING" ? "COMPLETED" : "PENDING") as any } : a
          );
          return { ...m, action_items: updatedActions };
        }
        return m;
      })
    );
  };

  const activeMeeting = meetings.find(m => m.id === selectedMeetingId);

  return (
    <div className="space-y-6">
      {!activeMeeting ? (
        // DASHBOARD INDEX VIEW: List of meetings
        <>
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <h2 className="text-2xl font-bold tracking-tight">AI Meeting Minutes & Task Generator</h2>
              <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
                Upload raw meeting audio files. Convert speech to text via Whisper, extract executive summaries, and generate actionable tasks.
              </p>
            </div>
            <button
              onClick={() => setShowUploadModal(true)}
              className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2.5 rounded-lg text-sm font-semibold transition-all shadow cursor-pointer"
            >
              <UploadCloud className="w-4 h-4" />
              <span>Transcribe Recording</span>
            </button>
          </div>

          <div className="bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden">
            <div className="p-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-[#111827] flex justify-between items-center">
              <span className="font-bold text-sm text-slate-700 dark:text-slate-300">Recorded Sessions</span>
              <span className="text-xs text-slate-400">{meetings.length} Total</span>
            </div>

            <div className="divide-y divide-slate-100 dark:divide-slate-850">
              {meetings.map((meet) => {
                const completedCount = meet.action_items.filter(a => a.status === "COMPLETED").length;
                const totalCount = meet.action_items.length;
                return (
                  <div
                    key={meet.id}
                    className="p-5 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 hover:bg-slate-50/30 dark:hover:bg-slate-800/10 transition-all"
                  >
                    <div className="space-y-1.5 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm leading-snug">{meet.title}</span>
                      </div>
                      <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400">
                        <span className="flex items-center gap-1.5">
                          <Calendar className="w-3.5 h-3.5" />
                          <span>{meet.date}</span>
                        </span>
                        <span className="h-1.5 w-1.5 rounded-full bg-slate-200 dark:bg-slate-800"></span>
                        <span className="flex items-center gap-1.5">
                          <Clock className="w-3.5 h-3.5" />
                          <span>{meet.duration}</span>
                        </span>
                        <span className="h-1.5 w-1.5 rounded-full bg-slate-200 dark:bg-slate-800"></span>
                        <span>Organized by: {meet.organized_by}</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-4 flex-shrink-0 self-end md:self-center">
                      <span className="text-xs bg-slate-100 dark:bg-slate-800 text-slate-500 px-2.5 py-1 rounded-full font-semibold">
                        {completedCount}/{totalCount} Tasks Done
                      </span>

                      <button
                        onClick={() => {
                          setSelectedMeetingId(meet.id);
                          setActiveTab("SUMMARY");
                        }}
                        className="flex items-center gap-1 bg-slate-50 dark:bg-slate-900 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-800 px-3.5 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer text-slate-700 dark:text-slate-200"
                      >
                        <span>View Minutes</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </>
      ) : (
        // DETAILED MEETING VIEW
        <div className="space-y-6 animate-fade-in">
          {/* Detailed Header back navigation */}
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <button
              onClick={() => setSelectedMeetingId(null)}
              className="flex items-center gap-2 text-slate-500 hover:text-slate-900 dark:hover:text-slate-100 text-xs font-semibold cursor-pointer"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Meetings</span>
            </button>

            <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider flex items-center gap-1">
              <Sparkles className="w-4 h-4 text-blue-500" />
              <span>Whisper Speech Transcribed</span>
            </span>
          </div>

          <div className="bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-xl p-5 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div className="space-y-1.5">
              <span className="text-[10px] font-bold text-blue-600 dark:text-blue-400 uppercase tracking-widest">Meeting Audit Screen</span>
              <h3 className="font-bold text-lg leading-tight">{activeMeeting.title}</h3>
              <p className="text-xs text-slate-400">Recorded Date: {activeMeeting.date} | Duration: {activeMeeting.duration}</p>
            </div>

            {/* Custom Interactive Audio Player */}
            <div className="bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 px-4 py-2.5 rounded-xl flex items-center gap-3 w-full md:w-80">
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className="h-8 w-8 rounded-full bg-blue-600 hover:bg-blue-700 text-white flex items-center justify-center flex-shrink-0 cursor-pointer transition-all"
              >
                {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 pl-0.5" />}
              </button>
              
              <div className="flex-1 space-y-1">
                <div className="flex justify-between text-[9px] text-slate-400 font-bold leading-none">
                  <span>04:12</span>
                  <span>14:20</span>
                </div>
                <div className="w-full bg-slate-200 dark:bg-slate-800 h-1 rounded-full overflow-hidden relative cursor-pointer">
                  <div className="h-full bg-blue-600" style={{ width: `${audioProgress}%` }}></div>
                </div>
              </div>
              <FileAudio className="w-4 h-4 text-slate-400" />
            </div>
          </div>

          {/* Multi-Tab Panel section */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left 2/3: Content Panel (Summary / Transcript) */}
            <div className="lg:col-span-2 bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-xl flex flex-col h-[500px] overflow-hidden">
              <div className="flex border-b border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-[#111827] flex-shrink-0">
                <button
                  onClick={() => setActiveTab("SUMMARY")}
                  className={`px-5 py-3 text-xs font-semibold border-b-2 transition-all cursor-pointer ${
                    activeTab === "SUMMARY"
                      ? "border-blue-600 text-blue-600 dark:text-blue-400 bg-white dark:bg-[#111827]"
                      : "border-transparent text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
                  }`}
                >
                  Minutes Summary
                </button>
                <button
                  onClick={() => setActiveTab("TRANSCRIPT")}
                  className={`px-5 py-3 text-xs font-semibold border-b-2 transition-all cursor-pointer ${
                    activeTab === "TRANSCRIPT"
                      ? "border-blue-600 text-blue-600 dark:text-blue-400 bg-white dark:bg-[#111827]"
                      : "border-transparent text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
                  }`}
                >
                  Speech Transcript
                </button>
              </div>

              <div className="flex-1 p-6 overflow-y-auto leading-relaxed">
                {activeTab === "SUMMARY" ? (
                  <div className="prose prose-slate dark:prose-invert max-w-none text-sm text-slate-700 dark:text-slate-350 space-y-4">
                    {/* Simplified render for markdown summary */}
                    {activeMeeting.summary.split("\n\n").map((para, idx) => {
                      if (para.startsWith("###")) {
                        return <h4 key={idx} className="font-bold text-slate-900 dark:text-slate-100 text-sm mt-4 uppercase tracking-wider">{para.replace("###", "").trim()}</h4>;
                      }
                      if (para.startsWith("-")) {
                        return (
                          <ul key={idx} className="list-disc pl-5 space-y-1.5">
                            {para.split("\n").map((li, lIdx) => (
                              <li key={lIdx}>{li.replace("-", "").trim()}</li>
                            ))}
                          </ul>
                        );
                      }
                      return <p key={idx}>{para}</p>;
                    })}
                  </div>
                ) : (
                  <div className="space-y-4 text-sm font-mono text-slate-600 dark:text-slate-450 whitespace-pre-line leading-relaxed">
                    {activeMeeting.transcript}
                  </div>
                )}
              </div>
            </div>

            {/* Right 1/3: Action items checklist */}
            <div className="lg:col-span-1 bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-xl p-5 flex flex-col h-[500px] overflow-hidden">
              <h3 className="font-bold text-sm text-slate-700 dark:text-slate-300 mb-4 flex items-center gap-2 flex-shrink-0">
                <ListTodo className="w-4.5 h-4.5 text-blue-600" />
                <span>Extracted Tasks ({activeMeeting.action_items.length})</span>
              </h3>

              <div className="flex-1 overflow-y-auto space-y-3 pr-1">
                {activeMeeting.action_items.map((action) => {
                  const isDone = action.status === "COMPLETED";
                  return (
                    <div
                      key={action.id}
                      onClick={() => toggleActionItem(activeMeeting.id, action.id)}
                      className={`p-3 border rounded-xl cursor-pointer transition-colors flex gap-3 items-start select-none ${
                        isDone
                          ? "bg-slate-50 dark:bg-slate-900 border-slate-200 dark:border-slate-850 opacity-60"
                          : "bg-white dark:bg-slate-900/40 border-slate-100 dark:border-slate-800 hover:border-blue-200"
                      }`}
                    >
                      <div className="mt-0.5 flex-shrink-0 text-slate-400 hover:text-blue-600">
                        {isDone ? (
                          <CheckSquare className="w-4 h-4 text-blue-600" />
                        ) : (
                          <Square className="w-4 h-4" />
                        )}
                      </div>
                      
                      <div className="space-y-2 flex-1">
                        <p className={`text-xs font-semibold leading-snug ${isDone ? "line-through text-slate-400" : ""}`}>
                          {action.task_description}
                        </p>
                        
                        <div className="flex flex-wrap items-center justify-between text-[9px] text-slate-400">
                          <span className="bg-slate-100 dark:bg-slate-800 text-slate-500 px-2 py-0.5 rounded font-bold uppercase">
                            {action.assignee_fallback_name}
                          </span>
                          
                          {action.deadline && (
                            <span className="flex items-center gap-1">
                              <Clock3 className="w-3 h-3 text-blue-500" />
                              <span>Due: {action.deadline}</span>
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* UPLOAD MEETING AUDIO RECORDING MODAL */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 w-full max-w-md rounded-xl overflow-hidden shadow-2xl animate-fade-in">
            <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center">
              <h3 className="font-bold text-lg">Upload Meeting Audio</h3>
              <button onClick={() => setShowUploadModal(false)} className="p-1 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full cursor-pointer">
                <X className="w-4 h-4 text-slate-400" />
              </button>
            </div>

            <div className="p-6 text-center space-y-6">
              {isUploading ? (
                <div className="space-y-4 py-6">
                  <div className="relative h-16 w-16 mx-auto flex items-center justify-center">
                    <span className="absolute animate-ping h-8 w-8 rounded-full bg-blue-400 opacity-75"></span>
                    <UploadCloud className="h-8 w-8 text-blue-600 relative z-10" />
                  </div>
                  <div className="space-y-2">
                    <p className="font-bold text-sm">Whisper Transcribing Audio...</p>
                    <p className="text-xs text-slate-400 truncate max-w-xs mx-auto">Extracting minutes from: {uploadFileName}</p>
                  </div>
                  <div className="w-full bg-slate-100 dark:bg-slate-800 h-1.5 rounded-full overflow-hidden max-w-xs mx-auto">
                    <div className="h-full bg-blue-600 transition-all duration-300" style={{ width: `${uploadProgress}%` }}></div>
                  </div>
                </div>
              ) : (
                <div className="border-2 border-dashed border-slate-200 dark:border-slate-800 hover:border-blue-500 rounded-xl p-8 transition-colors relative cursor-pointer group">
                  <input
                    type="file"
                    accept="audio/*"
                    onChange={handleFileUpload}
                    className="absolute inset-0 opacity-0 cursor-pointer"
                  />
                  <div className="space-y-3">
                    <UploadCloud className="h-10 w-10 text-slate-400 group-hover:text-blue-500 mx-auto transition-colors" />
                    <div className="space-y-1">
                      <p className="font-bold text-sm">Upload meeting recording</p>
                      <p className="text-xs text-slate-400">MP3, WAV, M4A audio files up to 25MB</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
