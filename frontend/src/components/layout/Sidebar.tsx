"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { GarudaLogo } from "@/components/brand/GarudaLogo";
import {
  LayoutDashboard,
  MessageSquareText,
  Globe,
  QrCode,
  History,
  FileCheck2,
  User,
  Shield,
  X,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

export const navItems: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Message Analyzer", href: "/message-analyzer", icon: MessageSquareText },
  { label: "URL Analyzer", href: "/url-analyzer", icon: Globe },
  { label: "QR Analyzer", href: "/qr-analyzer", icon: QrCode },
  { label: "History", href: "/history", icon: History },
  { label: "Reports", href: "/reports", icon: FileCheck2 },
  { label: "Profile", href: "/profile", icon: User },
];

interface SidebarProps {
  mobileOpen?: boolean;
  onCloseMobile?: () => void;
}

export function Sidebar({ mobileOpen = false, onCloseMobile }: SidebarProps) {
  const pathname = usePathname();

  const sidebarContent = (
    <div className="flex flex-col h-full bg-surface border-r border-border select-none">
      {/* Brand Header */}
      <div className="h-16 flex items-center justify-between px-5 border-b border-border">
        <Link href="/dashboard" className="flex items-center gap-2">
          <GarudaLogo size={30} showWordmark={true} subtitle="CONSOLE" />
        </Link>
        {onCloseMobile && (
          <button
            onClick={onCloseMobile}
            className="md:hidden text-muted-foreground hover:text-white p-1 rounded"
            aria-label="Close menu"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="px-3 mb-2 font-mono text-[10px] uppercase tracking-wider text-muted-foreground font-semibold">
          Defense Modules
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));

          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onCloseMobile}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-mono font-medium transition-colors ${
                isActive
                  ? "bg-primary/15 text-white border-l-2 border-primary"
                  : "text-muted-foreground hover:text-white hover:bg-elevated"
              }`}
            >
              <Icon
                className={`w-4 h-4 shrink-0 ${
                  isActive ? "text-accent-cyan" : "text-muted-foreground"
                }`}
              />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Footer System Status - MOCK: Placeholder for GET /api/health status check */}
      <div className="p-4 border-t border-border bg-background/50 space-y-2">
        <div className="flex items-center justify-between text-[11px] font-mono text-muted-foreground">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Threat Engine: Active
          </span>
          <span className="text-slate-400">v2.0</span>
        </div>
        <div className="text-[10px] font-mono text-slate-500">
          Access controlled
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Persistent Sidebar */}
      <aside className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0 z-30">
        {sidebarContent}
      </aside>

      {/* Mobile Drawer Backdrop & Drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex">
          <div
            className="fixed inset-0 bg-background/80 backdrop-blur-sm"
            onClick={onCloseMobile}
          />
          <div className="relative flex-1 flex flex-col max-w-xs w-full">
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  );
}
