"use client";

import React, { useState } from "react";
import {
  Plus,
  Briefcase,
  Users,
  UploadCloud,
  FileText,
  Search,
  CheckCircle,
  AlertTriangle,
  XCircle,
  ChevronRight,
  Eye,
  Building,
  Award
} from "lucide-react";

interface Job {
  id: string;
  title: string;
  department: string;
  status: string;
  requirements: string[];
  description: string;
}

interface Candidate {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  suitability_score: number;
  match_explanation: string;
  parsed_skills: string[];
  parsed_experience: { role: string; company: string; duration: string; description?: string }[];
  status: string;
}

export default function HiringDashboard() {
  // 1. Initial Mock State for robust SaaS experience
  const [jobs, setJobs] = useState<Job[]>([
    {
      id: "job-1",
      title: "Senior Full Stack Engineer (Next.js & Python)",
      department: "Engineering",
      status: "Active",
      requirements: ["Next.js 14/15", "FastAPI", "PostgreSQL", "OpenAI APIs"],
      description: "We are seeking a high-caliber Senior Full Stack Engineer to drive development on our workplace automation products. The ideal candidate has strong skills in TypeScript, React, and Python microservices."
    },
    {
      id: "job-2",
      title: "AI Systems Architect",
      department: "Data & AI",
      status: "Active",
      requirements: ["LLMOps", "Vector Stores (Chroma/Pinecone)", "RAG Systems", "Python"],
      description: "Join our core AI research group. You will build and scale Retrieval-Augmented Generation services, semantic searches, and fine-tune pipeline orchestrations for enterprise workloads."
    }
  ]);

  const [candidates, setCandidates] = useState<Record<string, Candidate[]>>({
    "job-1": [
      {
        id: "cand-1",
        first_name: "Sarah",
        last_name: "Conner",
        email: "sarah.conner@skynet.com",
        suitability_score: 94,
        match_explanation: "Sarah matches nearly 100% of the core competencies. She has 5+ years of production experience building Next.js apps and scaling FastAPI endpoints. Her background in database migrations is a great fit for our Supabase roadmap. Minor area for growth: could expand on RAG vector store experience, but she has solid basic understanding.",
        parsed_skills: ["Next.js", "FastAPI", "TypeScript", "SQL", "OpenAI Integration", "React"],
        parsed_experience: [
          { role: "Lead Developer", company: "Cyberdyne Systems", duration: "2023 - Present", description: "Led Next.js 14 migration, improving site performance by 40% and deploying 12 Python endpoints." },
          { role: "Full Stack Engineer", company: "TechCom Corp", duration: "2020 - 2023", description: "Maintained React portals and orchestrated backend integrations with third-party webhooks." }
        ],
        status: "SHORTLISTED"
      },
      {
        id: "cand-2",
        first_name: "James",
        last_name: "Sunderland",
        email: "james.s@silent-hill.org",
        suitability_score: 62,
        match_explanation: "James has strong React skills but has limited exposure to Next.js App Router and Python backend systems. He exhibits great problem-solving aptitude, but would require heavy mentorship to meet the requirements of a Senior Full Stack Engineer role.",
        parsed_skills: ["React", "JavaScript", "Node.js", "CSS", "UI Design"],
        parsed_experience: [
          { role: "Frontend Developer", company: "Lakeview Hotels Ltd", duration: "2021 - 2024", description: "Built accessible administrative dashboards using standard React and Tailwind CSS." }
        ],
        status: "SCREENING"
      }
    ],
    "job-2": [
      {
        id: "cand-3",
        first_name: "Bruce",
        last_name: "Wayne",
        email: "bruce@wayne-enterprises.com",
        suitability_score: 88,
        match_explanation: "Bruce shows excellent depth in machine learning architecture, vector database designs (ChromaDB), and embeddings indexing. His work on cognitive automated detection pipelines aligns directly with the Knowledge Assistant module. A highly competent engineer.",
        parsed_skills: ["ChromaDB", "Python", "GPT models", "LangChain", "LLMOps", "PyTorch"],
        parsed_experience: [
          { role: "Director of Applied AI", company: "Wayne Enterprises", duration: "2021 - Present", description: "Designed semantic search engine for secure defense systems using custom embedding architectures." }
        ],
        status: "SHORTLISTED"
      }
    ]
  });

  const [selectedJobId, setSelectedJobId] = useState<string>("job-1");
  const [showAddJobModal, setShowAddJobModal] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);

  // Form State variables
  const [newJobTitle, setNewJobTitle] = useState("");
  const [newJobDept, setNewJobDept] = useState("Engineering");
  const [newJobReqs, setNewJobReqs] = useState("");
  const [newJobDesc, setNewJobDesc] = useState("");

  const [isUploading, setIsUploading] = useState(false);
  const [uploadFileName, setUploadFileName] = useState("");
  const [uploadProgress, setUploadProgress] = useState(0);

  const handleCreateJob = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newJobTitle || !newJobDesc) return;

    const newJob: Job = {
      id: `job-${Date.now()}`,
      title: newJobTitle,
      department: newJobDept,
      status: "Active",
      requirements: newJobReqs.split(",").map(r => r.trim()).filter(Boolean),
      description: newJobDesc
    };

    setJobs([...jobs, newJob]);
    setCandidates({ ...candidates, [newJob.id]: [] });
    setSelectedJobId(newJob.id);
    setShowAddJobModal(false);
    
    // Clear inputs
    setNewJobTitle("");
    setNewJobReqs("");
    setNewJobDesc("");
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadFileName(file.name);
    setIsUploading(true);
    setUploadProgress(10);

    // Simulate standard document analysis / fastapi screening triggers
    const timer = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 90) {
          clearInterval(timer);
          return 90;
        }
        return prev + 25;
      });
    }, 400);

    setTimeout(() => {
      clearInterval(timer);
      setUploadProgress(100);
      
      // Auto-generate a beautiful mock parsed candidate
      const parsedCandidate: Candidate = {
        id: `cand-${Date.now()}`,
        first_name: "Divyansh",
        last_name: "Saxena",
        email: "divyansh.saxena@soprasteria.com",
        suitability_score: 91,
        match_explanation: "The candidate demonstrates stellar, comprehensive matching with the JD. Expert-level capability in Next.js, FastAPI, and Supabase database modeling. Directly fits the AI Systems Architect scope as well. Outstanding documentation skills and clear structured delivery.",
        parsed_skills: ["Next.js 15", "FastAPI", "TypeScript", "Tailwind CSS", "Supabase", "PostgreSQL", "ChromaDB", "OpenAI APIs"],
        parsed_experience: [
          { role: "Senior Full Stack & AI Architect", company: "Sopra Steria India", duration: "2024 - Present", description: "Successfully spearheaded AI-powered enterprise assistant platform, automating HR pipelines and transcribing meeting audio transcripts." }
        ],
        status: "SHORTLISTED"
      };

      setCandidates(prev => ({
        ...prev,
        [selectedJobId]: [...(prev[selectedJobId] || []), parsedCandidate]
      }));

      setIsUploading(false);
      setShowUploadModal(false);
      setUploadFileName("");
      setUploadProgress(0);
      setSelectedCandidate(parsedCandidate); // Show results modal immediately!
    }, 2500);
  };

  const getScoreBadgeColor = (score: number) => {
    if (score >= 85) return "bg-emerald-100 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800";
    if (score >= 60) return "bg-amber-100 dark:bg-amber-950/40 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800";
    return "bg-rose-100 dark:bg-rose-950/40 text-rose-700 dark:text-rose-400 border border-rose-200 dark:border-rose-800";
  };

  const currentJob = jobs.find(j => j.id === selectedJobId) || jobs[0];
  const currentCandidates = candidates[selectedJobId] || [];

  return (
    <div className="space-y-6">
      {/* Upper overview header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Resume Screening & Screening Portal</h2>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
            Analyze, evaluate and rank candidate resumes against Job Descriptions instantly using GPT-4o.
          </p>
        </div>
        <button
          onClick={() => setShowAddJobModal(true)}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2.5 rounded-lg text-sm font-semibold transition-all shadow-md shadow-blue-500/10 cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>New Job Posting</span>
        </button>
      </div>

      {/* Main Section layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Side: Jobs list selector */}
        <div className="lg:col-span-1 space-y-4">
          <div className="bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-xl p-4">
            <h3 className="font-bold text-slate-800 dark:text-slate-200 mb-4 flex items-center gap-2">
              <Briefcase className="w-5 h-5 text-blue-600" />
              <span>Active Job Profiles</span>
            </h3>
            
            <div className="space-y-2">
              {jobs.map((job) => {
                const isActive = job.id === selectedJobId;
                const count = candidates[job.id]?.length || 0;
                return (
                  <button
                    key={job.id}
                    onClick={() => setSelectedJobId(job.id)}
                    className={`w-full text-left p-3.5 rounded-xl transition-all border cursor-pointer ${
                      isActive
                        ? "bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800/60"
                        : "bg-transparent border-slate-100 dark:border-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800/40"
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <span className="font-bold text-sm leading-snug truncate max-w-[80%] block">
                        {job.title}
                      </span>
                      <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500">
                        {job.department}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 mt-3 text-xs text-slate-400">
                      <span className="flex items-center gap-1">
                        <Users className="w-3.5 h-3.5" />
                        <span>{count} Candidates</span>
                      </span>
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-500"></span>
                      <span>Active</span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Job Requirements display */}
          <div className="bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-xl p-5 space-y-4">
            <h4 className="font-bold text-sm text-slate-700 dark:text-slate-300">Job Specifications</h4>
            <div>
              <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-3 leading-relaxed">
                {currentJob.description}
              </p>
            </div>
            <div className="space-y-2">
              <h5 className="text-xs font-semibold text-slate-400">Keywords/Requirements</h5>
              <div className="flex flex-wrap gap-1.5">
                {currentJob.requirements.map((req, idx) => (
                  <span key={idx} className="text-[10px] bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 px-2 py-1 rounded">
                    {req}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Right Side: Candidate screening dashboard */}
        <div className="lg:col-span-2 space-y-6">
          {/* Header indicator */}
          <div className="bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-xl p-5 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div className="space-y-1">
              <span className="text-xs text-slate-400 uppercase tracking-widest font-semibold">Active Screening Screen</span>
              <h3 className="font-bold text-lg leading-tight">{currentJob.title}</h3>
            </div>
            
            <button
              onClick={() => setShowUploadModal(true)}
              className="flex items-center gap-2 bg-slate-900 hover:bg-slate-800 dark:bg-blue-600 dark:hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-xs font-semibold transition-all shadow cursor-pointer"
            >
              <UploadCloud className="w-4 h-4" />
              <span>Screen New Candidate</span>
            </button>
          </div>

          {/* Candidate list table/cards */}
          <div className="bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden">
            <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center bg-slate-50/50 dark:bg-[#111827]">
              <span className="font-bold text-sm text-slate-700 dark:text-slate-300">Screened Applicants</span>
              <span className="text-xs text-slate-400">{currentCandidates.length} Total</span>
            </div>

            {currentCandidates.length === 0 ? (
              <div className="p-12 text-center space-y-4">
                <div className="h-12 w-12 rounded-full bg-slate-50 dark:bg-slate-800 flex items-center justify-center mx-auto text-slate-400">
                  <FileText className="w-6 h-6" />
                </div>
                <div className="space-y-1 max-w-xs mx-auto">
                  <p className="font-bold text-sm">No Candidate Screened Yet</p>
                  <p className="text-xs text-slate-400">
                    Upload resume papers to let GPT-4o analyze, parse details, extract skill terms and rank candidates.
                  </p>
                </div>
              </div>
            ) : (
              <div className="divide-y divide-slate-100 dark:divide-slate-850">
                {currentCandidates.map((cand) => (
                  <div key={cand.id} className="p-4 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 hover:bg-slate-50/40 dark:hover:bg-slate-800/10 transition-colors">
                    <div className="space-y-1.5 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm">{cand.first_name} {cand.last_name}</span>
                        <span className="text-xs text-slate-400">({cand.email})</span>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {cand.parsed_skills.slice(0, 4).map((skill, idx) => (
                          <span key={idx} className="text-[10px] bg-slate-50 dark:bg-slate-800 border border-slate-100 dark:border-slate-700 px-1.5 py-0.5 rounded text-slate-500">
                            {skill}
                          </span>
                        ))}
                        {cand.parsed_skills.length > 4 && (
                          <span className="text-[9px] text-slate-400 px-1 py-0.5">+{cand.parsed_skills.length - 4} more</span>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-4 flex-shrink-0 self-end sm:self-center">
                      {/* Suitability Score bar */}
                      <div className="flex items-center gap-3">
                        <div className="w-16 bg-slate-100 dark:bg-slate-800 h-1.5 rounded-full overflow-hidden hidden sm:block">
                          <div
                            className={`h-full rounded-full ${
                              cand.suitability_score >= 85 ? "bg-emerald-500" : cand.suitability_score >= 60 ? "bg-amber-500" : "bg-rose-500"
                            }`}
                            style={{ width: `${cand.suitability_score}%` }}
                          ></div>
                        </div>
                        <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${getScoreBadgeColor(cand.suitability_score)}`}>
                          {cand.suitability_score}% Match
                        </span>
                      </div>

                      {/* Detail View action button */}
                      <button
                        onClick={() => setSelectedCandidate(cand)}
                        className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition-all cursor-pointer"
                        title="View Full Evaluation"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* MODAL 1: Create New Job Description */}
      {showAddJobModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 w-full max-w-lg rounded-xl overflow-hidden shadow-2xl animate-fade-in">
            <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center">
              <h3 className="font-bold text-lg">Create Job Profile</h3>
              <button onClick={() => setShowAddJobModal(false)} className="p-1 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full cursor-pointer">
                <XCircle className="w-5 h-5 text-slate-400" />
              </button>
            </div>
            
            <form onSubmit={handleCreateJob} className="p-5 space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-bold text-slate-400">JOB TITLE</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Senior Frontend Engineer"
                  value={newJobTitle}
                  onChange={(e) => setNewJobTitle(e.target.value)}
                  className="w-full bg-transparent border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-600"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-xs font-bold text-slate-400">DEPARTMENT</label>
                  <select
                    value={newJobDept}
                    onChange={(e) => setNewJobDept(e.target.value)}
                    className="w-full bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-2 text-sm focus:outline-none"
                  >
                    <option value="Engineering">Engineering</option>
                    <option value="Data & AI">Data & AI</option>
                    <option value="Product">Product</option>
                    <option value="HR & Operations">HR & Operations</option>
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-bold text-slate-400">KEYWORDS (COMMA SEPARATED)</label>
                  <input
                    type="text"
                    placeholder="React, Next.js, AWS"
                    value={newJobReqs}
                    onChange={(e) => setNewJobReqs(e.target.value)}
                    className="w-full bg-transparent border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-600"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-bold text-slate-400">JOB DESCRIPTION</label>
                <textarea
                  rows={4}
                  required
                  placeholder="Describe the role responsibilities and qualifications..."
                  value={newJobDesc}
                  onChange={(e) => setNewJobDesc(e.target.value)}
                  className="w-full bg-transparent border border-slate-200 dark:border-slate-800 rounded-lg p-3 text-sm focus:outline-none focus:border-blue-600 resize-none"
                />
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-850">
                <button
                  type="button"
                  onClick={() => setShowAddJobModal(false)}
                  className="px-4 py-2 border border-slate-200 dark:border-slate-800 rounded-lg text-xs font-semibold hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold cursor-pointer"
                >
                  Create Posting
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: Upload Resume for analysis */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 w-full max-w-md rounded-xl overflow-hidden shadow-2xl animate-fade-in">
            <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center">
              <h3 className="font-bold text-lg">Screen Candidate</h3>
              <button onClick={() => setShowUploadModal(false)} className="p-1 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full cursor-pointer">
                <XCircle className="w-5 h-5 text-slate-400" />
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
                    <p className="font-bold text-sm">Processing Resume with GPT-4o...</p>
                    <p className="text-xs text-slate-400 truncate max-w-xs mx-auto">Analyzing content of: {uploadFileName}</p>
                  </div>
                  <div className="w-full bg-slate-100 dark:bg-slate-800 h-1.5 rounded-full overflow-hidden max-w-xs mx-auto">
                    <div className="h-full bg-blue-600 transition-all duration-300" style={{ width: `${uploadProgress}%` }}></div>
                  </div>
                </div>
              ) : (
                <div className="border-2 border-dashed border-slate-200 dark:border-slate-800 hover:border-blue-500 rounded-xl p-8 transition-colors relative cursor-pointer group">
                  <input
                    type="file"
                    accept=".pdf,.docx"
                    onChange={handleFileUpload}
                    className="absolute inset-0 opacity-0 cursor-pointer"
                  />
                  <div className="space-y-3">
                    <UploadCloud className="h-10 w-10 text-slate-400 group-hover:text-blue-500 mx-auto transition-colors" />
                    <div className="space-y-1">
                      <p className="font-bold text-sm">Upload resume files</p>
                      <p className="text-xs text-slate-400">PDF or DOCX documents up to 10MB</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* MODAL 3: Detailed Candidate evaluation view */}
      {selectedCandidate && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 w-full max-w-2xl rounded-xl overflow-hidden shadow-2xl max-h-[85vh] flex flex-col animate-fade-in">
            {/* Header info */}
            <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center">
              <div className="space-y-1">
                <span className="text-[10px] font-bold uppercase tracking-wider text-blue-600 dark:text-blue-400">Applicant Assessment</span>
                <h3 className="font-bold text-lg leading-tight">{selectedCandidate.first_name} {selectedCandidate.last_name}</h3>
                <p className="text-xs text-slate-400">{selectedCandidate.email}</p>
              </div>
              
              <div className="flex items-center gap-4">
                <span className={`text-sm font-bold px-3 py-1 rounded-full ${getScoreBadgeColor(selectedCandidate.suitability_score)}`}>
                  {selectedCandidate.suitability_score}% Match
                </span>
                <button onClick={() => setSelectedCandidate(null)} className="p-1 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full cursor-pointer">
                  <XCircle className="w-5 h-5 text-slate-400" />
                </button>
              </div>
            </div>

            {/* Scrollable details body */}
            <div className="p-6 space-y-6 overflow-y-auto flex-1">
              
              {/* Suitability rationale summary */}
              <div className="space-y-2">
                <h4 className="font-bold text-xs uppercase tracking-widest text-slate-400 flex items-center gap-1.5">
                  <Award className="w-4 h-4 text-blue-600" />
                  <span>AI Match Assessment</span>
                </h4>
                <p className="text-sm bg-slate-50 dark:bg-slate-900/60 p-4 border border-slate-100 dark:border-slate-800 rounded-xl leading-relaxed text-slate-700 dark:text-slate-300">
                  {selectedCandidate.match_explanation}
                </p>
              </div>

              {/* Parsed Skills terms tags */}
              <div className="space-y-2">
                <h4 className="font-bold text-xs uppercase tracking-widest text-slate-400">Core Competencies Identified</h4>
                <div className="flex flex-wrap gap-1.5">
                  {selectedCandidate.parsed_skills.map((skill, idx) => (
                    <span key={idx} className="text-xs font-medium bg-blue-50 dark:bg-blue-950/20 text-blue-700 dark:text-blue-400 px-3 py-1 rounded-lg border border-blue-100 dark:border-blue-900/50">
                      {skill}
                    </span>
                  ))}
                </div>
              </div>

              {/* Work history mapping details */}
              <div className="space-y-3">
                <h4 className="font-bold text-xs uppercase tracking-widest text-slate-400">Professional Work History</h4>
                
                <div className="space-y-4">
                  {selectedCandidate.parsed_experience.map((exp, idx) => (
                    <div key={idx} className="relative pl-5 border-l-2 border-slate-200 dark:border-slate-850 space-y-1">
                      <div className="absolute h-2.5 w-2.5 bg-blue-600 rounded-full -left-[6px] top-1"></div>
                      
                      <div className="flex justify-between items-start text-xs sm:text-sm">
                        <span className="font-bold text-slate-800 dark:text-slate-200">{exp.role}</span>
                        <span className="text-xs font-semibold text-slate-400">{exp.duration}</span>
                      </div>
                      
                      <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 flex items-center gap-1">
                        <Building className="w-3.5 h-3.5" />
                        <span>{exp.company}</span>
                      </p>
                      
                      {exp.description && (
                        <p className="text-xs leading-relaxed text-slate-500 mt-2">
                          {exp.description}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Footer action trigger */}
            <div className="p-4 border-t border-slate-200 dark:border-slate-800 flex justify-between items-center bg-slate-50/50 dark:bg-[#111827]">
              <span className="text-xs text-slate-400">Status: Screening Complete</span>
              <button
                onClick={() => setSelectedCandidate(null)}
                className="px-5 py-2 bg-slate-900 hover:bg-slate-800 dark:bg-blue-600 dark:hover:bg-blue-700 text-white rounded-lg text-xs font-semibold cursor-pointer"
              >
                Close Assessment
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
