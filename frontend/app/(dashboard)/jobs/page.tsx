"use client";

import React, { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { Plus, Briefcase, MapPin, Users, Sparkles, Loader2, AlertCircle, X, ChevronDown, Upload } from "lucide-react";
import { useRouter } from "next/navigation";
import { getJobs, createJob, publishJob } from "@/lib/api/jobs";
import { uploadResume } from "@/lib/api/candidates";
import { createApplication } from "@/lib/api/applications";
import { useUser } from "@/lib/context/UserContext";

export default function JobsPage() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const { profile, accessToken } = useUser();
  const isManagement = profile?.role === "MANAGEMENT";

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [applyModalOpen, setApplyModalOpen] = useState(false);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [applyLoading, setApplyLoading] = useState(false);
  const [applySuccess, setApplySuccess] = useState(false);
  const [submitLoading, setSubmitLoading] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    title: "",
    department: "Information Technology (IT)",
    custom_department: "",
    employment_type: "Full-time",
    work_model: "On-site",
    city: "",
    description: "",
    requirements: "Included in Description",
    salary_range: ""
  });

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const response = await getJobs();
      setJobs(response.data || []);
    } catch (err: any) {
      setError(err.message || "Failed to fetch job requisitions.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  return (
    <div className="space-y-8 pb-10">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 relative z-10">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-white flex items-center gap-3">
            <div className="p-2 bg-white/10 rounded-xl border border-white/20 shadow-[0_0_15px_rgba(255,255,255,0.1)]">
              <Sparkles className="w-6 h-6 text-white animate-pulse" />
            </div>
            Talent Acquisition Operations
          </h1>
          <p className="text-sm text-muted-foreground mt-2 max-w-xl leading-relaxed">
            Manage active corporate openings, track application pipelines, and deploy position templates.
          </p>
        </div>
        {isManagement && (
          <button 
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-2 bg-white text-black hover:bg-gray-200 px-6 py-3 rounded-xl text-xs font-black uppercase tracking-wider transition-all shadow-[0_0_20px_rgba(255,255,255,0.3)] hover:shadow-[0_0_30px_rgba(255,255,255,0.5)] hover-lift cursor-pointer"
          >
            <Plus size={16} />
            Initiate
          </button>
        )}
      </div>

      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-2xl text-red-400 text-sm font-semibold relative z-10 text-center">
          <AlertCircle size={18} className="inline-block mr-2 -mt-1" />
          {error}
        </div>
      )}

      {/* Grid List */}
      <div className="grid grid-cols-1 gap-4 relative z-10">
        {loading ? (
           <div className="flex flex-col items-center justify-center py-20 text-muted-foreground space-y-4">
             <Loader2 className="w-8 h-8 animate-spin" />
             <p className="text-xs uppercase tracking-widest font-bold">Querying Requisitions...</p>
           </div>
        ) : jobs.length === 0 && !error ? (
           <div className="flex flex-col items-center justify-center py-20 text-muted-foreground glass-panel rounded-3xl border-dashed">
             <Briefcase className="w-12 h-12 mb-4 opacity-20" />
             <p className="text-sm font-semibold">No active job requisitions found.</p>
           </div>
        ) : (
          jobs.map((job) => (
            <div key={job.id} onClick={() => router.push(`/jobs/${job.id}`)} className="p-6 glass-panel rounded-2xl hover:border-white/20 hover:bg-white/5 cursor-pointer transition-all duration-300 flex items-center justify-between group hover-lift relative overflow-hidden">
              {/* Subtle success glow if active */}
              {job.status === "Published" && (
                <div className="absolute top-0 left-0 w-1 h-full bg-white shadow-[0_0_10px_rgba(255,255,255,0.8)]" />
              )}
              
              <div className="flex items-center gap-5 pl-2">
                <div className="w-12 h-12 rounded-2xl bg-black/50 flex items-center justify-center text-muted-foreground group-hover:text-white transition-colors border border-white/10 shadow-inner">
                  <Briefcase size={20} />
                </div>
                <div>
                  <h3 className="font-black text-base tracking-tight text-white">{job.title}</h3>
                  <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground mt-2 font-medium">
                    <span className="flex items-center gap-1.5"><MapPin size={12} className="text-white/70" /> {job.location || "Remote"}</span>
                    <span className="flex items-center gap-1.5"><Users size={12} className="text-white/70" /> {job.department || "General"}</span>
                    <span className="px-2.5 py-0.5 bg-white/10 border border-white/10 rounded-full text-[9px] uppercase tracking-widest text-white/80 font-bold backdrop-blur-sm">{job.employment_type || "Full-time"}</span>
                  </div>
                </div>
              </div>
              
              <div>
                <span className={`px-4 py-1.5 text-[10px] uppercase tracking-widest font-bold rounded-lg border shadow-sm backdrop-blur-md ${
                  job.status === "Published" 
                    ? "bg-white/15 text-white border-white/20" 
                    : "bg-black/50 text-muted-foreground border-white/10"
                }`}>
                  {job.status || "Draft"}
                </span>
                {!isManagement && job.status === "Published" && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedJobId(job.id);
                      setApplyModalOpen(true);
                      setApplySuccess(false);
                      setResumeFile(null);
                    }}
                    className="ml-4 px-5 py-2 bg-white text-black hover:bg-gray-200 rounded-lg text-[10px] uppercase tracking-widest font-black transition-all shadow-[0_0_15px_rgba(255,255,255,0.2)] hover:shadow-[0_0_25px_rgba(255,255,255,0.4)]"
                  >
                    Apply Now
                  </button>
                )}
                {isManagement && job.status === "Draft" && (
                  <button
                    onClick={async (e) => {
                      e.stopPropagation();
                      try {
                        await publishJob(job.id, accessToken);
                        fetchJobs(); // refresh the list
                      } catch (err: any) {
                        alert(err.message || "Failed to publish job");
                      }
                    }}
                    className="ml-4 px-5 py-2 bg-zinc-800 text-white hover:bg-zinc-700 border border-white/20 rounded-lg text-[10px] uppercase tracking-widest font-black transition-all shadow-[0_0_10px_rgba(255,255,255,0.05)] hover:shadow-[0_0_15px_rgba(255,255,255,0.1)]"
                  >
                    Publish
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Modal */}
      {isModalOpen && typeof document !== "undefined" && createPortal(
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-zinc-900 border border-white/20 rounded-2xl w-full max-w-3xl shadow-2xl relative flex flex-col max-h-[95vh] overflow-hidden">
            
            {/* Header */}
            <div className="p-6 pb-4 flex-shrink-0 border-b border-white/10 relative">
              <button 
                onClick={() => setIsModalOpen(false)}
                className="absolute top-6 right-6 text-muted-foreground hover:text-white transition-colors"
              >
                <X size={20} />
              </button>
              <h2 className="text-xl font-black tracking-tight text-white m-0 py-1">Initiate Job Requisition</h2>
            </div>

            <form onSubmit={async (e) => {
              e.preventDefault();
              setSubmitLoading(true);
              setSubmitError(null);
              try {
                const payload = {
                  title: formData.title,
                  department: formData.department === "Others" ? formData.custom_department : formData.department,
                  employment_type: formData.employment_type,
                  location: formData.work_model === "Remote" ? "Remote" : `${formData.work_model} - ${formData.city}`,
                  description: formData.description,
                  requirements: "Included in Description",
                  salary_range: formData.salary_range || undefined
                };
                
                await createJob(payload, accessToken);
                setIsModalOpen(false);
                setFormData({
                  title: "", department: "Information Technology (IT)", custom_department: "",
                  employment_type: "Full-time", work_model: "On-site", city: "",
                  description: "", requirements: "Included in Description", salary_range: ""
                });
                fetchJobs();
              } catch (err: any) {
                console.error("[handleSubmit] Caught error:", err);
                setSubmitError(err.message || "Failed to create job.");
              } finally {
                setSubmitLoading(false);
              }
            }} className="flex flex-col flex-1 min-h-0">
              
              {/* Scrollable Body */}
              <div className="p-6 overflow-y-auto flex-1 space-y-5">
                
                {submitError && (
                  <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm font-semibold">
                    {submitError}
                  </div>
                )}
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div>
                    <label className="block text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-1.5">Job Title *</label>
                    <input type="text" required value={formData.title} onChange={e => setFormData({...formData, title: e.target.value})} className="w-full bg-black border border-white/10 rounded-lg p-2.5 text-sm focus:border-white/30 outline-none text-white shadow-inner" placeholder="e.g. Senior Engineer" />
                  </div>
                  
                  <div className="flex gap-2">
                    <div className="flex-1">
                      <label className="block text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-1.5">Department *</label>
                      <div className="relative">
                        <select value={formData.department} onChange={e => setFormData({...formData, department: e.target.value})} className="w-full bg-black border border-white/10 rounded-lg p-2.5 pr-10 text-sm focus:border-white/30 outline-none text-white shadow-inner appearance-none cursor-pointer">
                          <option value="Information Technology (IT)">Information Technology (IT)</option>
                          <option value="Human Resources (HR)">Human Resources (HR)</option>
                          <option value="Finance and Accounting">Finance and Accounting</option>
                          <option value="Marketing and Sales">Marketing and Sales</option>
                          <option value="Operations and Supply Chain">Operations and Supply Chain</option>
                          <option value="Legal and Compliance">Legal and Compliance</option>
                          <option value="Research and Development (R&D)">Research and Development (R&D)</option>
                          <option value="Others">Others</option>
                        </select>
                        <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none w-4 h-4" />
                      </div>
                    </div>
                    {formData.department === "Others" && (
                      <div className="flex-1">
                        <label className="block text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-1.5">Specify *</label>
                        <input type="text" required value={formData.custom_department} onChange={e => setFormData({...formData, custom_department: e.target.value})} className="w-full bg-black border border-white/10 rounded-lg p-2.5 text-sm focus:border-white/30 outline-none text-white shadow-inner" placeholder="Custom" />
                      </div>
                    )}
                  </div>

                  <div>
                    <label className="block text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-1.5">Job Type *</label>
                    <div className="relative">
                      <select value={formData.employment_type} onChange={e => setFormData({...formData, employment_type: e.target.value})} className="w-full bg-black border border-white/10 rounded-lg p-2.5 pr-10 text-sm focus:border-white/30 outline-none text-white shadow-inner appearance-none cursor-pointer">
                        <option value="Full-time">Full-time</option>
                        <option value="Part-time">Part-time</option>
                        <option value="Contractual">Contractual</option>
                        <option value="Intern">Intern</option>
                      </select>
                      <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none w-4 h-4" />
                    </div>
                  </div>
                  
                  <div className="flex gap-2">
                    <div className="flex-1">
                      <label className="block text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-1.5">Work Model *</label>
                      <div className="relative">
                        <select value={formData.work_model} onChange={e => setFormData({...formData, work_model: e.target.value})} className="w-full bg-black border border-white/10 rounded-lg p-2.5 pr-10 text-sm focus:border-white/30 outline-none text-white shadow-inner appearance-none cursor-pointer">
                          <option value="On-site">On-site</option>
                          <option value="Remote">Remote</option>
                          <option value="Hybrid">Hybrid</option>
                        </select>
                        <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none w-4 h-4" />
                      </div>
                    </div>
                    {(formData.work_model === "On-site" || formData.work_model === "Hybrid") && (
                      <div className="flex-1">
                        <label className="block text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-1.5">City / Location *</label>
                        <input type="text" required value={formData.city} onChange={e => setFormData({...formData, city: e.target.value})} className="w-full bg-black border border-white/10 rounded-lg p-2.5 text-sm focus:border-white/30 outline-none text-white shadow-inner" placeholder="e.g. London" />
                      </div>
                    )}
                  </div>
                </div>
                
                <div className="flex flex-col space-y-1.5">
                  <label className="block text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Job Description & Requirements *</label>
                  <textarea required value={formData.description} onChange={e => setFormData({...formData, description: e.target.value})} className="w-full bg-black border border-white/10 rounded-lg p-3 text-sm focus:border-white/30 outline-none text-white resize-y shadow-inner min-h-[120px]" placeholder="Enter full job description and requirements..."></textarea>
                </div>
              </div>

              {/* Fixed Footer */}
              <div className="p-6 pt-4 flex justify-end gap-3 border-t border-white/10 flex-shrink-0 bg-zinc-900/50">
                <button type="button" onClick={() => setIsModalOpen(false)} className="px-5 py-2.5 rounded-lg text-sm font-bold text-muted-foreground hover:text-white transition-colors cursor-pointer">
                  Cancel
                </button>
                <button type="submit" disabled={submitLoading} className="px-6 py-2.5 rounded-lg text-sm font-black uppercase tracking-wider bg-white text-black hover:bg-gray-200 transition-all shadow-[0_0_10px_rgba(255,255,255,0.2)] hover:shadow-[0_0_20px_rgba(255,255,255,0.4)] flex items-center gap-2 disabled:opacity-50 cursor-pointer">
                  {submitLoading ? <Loader2 size={16} className="animate-spin" /> : null}
                  Create Requisition
                </button>
              </div>
            </form>
          </div>
        </div>,
        document.body
      )}

      {/* Apply Modal */}
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
                    onClick={() => setApplyModalOpen(false)}
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
                      if (!resumeFile || !selectedJobId) return;
                      setApplyLoading(true);
                      setSubmitError(null);
                      try {
                        const uploadRes = await uploadResume(resumeFile);
                        if (uploadRes.candidate_id && uploadRes.resume_id) {
                          await createApplication({
                            job_id: selectedJobId,
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
