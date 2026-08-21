"use client";
import React from "react";
import { useUser } from "@/lib/context/UserContext";
import ManagementDashboard from "@/components/dashboard/ManagementDashboard";
import EmployeeDashboard from "@/components/dashboard/EmployeeDashboard";
import { Loader2 } from "lucide-react";
export default function DashboardPage() {
  const { profile, loading } = useUser();
  if (loading) {
    return (
      <div className="flex justify-center p-20">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }
  const isManagement = profile?.role === "MANAGEMENT" || profile?.role === "ADMIN" || profile?.role === "HR";
  if (isManagement) {
    return <ManagementDashboard />;
  }
  return <EmployeeDashboard />;
}
