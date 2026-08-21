"use client";
import React, { useEffect, useState } from "react";
import { useUser } from "@/lib/context/UserContext";
import { createClient } from "@/lib/supabase/client";
import Link from "next/link";
import { ArrowRight, CheckCircle, Clock, PlayCircle, Loader2 } from "lucide-react";
export default function EmployeeHomeDashboard() {
  const { profile, loading: profileLoading } = useUser();
  const supabase = createClient();
  const [progressData, setProgressData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const fetchProgress = React.useCallback(async () => {
    if (!profile) return;
    setLoading(true);
    try {
      const { data, error } = await supabase
        .from("employee_onboarding_progress")
        .select(`
          id, status, notes,
          onboarding_steps ( id, step_name, description, step_order )
        `)
        .eq("employee_id", profile.id);
      if (data) {
        const sortedData = data.sort((a: any, b: any) => (a.onboarding_steps?.step_order || 0) - (b.onboarding_steps?.step_order || 0));
        setProgressData(sortedData);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [profile, supabase]);
  useEffect(() => {
    if (!profileLoading && profile) {
      fetchProgress();
    }
  }, [profileLoading, profile, fetchProgress]);
  if (profileLoading || loading) {
    return (
      <div className="flex justify-center p-10"><Loader2 className="w-6 h-6 animate-spin text-muted-foreground" /></div>
    );
  }
  const completed = progressData.filter(p => p.status === "COMPLETED");
  const pending = progressData.filter(p => p.status === "PENDING" || p.status === "BLOCKED");
  const inProgress = progressData.filter(p => p.status === "IN_PROGRESS");
  const total = progressData.length;
  const percentage = total > 0 ? Math.round((completed.length / total) * 100) : 0;
  const lastCompleted = completed.length > 0 ? completed[completed.length - 1].onboarding_steps.step_name : "None yet";
  const nextPending = inProgress.length > 0 
    ? inProgress[0].onboarding_steps.step_name 
    : pending.length > 0 ? pending[0].onboarding_steps.step_name : "All done!";
  return (
    <div className="space-y-6">
      <div className="bg-foreground text-background rounded-3xl p-8 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div>
          <h1 className="text-3xl font-black tracking-tight">Welcome, {profile?.full_name?.split(' ')[0] || "Professional"}!</h1>
          <p className="text-background/80 mt-2 max-w-lg">
            Stay on top of your onboarding and quickly jump back into your training tasks.
          </p>
        </div>
      </div>
      <div className="bg-card border border-border p-6 md:p-8 rounded-3xl shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
          <div>
            <h2 className="text-lg font-black tracking-tight flex items-center gap-2">
              <CheckCircle className="w-5 h-5" /> Onboarding Overview
            </h2>
            <p className="text-xs text-muted-foreground mt-1">Your current progress</p>
          </div>
          <Link href="/onboarding" className="flex items-center gap-2 px-4 py-2 bg-secondary hover:bg-foreground hover:text-background text-foreground transition-colors rounded-xl text-xs font-bold uppercase tracking-wider border border-border">
            View Full Timeline <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-5 border border-border rounded-2xl bg-secondary/30 flex items-center gap-4">
            <div className="relative w-16 h-16 flex items-center justify-center">
              <svg className="w-full h-full absolute inset-0 -rotate-90" viewBox="0 0 36 36">
                <path className="text-border" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="3" />
                <path className="text-foreground" strokeDasharray={`${percentage}, 100`} d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
              </svg>
              <span className="text-sm font-black text-foreground z-10">{percentage}%</span>
            </div>
            <div>
              <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Completion</p>
              <p className="text-lg font-black">{completed.length} / {total}</p>
            </div>
          </div>
          <div className="p-5 border border-border rounded-2xl bg-background flex flex-col justify-center">
            <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-2"><PlayCircle className="w-3 h-3 text-blue-500" /> Next Pending Task</p>
            <p className="font-bold text-sm text-foreground truncate">{nextPending}</p>
          </div>
          <div className="p-5 border border-border rounded-2xl bg-background flex flex-col justify-center">
            <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-2"><CheckCircle className="w-3 h-3 text-green-500" /> Last Completed Task</p>
            <p className="font-bold text-sm text-foreground truncate">{lastCompleted}</p>
          </div>
          <div className="p-5 border border-border rounded-2xl bg-background flex flex-col justify-center md:col-span-3">
            <div className="flex justify-between items-center mb-2">
              <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Remaining Tasks</p>
              <p className="text-[10px] font-black">{total - completed.length} left</p>
            </div>
            <div className="w-full h-1.5 bg-secondary rounded-full overflow-hidden">
               <div className="h-full bg-foreground transition-all duration-1000 ease-out" style={{ width: `${percentage}%` }}></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
