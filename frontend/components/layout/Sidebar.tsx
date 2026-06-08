"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Settings, User, Compass, Sparkles } from "lucide-react";
import { useUser } from "@/lib/context/UserContext";

export default function Sidebar() {
  const pathname = usePathname();
  const { profile } = useUser();

  return (
    <aside className="w-[240px] border-r border-border bg-card hidden md:flex flex-col h-screen select-none">
      {/* Branding Header */}
      <div className="h-16 border-b border-border/50 flex items-center px-6 gap-2 bg-secondary/20">
        <Sparkles className="w-5 h-5 text-foreground animate-pulse" />
        <span className="font-bold text-sm tracking-wider uppercase text-foreground">Workforce OS</span>
      </div>
      
      {/* Navigation Links */}
      <div className="flex-1 overflow-y-auto py-6 px-3 custom-scrollbar flex flex-col justify-between">
        <div className="space-y-4">
          <nav className="space-y-1">
            <NavItem 
              href="/profile" 
              icon={<User size={16} />} 
              label="Personnel Profile" 
              isActive={pathname === "/profile"} 
            />
            <NavItem 
              href="/settings" 
              icon={<Settings size={16} />} 
              label="System Settings" 
              isActive={pathname === "/settings"} 
            />
          </nav>

          {/* Future Expandable Items Placeholder */}
          <div className="pt-4 border-t border-border/50">
            <span className="px-3 text-[10px] font-bold uppercase tracking-widest text-muted-foreground block mb-2">Extended Logs</span>
            <nav className="space-y-1">
              <div className="flex items-center gap-3 px-3 py-2 rounded-md text-xs font-semibold text-muted-foreground/60 cursor-not-allowed">
                <Compass size={14} />
                <span>Audit Logs</span>
              </div>
              <div className="flex items-center gap-3 px-3 py-2 rounded-md text-xs font-semibold text-muted-foreground/60 cursor-not-allowed">
                <Compass size={14} />
                <span>Security Policies</span>
              </div>
            </nav>
          </div>
        </div>

        {/* Small Profile Card Footer */}
        {profile && (
          <div className="p-3 bg-secondary/30 border border-border/50 rounded-xl flex items-center gap-3">
            <img 
              src={profile.avatar_url || `https://api.dicebear.com/7.x/adventurer/svg?seed=${encodeURIComponent(profile.full_name)}`}
              alt={profile.full_name} 
              className="w-9 h-9 rounded-full border border-border object-cover"
            />
            <div className="overflow-hidden">
              <p className="text-xs font-bold text-foreground truncate">{profile.full_name}</p>
              <p className="text-[10px] text-muted-foreground font-medium truncate uppercase tracking-wider mt-0.5">{profile.role}</p>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}

function NavItem({ href, icon, label, isActive }: { href: string; icon: React.ReactNode; label: string; isActive?: boolean }) {
  return (
    <Link 
      href={href} 
      className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-semibold transition-all duration-200 group ${
        isActive 
          ? "bg-foreground text-background shadow-sm" 
          : "text-muted-foreground hover:bg-secondary hover:text-foreground"
      }`}
    >
      <div className={`${isActive ? "text-background" : "text-muted-foreground group-hover:text-foreground"} transition-colors`}>
        {icon}
      </div>
      {label}
    </Link>
  );
}
