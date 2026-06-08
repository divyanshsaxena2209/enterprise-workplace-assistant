"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Bell, User, Settings, LogOut, ShieldCheck, ChevronDown, Loader2 } from "lucide-react";
import { useUser } from "@/lib/context/UserContext";
import { createClient } from "@/lib/supabase/client";

export default function TopNavbar() {
  const pathname = usePathname();
  const router = useRouter();
  const { profile, loading } = useUser();
  const supabase = createClient();
  
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
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

  const tabs = [
    {
      name: "Organizational Intelligence",
      href: "/knowledge",
      active: pathname.startsWith("/knowledge"),
    },
    {
      name: "Talent Acquisition Pipeline",
      href: "/jobs",
      active: pathname.startsWith("/jobs") || pathname.startsWith("/resume-screening"),
    },
    {
      name: "Workforce Onboarding Operations",
      href: "/onboarding",
      active: pathname.startsWith("/onboarding"),
    },
    {
      name: "Operational Analytics",
      href: "/analytics",
      active: pathname.startsWith("/analytics") || pathname === "/dashboard",
    }
  ];

  return (
    <header className="h-16 border-b border-border bg-card flex items-center justify-between px-6 sticky top-0 z-30 select-none">
      
      {/* Primary Workspace Navigation Tabs */}
      <nav className="hidden lg:flex items-center gap-6 h-full">
        {tabs.map((tab) => (
          <Link
            key={tab.name}
            href={tab.href}
            className={`text-xs font-bold uppercase tracking-wider h-full flex items-center px-1 border-b-2 transition-all relative top-[1px] ${
              tab.active
                ? "border-foreground text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab.name}
          </Link>
        ))}
      </nav>

      {/* Small Screen Nav Trigger Link or Placeholder */}
      <div className="lg:hidden flex items-center gap-2">
        <span className="text-xs font-bold uppercase tracking-wider text-foreground">
          {tabs.find(t => t.active)?.name || "Workforce OS"}
        </span>
      </div>

      {/* User Context, Notifications & Profile Dropdown */}
      <div className="flex items-center gap-4">
        
        {/* Notifications */}
        <button className="p-2 rounded-md text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors relative">
          <Bell size={18} />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-foreground rounded-full border border-card"></span>
        </button>

        <div className="h-4 w-px bg-border"></div>

        {/* Profile Dropdown */}
        <div className="relative" ref={dropdownRef}>
          {loading ? (
            <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
          ) : profile ? (
            <button
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="flex items-center gap-2 text-left focus:outline-none group"
            >
              <img
                src={profile.avatar_url || `https://api.dicebear.com/7.x/adventurer/svg?seed=${encodeURIComponent(profile.full_name)}`}
                alt={profile.full_name}
                className="w-8 h-8 rounded-full border border-border object-cover bg-secondary group-hover:border-foreground transition-colors"
              />
              <div className="hidden sm:block">
                <p className="text-xs font-bold text-foreground leading-none">{profile.full_name}</p>
                <p className="text-[9px] text-muted-foreground uppercase tracking-widest font-semibold mt-0.5">{profile.role}</p>
              </div>
              <ChevronDown size={14} className="text-muted-foreground group-hover:text-foreground transition-colors" />
            </button>
          ) : (
            <Link 
              href="/login" 
              className="flex items-center gap-2 bg-foreground text-background px-3 py-1.5 rounded-md text-xs font-bold uppercase tracking-wider"
            >
              <User size={14} />
              Sign In
            </Link>
          )}

          {/* Dropdown Menu */}
          {dropdownOpen && profile && (
            <div className="absolute right-0 mt-2.5 w-56 bg-card border border-border rounded-xl shadow-xl py-2 z-50 animate-fade-in">
              <div className="px-4.5 py-3 border-b border-border/50">
                <p className="text-xs font-bold text-foreground truncate">{profile.full_name}</p>
                <p className="text-[10px] text-muted-foreground truncate font-medium mt-0.5">{profile.email}</p>
                {profile.department && (
                  <p className="text-[9px] text-muted-foreground uppercase font-bold tracking-wider mt-1">{profile.department}</p>
                )}
              </div>

              <div className="p-1">
                <Link
                  href="/profile"
                  onClick={() => setDropdownOpen(false)}
                  className="flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-semibold text-foreground hover:bg-secondary transition-all"
                >
                  <User size={14} />
                  My Profile
                </Link>
                <Link
                  href="/settings"
                  onClick={() => setDropdownOpen(false)}
                  className="flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-semibold text-foreground hover:bg-secondary transition-all"
                >
                  <Settings size={14} />
                  System Settings
                </Link>
                
                <div className="h-px bg-border/50 my-1"></div>
                
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-bold text-destructive hover:bg-destructive/10 transition-all text-left"
                >
                  <LogOut size={14} />
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
