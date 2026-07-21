import React from "react";
import TopNavbar from "./TopNavbar";

export default function DashboardShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen overflow-hidden bg-background text-foreground selection:bg-white selection:text-black relative z-0">
      
      {/* Ambient background glows */}
      <div className="fixed top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-white/5 blur-[120px] pointer-events-none -z-10 mix-blend-screen" />
      <div className="fixed bottom-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-white/5 blur-[120px] pointer-events-none -z-10 mix-blend-screen" />

      <div className="flex flex-col flex-1 overflow-hidden relative z-10 min-w-0 min-h-0">
        <TopNavbar />
        <main className="flex-1 min-h-0 overflow-y-auto p-6 md:p-8 lg:p-10 custom-scrollbar scroll-smooth">
          <div className="mx-auto max-w-7xl animate-fade-in">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
