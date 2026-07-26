"use client";

import React from "react";
import { useUser } from "@/lib/context/UserContext";
import EmployeeOnboardingDashboard from "@/components/onboarding/EmployeeOnboardingDashboard";
import ManagementOnboardingDashboard from "@/components/onboarding/ManagementOnboardingDashboard";
import { Loader2 } from "lucide-react";

export default function OnboardingPage() {
  const { profile, loading } = useUser();

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const isManagement = profile?.role === "MANAGEMENT" || profile?.role === "ADMIN" || profile?.role === "HR";

  if (isManagement) {
    return <ManagementOnboardingDashboard />;
  }

  return <EmployeeOnboardingDashboard />;
}

