import Link from "next/link";
import { LayoutDashboard, FileText, Users, BookOpen, Video, Settings, Briefcase } from "lucide-react";

export default function Sidebar() {
  return (
    <aside className="w-64 border-r border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-950 hidden md:flex flex-col">
      <div className="h-16 flex items-center px-6 border-b border-gray-200 dark:border-gray-800 font-bold text-lg">
        Enterprise AI
      </div>
      <nav className="flex-1 px-4 py-6 space-y-2">
        <NavItem href="/dashboard" icon={<LayoutDashboard size={20} />} label="Dashboard" />
        <NavItem href="/jobs" icon={<Briefcase size={20} />} label="Jobs" />
        <NavItem href="/resume-screening" icon={<FileText size={20} />} label="Resume Screening" />
        <NavItem href="/knowledge" icon={<BookOpen size={20} />} label="Knowledge Hub" />
        <NavItem href="/meetings" icon={<Video size={20} />} label="Meetings AI" />
        <NavItem href="/onboarding" icon={<Users size={20} />} label="Onboarding" />
        <NavItem href="/meetings" icon={<Video size={20} />} label="Meetings" />
        <NavItem href="/settings" icon={<Settings size={20} />} label="Settings" />
      </nav>
    </aside>
  );
}

function NavItem({ href, icon, label }: { href: string; icon: React.ReactNode; label: string }) {
  return (
    <Link href={href} className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-gray-50 transition-all">
      {icon}
      {label}
    </Link>
  );
}
