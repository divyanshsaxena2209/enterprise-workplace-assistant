"use client";

import React, { useState } from "react";
import { Plus, Briefcase, MapPin, Users } from "lucide-react";

export default function JobsPage() {
  const [jobs] = useState([
    { id: 1, title: "Senior Frontend Engineer", department: "Engineering", type: "Full-time", location: "Remote", applicants: 45, status: "Open" },
    { id: 2, title: "Product Manager", department: "Product", type: "Full-time", location: "New York, NY", applicants: 12, status: "Open" },
    { id: 3, title: "HR Business Partner", department: "Human Resources", type: "Contract", location: "San Francisco, CA", applicants: 8, status: "Draft" },
  ]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Job Listings</h1>
          <p className="text-gray-500">Manage your active openings and drafts.</p>
        </div>
        <button className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors">
          <Plus size={18} />
          Create Job
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {jobs.map((job) => (
          <div key={job.id} className="p-5 bg-white dark:bg-gray-950 rounded-xl shadow-sm border border-gray-100 dark:border-gray-800 hover:border-gray-200 dark:hover:border-gray-700 transition flex items-center justify-between cursor-pointer">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-blue-50 dark:bg-blue-900/30 rounded-lg flex items-center justify-center text-blue-600">
                <Briefcase size={24} />
              </div>
              <div>
                <h3 className="font-semibold text-lg">{job.title}</h3>
                <div className="flex items-center gap-4 text-sm text-gray-500 mt-1">
                  <span className="flex items-center gap-1"><MapPin size={14} /> {job.location}</span>
                  <span className="flex items-center gap-1"><Users size={14} /> {job.applicants} Applicants</span>
                  <span>{job.type}</span>
                </div>
              </div>
            </div>
            <div>
              <span className={`px-3 py-1 text-xs font-medium rounded-full ${job.status === "Open" ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400" : "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400"}`}>
                {job.status}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
