import React, { useState } from "react";
import { X, Calendar, Clock, Link as LinkIcon, UserCircle, Bot, Loader2 } from "lucide-react";
import { createClient } from "@/lib/supabase/client";

interface InterviewSchedulerModalProps {
  isOpen: boolean;
  onClose: () => void;
  applicationId: string;
  candidateName: string;
  jobTitle: string;
  matchScore: number;
  avatarUrl?: string;
  onSuccess: (interviewData: any) => void;
}

export default function InterviewSchedulerModal({
  isOpen,
  onClose,
  applicationId,
  candidateName,
  jobTitle,
  matchScore,
  avatarUrl,
  onSuccess
}: InterviewSchedulerModalProps) {
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [meetingLink, setMeetingLink] = useState("");
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const formData = new FormData(e.currentTarget);
      const dateVal = formData.get("date") as string;
      const timeVal = formData.get("time") as string;
      let meetingLinkVal = formData.get("meetingLink") as string;
      if (meetingLinkVal && !/^https?:\/\//i.test(meetingLinkVal)) {
        meetingLinkVal = `https://${meetingLinkVal}`;
      }
      const notesVal = formData.get("notes") as string;

      if (!dateVal || !timeVal) throw new Error("Please select a date and time.");
      
      const [year, month, day] = dateVal.split('-');
      const [hour, minute] = timeVal.split(':');
      const scheduled_at = new Date(parseInt(year), parseInt(month) - 1, parseInt(day), parseInt(hour), parseInt(minute)).toISOString();
      const payload = {
        scheduled_at,
        meeting_link: meetingLinkVal || null,
        management_notes: notesVal || null
      };

      const supabase = createClient();
      const { data: session } = await supabase.auth.getSession();
      
      const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const API_URL = BASE_URL.includes("/api/v1") ? BASE_URL : `${BASE_URL.replace(/\/$/, "")}/api/v1`;

      const res = await fetch(`${API_URL}/applications/${applicationId}/interviews`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${session.session?.access_token}`
        },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Failed to schedule interview.");
      }

      const newInterview = await res.json();
      onSuccess(newInterview);
      onClose();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-black border border-border w-full max-w-4xl rounded-2xl shadow-2xl flex flex-col md:flex-row overflow-hidden relative" onClick={e => e.stopPropagation()}>
        
        {/* Left Side: Form */}
        <div className="w-full md:w-3/5 p-8 flex flex-col">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-bold tracking-tight">Schedule Interview</h2>
            <button type="button" onClick={onClose} className="p-2 hover:bg-secondary rounded-full text-muted-foreground transition-colors md:hidden">
              <X size={20} />
            </button>
          </div>

          {error && (
            <div className="mb-6 p-3 bg-red-500/10 text-red-500 border border-red-500/20 rounded-lg text-sm font-medium">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5 flex-1">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Date</label>
                <div className="relative">
                  <Calendar size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none" />
                  <input 
                    name="date"
                    type="date" 
                    required
                    onClick={e => {
                      try { if ('showPicker' in e.currentTarget) e.currentTarget.showPicker(); } catch (err) {}
                    }}
                    className="w-full pl-9 pr-3 py-2.5 rounded-lg border border-border bg-secondary/50 text-sm focus:outline-none focus:border-foreground transition-colors cursor-pointer"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Time</label>
                <div className="relative">
                  <Clock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none" />
                  <input 
                    name="time"
                    type="time" 
                    required
                    onClick={e => {
                      try { if ('showPicker' in e.currentTarget) e.currentTarget.showPicker(); } catch (err) {}
                    }}
                    className="w-full pl-9 pr-3 py-2.5 rounded-lg border border-border bg-secondary/50 text-sm focus:outline-none focus:border-foreground transition-colors cursor-pointer"
                  />
                </div>
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Meeting Link</label>
              <div className="relative">
                <LinkIcon size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none" />
                <input 
                  name="meetingLink"
                  type="text" 
                  placeholder="https://meet.google.com/..."
                  className="w-full pl-9 pr-3 py-2.5 rounded-lg border border-border bg-secondary/50 text-sm focus:outline-none focus:border-foreground transition-colors"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Notes for Candidate</label>
              <textarea 
                name="notes"
                rows={4}
                placeholder="Looking forward to speaking with you!"
                className="w-full p-3 rounded-lg border border-border bg-secondary/50 text-sm focus:outline-none focus:border-foreground transition-colors resize-none"
              />
            </div>

            <div className="pt-4 flex justify-end gap-3">
              <button 
                type="button" 
                onClick={onClose}
                className="px-5 py-2.5 rounded-lg text-sm font-semibold hover:bg-secondary transition-colors"
              >
                Cancel
              </button>
              <button 
                type="submit" 
                disabled={loading}
                className="flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-bold bg-foreground text-background hover:bg-foreground/90 transition-colors shadow-sm disabled:opacity-50"
              >
                {loading && <Loader2 size={16} className="animate-spin" />}
                Send Invitation
              </button>
            </div>
          </form>
        </div>

        {/* Right Side: Candidate Profile summary */}
        <div className="w-full md:w-2/5 bg-secondary/30 border-l border-border p-8 flex flex-col items-center justify-center relative overflow-hidden">
          <button onClick={onClose} className="absolute top-6 right-6 p-2 hover:bg-secondary rounded-full text-muted-foreground transition-colors hidden md:block z-10">
            <X size={20} />
          </button>
          
          <div className="absolute top-0 right-0 w-64 h-64 bg-foreground/5 rounded-bl-[100px] -z-10 blur-3xl"></div>
          <div className="absolute bottom-0 left-0 w-64 h-64 bg-foreground/5 rounded-tr-[100px] -z-10 blur-3xl"></div>

          <div className="w-32 h-32 mb-6 rounded-full border-4 border-background shadow-xl overflow-hidden bg-secondary flex items-center justify-center z-10">
            {avatarUrl ? (
              <img src={avatarUrl} alt={candidateName} className="w-full h-full object-cover" />
            ) : (
              <UserCircle size={64} className="text-muted-foreground stroke-[1]" />
            )}
          </div>
          
          <h3 className="text-xl font-bold tracking-tight text-center z-10">{candidateName}</h3>
          <p className="text-sm text-muted-foreground mt-1 font-medium text-center z-10">{jobTitle}</p>
          
          <div className="mt-8 bg-background border border-border p-4 rounded-xl flex items-center gap-4 shadow-sm z-10">
            <div className="p-2 bg-foreground text-background rounded-lg">
              <Bot size={20} />
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">AI Match</p>
              <p className="text-xl font-black">{matchScore}%</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
