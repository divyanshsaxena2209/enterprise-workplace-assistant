import React from "react";
import Sidebar from "./Sidebar";
import TopNavbar from "./TopNavbar";

export default function DashboardShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen overflow-hidden bg-background text-foreground selection:bg-foreground selection:text-background">
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden relative">
        <TopNavbar />
        <main className="flex-1 overflow-y-auto p-6 md:p-8 custom-scrollbar">
          <div className="mx-auto max-w-6xl animate-fade-in">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
