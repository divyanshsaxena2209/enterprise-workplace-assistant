"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Bell, User, Settings, LogOut, ChevronDown, Loader2, FileText } from "lucide-react";
import { useUser } from "@/lib/context/UserContext";
import { createClient } from "@/lib/supabase/client";

export default function TopNavbar() {
  const pathname = usePathname();
  const router = useRouter();
  const { profile, loading } = useUser();
  const supabase = createClient();
  
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLogout = async () => {
    await supabase.auth.signOut();
    router.push("/login");
  };

  const isManagement = profile?.role === "MANAGEMENT" || profile?.role === "ADMIN" || profile?.role === "HR";
  const hasAnalyticsAccess = isManagement || !!profile?.employee_id;

  const allTabs = [
    { name: "Organizational Intelligence", href: "/knowledge", active: pathname.startsWith("/knowledge") },
    { name: "Talent Acquisition Pipeline", href: "/jobs", active: pathname.startsWith("/jobs") || pathname.startsWith("/candidates") },
    { name: "Workforce Onboarding Operations", href: "/onboarding", active: pathname.startsWith("/onboarding") },
    { name: "Operational Analytics", href: "/analytics", active: pathname.startsWith("/analytics") || pathname === "/dashboard", hidden: !hasAnalyticsAccess }
  ];

  const tabs = allTabs.filter(t => !t.hidden);

  return (
    <header className="h-20 glass-panel border-b border-white/5 flex items-center justify-between px-8 sticky top-0 z-30 select-none">
      
      <nav className="hidden lg:flex items-center gap-8 h-full">
        {tabs.map((tab) => (
          <Link
            key={tab.name}
            href={tab.href}
            className={`text-xs font-bold uppercase tracking-[0.1em] h-full flex items-center px-1 border-b-[3px] transition-all duration-300 relative ${
              tab.active
                ? "border-white text-white shadow-[0_1px_15px_rgba(255,255,255,0.4)]"
                : "border-transparent text-muted-foreground hover:text-white hover:border-white/20"
            }`}
          >
            {tab.name}
          </Link>
        ))}
      </nav>

      <div className="lg:hidden flex items-center gap-2">
        <span className="text-xs font-bold uppercase tracking-wider text-white">
          {tabs.find(t => t.active)?.name || "Workforce OS"}
        </span>
      </div>

      <div className="flex items-center gap-5">
        
        <button className="w-10 h-10 rounded-full flex items-center justify-center text-muted-foreground hover:bg-white/10 hover:text-white transition-colors relative border border-transparent hover:border-white/10">
          <Bell size={18} />
          <span className="absolute top-2.5 right-2.5 w-2 h-2 bg-white rounded-full shadow-[0_0_8px_rgba(255,255,255,0.8)]"></span>
        </button>

        <div className="h-6 w-px bg-white/10"></div>

        <div className="relative" ref={dropdownRef}>
          {loading ? (
            <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center">
              <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
            </div>
          ) : profile ? (
            <button
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="flex items-center gap-3 text-left focus:outline-none group px-2 py-1 rounded-full hover:bg-white/5 transition-colors border border-transparent hover:border-white/10"
            >
              <img
                src={profile.avatar_url || `https://api.dicebear.com/7.x/adventurer/svg?seed=${encodeURIComponent(profile.full_name)}`}
                alt={profile.full_name}
                className="w-10 h-10 rounded-full border border-white/20 object-cover bg-black/50 shadow-sm"
              />
              <div className="hidden sm:block">
                <p className="text-xs font-bold text-white leading-none">{profile.full_name}</p>
                <p className="text-[10px] text-muted-foreground uppercase tracking-widest font-semibold mt-1">{profile.role}</p>
              </div>
              <ChevronDown size={14} className="text-muted-foreground group-hover:text-white transition-colors ml-1" />
            </button>
          ) : (
            <Link 
              href="/login" 
              className="flex items-center gap-2 bg-white text-black px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider hover-lift"
            >
              <User size={14} />
              Sign In
            </Link>
          )}

          {dropdownOpen && profile && (
            <div className="absolute right-0 mt-3 w-64 glass-panel-heavy rounded-2xl shadow-2xl py-2 z-50 animate-fade-in border-white/10">
              <div className="px-5 py-4 border-b border-white/5 bg-white/5">
                <p className="text-sm font-bold text-white truncate">{profile.full_name}</p>
                <p className="text-[11px] text-muted-foreground truncate font-medium mt-1">{profile.email}</p>
                {profile.department && (
                  <p className="text-[10px] text-white/70 uppercase font-bold tracking-widest mt-2 bg-white/10 inline-block px-2 py-1 rounded-md">{profile.department}</p>
                )}
              </div>

              <div className="p-2 space-y-1 mt-1">
                <Link
                  href="/profile"
                  onClick={() => setDropdownOpen(false)}
                  className="flex items-center gap-3 px-4 py-2.5 rounded-xl text-xs font-semibold text-white/90 hover:bg-white/10 hover:text-white transition-all"
                >
                  <User size={16} />
                  My Profile
                </Link>
                {!isManagement && (
                  <Link
                    href="/my-applications"
                    onClick={() => setDropdownOpen(false)}
                    className="flex items-center gap-3 px-4 py-2.5 rounded-xl text-xs font-semibold text-white/90 hover:bg-white/10 hover:text-white transition-all"
                  >
                    <FileText size={16} />
                    My Applications
                  </Link>
                )}
                <Link
                  href="/settings"
                  onClick={() => setDropdownOpen(false)}
                  className="flex items-center gap-3 px-4 py-2.5 rounded-xl text-xs font-semibold text-white/90 hover:bg-white/10 hover:text-white transition-all"
                >
                  <Settings size={16} />
                  System Settings
                </Link>
                
                <div className="h-px bg-white/5 my-2 mx-2"></div>
                
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-xs font-bold text-red-400 hover:bg-red-500/10 hover:text-red-300 transition-all text-left"
                >
                  <LogOut size={16} />
                  Log Out
                </button>
              </div>
            </div>
          )}
        </div>

      </div>
    </header>
  );
}
