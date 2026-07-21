"use client";

import React, { useState, useEffect } from "react";
import { CheckCircle, Clock, Bot, ArrowRight, BookOpen, ShieldCheck, Sparkles, Loader2 } from "lucide-react";
import Link from "next/link";
import { useUser } from "@/lib/context/UserContext";
import { createClient } from "@/lib/supabase/client";
import LockedFeature from "@/components/layout/LockedFeature";

interface OnboardingTask {
  id: string;
  title: string;
  type: string;
  status: string;
  due: string;
}

export default function OnboardingDashboard() {
  const { profile, isHired } = useUser();
  const supabase = createClient();
  const [tasks, setTasks] = useState<OnboardingTask[]>([]);
  const [loading, setLoading] = useState(true);

  const defaultTasks: OnboardingTask[] = [
    { id: "1", title: "Sign Employment Contract", type: "Document Verification", status: "Completed", due: "Immediate" },
    { id: "2", title: "Upload Official ID Verification", type: "Document Submission", status: "Pending", due: "Within 24 Hours" },
    { id: "3", title: "Review IT Security Compliance Policy", type: "Required Reading", status: "Pending", due: "Within 3 Days" },
    { id: "4", title: "Configure Professional Work Environment", type: "Operational Setup", status: "Pending", due: "Within 5 Days" },
  ];

  const fetchOnboardingTasks = React.useCallback(async () => {
    setLoading(true);
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        setTasks(defaultTasks);
        setLoading(false);
        return;
      }

      // Try fetching from public.employee_onboarding_tasks joined with onboarding_steps
      const { data, error } = await supabase
        .from("employee_onboarding_tasks")
        .select(`
          id,
          status,
          onboarding_steps (
            title,
            target_role
          )
        `)
        .eq("employee_id", user.id);

      if (error || !data || data.length === 0) {
        setTasks(defaultTasks);
      } else {
        // Map postgres records to frontend tasks
        const mapped: OnboardingTask[] = (data as unknown as Array<{
          id: string;
          status: string;
          onboarding_steps: { title: string; target_role: string } | null;
        }>).map((t) => ({
          id: t.id,
          title: t.onboarding_steps?.title || "Onboarding Task",
          type: "Required Task",
          status: t.status === "COMPLETED" ? "Completed" : "Pending",
          due: "Standard Timeline",
        }));
        setTasks(mapped);
      }
    } catch (err) {
      console.error("Failed to load onboarding tasks:", err);
      setTasks(defaultTasks);
    } finally {
      setLoading(false);
    }
  }, [supabase]);

  useEffect(() => {
    fetchOnboardingTasks();
  }, [profile, fetchOnboardingTasks]);

  const handleCompleteTask = async (id: string) => {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return;

      // Update local state first
      setTasks(prev => prev.map(t => t.id === id ? { ...t, status: "Completed" } : t));

      // Attempt Supabase update
      await supabase
        .from("employee_onboarding_tasks")
        .update({ status: "COMPLETED", completed_at: new Date().toISOString() })
        .eq("id", id)
        .eq("employee_id", user.id);
    } catch (err) {
      console.error("Failed to complete task:", err);
    }
  };

  const completedCount = tasks.filter(t => t.status === "Completed").length;
  const completionPercentage = tasks.length > 0 ? Math.round((completedCount / tasks.length) * 100) : 0;

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        <p className="text-xs text-muted-foreground font-semibold uppercase tracking-wider">Loading onboarding records...</p>
      </div>
    );
  }

  return (
    <LockedFeature isLocked={!isHired}>
      <div className="space-y-8 pb-10">
      
      {/* Header Area */}
      <div className="bg-foreground rounded-2xl p-8 text-background shadow-sm flex items-center justify-between relative overflow-hidden">
        <div className="relative z-10 space-y-2">
          <div className="inline-flex items-center gap-2 bg-secondary text-foreground px-3 py-1 rounded border border-border/50 text-[10px] font-bold tracking-wider uppercase">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Workforce Onboarding Program</span>
          </div>
          <h1 className="text-3xl font-black tracking-tight">
            Welcome, {profile?.full_name || "Enterprise Professional"}!
          </h1>
          <p className="text-background/80 max-w-lg leading-relaxed text-sm">
            We are thrilled to have you join as a {profile?.job_title || "Team Associate"} in the {profile?.department || "Operations"} department. Complete your roadmap below to configure your workspace.
          </p>
        </div>
        <div className="hidden md:block relative z-10">
          <div className="w-24 h-24 rounded-full border-[3px] border-background/20 flex items-center justify-center relative bg-background/5 backdrop-blur-sm">
            <svg className="w-full h-full absolute inset-0 -rotate-90" viewBox="0 0 36 36">
              <path className="text-transparent" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="3" />
              <path className="text-background" strokeDasharray={`${completionPercentage}, 100`} d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
            </svg>
            <span className="text-xl font-bold tracking-tight">{completionPercentage}%</span>
          </div>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row gap-6">
        
        {/* Left: Checklist */}
        <div className="lg:w-2/3 space-y-6">
          <div className="bg-card border border-border rounded-2xl shadow-sm overflow-hidden">
            <div className="p-5 border-b border-border bg-secondary/30">
              <h2 className="text-xs font-bold tracking-wider uppercase text-foreground">Operational Onboarding Roadmap</h2>
            </div>
            <div className="divide-y divide-border">
              {tasks.map((task) => (
                <div key={task.id} className="p-5 flex items-center justify-between hover:bg-secondary/30 transition-colors group">
                  <div className="flex items-start gap-4">
                    <div className={`mt-0.5 ${task.status === 'Completed' ? 'text-foreground' : 'text-muted-foreground'}`}>
                      {task.status === 'Completed' ? <CheckCircle size={20} /> : <div className="w-5 h-5 rounded-full border-2 border-muted-foreground/50 group-hover:border-foreground transition-colors cursor-pointer" onClick={() => handleCompleteTask(task.id)} />}
                    </div>
                    <div>
                      <h4 className={`font-semibold tracking-tight text-sm ${task.status === 'Completed' ? 'text-muted-foreground line-through decoration-muted-foreground/50' : 'text-foreground'}`}>
                        {task.title}
                      </h4>
                      <div className="flex items-center gap-3 text-[10px] font-bold uppercase tracking-wider text-muted-foreground mt-2">
                        <span className="flex items-center gap-1.5"><Clock size={12} /> Due: {task.due}</span>
                        <span className="px-2 py-0.5 bg-secondary border border-border/50 rounded-md">{task.type}</span>
                      </div>
                    </div>
                  </div>
                  {task.status !== 'Completed' && (
                    <button 
                      onClick={() => handleCompleteTask(task.id)}
                      className="px-4 py-2 bg-secondary hover:bg-foreground hover:text-background border border-border text-foreground text-xs font-bold uppercase tracking-wider rounded-lg transition-colors cursor-pointer"
                    >
                      Complete
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right: AI Onboarding Guide */}
        <div className="lg:w-1/3 space-y-6">
          <div className="bg-card border border-border rounded-2xl p-6 shadow-sm relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-32 h-32 bg-foreground/5 rounded-bl-full -z-10 group-hover:bg-foreground/10 transition-colors"></div>
            <div className="flex items-center gap-3 mb-5">
              <div className="w-10 h-10 bg-foreground text-background rounded-lg flex items-center justify-center shadow-sm">
                <Bot size={20} />
              </div>
              <div>
                <h3 className="font-bold text-sm tracking-tight text-foreground">AI Onboarding Assistant</h3>
                <p className="text-[9px] font-semibold uppercase tracking-wider text-muted-foreground mt-0.5">Policy & configuration setup</p>
              </div>
            </div>
            
            <div className="bg-secondary/50 border border-border rounded-xl p-4 mb-5 text-xs text-muted-foreground leading-relaxed">
              <p>Hi {profile?.full_name?.split(" ")[0] || "there"}! Since you are working as a {profile?.job_title || "professional"} in our {profile?.department || "Operations"} team, make sure to read the onboarding files in the Organizational Intelligence Hub.</p>
            </div>
            
            <Link href="/knowledge/chat" className="flex items-center justify-center gap-2 w-full bg-foreground hover:bg-foreground/90 text-background py-3 rounded-lg text-xs font-bold uppercase tracking-wider transition-all shadow-sm">
              Open Chat <ArrowRight size={14} />
            </Link>
          </div>

          <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">
            <h3 className="font-bold text-xs uppercase tracking-wider text-foreground mb-4">Quick Resources</h3>
            <div className="space-y-3">
              <Link href="/knowledge" className="flex items-center gap-3 p-3 border border-border rounded-xl hover:bg-secondary hover:border-foreground/30 transition-all group">
                <div className="bg-secondary p-1.5 rounded-lg border border-border/50 text-muted-foreground group-hover:text-foreground group-hover:bg-background transition-colors">
                  <BookOpen size={16} />
                </div>
                <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground group-hover:text-foreground transition-colors">Company Handbook</span>
              </Link>
              <Link href="/knowledge" className="flex items-center gap-3 p-3 border border-border rounded-xl hover:bg-secondary hover:border-foreground/30 transition-all group">
                <div className="bg-secondary p-1.5 rounded-lg border border-border/50 text-muted-foreground group-hover:text-foreground group-hover:bg-background transition-colors">
                  <ShieldCheck size={16} />
                </div>
                <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground group-hover:text-foreground transition-colors">IT Security Policies</span>
              </Link>
            </div>
          </div>
        </div>

      </div>
    </LockedFeature>
  );
}
