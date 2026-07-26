"use client";

import React from "react";

interface OnboardingProgressMeterProps {
  completedTasks: number;
  totalTasks: number;
}

export default function OnboardingProgressMeter({
  completedTasks,
  totalTasks,
}: OnboardingProgressMeterProps) {
  const percentage = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;
  const remainingTasks = totalTasks - completedTasks;

  return (
    <div className="flex items-center gap-6">
      <div className="relative w-24 h-24 rounded-full border-[3px] border-border/50 flex items-center justify-center bg-card shadow-inner">
        <svg className="w-full h-full absolute inset-0 -rotate-90" viewBox="0 0 36 36">
          <path
            className="text-transparent"
            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
          />
          <path
            className="text-foreground transition-all duration-1000 ease-in-out"
            strokeDasharray={`${percentage}, 100`}
            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
            strokeLinecap="round"
          />
        </svg>
        <span className="text-xl font-bold tracking-tight text-foreground z-10">{percentage}%</span>
      </div>
      
      <div className="space-y-1">
        <h3 className="text-sm font-bold tracking-tight text-foreground">Completion Status</h3>
        <div className="flex gap-4 mt-2">
          <div className="flex flex-col">
            <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Completed</span>
            <span className="text-lg font-black text-foreground">{completedTasks}</span>
          </div>
          <div className="w-px bg-border"></div>
          <div className="flex flex-col">
            <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Remaining</span>
            <span className="text-lg font-black text-foreground">{remainingTasks}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
