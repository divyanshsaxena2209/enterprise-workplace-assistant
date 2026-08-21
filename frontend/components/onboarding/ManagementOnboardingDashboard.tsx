"use client";
import React, { useEffect, useState } from "react";
import { useUser } from "@/lib/context/UserContext";
import { createClient } from "@/lib/supabase/client";
import { CheckCircle, Clock, Search, ChevronRight, GripVertical, AlertTriangle, PlayCircle, Plus, Loader2, ArrowLeft, ArrowRight } from "lucide-react";
import LockedFeature from "@/components/layout/LockedFeature";
import EmployeeOnboardingEditor from "./EmployeeOnboardingEditor";
import OnboardingProgressMeter from "./OnboardingProgressMeter";
interface Employee {
  id: string;
  full_name: string;
  email: string;
  department: string;
  job_title: string;
  employee_id?: string;
  progress: any[];
}
import { useSearchParams } from "next/navigation";
export default function ManagementOnboardingDashboard() {
  const { profile, loading: profileLoading } = useUser();
  const searchParams = useSearchParams();
  const supabase = createClient();
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [selectedEmployee, setSelectedEmployee] = useState<Employee | null>(null);
  const [loading, setLoading] = useState(true);
  const fetchEmployees = React.useCallback(async () => {
    setLoading(true);
    try {
      const { data: profData, error: profError } = await supabase
        .from("profiles")
        .select(`
          id, full_name, email, department, job_title, employee_id,
          employee_onboarding_progress (
            id, step_id, status, notes, completion_date,
            onboarding_steps ( id, step_name, description, step_order )
          )
        `);
      if (profError) {
        console.error("Error fetching employees:", profError.message || profError);
        return;
      }
      if (profData) {
        const activeEmployees = profData.filter((emp: any) => 
          emp.employee_onboarding_progress && emp.employee_onboarding_progress.length > 0
        );
        const { data: appsData } = await supabase.from("applications").select(`id, jobs(title, department)`).in("status", ["Hired", "HIRED"]);
        const appMap = new Map();
        if (appsData) {
          appsData.forEach((app: any) => {
            appMap.set(app.id, app.jobs);
          });
        }
        const mapped: any[] = [];
        activeEmployees.forEach((emp: any) => {
          const appIds = new Set<string>();
          emp.employee_onboarding_progress.forEach((p: any) => {
            const match = p.notes?.match(/APP_ID:([a-f0-9-]+)/);
            if (match) appIds.add(match[1]);
          });
          if (appIds.size === 0) {
            mapped.push({
              id: emp.id,
              full_name: emp.full_name,
              email: emp.email,
              department: emp.department,
              job_title: emp.job_title,
              employee_id: emp.employee_id,
              progress: emp.employee_onboarding_progress
            });
          } else {
            appIds.forEach(appId => {
              const filteredProgress = emp.employee_onboarding_progress.filter((p: any) => p.notes?.includes(`APP_ID:${appId}`));
              const jobData = appMap.get(appId) || { title: emp.job_title, department: emp.department };
              mapped.push({
                id: `${emp.id}_${appId}`,
                full_name: emp.full_name,
                email: emp.email,
                department: jobData.department || emp.department,
                job_title: jobData.title || emp.job_title,
                employee_id: emp.employee_id,
                progress: filteredProgress
              });
            });
          }
        });
        setEmployees(mapped);
        const targetId = searchParams.get("employee_id");
        const targetEmail = searchParams.get("employee_email");
        if (targetEmail || targetId) {
          const targetEmp = mapped.find((e: any) => 
            (targetEmail && e.email === targetEmail) || 
            (targetId && (e.id === targetId || e.employee_id === targetId))
          );
          if (targetEmp) {
            setSelectedEmployee(targetEmp);
            return;
          }
        }
        setSelectedEmployee(prev => {
          if (!prev) return prev;
          return mapped.find((e: any) => e.id === prev.id) || prev;
        });
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [supabase]);
  useEffect(() => {
    fetchEmployees();
  }, [fetchEmployees]);
  const totalEmployees = employees.length;
  let totalCompleted = 0;
  let totalBlocked = 0;
  let totalPercentageSum = 0;
  employees.forEach(emp => {
    const comp = emp.progress.filter(p => p.status === "COMPLETED").length;
    const blocked = emp.progress.filter(p => p.status === "BLOCKED").length;
    const total = emp.progress.length;
    const percent = total > 0 ? (comp / total) * 100 : 0;
    totalCompleted += (comp === total && total > 0) ? 1 : 0;
    totalBlocked += (blocked > 0) ? 1 : 0;
    totalPercentageSum += percent;
  });
  const avgCompletion = totalEmployees > 0 ? Math.round(totalPercentageSum / totalEmployees) : 0;
  if (profileLoading || (loading && employees.length === 0)) {
    return (
      <div className="flex justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-muted-foreground" /></div>
    );
  }
  return (
    <LockedFeature isLocked={profile?.role !== "MANAGEMENT" && profile?.role !== "HR" && profile?.role !== "ADMIN"}>
      <div className="space-y-8 pb-10">
        {}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-card border border-border p-5 rounded-2xl shadow-sm hover:border-foreground/30 transition-colors">
            <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Total Onboarding</p>
            <p className="text-3xl font-black mt-2 text-foreground">{totalEmployees}</p>
          </div>
          <div className="bg-card border border-border p-5 rounded-2xl shadow-sm hover:border-foreground/30 transition-colors">
            <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Completed</p>
            <p className="text-3xl font-black mt-2 text-green-500">{totalCompleted}</p>
          </div>
          <div className="bg-card border border-border p-5 rounded-2xl shadow-sm hover:border-foreground/30 transition-colors">
            <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Blocked</p>
            <p className="text-3xl font-black mt-2 text-red-500">{totalBlocked}</p>
          </div>
          <div className="bg-card border border-border p-5 rounded-2xl shadow-sm hover:border-foreground/30 transition-colors">
            <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Avg Completion</p>
            <p className="text-3xl font-black mt-2 text-foreground">{avgCompletion}%</p>
          </div>
        </div>
        {selectedEmployee ? (
          <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <button 
              onClick={() => setSelectedEmployee(null)}
              className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-muted-foreground hover:text-foreground transition-colors group"
            >
              <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
              Back to Dashboard
            </button>
            <EmployeeOnboardingEditor 
              employee={selectedEmployee} 
              onClose={() => setSelectedEmployee(null)} 
              onUpdate={fetchEmployees}
            />
          </div>
        ) : (
          <div className="space-y-6 animate-in fade-in duration-500">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-black tracking-tight text-foreground">Active Employees</h2>
              <div className="relative w-64">
                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                <input 
                  type="text" 
                  placeholder="Search employees..." 
                  className="w-full bg-card border border-border rounded-xl pl-9 pr-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-foreground/50 transition-all shadow-sm" 
                />
              </div>
            </div>
            {employees.length === 0 ? (
              <div className="flex flex-col items-center justify-center p-12 bg-card border border-border rounded-3xl border-dashed">
                <CheckCircle className="w-12 h-12 text-muted-foreground/30 mb-4" />
                <p className="text-muted-foreground font-semibold">No onboarding records found.</p>
                <p className="text-xs text-muted-foreground/70 mt-1">Accept a candidate in Talent Acquisition to see them here.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                {employees.map(emp => {
                  const comp = emp.progress.filter(p => p.status === "COMPLETED").length;
                  const total = emp.progress.length;
                  const percent = total > 0 ? Math.round((comp / total) * 100) : 0;
                  return (
                    <button 
                      key={emp.id}
                      onClick={() => setSelectedEmployee(emp)}
                      className="group flex flex-col bg-card border border-border rounded-3xl p-6 hover:border-foreground/30 hover:shadow-lg transition-all text-left relative overflow-hidden"
                    >
                      <div className="absolute top-0 right-0 p-6 opacity-0 group-hover:opacity-100 transition-opacity translate-x-2 group-hover:translate-x-0">
                        <ArrowRight className="w-5 h-5 text-foreground" />
                      </div>
                      <div className="flex items-center gap-4 mb-6">
                        <div className="w-14 h-14 bg-secondary rounded-2xl flex items-center justify-center border border-border/50 text-xl font-black text-foreground">
                          {emp.full_name.charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <h3 className="font-bold text-lg text-foreground truncate max-w-[180px]">{emp.full_name || "Unnamed Employee"}</h3>
                          <p className="text-[11px] font-bold text-muted-foreground mt-1 uppercase tracking-widest truncate max-w-[180px]">{emp.job_title} • {emp.department}</p>
                        </div>
                      </div>
                      <div className="mt-auto">
                        <div className="flex justify-between items-end mb-2">
                          <span className="text-xs font-bold text-foreground">Onboarding Progress</span>
                          <span className="text-xs font-black text-muted-foreground">{percent}%</span>
                        </div>
                        <div className="h-2 w-full bg-secondary rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-foreground transition-all duration-1000 ease-out" 
                            style={{ width: `${percent}%` }}
                          ></div>
                        </div>
                        <p className="text-[10px] font-semibold text-muted-foreground mt-3 uppercase tracking-wider">
                          {comp} of {total} steps completed
                        </p>
                      </div>
                    </button>
                  )
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </LockedFeature>
  );
}
