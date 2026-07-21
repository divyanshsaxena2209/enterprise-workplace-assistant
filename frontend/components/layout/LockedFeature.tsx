import React from "react";
import { Lock } from "lucide-react";

interface LockedFeatureProps {
  isLocked: boolean;
  children: React.ReactNode;
}

export default function LockedFeature({ isLocked, children }: LockedFeatureProps) {
  if (!isLocked) {
    return <>{children}</>;
  }

  return (
    <div className="relative">
      <div className="blur-sm pointer-events-none select-none opacity-40 transition-all duration-500">
        {children}
      </div>
      <div className="absolute inset-0 z-20 flex flex-col items-center justify-center">
        <div className="bg-background/80 backdrop-blur-md border border-white/10 p-8 rounded-3xl shadow-2xl flex flex-col items-center justify-center gap-4 animate-fade-in max-w-sm text-center">
          <div className="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center border border-red-500/20 shadow-[0_0_20px_rgba(239,68,68,0.2)]">
            <Lock className="w-8 h-8 text-red-500" />
          </div>
          <h2 className="text-xl font-bold tracking-tight text-white">Access Denied</h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            This module is restricted. Your profile has not met the requirements to unlock these enterprise operations.
          </p>
        </div>
      </div>
    </div>
  );
}
