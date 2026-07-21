"use client";

import React from "react";
import { ArrowLeft, UserCircle, CheckCircle, FileText, Bot } from "lucide-react";
import Link from "next/link";

import { useParams } from "next/navigation";
import { getApplicationDetails, rejectApplication } from "@/lib/api/applications";
import { Loader2 } from "lucide-react";
import InterviewSchedulerModal from "@/components/candidates/InterviewSchedulerModal";

export default function CandidateDetailPage() {
  const { id } = useParams();
  const [appData, setAppData] = React.useState<any>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [rejecting, setRejecting] = React.useState(false);
  const [isInterviewModalOpen, setIsInterviewModalOpen] = React.useState(false);

  const fetchDetails = async () => {
    try {
      const data = await getApplicationDetails(id as string);
      setAppData(data);
      return data;
    } catch (err: any) {
      setError(err.message || "Failed to fetch details.");
      return null;
    } finally {
      if (loading) setLoading(false);
    }
  };

  React.useEffect(() => {
    let timeoutId: any;
    
    const initFetch = async () => {
      const data = await fetchDetails();
      if (data) {
        // If evaluation is still pending, poll again in 3 seconds
        if (!data.score || data.score.recommendation === "PENDING" || !data.score.ai_summary) {
          timeoutId = setTimeout(initFetch, 3000);
        }
      }
    };
    if (id) initFetch();

    return () => {
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [id, loading]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || !appData) {
    return (
      <div className="p-8 text-center text-red-500 bg-red-500/10 rounded-xl">
        {error || "Application not found"}
      </div>
    );
  }

  const handleReject = async () => {
    setRejecting(true);
    try {
      await rejectApplication(id as string, "Candidate rejected via dashboard.");
      await fetchDetails();
    } catch (err: any) {
      alert("Failed to reject candidate: " + err.message);
    } finally {
      setRejecting(false);
    }
  };

  const handleInterviewSuccess = async () => {
    await fetchDetails();
  };

  const { application, candidate, job, score, resume } = appData;
  const match = score?.relative_score ?? score?.match_percentage ?? 0;
  const aiSummary = score?.ai_summary || "Evaluation pending...";
  const strengths = score?.strengths || [];
  const weaknesses = score?.weaknesses || [];
  const recommendation = score?.recommendation || "Pending";
  const interviews = appData.interviews || [];

  return (
    <div className="space-y-8 pb-10">
      <Link href={job?.id ? `/jobs/${job.id}` : "/jobs"} className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground font-medium transition-colors">
        <ArrowLeft size={16} />
        Back to Requisition
      </Link>

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Left Column: Profile & Resume Preview */}
        <div className="lg:w-1/2 space-y-6">
          <div className="bg-card border border-border rounded-xl p-6 shadow-sm relative overflow-hidden">
            {application?.status?.toUpperCase() === "REJECTED" && (
              <div className="absolute top-6 right-8 w-24 h-24 rounded-full border-4 border-red-600 text-red-600 flex items-center justify-center -rotate-12 opacity-90 shadow-lg bg-red-950/20 backdrop-blur-sm z-20 pointer-events-none">
                <span className="text-sm font-black uppercase tracking-widest">Rejected</span>
              </div>
            )}
            <div className="flex items-start justify-between relative z-10">
              <div className="flex gap-5">
                <UserCircle size={64} className="text-muted-foreground stroke-[1.5]" />
                <div>
                  <h1 className="text-2xl font-bold tracking-tight text-foreground">{candidate?.full_name || "Unknown"}</h1>
                  <p className="text-sm font-medium text-muted-foreground mt-0.5">{job?.title || "Unknown Role"}</p>
                  <p className="text-xs text-muted-foreground mt-1 bg-secondary inline-block px-2 py-0.5 rounded border border-border/50">{candidate?.email || "No Email"}</p>
                </div>
              </div>
              <span className="px-3 py-1 bg-foreground text-background text-xs uppercase tracking-wider rounded-md font-semibold">
                {application?.status}
              </span>
            </div>
          </div>

          <div className="bg-card border border-border rounded-xl p-6 flex-1 min-h-[500px] flex flex-col shadow-sm relative">
            <h3 className="font-semibold text-sm uppercase tracking-wide text-foreground mb-4 flex items-center gap-2">
              <FileText size={16} className="text-muted-foreground" /> Original Resume
            </h3>
            <div className="flex-1 bg-secondary/50 rounded-lg border border-border flex overflow-hidden border-dashed">
              {resume?.file_url ? (
                <iframe 
                  src={resume.file_url.toLowerCase().endsWith('.docx') || resume.file_url.toLowerCase().endsWith('.doc') || resume.file_url.includes('.docx?') || resume.file_url.includes('.doc?')
                    ? `https://view.officeapps.live.com/op/embed.aspx?src=${encodeURIComponent(resume.file_url)}`
                    : resume.file_url} 
                  className="w-full h-full min-h-[400px] border-0" 
                  title="Candidate Resume"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-muted-foreground text-sm font-medium">
                  No Resume Available
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: AI Match & Insights */}
        <div className="lg:w-1/2 space-y-6">
          <div className="bg-card border border-border rounded-xl p-6 shadow-sm relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-foreground/5 rounded-bl-full -z-10"></div>
            <div className="flex items-center justify-between mb-6">
              <h3 className="font-semibold flex items-center gap-2 text-foreground tracking-tight">
                <div className="p-1.5 bg-foreground text-background rounded-md">
                  <Bot size={16} />
                </div>
                AI Evaluation
              </h3>
              <div className="text-right flex items-center gap-3">
                <div className="text-right">
                  <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold block mb-0.5">Match Score</span>
                  <div className="flex items-center justify-end gap-2">
                    <div className="w-20 h-1.5 bg-secondary rounded-full overflow-hidden">
                      <div className="h-full bg-foreground" style={{ width: `${match}%` }}></div>
                    </div>
                  </div>
                </div>
                <span className="text-2xl font-bold tracking-tight text-foreground">{match}%</span>
              </div>
            </div>
            
            <div className="bg-secondary/50 border border-border rounded-lg p-4 mb-6">
              <p className="text-sm text-muted-foreground leading-relaxed">
                {aiSummary}
              </p>
            </div>
            
            <div className="space-y-6 mt-6">
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-foreground mb-3 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-foreground"></span>
                  Strengths
                </h4>
                <ul className="space-y-2.5">
                  {strengths.length > 0 ? strengths.map((s: string, i: number) => (
                    <li key={i} className="text-sm text-muted-foreground flex items-start gap-3">
                      <CheckCircle size={16} className="text-foreground shrink-0 mt-0.5" />
                      {s}
                    </li>
                  )) : (
                    <li className="text-sm text-muted-foreground italic">No specific strengths identified.</li>
                  )}
                </ul>
              </div>
              
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-foreground mb-3 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-muted-foreground"></span>
                  Missing / Weaknesses
                </h4>
                <ul className="space-y-2.5">
                  {weaknesses.length > 0 ? weaknesses.map((w: string, i: number) => (
                    <li key={i} className="text-sm text-muted-foreground flex items-start gap-3">
                      <div className="w-1.5 h-1.5 rounded-full bg-muted-foreground shrink-0 mt-2 ml-1" />
                      {w}
                    </li>
                  )) : (
                    <li className="text-sm text-muted-foreground italic">No specific weaknesses identified.</li>
                  )}
                </ul>
              </div>
            </div>
            
            <div className="mt-8 pt-6 border-t border-border">
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Recommendation</span>
                <span className="px-4 py-1.5 bg-foreground text-background text-xs uppercase tracking-wider rounded-md font-semibold">
                  {recommendation}
                </span>
              </div>
            </div>
          </div>
          
          <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
            <h3 className="font-semibold text-sm uppercase tracking-wide text-foreground mb-4">Recruiter Actions</h3>
            <div className="flex flex-col sm:flex-row gap-3">
              <button 
                onClick={() => setIsInterviewModalOpen(true)}
                disabled={application?.status === "Rejected"}
                className="flex-1 bg-foreground hover:bg-foreground/90 text-background py-2.5 rounded-md text-sm font-semibold transition-all shadow-sm disabled:opacity-50"
              >
                Schedule Interview
              </button>
              <button 
                onClick={handleReject}
                disabled={rejecting || application?.status === "Rejected"}
                className="flex-1 bg-secondary hover:bg-secondary/80 text-foreground border border-border py-2.5 rounded-md text-sm font-semibold transition-all disabled:opacity-50"
              >
                {rejecting ? <Loader2 size={16} className="animate-spin inline mr-2" /> : null}
                Reject Candidate
              </button>
            </div>
          </div>

          {interviews.length > 0 && (
            <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
              <h3 className="font-semibold text-sm uppercase tracking-wide text-foreground mb-4">Interviews</h3>
              <div className="space-y-4">
                {interviews.map((interview: any) => (
                  <div key={interview.id} className="p-4 bg-secondary/50 rounded-lg border border-border">
                    <div className="flex justify-between items-start mb-2">
                      <p className="text-sm font-bold">{new Date(interview.scheduled_at).toLocaleString()}</p>
                      <span className="px-2 py-1 text-[10px] font-bold uppercase tracking-widest bg-foreground text-background rounded">
                        {interview.status}
                      </span>
                    </div>
                    {interview.meeting_link && (
                      <a href={interview.meeting_link} target="_blank" rel="noreferrer" className="text-xs text-blue-400 hover:underline mb-2 block">
                        {interview.meeting_link}
                      </a>
                    )}
                    {interview.candidate_notes && (
                      <div className="mt-3 p-3 bg-background rounded border border-border/50">
                        <p className="text-xs font-bold text-muted-foreground uppercase tracking-widest mb-1">Candidate Response:</p>
                        <p className="text-sm">{interview.candidate_notes}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      <InterviewSchedulerModal
        isOpen={isInterviewModalOpen}
        onClose={() => setIsInterviewModalOpen(false)}
        applicationId={id as string}
        candidateName={candidate?.full_name}
        jobTitle={job?.title}
        matchScore={match}
        avatarUrl={candidate?.avatar_url}
        onSuccess={handleInterviewSuccess}
      />
    </div>
  );
}
