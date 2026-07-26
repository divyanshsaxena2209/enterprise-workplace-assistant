"use client";

import React, { useState, useEffect } from "react";
import { createClient } from "@/lib/supabase/client";
import { CheckCircle, Clock, Search, ChevronRight, X, GripVertical, Plus, Trash2, ArrowUp, ArrowDown, Save, Calendar, AlertTriangle, Circle, CheckCircle2, MoreHorizontal, HelpCircle } from "lucide-react";
import OnboardingProgressMeter from "./OnboardingProgressMeter";

export default function EmployeeOnboardingEditor({ employee, onClose, onUpdate }: { employee: any, onClose: () => void, onUpdate: () => void }) {
  const supabase = createClient();
  const [progresses, setProgresses] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [draggedIdx, setDraggedIdx] = useState<number | null>(null);

  useEffect(() => {
    
    const sorted = [...(employee.progress || [])].sort((a, b) => (a.onboarding_steps?.step_order || 0) - (b.onboarding_steps?.step_order || 0));
    setProgresses(sorted);
  }, [employee]);

  const handleStatusChange = async (progressId: string, newStatus: string) => {
    setLoading(true);
    const dateStr = newStatus === 'COMPLETED' ? new Date().toISOString() : null;
    await supabase.from("employee_onboarding_progress").update({ status: newStatus, completion_date: dateStr }).eq("id", progressId);
    
    
    if (newStatus === 'COMPLETED' && !employee.employee_id) {
      const sortedProgresses = [...progresses].sort((a, b) => (a.onboarding_steps?.step_order || 0) - (b.onboarding_steps?.step_order || 0));
      const day1Tasks = sortedProgresses.filter(p => p.onboarding_steps?.description?.includes('Day 1'));
      if (day1Tasks.length > 0 && day1Tasks[0].id === progressId) {
        const newEmployeeId = `SS-${Math.floor(50000 + Math.random() * 10000)}`;
        try {
          const res = await fetch("/api/assign-employee-id", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ employeeId: employee.id, newEmployeeId })
          });
          if (res.ok) {
            employee.employee_id = newEmployeeId; 
          } else {
            console.error("Failed to assign employee ID:", await res.text());
          }
        } catch (e) {
          console.error("Error assigning employee ID:", e);
        }
      }
    }

    setProgresses(prev => prev.map(p => p.id === progressId ? { ...p, status: newStatus, completion_date: dateStr } : p));
    onUpdate();
    setLoading(false);
  };

  const handleDragStart = (e: React.DragEvent, index: number) => {
    setDraggedIdx(index);
    e.dataTransfer.effectAllowed = "move";
  };

  const handleDrop = async (e: React.DragEvent, index: number) => {
    e.preventDefault();
    if (draggedIdx === null || draggedIdx === index) return;
    
    setLoading(true);
    const newProgresses = [...progresses];
    const item = newProgresses.splice(draggedIdx, 1)[0];
    newProgresses.splice(index, 0, item);

    
    const updates = newProgresses.map((prog, i) => {
      prog.onboarding_steps.step_order = i;
      return supabase.from("onboarding_steps").update({ step_order: i }).eq("id", prog.onboarding_steps.id);
    });

    await Promise.all(updates);

    setProgresses(newProgresses);
    setDraggedIdx(null);
    onUpdate();
    setLoading(false);
  };

  const handleDelete = async (progressId: string, stepId: string) => {
    if (!confirm("Are you sure you want to delete this step?")) return;
    setLoading(true);
    await supabase.from("onboarding_steps").delete().eq("id", stepId);
    setProgresses(prev => prev.filter(p => p.id !== progressId));
    onUpdate();
    setLoading(false);
  };

  const handleAddStep = async () => {
    const stepName = prompt("Enter new step name:");
    if (!stepName) return;
    
    setLoading(true);
    const maxOrder = progresses.length > 0 ? Math.max(...progresses.map(p => p.onboarding_steps?.step_order || 0)) : 0;
    
    const { data: stepData } = await supabase.from("onboarding_steps").insert({
      step_name: stepName,
      description: "Custom step added by management.",
      step_order: maxOrder + 1,
      template_id: null
    }).select().single();

    if (stepData) {
      const { data: progData } = await supabase.from("employee_onboarding_progress").insert({
        employee_id: employee.id,
        step_id: stepData.id,
        status: "PENDING",
        notes: ""
      }).select().single();

      if (progData) {
        setProgresses(prev => [...prev, { ...progData, onboarding_steps: stepData }]);
        onUpdate();
      }
    }
    setLoading(false);
  };

  const completed = progresses.filter(p => p.status === "COMPLETED").length;

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'COMPLETED': return <CheckCircle2 className="w-5 h-5 text-green-500" />;
      case 'IN_PROGRESS': return <HelpCircle className="w-5 h-5 text-blue-500" />;
      case 'BLOCKED': return <AlertTriangle className="w-5 h-5 text-red-500" />;
      default: return <Circle className="w-5 h-5 text-muted-foreground/50" />;
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'COMPLETED': return 'Completed';
      case 'IN_PROGRESS': return 'In Progress';
      case 'BLOCKED': return 'Blocked';
      default: return 'Pending';
    }
  };

  return (
    <div className="flex-1 bg-card border border-border rounded-3xl shadow-lg flex flex-col relative overflow-hidden h-full">
      
      {}
      <div className="p-8 border-b border-border flex items-center justify-between bg-secondary/30 relative">
        <div className="absolute inset-0 bg-gradient-to-r from-secondary/50 to-transparent pointer-events-none"></div>
        <div className="relative flex items-center gap-6">
          <div className="w-16 h-16 bg-background rounded-2xl flex items-center justify-center border border-border shadow-sm text-2xl font-black text-foreground">
            {employee.full_name.charAt(0).toUpperCase()}
          </div>
          <div>
            <h2 className="text-3xl font-black tracking-tight">{employee.full_name}</h2>
            <p className="text-sm font-bold text-muted-foreground mt-1 uppercase tracking-widest">{employee.job_title} • {employee.department}</p>
          </div>
        </div>
        <div className="relative">
          <OnboardingProgressMeter completedTasks={completed} totalTasks={progresses.length} />
        </div>
      </div>
      
      {}
      <div className="p-4 border-b border-border bg-background flex items-center justify-between">
        <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground ml-4">Timeline Editor</p>
        <button onClick={handleAddStep} disabled={loading} className="flex items-center gap-2 px-4 py-2 bg-foreground text-background text-xs font-bold uppercase tracking-wider rounded-lg hover:bg-foreground/90 transition-colors shadow-sm disabled:opacity-50">
          <Plus className="w-4 h-4" /> Add Step
        </button>
      </div>

      {}
      <div className="p-6 overflow-y-auto flex-1 custom-scrollbar bg-background/50">
        <div className="space-y-2 max-w-5xl mx-auto relative before:absolute before:inset-0 before:ml-[3.5rem] before:-translate-x-px before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-border before:to-transparent">
          {progresses.map((prog, idx) => (
            <div 
              key={prog.id} 
              draggable={true}
              onDragStart={(e) => handleDragStart(e, idx)}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => handleDrop(e, idx)}
              className={`group relative flex items-center gap-6 py-4 transition-all ${draggedIdx === idx ? 'opacity-50' : ''}`}
            >
              
              {}
              <div className="flex flex-col items-center justify-center text-muted-foreground/30 group-hover:text-muted-foreground transition-colors cursor-grab active:cursor-grabbing shrink-0 w-6">
                <GripVertical className="w-5 h-5" />
              </div>

              {}
              <div className="relative flex items-center justify-center w-10 h-10 rounded-full border-4 border-black bg-black shadow shrink-0 z-10 transition-transform hover:scale-110 duration-300 cursor-pointer" onClick={() => handleStatusChange(prog.id, prog.status === 'COMPLETED' ? 'PENDING' : 'COMPLETED')}>
                {getStatusIcon(prog.status)}
              </div>
              
              {}
              <div className={`flex-1 min-w-0 p-5 rounded-2xl border transition-all duration-300 ${prog.status === 'COMPLETED' ? 'bg-background border-green-500/30' : prog.status === 'IN_PROGRESS' ? 'bg-card border-blue-500/30 shadow-lg shadow-blue-500/5' : 'bg-background border-border hover:bg-card hover:shadow-md'}`}>
                <div className="flex items-center justify-between mb-1">
                  <h4 className={`font-bold text-sm cursor-pointer transition-colors ${prog.status === 'COMPLETED' ? 'text-muted-foreground line-through' : 'text-foreground hover:text-blue-500'}`} onClick={() => handleStatusChange(prog.id, prog.status === 'COMPLETED' ? 'PENDING' : 'COMPLETED')}>
                    {prog.onboarding_steps?.step_name}
                  </h4>
                  <div className="flex items-center gap-3">
                    {prog.status === 'COMPLETED' && prog.completion_date && (
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-bold text-green-500 uppercase tracking-widest bg-green-500/10 px-2 py-0.5 rounded-full">
                          Completed on: {new Date(prog.completion_date).toLocaleDateString()}
                        </span>
                      </div>
                    )}
                    <button onClick={() => handleDelete(prog.id, prog.onboarding_steps?.id)} disabled={loading} className="text-red-500/50 hover:text-red-500 transition-colors">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <p className="text-xs text-muted-foreground/70 leading-relaxed cursor-pointer" onClick={() => handleStatusChange(prog.id, prog.status === 'COMPLETED' ? 'PENDING' : 'COMPLETED')}>
                  {prog.onboarding_steps?.description}
                </p>
                
                {prog.status === 'BLOCKED' && (
                  <p className="text-[10px] font-bold text-red-500 uppercase tracking-wider mt-3 flex items-center gap-1"><AlertTriangle className="w-3 h-3"/> Blocked</p>
                )}
              </div>
            </div>
          ))}
          {progresses.length === 0 && (
            <div className="flex flex-col items-center justify-center p-12 border border-dashed border-border rounded-3xl text-muted-foreground">
              <Plus className="w-8 h-8 mb-4 opacity-50" />
              <p className="text-sm font-bold uppercase tracking-widest">No steps found</p>
              <p className="text-xs mt-1">Add a custom step to get started.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
