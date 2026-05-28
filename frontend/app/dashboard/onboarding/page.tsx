"use client";

import React, { useState } from "react";
import {
  ClipboardCheck,
  UserCheck,
  UploadCloud,
  FileCheck,
  AlertCircle,
  Clock,
  CheckCircle,
  HelpCircle,
  Eye,
  Check,
  X,
  FileText,
  Send,
  Building,
  Computer,
  ShieldCheck,
  ArrowRight
} from "lucide-react";

interface OnboardingTask {
  id: string;
  title: string;
  description: string;
  category: "HR" | "IT" | "LEGAL";
  status: "PENDING" | "IN_PROGRESS" | "WAITING_VERIFICATION" | "COMPLETED";
  dueDate: string;
  documentPath?: string;
  submittedAt?: string;
  feedback?: string;
}

interface EmployeeOnboardingState {
  id: string;
  full_name: string;
  email: string;
  role: string;
  progress: number;
  tasks: OnboardingTask[];
}

export default function OnboardingDashboard() {
  // 1. Initial State covering multiple onboarding employees
  const [employees, setEmployees] = useState<EmployeeOnboardingState[]>([
    {
      id: "emp-101",
      full_name: "Alice Smith",
      email: "alice.smith@soprasteria.com",
      role: "Associate software engineer",
      progress: 60,
      tasks: [
        {
          id: "step-1",
          title: "Complete Personal Profile & Emergency Contacts",
          description: "Fill in emergency details, bank accounts, and personal contacts in the profile directory.",
          category: "HR",
          status: "COMPLETED",
          dueDate: "2026-05-26",
          submittedAt: "2026-05-24"
        },
        {
          id: "step-2",
          title: "Signed Employment Contract Upload",
          description: "Sign and upload the scanned copy of your official Sopra Steria employment offer letter.",
          category: "LEGAL",
          status: "COMPLETED",
          dueDate: "2026-05-28",
          submittedAt: "2026-05-24",
          documentPath: "contract_alice.pdf"
        },
        {
          id: "step-3",
          title: "Submit Government Identity Verification Papers",
          description: "Upload copies of passport, tax cards or local state identification papers for background check verification.",
          category: "LEGAL",
          status: "WAITING_VERIFICATION",
          dueDate: "2026-05-30",
          submittedAt: "2026-05-24",
          documentPath: "passport_alice.jpg"
        },
        {
          id: "step-4",
          title: "Security & Anti-Bribery Compliance Module",
          description: "Read the security compliance document and pass the basic code-of-conduct test.",
          category: "HR",
          status: "IN_PROGRESS",
          dueDate: "2026-06-02"
        },
        {
          id: "step-5",
          title: "IT Assets Allocation & Credentials Setup",
          description: "Submit preferences for your development laptop, workspace setup and wait for corporate email credentials.",
          category: "IT",
          status: "PENDING",
          dueDate: "2026-06-05"
        }
      ]
    },
    {
      id: "emp-102",
      full_name: "Bob Jones",
      email: "bob.jones@soprasteria.com",
      role: "AI Developer",
      progress: 20,
      tasks: [
        {
          id: "step-1",
          title: "Complete Personal Profile & Emergency Contacts",
          description: "Fill in emergency details, bank accounts, and personal contacts in the profile directory.",
          category: "HR",
          status: "COMPLETED",
          dueDate: "2026-05-26",
          submittedAt: "2026-05-23"
        },
        {
          id: "step-2",
          title: "Signed Employment Contract Upload",
          description: "Sign and upload the scanned copy of your official Sopra Steria employment offer letter.",
          category: "LEGAL",
          status: "PENDING",
          dueDate: "2026-05-28"
        },
        {
          id: "step-3",
          title: "Submit Government Identity Verification Papers",
          description: "Upload copies of passport, tax cards or local state identification papers for background check verification.",
          category: "LEGAL",
          status: "PENDING",
          dueDate: "2026-05-30"
        },
        {
          id: "step-4",
          title: "Security & Anti-Bribery Compliance Module",
          description: "Read the security compliance document and pass the basic code-of-conduct test.",
          category: "HR",
          status: "PENDING",
          dueDate: "2026-06-02"
        },
        {
          id: "step-5",
          title: "IT Assets Allocation & Credentials Setup",
          description: "Submit preferences for your development laptop, workspace setup and wait for corporate email credentials.",
          category: "IT",
          status: "PENDING",
          dueDate: "2026-06-05"
        }
      ]
    }
  ]);

  // Views switch state: employee simulation or HR monitoring dashboard
  const [currentUserRole, setCurrentUserRole] = useState<"EMPLOYEE" | "HR_ADMIN">("EMPLOYEE");
  const [activeEmployeeId, setActiveEmployeeId] = useState<string>("emp-101");
  const [selectedTask, setSelectedTask] = useState<OnboardingTask | null>(null);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadFileName, setUploadFileName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Helper values
  const currentEmployee = employees.find(e => e.id === activeEmployeeId) || employees[0];
  const pendingVerificationTasks = employees.flatMap(emp => 
    emp.tasks
      .filter(t => t.status === "WAITING_VERIFICATION")
      .map(t => ({ employee: emp, task: t }))
  );

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "COMPLETED":
        return <CheckCircle className="w-5 h-5 text-emerald-500" />;
      case "WAITING_VERIFICATION":
        return <Clock className="w-5 h-5 text-amber-500" />;
      case "IN_PROGRESS":
        return <Clock className="w-5 h-5 text-blue-500" />;
      default:
        return <AlertCircle className="w-5 h-5 text-slate-300 dark:text-slate-700" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "COMPLETED":
        return "bg-emerald-50 dark:bg-emerald-950/20 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900";
      case "WAITING_VERIFICATION":
        return "bg-amber-50 dark:bg-amber-950/20 text-amber-600 dark:text-amber-400 border border-amber-250 dark:border-amber-900";
      case "IN_PROGRESS":
        return "bg-blue-50 dark:bg-blue-950/20 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-900";
      default:
        return "bg-slate-50 dark:bg-slate-800/40 text-slate-500 border border-slate-200 dark:border-slate-800";
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "IT":
        return <Computer className="w-4 h-4 text-blue-500" />;
      case "LEGAL":
        return <ShieldCheck className="w-4 h-4 text-purple-500" />;
      default:
        return <Building className="w-4 h-4 text-emerald-500" />;
    }
  };

  // Actions
  const handleTaskAction = (task: OnboardingTask) => {
    setSelectedTask(task);
    if (task.status === "PENDING" || task.status === "IN_PROGRESS") {
      setShowUploadModal(true);
    }
  };

  const handleDocumentSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTask || !uploadFileName) return;

    setIsSubmitting(true);

    setTimeout(() => {
      // Update employee task status in the state
      const updatedEmployees = employees.map(emp => {
        if (emp.id === activeEmployeeId) {
          const updatedTasks = emp.tasks.map(t => {
            if (t.id === selectedTask.id) {
              return {
                ...t,
                status: "WAITING_VERIFICATION" as const,
                documentPath: uploadFileName,
                submittedAt: new Date().toISOString().split("T")[0]
              };
            }
            return t;
          });

          // Calculate new progress percentage
          const completedCount = updatedTasks.filter(t => t.status === "COMPLETED").length;
          const newProgress = Math.round((completedCount / updatedTasks.length) * 100);

          return { ...emp, tasks: updatedTasks, progress: newProgress };
        }
        return emp;
      });

      setEmployees(updatedEmployees);
      setIsSubmitting(false);
      setShowUploadModal(false);
      setSelectedTask(null);
      setUploadFileName("");
    }, 1500);
  };

  const handleVerificationAudit = (empId: string, taskId: string, approve: boolean) => {
    const updatedEmployees = employees.map(emp => {
      if (emp.id === empId) {
        const updatedTasks = emp.tasks.map(t => {
          if (t.id === taskId) {
            return {
              ...t,
              status: (approve ? "COMPLETED" : "PENDING") as any,
              feedback: approve ? undefined : "Submitted document was blurred. Please re-upload.",
              documentPath: approve ? t.documentPath : undefined
            };
          }
          return t;
        });

        const completedCount = updatedTasks.filter(t => t.status === "COMPLETED").length;
        const newProgress = Math.round((completedCount / updatedTasks.length) * 100);

        return { ...emp, tasks: updatedTasks, progress: newProgress };
      }
      return emp;
    });

    setEmployees(updatedEmployees);
  };

  return (
    <div className="space-y-6">
      {/* Switch role simulator header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-xl p-4">
        <div>
          <span className="text-[10px] font-bold text-blue-600 dark:text-blue-400 uppercase tracking-widest">Enterprise Role Simulator</span>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Toggle roles to explore onboarding portal experiences.</p>
        </div>
        <div className="flex bg-slate-100 dark:bg-slate-800 p-1 rounded-lg">
          <button
            onClick={() => {
              setCurrentUserRole("EMPLOYEE");
              setActiveEmployeeId("emp-101");
            }}
            className={`px-4 py-1.5 rounded-md text-xs font-semibold transition-all cursor-pointer ${
              currentUserRole === "EMPLOYEE"
                ? "bg-white dark:bg-[#111827] text-slate-900 dark:text-slate-100 shadow-sm"
                : "text-slate-500 hover:text-slate-900 dark:hover:text-slate-100"
            }`}
          >
            Employee Portal
          </button>
          <button
            onClick={() => setCurrentUserRole("HR_ADMIN")}
            className={`px-4 py-1.5 rounded-md text-xs font-semibold transition-all cursor-pointer ${
              currentUserRole === "HR_ADMIN"
                ? "bg-white dark:bg-[#111827] text-slate-900 dark:text-slate-100 shadow-sm"
                : "text-slate-500 hover:text-slate-900 dark:hover:text-slate-100"
            }`}
          >
            HR monitoring panel
          </button>
        </div>
      </div>

      {/* VIEW A: EMPLOYEE ONBOARDING PORTAL */}
      {currentUserRole === "EMPLOYEE" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column: Progress status milestone */}
          <div className="lg:col-span-1 space-y-6">
            <div className="bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-xl p-6 space-y-6">
              <div className="text-center space-y-2">
                <div className="h-14 w-14 rounded-full bg-blue-100 dark:bg-blue-950/40 flex items-center justify-center mx-auto text-blue-600">
                  <UserCheck className="w-8 h-8" />
                </div>
                <div>
                  <h3 className="font-bold text-lg">{currentEmployee.full_name}</h3>
                  <p className="text-xs text-slate-400 capitalize">{currentEmployee.role}</p>
                </div>
              </div>

              {/* Milestones Progress bar */}
              <div className="space-y-2">
                <div className="flex justify-between items-center text-xs font-bold">
                  <span className="text-slate-400 uppercase tracking-widest">Onboarding Progress</span>
                  <span className="text-blue-600 dark:text-blue-400">{currentEmployee.progress}%</span>
                </div>
                <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-600 transition-all duration-500" style={{ width: `${currentEmployee.progress}%` }}></div>
                </div>
              </div>

              {/* Milestones Timeline */}
              <div className="space-y-4 pt-4 border-t border-slate-150 dark:border-slate-800">
                <h4 className="font-bold text-xs uppercase tracking-widest text-slate-400">Milestone Path</h4>
                <div className="space-y-4">
                  {currentEmployee.tasks.map((task, idx) => {
                    const isDone = task.status === "COMPLETED";
                    const isWait = task.status === "WAITING_VERIFICATION";
                    return (
                      <div key={task.id} className="flex gap-3 text-xs items-center">
                        <div className={`h-6 w-6 rounded-full flex items-center justify-center flex-shrink-0 font-bold border ${
                          isDone 
                            ? "bg-emerald-50 dark:bg-emerald-950/20 border-emerald-300 text-emerald-600" 
                            : isWait 
                              ? "bg-amber-50 dark:bg-amber-950/20 border-amber-300 text-amber-600"
                              : "bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-400"
                        }`}>
                          {isDone ? <Check className="w-3.5 h-3.5" /> : idx + 1}
                        </div>
                        <div className="overflow-hidden">
                          <p className={`font-semibold truncate max-w-[180px] ${isDone ? "line-through text-slate-400" : ""}`}>
                            {task.title}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Task tracking list */}
          <div className="lg:col-span-2 space-y-4">
            <h3 className="font-bold text-lg flex items-center gap-2">
              <ClipboardCheck className="w-5 h-5 text-blue-600" />
              <span>Pending Checklists</span>
            </h3>

            <div className="space-y-3">
              {currentEmployee.tasks.map((task) => (
                <div
                  key={task.id}
                  className="bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-xl p-5 hover:border-slate-350 dark:hover:border-slate-700 transition-all flex flex-col md:flex-row justify-between items-start md:items-center gap-4 animate-fade-in"
                >
                  <div className="space-y-2 flex-1">
                    <div className="flex items-center gap-2">
                      {getCategoryIcon(task.category)}
                      <span className="font-bold text-sm leading-snug">{task.title}</span>
                    </div>
                    <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                      {task.description}
                    </p>
                    
                    {task.feedback && (
                      <p className="text-[11px] bg-rose-50 dark:bg-rose-950/20 text-rose-600 dark:text-rose-400 p-2 rounded-lg border border-rose-100 dark:border-rose-900/50 flex items-center gap-1.5">
                        <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
                        <span>{task.feedback}</span>
                      </p>
                    )}
                  </div>

                  <div className="flex items-center gap-4 flex-shrink-0 self-end md:self-center">
                    <span className={`text-[10px] uppercase font-bold px-2.5 py-1 rounded-full ${getStatusBadge(task.status)}`}>
                      {task.status.replace("_", " ")}
                    </span>

                    {(task.status === "PENDING" || task.status === "IN_PROGRESS" || task.feedback) && (
                      <button
                        onClick={() => handleTaskAction(task)}
                        className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer"
                      >
                        <UploadCloud className="w-3.5 h-3.5" />
                        <span>Upload Proof</span>
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* VIEW B: HR MONITORING AUDIT DASHBOARD */}
      {currentUserRole === "HR_ADMIN" && (
        <div className="space-y-6">
          {/* HR overview stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-xl p-5 flex items-center gap-4">
              <div className="h-10 w-10 rounded-full bg-blue-100 dark:bg-blue-950/40 text-blue-600 flex items-center justify-center flex-shrink-0">
                <Users className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Total Onboardees</p>
                <p className="text-xl font-bold">{employees.length}</p>
              </div>
            </div>

            <div className="bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-xl p-5 flex items-center gap-4">
              <div className="h-10 w-10 rounded-full bg-amber-100 dark:bg-amber-950/40 text-amber-600 flex items-center justify-center flex-shrink-0">
                <Clock className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Pending Audit Tasks</p>
                <p className="text-xl font-bold">{pendingVerificationTasks.length}</p>
              </div>
            </div>

            <div className="bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-xl p-5 flex items-center gap-4">
              <div className="h-10 w-10 rounded-full bg-emerald-100 dark:bg-emerald-950/40 text-emerald-600 flex items-center justify-center flex-shrink-0">
                <CheckCircle className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Verification Complete</p>
                <p className="text-xl font-bold">1/2 Employees</p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left: Employee tracking Selector */}
            <div className="lg:col-span-1 space-y-4">
              <div className="bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-xl p-4">
                <h3 className="font-bold text-sm text-slate-700 dark:text-slate-300 mb-3">Onboarding Employees</h3>
                <div className="space-y-2">
                  {employees.map(emp => {
                    const isActive = emp.id === activeEmployeeId;
                    return (
                      <button
                        key={emp.id}
                        onClick={() => setActiveEmployeeId(emp.id)}
                        className={`w-full text-left p-3 rounded-lg border cursor-pointer ${
                          isActive
                            ? "bg-slate-50 dark:bg-slate-800/40 border-slate-200 dark:border-slate-700"
                            : "bg-transparent border-transparent hover:bg-slate-50/50 dark:hover:bg-slate-800/20"
                        }`}
                      >
                        <div className="flex justify-between items-start">
                          <div>
                            <p className="font-bold text-xs leading-none">{emp.full_name}</p>
                            <p className="text-[10px] text-slate-400 mt-1">{emp.role}</p>
                          </div>
                          <span className="text-xs text-blue-600 dark:text-blue-400 font-bold">{emp.progress}%</span>
                        </div>
                        <div className="w-full bg-slate-100 dark:bg-slate-850 h-1 rounded-full overflow-hidden mt-3">
                          <div className="h-full bg-blue-600" style={{ width: `${emp.progress}%` }}></div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Right: Employee tasks audit grid */}
            <div className="lg:col-span-2 space-y-4">
              <div className="bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden">
                <div className="p-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-[#111827] flex justify-between items-center">
                  <span className="font-bold text-sm text-slate-700 dark:text-slate-300">Auditing Checklists: {currentEmployee.full_name}</span>
                  <span className="text-xs text-slate-400 capitalize">{currentEmployee.role}</span>
                </div>

                <div className="divide-y divide-slate-100 dark:divide-slate-850">
                  {currentEmployee.tasks.map((task) => (
                    <div key={task.id} className="p-4 space-y-3">
                      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-2">
                        <div className="flex items-center gap-2">
                          {getCategoryIcon(task.category)}
                          <span className="font-bold text-sm leading-none">{task.title}</span>
                        </div>
                        <span className={`text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full self-start sm:self-auto ${getStatusBadge(task.status)}`}>
                          {task.status.replace("_", " ")}
                        </span>
                      </div>

                      <p className="text-xs text-slate-400 leading-relaxed">{task.description}</p>

                      {/* If task has document waiting approval */}
                      {task.status === "WAITING_VERIFICATION" && task.documentPath && (
                        <div className="bg-slate-50 dark:bg-slate-900/60 p-3 rounded-lg border border-slate-150 dark:border-slate-800/80 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                          <div className="flex items-center gap-2 text-xs">
                            <FileText className="w-4 h-4 text-blue-500 flex-shrink-0" />
                            <div className="overflow-hidden">
                              <p className="font-semibold truncate max-w-[200px]">{task.documentPath}</p>
                              <p className="text-[10px] text-slate-400 mt-0.5">Submitted: {task.submittedAt}</p>
                            </div>
                          </div>

                          <div className="flex items-center gap-2 self-end sm:self-auto">
                            <button
                              onClick={() => handleVerificationAudit(currentEmployee.id, task.id, false)}
                              className="p-1.5 rounded-lg border border-rose-200 dark:border-rose-900/50 hover:bg-rose-50 dark:hover:bg-rose-950/20 text-rose-500 transition-all cursor-pointer"
                              title="Reject Document"
                            >
                              <X className="w-3.5 h-3.5" />
                            </button>
                            <button
                              onClick={() => handleVerificationAudit(currentEmployee.id, task.id, true)}
                              className="flex items-center gap-1 bg-emerald-600 hover:bg-emerald-700 text-white px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer"
                            >
                              <Check className="w-3.5 h-3.5" />
                              <span>Verify Approve</span>
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* UPLOAD PROOF MODAL */}
      {showUploadModal && selectedTask && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 w-full max-w-md rounded-xl overflow-hidden shadow-2xl animate-fade-in">
            <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center">
              <div className="space-y-0.5">
                <span className="text-[9px] font-bold text-blue-600 dark:text-blue-400 uppercase tracking-widest">Document Upload Panel</span>
                <h3 className="font-bold text-sm leading-tight max-w-[280px] truncate">{selectedTask.title}</h3>
              </div>
              <button onClick={() => setShowUploadModal(false)} className="p-1 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full cursor-pointer">
                <X className="w-4 h-4 text-slate-400" />
              </button>
            </div>

            <form onSubmit={handleDocumentSubmit} className="p-5 space-y-4">
              {isSubmitting ? (
                <div className="text-center py-6 space-y-3">
                  <div className="h-9 w-9 rounded-full border-2 border-blue-500 border-t-transparent animate-spin mx-auto"></div>
                  <p className="text-xs font-bold">Uploading document to secure storage...</p>
                </div>
              ) : (
                <>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-slate-400 uppercase">Document Proof Name</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. passport_scan.jpg, offer_letter_signed.pdf"
                      value={uploadFileName}
                      onChange={(e) => setUploadFileName(e.target.value)}
                      className="w-full bg-transparent border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-blue-600"
                    />
                  </div>

                  <div className="border-2 border-dashed border-slate-200 dark:border-slate-800 hover:border-blue-500 rounded-lg p-6 text-center transition-colors relative cursor-pointer group">
                    <input
                      type="file"
                      required
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) setUploadFileName(file.name);
                      }}
                      className="absolute inset-0 opacity-0 cursor-pointer"
                    />
                    <UploadCloud className="w-8 h-8 text-slate-400 group-hover:text-blue-500 mx-auto transition-colors" />
                    <p className="text-xs font-bold text-slate-600 mt-2">Select file proof from computer</p>
                    <p className="text-[10px] text-slate-400 mt-0.5">PDF, PNG, JPG files accepted</p>
                  </div>

                  <div className="flex justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-850">
                    <button
                      type="button"
                      onClick={() => setShowUploadModal(false)}
                      className="px-4 py-2 border border-slate-200 dark:border-slate-800 rounded-lg text-xs font-semibold hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold cursor-pointer"
                    >
                      Submit Verification
                    </button>
                  </div>
                </>
              )}
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
