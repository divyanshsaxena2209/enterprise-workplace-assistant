"use client";
import React, { useEffect, useState } from "react";
import { useUser } from "@/lib/context/UserContext";
import { createClient } from "@/lib/supabase/client";
import { CheckCircle2, Clock, Loader2, AlertTriangle, PlayCircle, HelpCircle, Circle, Calendar, ChevronRight } from "lucide-react";
import LockedFeature from "@/components/layout/LockedFeature";
import { getMyApplications } from "@/lib/api/applications";
import { Briefcase, ArrowLeft } from "lucide-react";
interface Step {
  id: string;
  step_name: string;
  description: string;
  step_order: number;
}
interface Progress {
  id: string;
  step_id: string;
  status: "PENDING" | "IN_PROGRESS" | "COMPLETED" | "BLOCKED";
  notes: string;
  completion_date: string | null;
  step: Step;
}
export default function EmployeeOnboardingDashboard() {
  const { profile, isHired, loading: profileLoading } = useUser();
  const supabase = createClient();
  const [progressData, setProgressData] = useState<Progress[]>([]);
  const [hiredJobs, setHiredJobs] = useState<any[]>([]);
  const [selectedJob, setSelectedJob] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [jobsLoading, setJobsLoading] = useState(true);
  useEffect(() => {
    const fetchJobs = async () => {
      setJobsLoading(true);
      try {
        const res = await getMyApplications(1, 100);
        const hired = (res.items || []).filter((app: any) => app.status === "Hired" || app.status === "HIRED");
        setHiredJobs(hired);
      } catch (e) {
        console.error("Failed to fetch hired jobs:", e);
      } finally {
        setJobsLoading(false);
      }
    };
    if (profile && isHired) {
      fetchJobs();
    } else if (profile && !isHired) {
      setJobsLoading(false);
    }
  }, [profile, isHired]);
  const fetchProgress = React.useCallback(async () => {
    if (!profile) return;
    setLoading(true);
    try {
      const { data, error } = await supabase
        .from("employee_onboarding_progress")
        .select(`
          id, step_id, status, notes, completion_date,
          onboarding_steps ( id, step_name, description, step_order )
        `)
        .eq("employee_id", profile.id);
      if (error) {
        console.error("Error fetching onboarding progress:", error);
      } else if (data) {
        let mapped: Progress[] = data.map((d: any) => ({
          id: d.id,
          step_id: d.step_id,
          status: d.status,
          notes: d.notes,
          completion_date: d.completion_date,
          step: d.onboarding_steps,
        })).sort((a: any, b: any) => (a.step?.step_order || 0) - (b.step?.step_order || 0));
        if (selectedJob) {
          mapped = mapped.filter(m => m.notes && m.notes.includes(`APP_ID:${selectedJob.id}`));
        }
        setProgressData(mapped);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [profile, supabase, selectedJob]);
  useEffect(() => {
    if (!profileLoading && profile) {
      fetchProgress();
    }
  }, [profileLoading, profile, fetchProgress]);
  useEffect(() => {
    if (!profile) return;
    const channel = supabase.channel('schema-db-changes')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'employee_onboarding_progress', filter: `employee_id=eq.${profile.id}` }, () => fetchProgress())
      .on('postgres_changes', { event: '*', schema: 'public', table: 'onboarding_steps' }, () => fetchProgress())
      .subscribe();
    return () => {
      supabase.removeChannel(channel);
    };
  }, [profile, supabase, fetchProgress]);
  if (profileLoading || loading || jobsLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        <p className="text-xs text-muted-foreground font-semibold uppercase tracking-wider">Loading your onboarding roadmap...</p>
      </div>
    );
  }
  const completedCount = progressData.filter(p => p.status === "COMPLETED").length;
  const totalCount = progressData.length;
  const remainingCount = totalCount - completedCount;
  const percentage = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;
  const activeStepIndex = progressData.findIndex(p => p.status !== "COMPLETED");
  const activeStep = activeStepIndex !== -1 ? progressData[activeStepIndex] : null;
  const completedSteps = progressData.filter(p => p.status === "COMPLETED");
  const upcomingSteps = progressData.filter(p => p.status !== "COMPLETED");
  const getStatusIcon = (status: string, isActive: boolean = false) => {
    switch (status) {
      case 'COMPLETED': return <CheckCircle2 className="w-6 h-6 text-green-500 bg-green-500/10 rounded-full p-0.5" />;
      case 'IN_PROGRESS': return <HelpCircle className={`w-6 h-6 ${isActive ? 'text-blue-500 bg-blue-500/20 shadow-[0_0_15px_rgba(59,130,246,0.5)]' : 'text-blue-500'} rounded-full p-0.5 transition-all`} />;
      case 'BLOCKED': return <AlertTriangle className="w-6 h-6 text-red-500 bg-red-500/10 rounded-full p-0.5" />;
      default: return <Circle className={`w-6 h-6 ${isActive ? 'text-foreground' : 'text-muted-foreground/30'} transition-colors`} />;
    }
  };
  return (
    <LockedFeature isLocked={!isHired}>
      {!selectedJob ? (
        <div className="space-y-8 animate-in fade-in duration-700">
          <div>
            <h1 className="text-3xl font-black tracking-tight text-white mb-2">Workforce Onboarding</h1>
            <p className="text-sm text-muted-foreground">Select a position to view its onboarding roadmap.</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {hiredJobs.length === 0 ? (
              <div className="col-span-full p-8 text-center glass-panel rounded-2xl border-dashed">
                <Briefcase className="w-12 h-12 mb-4 mx-auto opacity-20" />
                <p className="text-sm font-semibold text-muted-foreground">No onboarding profiles found.</p>
              </div>
            ) : (
              hiredJobs.map(app => (
                <div 
                  key={app.id} 
                  onClick={() => setSelectedJob(app)}
                  className="p-6 glass-panel rounded-2xl hover:border-white/20 hover:bg-white/5 cursor-pointer transition-all duration-300 flex items-center gap-5 group hover-lift"
                >
                  <div className="w-12 h-12 rounded-2xl bg-black/50 flex items-center justify-center text-muted-foreground group-hover:text-white transition-colors border border-white/10 shadow-inner">
                    <Briefcase size={20} />
                  </div>
                  <div>
                    <h3 className="font-black text-base tracking-tight text-white">{app.job?.title || "Unknown Position"}</h3>
                    <div className="text-xs text-muted-foreground mt-1 font-medium">{app.job?.department || "General"}</div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      ) : (
        <div className="max-w-7xl mx-auto space-y-10 pb-20 animate-in fade-in duration-700">
          <button 
            onClick={() => setSelectedJob(null)}
            className="flex items-center gap-2 text-sm text-muted-foreground hover:text-white transition-colors"
          >
            <ArrowLeft size={16} />
            Back to Positions
          </button>
          {}
        <div className="relative overflow-hidden rounded-3xl bg-card border border-border shadow-2xl p-10 flex flex-col md:flex-row items-center gap-12">
          {}
          <div className="relative w-48 h-48 flex-shrink-0 flex items-center justify-center">
            <svg className="w-full h-full -rotate-90 transform" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="45" className="stroke-secondary fill-none" strokeWidth="8" />
              <circle 
                cx="50" 
                cy="50" 
                r="45" 
                className="stroke-foreground fill-none transition-all duration-1000 ease-out" 
                strokeWidth="8"
                strokeDasharray={`${2 * Math.PI * 45}`}
                strokeDashoffset={`${2 * Math.PI * 45 * (1 - percentage / 100)}`}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-4xl font-black text-foreground">{percentage}%</span>
              <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mt-1">Completed</span>
            </div>
          </div>
          <div className="flex-1 space-y-6">
            <div>
              <h1 className="text-3xl font-black tracking-tight mb-2">Welcome aboard, {profile?.full_name?.split(' ')[0] || 'Team'}!</h1>
              <p className="text-muted-foreground text-sm leading-relaxed max-w-2xl">This is your personalized onboarding roadmap. It outlines everything you need to know and do to get fully integrated into the team. Your progress is tracked in real-time.</p>
            </div>
            <div className="flex flex-wrap gap-4">
              <div className="bg-background border border-border rounded-xl px-5 py-3 shadow-sm flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 text-green-500" />
                <div>
                  <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Finished Tasks</p>
                  <p className="text-lg font-black">{completedCount}</p>
                </div>
              </div>
              <div className="bg-background border border-border rounded-xl px-5 py-3 shadow-sm flex items-center gap-3">
                <Clock className="w-5 h-5 text-blue-500" />
                <div>
                  <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Remaining Tasks</p>
                  <p className="text-lg font-black">{remainingCount}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
          {}
          <div className="lg:col-span-8 space-y-8">
            {activeStep && (
              <div className="mb-8 p-6 bg-gradient-to-br from-blue-500/10 to-transparent border border-blue-500/30 rounded-3xl shadow-sm relative overflow-hidden">
                <div className="absolute top-0 right-0 p-8 opacity-10 blur-xl">
                  <PlayCircle className="w-32 h-32 text-blue-500" />
                </div>
                <div className="relative">
                  <span className="inline-block px-3 py-1 bg-blue-500 text-white text-[10px] font-black uppercase tracking-widest rounded-full mb-4">Current Active Step</span>
                  <h3 className="text-2xl font-black text-foreground">{activeStep.step?.step_name}</h3>
                  <p className="text-muted-foreground text-sm mt-2 max-w-xl leading-relaxed">{activeStep.step?.description}</p>
                  {activeStep.notes && (
                    <div className="mt-4 p-4 bg-background/50 border border-border rounded-xl">
                      <p className="text-xs font-semibold text-foreground/80 flex gap-2"><span className="font-black text-blue-500">Manager Note:</span> {activeStep.notes}</p>
                    </div>
                  )}
                  {activeStep.completion_date && (
                    <div className="mt-4 flex items-center gap-2 text-xs font-bold text-muted-foreground uppercase tracking-wider">
                      <Calendar className="w-4 h-4" /> Expected by: {new Date(activeStep.completion_date).toLocaleDateString()}
                    </div>
                  )}
                </div>
              </div>
            )}
            <div className="space-y-6">
              <h3 className="text-lg font-black tracking-tight flex items-center gap-2">
                Complete Roadmap <span className="text-xs font-bold px-2 py-0.5 bg-secondary text-muted-foreground rounded-full">{progressData.length}</span>
              </h3>
              <div className="relative before:absolute before:inset-0 before:ml-[1.15rem] before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-1 before:bg-white/80 before:shadow-[0_0_15px_rgba(255,255,255,0.8)] before:rounded-full">
                {progressData.map((prog) => {
                  const isActive = activeStep?.id === prog.id;
                  const isCompleted = prog.status === 'COMPLETED';
                  return (
                    <div key={prog.id} className={`relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group py-4 ${isCompleted ? '' : 'is-active'}`}>
                      <div className={`relative flex items-center justify-center w-10 h-10 rounded-full border-4 border-black bg-black shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10 transition-transform group-hover:scale-110 duration-300 ${isCompleted ? 'shadow-[0_0_15px_rgba(34,197,94,0.3)]' : ''}`}>
                        {getStatusIcon(prog.status, isActive)}
                      </div>
                      <div className={`w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-5 rounded-2xl border transition-all duration-300 ${isActive ? 'bg-card border-blue-500/30 shadow-lg shadow-blue-500/5' : isCompleted ? 'bg-background border-green-500/20' : 'bg-background border-border hover:bg-card hover:shadow-md'}`}>
                        <div className="flex items-center justify-between mb-1">
                          <h4 className={`font-bold text-sm ${isActive ? 'text-foreground' : isCompleted ? 'text-muted-foreground line-through' : 'text-muted-foreground group-hover:text-foreground transition-colors'}`}>{prog.step?.step_name}</h4>
                          {prog.completion_date && (
                            <span className={`text-[10px] font-bold flex items-center gap-1 ${isCompleted ? 'text-green-500' : 'text-muted-foreground'}`}>
                              <Calendar className="w-3 h-3"/> 
                              {isCompleted ? 'Completed:' : 'Expected:'} {new Date(prog.completion_date).toLocaleDateString()}
                            </span>
                          )}
                        </div>
                        <p className={`text-xs leading-relaxed ${isCompleted ? 'text-muted-foreground/50' : 'text-muted-foreground/70'}`}>{prog.step?.description}</p>
                        {prog.status === 'BLOCKED' && (
                          <p className="text-[10px] font-bold text-red-500 uppercase tracking-wider mt-3 flex items-center gap-1"><AlertTriangle className="w-3 h-3"/> Blocked - Contact HR</p>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
          {}
          <div className="lg:col-span-4 space-y-6">
            <div className="bg-card border border-border p-6 rounded-3xl shadow-sm sticky top-8">
              <h3 className="font-black text-sm uppercase tracking-widest text-foreground mb-6 flex items-center gap-2">
                <HelpCircle className="w-4 h-4 text-muted-foreground" /> Need Help?
              </h3>
              <p className="text-xs text-muted-foreground leading-relaxed mb-6">Your onboarding is automatically tracked and managed by your HR coordinator and direct manager. You do not need to manually check off items.</p>
              <div className="space-y-4">
                <div className="p-4 bg-background border border-border rounded-2xl flex gap-3">
                  <div className="w-10 h-10 rounded-full bg-secondary flex items-center justify-center font-black text-foreground shrink-0">HR</div>
                  <div>
                    <p className="text-sm font-bold text-foreground">HR Coordinator</p>
                    <p className="text-xs text-muted-foreground">Reach out for any administrative or paperwork issues.</p>
                  </div>
                </div>
                <div className="p-4 bg-background border border-border rounded-2xl flex gap-3">
                  <div className="w-10 h-10 rounded-full bg-secondary flex items-center justify-center font-black text-foreground shrink-0">IT</div>
                  <div>
                    <p className="text-sm font-bold text-foreground">IT Support</p>
                    <p className="text-xs text-muted-foreground">Contact for system access, hardware, or email issues.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      )}
    </LockedFeature>
  );
}
