"use client";

import React, { useState } from "react";
import { Plus, Briefcase, MapPin, Users, Sparkles } from "lucide-react";

export default function JobsPage() {
  const [jobs] = useState([
    { id: 1, title: "Senior Frontend System Architect", department: "Technology Solutions", type: "Full-time", location: "Distributed / Remote", applicants: 45, status: "Active" },
    { id: 2, title: "Principal Product Manager", department: "Product Innovation", type: "Full-time", location: "New York HQ", applicants: 12, status: "Active" },
    { id: 3, title: "HR Business Operations Partner", department: "People Operations", type: "Contract", location: "San Francisco Hub", applicants: 8, status: "Draft" },
  ]);

  return (
    <div className="space-y-8 pb-10">
      
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-foreground flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-foreground animate-pulse" />
            Talent Acquisition Operations
          </h1>
          <p className="text-sm text-muted-foreground mt-1">Manage active corporate openings, track application pipelines, and deploy position templates.</p>
        </div>
        <button className="flex items-center gap-2 bg-foreground hover:bg-foreground/90 text-background px-4 py-2.5 rounded-lg text-xs font-bold uppercase tracking-wider transition-colors shadow-sm">
          <Plus size={14} />
          Initiate Requisition
        </button>
      </div>

      {/* Grid List */}
      <div className="grid grid-cols-1 gap-4">
        {jobs.map((job) => (
          <div key={job.id} className="p-6 bg-card rounded-2xl shadow-sm border border-border hover:border-foreground/20 transition-all flex items-center justify-between cursor-pointer group">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-secondary border border-border/50 rounded-xl flex items-center justify-center text-foreground group-hover:bg-foreground group-hover:text-background transition-colors">
                <Briefcase size={20} />
              </div>
              <div>
                <h3 className="font-bold text-base tracking-tight text-foreground">{job.title}</h3>
                <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground mt-2 font-medium">
                  <span className="flex items-center gap-1.5"><MapPin size={12} className="text-foreground" /> {job.location}</span>
                  <span className="flex items-center gap-1.5"><Users size={12} className="text-foreground" /> {job.applicants} Evaluated Candidates</span>
                  <span className="px-2.5 py-0.5 bg-secondary border border-border/50 rounded-full text-[9px] uppercase tracking-wider text-muted-foreground font-semibold">{job.type}</span>
                </div>
              </div>
            </div>
            <div>
              <span className={`px-2.5 py-1 text-[10px] uppercase tracking-widest font-bold rounded-lg border shadow-sm ${
                job.status === "Active" 
                  ? "bg-foreground/5 text-foreground border-foreground/10" 
                  : "bg-secondary text-muted-foreground border-border"
              }`}>
                {job.status}
              </span>
            </div>
          </div>
        ))}
      </div>

    </div>
  );
}
