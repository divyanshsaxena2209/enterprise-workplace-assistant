"use client";

import React from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from "recharts";
import { ArrowUpRight, ArrowDownRight, MoreHorizontal, Sparkles, TrendingUp } from "lucide-react";

export default function AnalyticsPage() {
  const funnelData = [
    { name: "Applied", count: 450 },
    { name: "Screened", count: 320 },
    { name: "Interviewed", count: 150 },
    { name: "Offered", count: 35 },
    { name: "Hired", count: 28 },
  ];

  const trendData = [
    { month: "Jan", hires: 4, applications: 120 },
    { month: "Feb", hires: 6, applications: 150 },
    { month: "Mar", hires: 5, applications: 180 },
    { month: "Apr", hires: 8, applications: 210 },
    { month: "May", hires: 12, applications: 250 },
  ];

  return (
    <div className="space-y-8 pb-10">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-foreground flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-foreground" />
            Operational Analytics
          </h1>
          <p className="text-sm text-muted-foreground mt-1">Review workforce performance metrics, pipeline health, and onboarding velocity.</p>
        </div>
        <select className="bg-card border border-border rounded-lg px-4 py-2 text-xs font-semibold uppercase tracking-wider focus:outline-none focus:ring-1 focus:ring-ring shadow-sm cursor-pointer">
          <option>Last 30 Days</option>
          <option>This Quarter</option>
          <option>This Year</option>
        </select>
      </div>

      {/* Grid Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard title="Total Candidates" value="1,248" trend="+12% MoM" positive={true} />
        <StatCard title="Active Requisitions" value="24" trend="+3 New" positive={true} />
        <StatCard title="Average Time to Hire" value="18 Days" trend="-2 days" positive={true} />
        <StatCard title="Offer Acceptance Rate" value="82%" trend="-4% MoM" positive={false} />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Chart 1: Funnel */}
        <div className="bg-card border border-border p-6 rounded-2xl shadow-sm flex flex-col">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h3 className="font-bold text-sm uppercase tracking-wider text-foreground">Talent Acquisition Pipeline</h3>
              <p className="text-xs text-muted-foreground mt-1">Hiring funnel conversion rates across standard workflows</p>
            </div>
            <button className="text-muted-foreground hover:text-foreground transition-colors p-1 rounded-lg hover:bg-secondary">
              <MoreHorizontal size={18} />
            </button>
          </div>
          <div className="h-[280px] w-full mt-auto">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={funnelData} layout="vertical" margin={{ top: 0, right: 0, left: 10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--border)" strokeOpacity={0.5} />
                <XAxis type="number" tick={{ fill: "var(--muted-foreground)", fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis dataKey="name" type="category" width={80} tick={{ fill: "var(--foreground)", fontSize: 12, fontWeight: 600 }} axisLine={false} tickLine={false} />
                <Tooltip 
                  cursor={{ fill: 'var(--secondary)' }} 
                  contentStyle={{ backgroundColor: 'var(--card)', color: 'var(--foreground)', borderRadius: '8px', border: '1px solid var(--border)', boxShadow: '0 4px 12px rgba(0,0,0,0.05)', fontSize: '12px', fontWeight: 500 }} 
                />
                <Bar dataKey="count" fill="var(--foreground)" radius={[0, 4, 4, 0]} barSize={20} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Trends */}
        <div className="bg-card border border-border p-6 rounded-2xl shadow-sm flex flex-col">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h3 className="font-bold text-sm uppercase tracking-wider text-foreground">Workforce Acquisition Trends</h3>
              <p className="text-xs text-muted-foreground mt-1">Historical monthly applications and hired volumes</p>
            </div>
            <button className="text-muted-foreground hover:text-foreground transition-colors p-1 rounded-lg hover:bg-secondary">
              <MoreHorizontal size={18} />
            </button>
          </div>
          <div className="h-[280px] w-full mt-auto">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" strokeOpacity={0.5} />
                <XAxis dataKey="month" tick={{ fill: "var(--muted-foreground)", fontSize: 12 }} axisLine={false} tickLine={false} dy={10} />
                <YAxis yAxisId="left" tick={{ fill: "var(--muted-foreground)", fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis yAxisId="right" orientation="right" tick={{ fill: "var(--muted-foreground)", fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: 'var(--card)', color: 'var(--foreground)', borderRadius: '8px', border: '1px solid var(--border)', boxShadow: '0 4px 12px rgba(0,0,0,0.05)', fontSize: '12px', fontWeight: 500 }} 
                />
                <Line yAxisId="left" type="monotone" dataKey="applications" stroke="var(--muted-foreground)" strokeWidth={2.5} dot={{ fill: 'var(--card)', stroke: 'var(--muted-foreground)', strokeWidth: 2, r: 4 }} activeDot={{ r: 6, fill: 'var(--foreground)', stroke: 'var(--card)' }} />
                <Line yAxisId="right" type="monotone" dataKey="hires" stroke="var(--foreground)" strokeWidth={2.5} dot={{ fill: 'var(--card)', stroke: 'var(--foreground)', strokeWidth: 2, r: 4 }} activeDot={{ r: 6, fill: 'var(--foreground)', stroke: 'var(--card)' }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>
    </div>
  );
}

function StatCard({ title, value, trend, positive }: { title: string, value: string, trend: string, positive: boolean }) {
  return (
    <div className="p-6 bg-card rounded-2xl shadow-sm border border-border group hover:border-foreground/20 transition-all duration-300 flex flex-col justify-between h-36">
      <div className="flex items-center justify-between">
        <h3 className="text-muted-foreground text-[10px] font-bold uppercase tracking-wider">{title}</h3>
        <TrendingUp className={`w-4 h-4 ${positive ? "text-foreground" : "text-muted-foreground/50"}`} />
      </div>
      <div className="flex items-end justify-between mt-auto">
        <p className="text-3xl font-black tracking-tight text-foreground">{value}</p>
        <div className={`flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border border-border/50 ${positive ? "bg-foreground text-background" : "bg-secondary text-muted-foreground"}`}>
          {positive ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
          <span>{trend}</span>
        </div>
      </div>
    </div>
  );
}
