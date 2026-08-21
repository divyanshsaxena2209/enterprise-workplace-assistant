"use client";
import React, { useEffect, useState } from "react";
import { useUser } from "@/lib/context/UserContext";
import { createClient } from "@/lib/supabase/client";
import Link from "next/link";
import { ArrowRight, CheckCircle, PlayCircle, Loader2, BookOpen, FileText, Settings, User } from "lucide-react";
export default function EmployeeDashboard() {
  const { profile, loading: profileLoading } = useUser();
  const supabase = createClient();
  const [progressData, setProgressData] = useState<any[]>([]);
  const [stats, setStats] = useState({ applicationsCount: 0 });
  const [loading, setLoading] = useState(true);
  const fetchDashboardData = React.useCallback(async () => {
    if (!profile) return;
    setLoading(true);
    try {
      const [onboardingRes, applicationsRes] = await Promise.all([
        supabase
          .from("employee_onboarding_progress")
          .select(`id, status, onboarding_steps ( id, step_name, step_order )`)
          .eq("employee_id", profile.id),
        supabase
          .from("applications")
          .select("id", { count: "exact", head: true })
          .eq("candidate_id", profile.id) 
      ]);
      if (onboardingRes.data) {
        const sortedData = onboardingRes.data.sort((a: any, b: any) => (a.onboarding_steps?.step_order || 0) - (b.onboarding_steps?.step_order || 0));
        setProgressData(sortedData);
      }
      setStats({
        applicationsCount: applicationsRes.count || 0
      });
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [profile, supabase]);
  useEffect(() => {
    if (!profileLoading && profile) {
      fetchDashboardData();
    }
  }, [profileLoading, profile, fetchDashboardData]);
  if (profileLoading || loading) {
    return (
      <div className="flex justify-center p-20">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }
  const completed = progressData.filter(p => p.status === "COMPLETED");
  const pending = progressData.filter(p => p.status === "PENDING" || p.status === "BLOCKED");
  const inProgress = progressData.filter(p => p.status === "IN_PROGRESS");
  const total = progressData.length;
  const percentage = total > 0 ? Math.round((completed.length / total) * 100) : 0;
  const lastCompleted = completed.length > 0 ? completed[completed.length - 1].onboarding_steps?.step_name : "None yet";
  const nextPending = inProgress.length > 0 
    ? inProgress[0].onboarding_steps?.step_name 
    : pending.length > 0 ? pending[0].onboarding_steps?.step_name : "All done!";
  const quickLinks = [
    { title: "My Profile", icon: <User className="w-5 h-5" />, href: "/profile", color: "bg-blue-500/10 text-blue-500 border-blue-500/20" },
    { title: "My Applications", icon: <FileText className="w-5 h-5" />, href: "/my-applications", color: "bg-green-500/10 text-green-500 border-green-500/20" },
    { title: "Knowledge Base", icon: <BookOpen className="w-5 h-5" />, href: "/knowledge", color: "bg-purple-500/10 text-purple-500 border-purple-500/20" },
  ];
  return (
    <div className="space-y-8 animate-fade-in pb-10">
      {}
      <div className="bg-foreground text-background rounded-3xl p-8 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-6 relative overflow-hidden">
        <div className="absolute top-[-50%] left-[-10%] w-[50%] h-[200%] bg-white/5 rounded-full blur-3xl pointer-events-none mix-blend-screen" />
        <div className="relative z-10">
          <h1 className="text-3xl font-black tracking-tight">Welcome back, {profile?.full_name?.split(' ')[0] || "Professional"}!</h1>
          <p className="text-background/80 mt-2 max-w-xl text-sm leading-relaxed">
            Your personal hub to track onboarding tasks, manage your profile, and access organizational knowledge.
          </p>
        </div>
      </div>
      {}
      <div className="bg-card border border-border p-6 md:p-8 rounded-3xl shadow-sm relative overflow-hidden group">
        <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4 relative z-10">
          <div>
            <h2 className="text-lg font-black tracking-tight flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-foreground" /> Onboarding Progress
            </h2>
            <p className="text-xs text-muted-foreground mt-1">Track your mandatory training and setup steps.</p>
          </div>
          <Link href="/onboarding" className="flex items-center gap-2 px-5 py-2.5 bg-foreground text-background hover:opacity-90 transition-opacity rounded-xl text-xs font-bold uppercase tracking-wider shadow-md">
            View Tasks <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative z-10">
          {}
          <div className="p-6 border border-border rounded-2xl bg-secondary/20 flex flex-col items-center justify-center text-center">
            <div className="relative w-20 h-20 flex items-center justify-center mb-4">
              <svg className="w-full h-full absolute inset-0 -rotate-90" viewBox="0 0 36 36">
                <path className="text-border" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="3" />
                <path className="text-foreground transition-all duration-1000 ease-out" strokeDasharray={`${percentage}, 100`} d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
              </svg>
              <span className="text-lg font-black text-foreground z-10">{percentage}%</span>
            </div>
            <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Overall Completion</p>
            <p className="text-sm font-black text-foreground mt-1">{completed.length} of {total} Tasks</p>
          </div>
          {}
          <div className="p-6 border border-border rounded-2xl bg-background flex flex-col justify-center shadow-sm">
            <div className="w-10 h-10 rounded-full bg-blue-500/10 flex items-center justify-center mb-4 text-blue-500 border border-blue-500/20">
              <PlayCircle className="w-5 h-5" />
            </div>
            <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider mb-2">Next Pending Task</p>
            <p className="font-bold text-base text-foreground line-clamp-2">{nextPending}</p>
          </div>
          {}
          <div className="p-6 border border-border rounded-2xl bg-background flex flex-col justify-center shadow-sm">
            <div className="w-10 h-10 rounded-full bg-green-500/10 flex items-center justify-center mb-4 text-green-500 border border-green-500/20">
              <CheckCircle className="w-5 h-5" />
            </div>
            <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider mb-2">Last Completed Task</p>
            <p className="font-bold text-base text-foreground line-clamp-2">{lastCompleted}</p>
          </div>
        </div>
      </div>
      {}
      <div>
        <h2 className="text-sm font-bold uppercase tracking-wider text-muted-foreground mb-4 px-2">Quick Access</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {quickLinks.map((link) => (
            <Link 
              key={link.title} 
              href={link.href}
              className="bg-card border border-border p-5 rounded-2xl hover:border-foreground/30 transition-all duration-300 group shadow-sm hover:shadow-md flex flex-col items-start gap-4"
            >
              <div className={`p-3 rounded-xl border ${link.color}`}>
                {link.icon}
              </div>
              <div className="flex items-center justify-between w-full">
                <span className="font-bold text-foreground">{link.title}</span>
                <ArrowRight className="w-4 h-4 text-muted-foreground group-hover:text-foreground transition-colors group-hover:translate-x-1" />
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
