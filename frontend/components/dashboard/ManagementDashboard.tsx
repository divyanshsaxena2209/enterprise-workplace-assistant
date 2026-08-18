"use client";

import React, { useEffect, useState } from "react";
import { useUser } from "@/lib/context/UserContext";
import { createClient } from "@/lib/supabase/client";
import Link from "next/link";
import { Briefcase, Users, FileText, Settings, BookOpen, UserPlus, Loader2, ArrowRight } from "lucide-react";

export default function ManagementDashboard() {
  const { profile, loading: profileLoading } = useUser();
  const supabase = createClient();
  const [stats, setStats] = useState({
    jobsCount: 0,
    candidatesCount: 0,
    applicationsCount: 0,
    employeesCount: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchStats() {
      if (!profile) return;
      setLoading(true);
      try {
        const [jobsRes, candidatesRes, applicationsRes, profilesRes] = await Promise.all([
          supabase.from("jobs").select("id", { count: "exact", head: true }).in("status", ["PUBLISHED", "Published"]),
          supabase.from("candidates").select("id", { count: "exact", head: true }),
          supabase.from("applications").select("id", { count: "exact", head: true }),
          supabase.from("profiles").select("id", { count: "exact", head: true }).in("role", ["EMPLOYEE", "MANAGEMENT", "HR", "ADMIN"])
        ]);

        setStats({
          jobsCount: jobsRes.count || 0,
          candidatesCount: candidatesRes.count || 0,
          applicationsCount: applicationsRes.count || 0,
          employeesCount: profilesRes.count || 0
        });
      } catch (err) {
        console.error("Error fetching stats", err);
      } finally {
        setLoading(false);
      }
    }

    if (!profileLoading && profile) {
      fetchStats();
    }
  }, [profileLoading, profile, supabase]);

  if (profileLoading || loading) {
    return (
      <div className="flex justify-center p-20">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const quickLinks = [
    { title: "Manage Jobs", icon: <Briefcase className="w-5 h-5" />, href: "/jobs", color: "bg-blue-500/10 text-blue-500 border-blue-500/20" },
    { title: "Knowledge Base", icon: <BookOpen className="w-5 h-5" />, href: "/knowledge", color: "bg-purple-500/10 text-purple-500 border-purple-500/20" },
    { title: "Onboarding Setup", icon: <UserPlus className="w-5 h-5" />, href: "/onboarding", color: "bg-orange-500/10 text-orange-500 border-orange-500/20" },
  ];

  return (
    <div className="space-y-8 animate-fade-in pb-10">
      
      {}
      <div className="bg-foreground text-background rounded-3xl p-8 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-6 relative overflow-hidden">
        <div className="absolute top-[-50%] right-[-10%] w-[50%] h-[200%] bg-white/5 rounded-full blur-3xl pointer-events-none mix-blend-screen" />
        <div className="relative z-10">
          <h1 className="text-3xl font-black tracking-tight">Welcome, {profile?.full_name?.split(' ')[0] || "Manager"}!</h1>
          <p className="text-background/80 mt-2 max-w-xl text-sm leading-relaxed">
            Manage your team's jobs, candidates, and resources from here.
          </p>
        </div>
      </div>

      {}
      <div>
        <h2 className="text-sm font-bold uppercase tracking-wider text-muted-foreground mb-4 px-2">Overview</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard title="Active Jobs" value={stats.jobsCount.toString()} icon={<Briefcase size={16} />} />
          <StatCard title="Total Candidates" value={stats.candidatesCount.toString()} icon={<Users size={16} />} />
          <StatCard title="Job Applications" value={stats.applicationsCount.toString()} icon={<FileText size={16} />} />
          <StatCard title="Active Employees" value={stats.employeesCount.toString()} icon={<UserPlus size={16} />} />
        </div>
      </div>

      {}
      <div>
        <h2 className="text-sm font-bold uppercase tracking-wider text-muted-foreground mb-4 px-2">Shortcuts</h2>
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

function StatCard({ title, value, icon }: { title: string, value: string, icon: React.ReactNode }) {
  return (
    <div className="p-6 bg-card border border-border rounded-2xl shadow-sm flex items-center justify-between group hover:border-foreground/20 transition-colors">
      <div>
        <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider mb-1">{title}</p>
        <p className="text-3xl font-black text-foreground">{value}</p>
      </div>
      <div className="w-12 h-12 rounded-full bg-secondary/50 flex items-center justify-center text-muted-foreground group-hover:text-foreground group-hover:bg-secondary transition-colors">
        {icon}
      </div>
    </div>
  );
}
