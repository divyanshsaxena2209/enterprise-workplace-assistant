"use client";

import React, { useEffect, useState } from "react";
import { getMyApplications, respondInterview } from "@/lib/api/applications";
import { FileText, Calendar, Clock, Link as LinkIcon, CheckCircle, XCircle, Clock4, Loader2 } from "lucide-react";

export default function MyApplicationsPage() {
  const [applications, setApplications] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // States for response modal
  const [selectedInterview, setSelectedInterview] = useState<any>(null);
  const [responseAction, setResponseAction] = useState<"Accepted" | "Rejected" | "Reschedule Requested" | null>(null);
  const [notes, setNotes] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchApplications = async () => {
    try {
      setLoading(true);
      const data = await getMyApplications(1, 100);
      setApplications(data.items || []);
    } catch (err: any) {
      setError(err.message || "Failed to load applications");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApplications();
  }, []);

  const handleRespond = async () => {
    if (!selectedInterview || !responseAction) return;
    setIsSubmitting(true);
    try {
      await respondInterview(selectedInterview.application_id, selectedInterview.id, responseAction, notes);
      setSelectedInterview(null);
      setResponseAction(null);
      setNotes("");
      await fetchApplications();
    } catch (err: any) {
      alert("Failed to submit response: " + err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 text-center text-red-500 bg-red-500/10 rounded-xl">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-10 max-w-5xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">My Applications</h1>
        <p className="text-sm text-muted-foreground mt-1">Track your internal job applications and interview requests.</p>
      </div>

      {applications.length === 0 ? (
        <div className="bg-card border border-border rounded-xl p-10 text-center shadow-sm">
          <FileText className="w-12 h-12 text-muted-foreground/50 mx-auto mb-4" />
          <h3 className="font-semibold text-lg text-foreground mb-1">No Applications Yet</h3>
          <p className="text-sm text-muted-foreground">You haven't applied to any internal roles.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {applications.map((app) => (
            <div key={app.id} className="bg-card border border-border rounded-xl p-6 shadow-sm">
              <div className="flex justify-between items-start mb-6 relative">
                {app.status?.toUpperCase() === "REJECTED" && (
                  <div className="absolute top-0 right-24 w-20 h-20 rounded-full border-4 border-red-600 text-red-600 flex items-center justify-center -rotate-12 opacity-90 shadow-lg bg-red-950/20 backdrop-blur-sm z-10 pointer-events-none">
                    <span className="text-xs font-black uppercase tracking-widest">Rejected</span>
                  </div>
                )}
                <div className="relative z-20">
                  <h3 className="font-bold text-lg tracking-tight">{app.job?.title || "Unknown Role"}</h3>
                  <p className="text-sm text-muted-foreground font-medium mt-0.5">{app.job?.department || "General"} • {app.job?.location}</p>
                </div>
                <span className="relative z-20 px-3 py-1 bg-secondary text-secondary-foreground text-xs uppercase tracking-wider rounded-md font-bold border border-border">
                  {app.status}
                </span>
              </div>

              {app.interviews && app.interviews.length > 0 && (
                <div className="mt-6 pt-6">
                  <h4 className="text-xs font-bold uppercase tracking-widest text-muted-foreground mb-6">Interview Thread</h4>
                  <div className="relative border-l-2 border-border/60 ml-4 space-y-8">
                    {[...app.interviews].sort((a: any, b: any) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()).map((interview: any) => (
                      <div key={interview.id} className="relative pl-6">
                        <div className="absolute -left-[9px] top-1.5 w-4 h-4 rounded-full border-[3px] border-background bg-foreground"></div>
                        <div className="bg-secondary/30 border border-border rounded-xl p-5 shadow-sm">
                          <div className="flex justify-between items-start mb-4">
                            <div>
                              <span className="text-[10px] uppercase font-bold tracking-wider text-muted-foreground block mb-1">
                                {new Date(interview.created_at).toLocaleString()}
                              </span>
                              <span className="text-sm font-bold">Management scheduled an interview</span>
                            </div>
                            <span className={`text-[10px] uppercase font-bold tracking-wider px-2.5 py-1 rounded-md ${
                              interview.status === 'Accepted' ? 'bg-green-500/10 text-green-500 border border-green-500/20' :
                              interview.status === 'Rejected' ? 'bg-red-500/10 text-red-500 border border-red-500/20' :
                              interview.status === 'Reschedule Requested' ? 'bg-orange-500/10 text-orange-500 border border-orange-500/20' :
                              interview.status === 'Pending' ? 'bg-yellow-500/10 text-yellow-500 border border-yellow-500/20' :
                              'bg-blue-500/10 text-blue-500 border border-blue-500/20'
                            }`}>
                              {interview.status}
                            </span>
                          </div>

                          <div className="bg-background/80 border border-border/50 rounded-lg p-3.5 mb-4 flex flex-col gap-2">
                            <div className="flex flex-wrap items-center gap-y-2 gap-x-4 text-sm font-semibold text-foreground">
                              <div className="flex items-center gap-1.5">
                                <Calendar size={14} className="text-muted-foreground" />
                                <span>{new Date(interview.scheduled_at).toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'short', day: 'numeric' })}</span>
                              </div>
                              <div className="flex items-center gap-1.5">
                                <Clock size={14} className="text-muted-foreground" />
                                <span>{new Date(interview.scheduled_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                              </div>
                            </div>
                            {interview.meeting_link && (
                              <div className="flex items-center gap-1.5 text-sm mt-1 pt-2 border-t border-border/50">
                                <LinkIcon size={14} className="text-muted-foreground shrink-0" />
                                <a href={interview.meeting_link} target="_blank" rel="noreferrer" className="text-blue-400 hover:underline truncate">
                                  {interview.meeting_link}
                                </a>
                              </div>
                            )}
                          </div>

                          {interview.management_notes && (
                            <div className="text-sm text-foreground mb-4 pl-3 border-l-2 border-muted">
                              <span className="text-[10px] font-bold text-muted-foreground uppercase block mb-1">Note from Management</span>
                              {interview.management_notes}
                            </div>
                          )}

                          {interview.candidate_notes && (
                            <div className="text-sm text-foreground mb-4 pl-3 border-l-2 border-foreground/30 bg-foreground/5 p-2 rounded-r-md">
                              <span className="text-[10px] font-bold text-muted-foreground uppercase block mb-1">Your Reply</span>
                              {interview.candidate_notes}
                            </div>
                          )}
                          
                          {interview.status === 'Pending' && (
                            <div className="flex items-center gap-3 mt-5 pt-5 border-t border-border">
                              <button 
                                onClick={() => { setSelectedInterview(interview); setResponseAction("Accepted"); }}
                                className="flex-1 bg-foreground text-background py-2 rounded-lg text-xs font-bold hover:bg-foreground/90 transition-all shadow-sm"
                              >
                                Accept
                              </button>
                              <button 
                                onClick={() => { setSelectedInterview(interview); setResponseAction("Reschedule Requested"); }}
                                className="flex-1 bg-secondary text-foreground border border-border py-2 rounded-lg text-xs font-bold hover:bg-secondary/80 transition-all shadow-sm"
                              >
                                Request Reschedule
                              </button>
                              <button 
                                onClick={() => { setSelectedInterview(interview); setResponseAction("Rejected"); }}
                                className="px-4 bg-red-500/10 text-red-500 border border-red-500/20 py-2 rounded-lg text-xs font-bold hover:bg-red-500/20 transition-all shadow-sm"
                              >
                                Decline
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Response Modal */}
      {selectedInterview && responseAction && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-background border border-border w-full max-w-md rounded-2xl shadow-2xl p-6" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-bold mb-2">
              {responseAction === 'Accepted' ? 'Accept Interview' : 
               responseAction === 'Rejected' ? 'Decline Interview' : 'Request Reschedule'}
            </h3>
            <p className="text-sm text-muted-foreground mb-6">
              You are about to {responseAction.toLowerCase()} the interview scheduled for {new Date(selectedInterview.scheduled_at).toLocaleString()}.
            </p>

            <div className="space-y-4 mb-6">
              <div>
                <label className="block text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Optional Notes</label>
                <textarea 
                  rows={3}
                  value={notes}
                  onChange={e => setNotes(e.target.value)}
                  placeholder={responseAction === 'Reschedule Requested' ? "Please suggest alternative times..." : "Any additional notes..."}
                  required={responseAction === 'Reschedule Requested'}
                  className="w-full p-3 rounded-lg border border-border bg-secondary/50 text-sm focus:outline-none focus:border-foreground transition-colors resize-none"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3">
              <button 
                type="button" 
                onClick={() => { setSelectedInterview(null); setResponseAction(null); setNotes(""); }}
                className="px-4 py-2 rounded-lg text-sm font-semibold hover:bg-secondary transition-colors"
                disabled={isSubmitting}
              >
                Cancel
              </button>
              <button 
                onClick={handleRespond}
                disabled={isSubmitting || (responseAction === 'Reschedule Requested' && !notes.trim())}
                className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-bold bg-foreground text-background hover:bg-foreground/90 transition-colors disabled:opacity-50"
              >
                {isSubmitting && <Loader2 size={16} className="animate-spin" />}
                Confirm {responseAction}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
