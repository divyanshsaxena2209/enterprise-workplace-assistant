"use client";

import React, { useState } from "react";
import { Users, FileText, CheckCircle, AlertCircle, Clock, ChevronRight } from "lucide-react";

export default function HRAdminDashboard() {
  const [employees] = useState([
    { id: 1, name: "Divya Patel", role: "Software Engineer", dept: "Engineering", progress: 25, status: "Onboarding" },
    { id: 2, name: "Michael Chen", role: "Product Manager", dept: "Product", progress: 80, status: "Onboarding" },
    { id: 3, name: "Sarah Smith", role: "Account Executive", dept: "Sales", progress: 100, status: "Active" },
  ]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">HR Onboarding Center</h1>
          <p className="text-gray-500">Manage new hires, approve documents, and track onboarding pipelines.</p>
        </div>
        <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors">
          Create New Employee
        </button>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="p-6 bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-800 rounded-2xl shadow-sm">
          <div className="flex items-center gap-3 mb-2">
            <Users size={18} className="text-blue-500" />
            <h3 className="text-gray-500 text-sm font-medium">In Pipeline</h3>
          </div>
          <p className="text-3xl font-bold">12</p>
        </div>
        <div className="p-6 bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-800 rounded-2xl shadow-sm">
          <div className="flex items-center gap-3 mb-2">
            <FileText size={18} className="text-yellow-500" />
            <h3 className="text-gray-500 text-sm font-medium">Pending Approvals</h3>
          </div>
          <p className="text-3xl font-bold text-yellow-600">8</p>
        </div>
        <div className="p-6 bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-800 rounded-2xl shadow-sm">
          <div className="flex items-center gap-3 mb-2">
            <AlertCircle size={18} className="text-red-500" />
            <h3 className="text-gray-500 text-sm font-medium">Overdue Tasks</h3>
          </div>
          <p className="text-3xl font-bold text-red-600">3</p>
        </div>
        <div className="p-6 bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-800 rounded-2xl shadow-sm">
          <div className="flex items-center gap-3 mb-2">
            <CheckCircle size={18} className="text-green-500" />
            <h3 className="text-gray-500 text-sm font-medium">Completed This Month</h3>
          </div>
          <p className="text-3xl font-bold text-green-600">24</p>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Active Onboardings */}
        <div className="lg:w-2/3 bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-800 rounded-2xl shadow-sm overflow-hidden">
          <div className="p-6 border-b border-gray-100 dark:border-gray-800">
            <h3 className="font-semibold text-lg">Active Onboarding Pipelines</h3>
          </div>
          <div className="divide-y divide-gray-100 dark:divide-gray-800">
            {employees.map(emp => (
              <div key={emp.id} className="p-5 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-900/50 transition cursor-pointer">
                <div>
                  <h4 className="font-semibold">{emp.name}</h4>
                  <p className="text-sm text-gray-500">{emp.role} • {emp.dept}</p>
                </div>
                <div className="flex items-center gap-6">
                  <div className="w-32 text-right">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-medium text-gray-500">Progress</span>
                      <span className="text-xs font-bold">{emp.progress}%</span>
                    </div>
                    <div className="h-2 w-full bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                      <div className={`h-full ${emp.progress === 100 ? 'bg-green-500' : 'bg-blue-600'}`} style={{ width: `${emp.progress}%` }}></div>
                    </div>
                  </div>
                  <ChevronRight className="text-gray-400" size={20} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Verification Queue */}
        <div className="lg:w-1/3 bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-800 rounded-2xl shadow-sm overflow-hidden">
          <div className="p-6 border-b border-gray-100 dark:border-gray-800">
            <h3 className="font-semibold text-lg">Document Verification</h3>
          </div>
          <div className="p-4 space-y-3">
            <div className="p-4 border border-yellow-200 dark:border-yellow-900/30 bg-yellow-50 dark:bg-yellow-900/10 rounded-xl">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2 text-yellow-800 dark:text-yellow-500 font-medium text-sm">
                  <Clock size={16} /> Pending Review
                </div>
                <span className="text-xs text-gray-500">2h ago</span>
              </div>
              <p className="text-sm font-semibold mb-1">Michael Chen - ID Proof.pdf</p>
              <div className="flex gap-2 mt-3">
                <button className="flex-1 bg-green-600 hover:bg-green-700 text-white py-1.5 rounded-md text-sm font-medium transition">Approve</button>
                <button className="flex-1 bg-red-100 hover:bg-red-200 text-red-700 dark:bg-red-900/30 dark:hover:bg-red-900/50 py-1.5 rounded-md text-sm font-medium transition">Reject</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
