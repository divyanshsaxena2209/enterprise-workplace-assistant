"use client";
import React, { useState, useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Upload, Search, Filter, MoreHorizontal, FileText, Sparkles, CheckCircle2, Loader2, AlertCircle, ArrowLeft, MapPin, Users, Briefcase, UserCircle, X } from "lucide-react";
import { uploadResume } from "@/lib/api/candidates";
import { getApplications, createApplication, getMyApplications, getApplicationDetails, respondInterview } from "@/lib/api/applications";
import { getJob } from "@/lib/api/jobs";
import { useUser } from "@/lib/context/UserContext";
export default function JobDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [job, setJob] = useState<any>(null);
  const [jobLoading, setJobLoading] = useState(true);
  const [jobError, setJobError] = useState<string | null>(null);
  const { profile } = useUser();
  const isManagement = profile?.role === "MANAGEMENT";
  const [activeTab, setActiveTab] = useState("candidates");
  const [myApplications, setMyApplications] = useState<any[]>([]);
  const [myApplicationDetails, setMyApplicationDetails] = useState<any>(null);
  const [respondNotes, setRespondNotes] = useState("");
  const [isResponding, setIsResponding] = useState(false);
  const [applyModalOpen, setApplyModalOpen] = useState(false);
  const [applyLoading, setApplyLoading] = useState(false);
  const [applySuccess, setApplySuccess] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  useEffect(() => {
    const fetchJobDetails = async () => {
      try {
        const jobData = await getJob(id);
        setJob(jobData);
        if (profile?.role !== "MANAGEMENT") {
          try {
            const myApps = await getMyApplications(1, 100);
            setMyApplications(myApps.items || []);
            const myApp = myApps.items?.find((app: any) => app.job_id === id);
            if (myApp) {
              const details = await getApplicationDetails(myApp.id);
              setMyApplicationDetails(details);
            }
          } catch (e: any) {
            console.warn("Failed to load my applications:", e.message || e);
          }
        }
      } catch (err: any) {
        setJobError(err.message || "Failed to load job details.");
      } finally {
        setJobLoading(false);
      }
    };
    if (id) fetchJobDetails();
  }, [id]);
  if (jobLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] text-muted-foreground space-y-4">
        <Loader2 className="w-8 h-8 animate-spin" />
        <p className="text-xs uppercase tracking-widest font-bold">Querying Requisition Details...</p>
      </div>
    );
  }
  if (jobError || !job) {
    return (
      <div className="p-8 text-center text-red-500 bg-red-500/10 rounded-xl border border-red-500/20 max-w-xl mx-auto mt-10">
        <AlertCircle className="w-8 h-8 mx-auto mb-4" />
        <p className="font-bold">{jobError || "Job Requisition not found"}</p>
        <Link href="/jobs" className="inline-block mt-4 text-white underline text-sm">Return to Jobs</Link>
      </div>
    );
  }
  return (
    <div className="space-y-8 pb-10">
      <Link href="/jobs" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground font-medium transition-colors">
        <ArrowLeft size={16} />
        Back to Requisitions
      </Link>
      {}
      <div className="p-8 glass-panel-heavy rounded-3xl border border-white/10 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-bl-full -z-10 blur-3xl pointer-events-none" />
        <div className="flex flex-col sm:flex-row justify-between items-start gap-6">
          <div className="flex items-center gap-6">
            <div className="w-16 h-16 rounded-2xl bg-white/10 flex items-center justify-center text-white border border-white/20 shadow-inner">
              <Briefcase size={28} />
            </div>
            <div>
              <h1 className="text-3xl font-black tracking-tight text-white">{job.title}</h1>
              <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground mt-2 font-medium">
                <span className="flex items-center gap-1.5"><MapPin size={14} className="text-white/70" /> {job.location || "Remote"}</span>
                <span className="flex items-center gap-1.5"><Users size={14} className="text-white/70" /> {job.department || "General"}</span>
                <span className="px-2.5 py-0.5 bg-white/10 border border-white/10 rounded-full text-[10px] uppercase tracking-widest text-white/90 font-bold backdrop-blur-sm">{job.employment_type || "Full-time"}</span>
              </div>
            </div>
          </div>
          <div>
            <span className={`px-4 py-2 text-xs uppercase tracking-widest font-black rounded-xl border shadow-sm backdrop-blur-md ${
              job.status === "PUBLISHED" 
                ? "bg-white/15 text-white border-white/20 shadow-[0_0_15px_rgba(255,255,255,0.1)]" 
                : "bg-black/50 text-muted-foreground border-white/10"
            }`}>
              {job.status || "DRAFT"}
            </span>
          </div>
        </div>
        <div className="mt-8 pt-6 border-t border-white/10">
          <h4 className="text-xs font-bold uppercase tracking-widest text-muted-foreground mb-3">Requisition Description</h4>
          <p className="text-sm text-white/80 leading-relaxed max-w-4xl whitespace-pre-line">{job.description}</p>
        </div>
      </div>
      {}
      {isManagement ? (
        <>
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 pt-6">
            <div>
              <h2 className="text-2xl font-black tracking-tight text-white flex items-center gap-3">
                <Sparkles className="w-5 h-5 text-white animate-pulse" />
                Candidates
              </h2>
              <p className="text-xs text-muted-foreground mt-1 uppercase tracking-widest font-bold">Manage applicants for this specific requisition.</p>
            </div>
            <div className="flex p-1.5 glass-panel rounded-2xl shadow-xl">
              <button
                onClick={() => setActiveTab("candidates")}
                className={`px-5 py-2.5 rounded-xl text-xs font-bold uppercase tracking-wider transition-all duration-300 cursor-pointer ${
                  activeTab === "candidates" 
                    ? "bg-white/15 shadow-[0_0_15px_rgba(255,255,255,0.1)] text-white border border-white/10" 
                    : "text-muted-foreground hover:text-white hover:bg-white/5 border border-transparent"
                }`}
              >
                Evaluated Personnel
              </button>
              <button
                onClick={() => setActiveTab("upload")}
                className={`px-5 py-2.5 rounded-xl text-xs font-bold uppercase tracking-wider transition-all duration-300 cursor-pointer ${
                  activeTab === "upload" 
                    ? "bg-white/15 shadow-[0_0_15px_rgba(255,255,255,0.1)] text-white border border-white/10" 
                    : "text-muted-foreground hover:text-white hover:bg-white/5 border border-transparent"
                }`}
              >
                Ingest Resumes
              </button>
            </div>
          </div>
          {activeTab === "upload" ? <ResumeUploadFlow jobId={id} onComplete={() => setActiveTab("candidates")} /> : <CandidateDashboard jobId={id} />}
        </>
      ) : (
        <div className="pt-6 border-t border-white/10 flex flex-col items-center text-center">
          <h2 className="text-xl font-black tracking-tight text-white mb-2">Interested in this position?</h2>
          <p className="text-sm text-muted-foreground mb-6">Apply now to submit your resume and enter the candidate pool.</p>
          {myApplications.some(app => app.job_id === id) ? (
            <div className="w-full max-w-2xl mx-auto space-y-4">
              {(!myApplicationDetails?.interviews || myApplicationDetails.interviews.length === 0) && (
                <div className="px-8 py-4 bg-green-500/10 border border-green-500/20 rounded-xl text-green-400 font-black uppercase tracking-widest flex items-center justify-center gap-2">
                  <CheckCircle2 size={18} />
                  You have applied
                </div>
              )}
              {myApplicationDetails?.interviews && myApplicationDetails.interviews.length > 0 && (
                <div className="bg-white/5 border border-white/10 rounded-2xl p-6 text-left">
                  <h3 className="font-black text-lg text-white mb-4 flex items-center gap-2">
                    <Sparkles size={18} className="text-yellow-400" />
                    Interview Scheduled
                  </h3>
                  <div className="space-y-4">
                    {myApplicationDetails.interviews.map((interview: any) => (
                      <div key={interview.id} className="p-4 bg-black/40 rounded-xl border border-white/10 relative">
                        <div className="flex justify-between items-start mb-3">
                          <div>
                            <p className="text-[10px] text-muted-foreground font-bold uppercase tracking-widest">Scheduled For</p>
                            <p className="text-sm font-bold text-white">{new Date(interview.scheduled_at).toLocaleString()}</p>
                          </div>
                          <span className="px-2 py-1 text-[10px] font-bold uppercase tracking-widest bg-white/10 text-white rounded">
                            {interview.status}
                          </span>
                        </div>
                        {interview.meeting_link && (
                          <div className="mb-4">
                            <p className="text-[10px] text-muted-foreground font-bold uppercase tracking-widest mb-1">Meeting Link</p>
                            <a href={interview.meeting_link} target="_blank" rel="noreferrer" className="text-xs text-blue-400 hover:underline font-medium break-all">
                              {interview.meeting_link}
                            </a>
                          </div>
                        )}
                        {interview.status === "Accepted" ? (
                          <div className="mt-4 p-4 bg-green-500/10 rounded-xl border border-green-500/20 text-center">
                            <p className="text-sm font-black text-green-400 uppercase tracking-widest mb-1">Interview Confirmed</p>
                            <p className="text-xs text-green-400/80">You have confirmed your attendance.</p>
                            {interview.candidate_notes && (
                              <div className="mt-3 pt-3 border-t border-green-500/20 text-left">
                                <p className="text-[10px] text-green-400/60 font-bold uppercase tracking-widest mb-1">Your Note:</p>
                                <p className="text-xs text-green-400/90 font-medium">{interview.candidate_notes}</p>
                              </div>
                            )}
                          </div>
                        ) : interview.status === "Reschedule Requested" ? (
                          <div className="mt-4 p-4 bg-orange-500/10 rounded-xl border border-orange-500/20 text-center">
                            <p className="text-sm font-black text-orange-400 uppercase tracking-widest mb-1">Reschedule Requested</p>
                            <p className="text-xs text-orange-400/80">Awaiting recruiter response.</p>
                            {interview.candidate_notes && (
                              <div className="mt-3 pt-3 border-t border-orange-500/20 text-left">
                                <p className="text-[10px] text-orange-400/60 font-bold uppercase tracking-widest mb-1">Your Note:</p>
                                <p className="text-xs text-orange-400/90 font-medium">{interview.candidate_notes}</p>
                              </div>
                            )}
                          </div>
                        ) : (
                          <div className="mt-4 pt-4 border-t border-white/10">
                            <p className="text-xs text-muted-foreground mb-2">Please respond to confirm your attendance or request a reschedule.</p>
                            <textarea 
                              placeholder="Any notes for the recruiter? (e.g. 'I will be there!' or 'Can we reschedule to 3PM?')"
                              className="w-full bg-black/50 border border-white/10 rounded-xl p-3 text-sm text-white placeholder:text-white/30 focus:outline-none focus:border-white/30 min-h-[80px] mb-3"
                              value={respondNotes}
                              onChange={e => setRespondNotes(e.target.value)}
                            />
                            <div className="flex gap-2">
                              <button 
                                onClick={async () => {
                                  setIsResponding(true);
                                  try {
                                    await respondInterview(myApplicationDetails.application.id, interview.id, 'Accepted', respondNotes);
                                    const details = await getApplicationDetails(myApplicationDetails.application.id);
                                    setMyApplicationDetails(details);
                                  } catch (e: any) { alert(e.message); }
                                  finally { setIsResponding(false); }
                                }}
                                disabled={isResponding}
                                className="flex-1 bg-green-500/20 text-green-400 hover:bg-green-500/30 border border-green-500/30 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-colors disabled:opacity-50"
                              >
                                Accept Time
                              </button>
                              <button 
                                onClick={async () => {
                                  setIsResponding(true);
                                  try {
                                    await respondInterview(myApplicationDetails.application.id, interview.id, 'Reschedule Requested', respondNotes);
                                    const details = await getApplicationDetails(myApplicationDetails.application.id);
                                    setMyApplicationDetails(details);
                                  } catch (e: any) { alert(e.message); }
                                  finally { setIsResponding(false); }
                                }}
                                disabled={isResponding}
                                className="flex-1 bg-white/10 text-white hover:bg-white/20 border border-white/10 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-colors disabled:opacity-50"
                              >
                                Request Reschedule
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <button
              onClick={() => {
                setApplyModalOpen(true);
                setApplySuccess(false);
                setResumeFile(null);
                setSubmitError(null);
              }}
              className="px-8 py-4 bg-white text-black hover:bg-gray-200 rounded-xl text-xs font-black uppercase tracking-widest transition-all shadow-[0_0_15px_rgba(255,255,255,0.2)] hover:shadow-[0_0_25px_rgba(255,255,255,0.4)]"
            >
              Apply Now
            </button>
          )}
        </div>
      )}
      {}
      {applyModalOpen && typeof document !== "undefined" && createPortal(
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-zinc-900 border border-white/20 rounded-2xl w-full max-w-md shadow-2xl relative flex flex-col overflow-hidden">
            <div className="p-6 pb-4 flex-shrink-0 border-b border-white/10 relative">
              <button 
                onClick={() => setApplyModalOpen(false)}
                className="absolute top-6 right-6 text-muted-foreground hover:text-white transition-colors"
              >
                <X size={20} />
              </button>
              <h2 className="text-xl font-black tracking-tight text-white m-0 py-1">Apply for Position</h2>
            </div>
            <div className="p-6 space-y-6">
              {applySuccess ? (
                <div className="text-center py-8">
                  <div className="w-16 h-16 bg-green-500/20 text-green-400 rounded-full flex items-center justify-center mx-auto mb-4 border border-green-500/30">
                    <Sparkles className="w-8 h-8" />
                  </div>
                  <h3 className="text-xl font-bold text-white mb-2">Application Submitted!</h3>
                  <p className="text-sm text-muted-foreground">Your resume has been uploaded and passed to our intelligence engine.</p>
                  <button 
                    onClick={() => {
                      setApplyModalOpen(false);
                      try {
                        getMyApplications(1, 100).then(res => setMyApplications(res.items || []));
                      } catch(e){}
                    }}
                    className="mt-6 px-6 py-2.5 bg-white text-black hover:bg-gray-200 rounded-lg text-sm font-black uppercase tracking-wider w-full"
                  >
                    Done
                  </button>
                </div>
              ) : (
                <>
                  {submitError && (
                    <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm font-semibold text-center">
                      {submitError}
                    </div>
                  )}
                  <div className="border-2 border-dashed border-white/20 rounded-xl p-8 text-center bg-black/30 hover:bg-black/50 transition-colors relative">
                    <input 
                      type="file" 
                      accept=".pdf,.doc,.docx"
                      onChange={(e) => {
                        if (e.target.files && e.target.files[0]) {
                          setResumeFile(e.target.files[0]);
                        }
                      }}
                      className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    />
                    <Upload className="w-8 h-8 text-muted-foreground mx-auto mb-3" />
                    <p className="text-sm font-semibold text-white mb-1">
                      {resumeFile ? resumeFile.name : "Click or drag resume here"}
                    </p>
                    <p className="text-xs text-muted-foreground">PDF or DOCX up to 10MB</p>
                  </div>
                  <button 
                    disabled={!resumeFile || applyLoading}
                    onClick={async () => {
                      if (!resumeFile) return;
                      setApplyLoading(true);
                      setSubmitError(null);
                      try {
                        const uploadRes = await uploadResume(resumeFile);
                        if (uploadRes.candidate_id && uploadRes.resume_id) {
                          await createApplication({
                            job_id: id,
                            candidate_id: uploadRes.candidate_id,
                            resume_id: uploadRes.resume_id
                          });
                          setApplySuccess(true);
                        }
                      } catch (err: any) {
                        setSubmitError(err.message || "Failed to submit application.");
                      } finally {
                        setApplyLoading(false);
                      }
                    }}
                    className="w-full px-6 py-3 rounded-xl text-sm font-black uppercase tracking-wider bg-white text-black hover:bg-gray-200 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    {applyLoading ? <Loader2 size={16} className="animate-spin" /> : null}
                    Submit Application
                  </button>
                </>
              )}
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  );
}
function ResumeUploadFlow({ jobId, onComplete }: { jobId: string, onComplete: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };
  const handleUpload = async () => {
    if (!file) return;
    setIsUploading(true);
    setError(null);
    try {
      const uploadRes = await uploadResume(file);
      if (uploadRes.candidate_id && uploadRes.resume_id) {
        await createApplication({
          job_id: jobId,
          candidate_id: uploadRes.candidate_id,
          resume_id: uploadRes.resume_id
        });
      }
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      onComplete();
    } catch (err: any) {
      setError(err.message || "Failed to upload resume and evaluate application.");
    } finally {
      setIsUploading(false);
    }
  };
  return (
    <div className="glass-panel-heavy rounded-3xl p-12 flex flex-col items-center justify-center text-center min-h-[400px] border-dashed border-2 border-white/20 shadow-2xl relative overflow-hidden group">
      <div className="w-16 h-16 bg-white/5 rounded-2xl flex items-center justify-center text-white mb-6 border border-white/10 shadow-[0_0_30px_rgba(255,255,255,0.05)] relative z-10">
        {isUploading ? <Loader2 className="w-6 h-6 animate-spin" /> : <Upload className="w-6 h-6" />}
      </div>
      <h3 className="text-xl font-black tracking-tight mb-2 text-white relative z-10">Upload Candidate Resume</h3>
      <p className="text-sm text-muted-foreground mb-8 max-w-md leading-relaxed relative z-10">
        Directly ingest a candidate into this specific job requisition. PDF or DOCX format only.
      </p>
      {error && (
        <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center gap-3 text-red-400 text-sm font-semibold max-w-md relative z-10">
          <AlertCircle size={18} />
          {error}
        </div>
      )}
      {file ? (
        <div className="flex flex-col items-center gap-4 relative z-10">
          <div className="flex items-center gap-3 p-4 bg-white/10 rounded-xl border border-white/20">
            <FileText size={20} className="text-white" />
            <span className="text-sm font-bold text-white">{file.name}</span>
          </div>
          <div className="flex gap-3">
            <button 
              onClick={() => { setFile(null); if (fileInputRef.current) fileInputRef.current.value = ""; }}
              disabled={isUploading}
              className="px-6 py-3 rounded-xl text-xs font-bold uppercase tracking-wider text-muted-foreground hover:text-white transition-colors disabled:opacity-50 cursor-pointer"
            >
              Cancel
            </button>
            <button 
              onClick={handleUpload}
              disabled={isUploading}
              className="bg-white text-black hover:bg-gray-200 px-8 py-3 rounded-xl text-xs font-black uppercase tracking-wider transition-all shadow-[0_0_20px_rgba(255,255,255,0.3)] hover:shadow-[0_0_30px_rgba(255,255,255,0.5)] disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 cursor-pointer"
            >
              {isUploading ? (
                <><Loader2 size={16} className="animate-spin" /> Processing...</>
              ) : (
                <><Sparkles size={16} /> Run AI Evaluation</>
              )}
            </button>
          </div>
        </div>
      ) : (
        <div className="relative z-10">
          <input 
            type="file" 
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".pdf,.doc,.docx"
            className="hidden" 
            id="resume-upload-inline"
          />
          <label 
            htmlFor="resume-upload-inline"
            className="bg-white text-black hover:bg-gray-200 px-8 py-4 rounded-xl text-xs font-black uppercase tracking-wider transition-all shadow-[0_0_20px_rgba(255,255,255,0.3)] hover:shadow-[0_0_30px_rgba(255,255,255,0.5)] flex items-center gap-3 cursor-pointer hover-lift inline-flex"
          >
            <FileText size={16} />
            Select Files
          </label>
        </div>
      )}
    </div>
  );
}
function CandidateDashboard({ jobId }: { jobId: string }) {
  const [candidates, setCandidates] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    const fetchCandidates = async () => {
      try {
        const response = await getApplications(1, 100, { job_id: jobId });
        setCandidates(response.items || []);
      } catch (err: any) {
        setError(err.message || "Failed to fetch applications.");
      } finally {
        setLoading(false);
      }
    };
    fetchCandidates();
  }, [jobId]);
  return (
    <div className="space-y-4">
      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-2xl text-red-400 text-sm font-semibold text-center">
          {error}
        </div>
      )}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-20 text-muted-foreground space-y-4">
          <Loader2 className="w-8 h-8 animate-spin" />
          <p className="text-xs uppercase tracking-widest font-bold">Querying Data Matrix...</p>
        </div>
      ) : candidates.length === 0 && !error ? (
        <div className="flex flex-col items-center justify-center py-20 text-muted-foreground glass-panel rounded-3xl border-dashed">
          <FileText className="w-12 h-12 mb-4 opacity-20" />
          <p className="text-sm font-semibold">No candidates found for this requisition.</p>
          <p className="text-xs mt-2 opacity-60 max-w-xs text-center">Switch to the 'Ingest Resumes' tab to upload a new profile for evaluation.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {candidates.map((c) => {
            const absScore = c.score?.match_percentage || 0;
            const relScore = c.score?.relative_score ?? absScore;
            const isHighMatch = relScore >= 85;
            return (
              <Link key={c.id} href={`/candidates/${c.id}`} className="block h-full">
                <div className="p-5 glass-panel rounded-2xl hover:border-white/20 hover:bg-white/5 cursor-pointer transition-all duration-300 flex flex-col h-full justify-between group hover-lift relative overflow-hidden">
                  {isHighMatch && (
                    <div className="absolute top-0 left-0 w-full h-1 bg-white shadow-[0_0_10px_rgba(255,255,255,0.8)]" />
                  )}
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-xl bg-black/50 flex items-center justify-center text-muted-foreground group-hover:text-white transition-colors border border-white/10 shadow-inner">
                        <UserCircle size={20} />
                      </div>
                      <div>
                        <h4 className="font-black text-sm text-white tracking-tight">{c.candidate?.full_name || "Unknown"}</h4>
                        <div className="text-[10px] text-muted-foreground font-medium mt-0.5">{c.candidate?.email || "No Email"}</div>
                      </div>
                    </div>
                    <span className="px-2.5 py-1 bg-white/10 border border-white/10 text-[9px] uppercase font-bold tracking-widest rounded-lg text-white shadow-sm backdrop-blur-md">
                      {c.status || "Registered"}
                    </span>
                  </div>
                  <div className="flex items-end justify-between border-t border-white/5 pt-4 mt-auto">
                    <div className="flex-1 mr-4">
                      <div className="text-[9px] uppercase tracking-widest text-muted-foreground font-bold mb-1">Match Score</div>
                      <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden shadow-inner">
                        <div
                          className={`h-full transition-all duration-1000 ease-out ${isHighMatch ? 'bg-white shadow-[0_0_10px_rgba(255,255,255,0.8)]' : 'bg-white/40'}`}
                          style={{ width: `${relScore}%` }}
                        ></div>
                      </div>
                    </div>
                    <span className={`text-2xl font-black leading-none ${isHighMatch ? "text-white" : "text-white/70"}`}>{relScore}%</span>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
