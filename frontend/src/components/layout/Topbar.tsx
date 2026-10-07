"use client";

import React, { useState, useRef, useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Menu, LogOut, User as UserIcon, Shield, ChevronDown } from "lucide-react";
import { navItems } from "./Sidebar";

interface TopbarProps {
  onOpenMobile: () => void;
}

export function Topbar({ onOpenMobile }: TopbarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Derive dynamic page title from nav items
  const currentItem = navItems.find(
    (item) => item.href === pathname || (item.href !== "/dashboard" && pathname.startsWith(item.href))
  );
  const pageTitle = currentItem ? currentItem.label : "Security Console";

  // Compute initials
  const initials = user?.full_name
    ? user.full_name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .substring(0, 2)
        .toUpperCase()
    : "JS";

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
    setDropdownOpen(false);
    await logout();
    router.push("/login");
  };

  return (
    <header className="sticky top-0 z-20 h-16 border-b border-border bg-background/80 backdrop-blur-md flex items-center justify-between px-4 sm:px-6">
      {/* Left: Mobile Toggle & Page Title */}
      <div className="flex items-center gap-3">
        <button
          onClick={onOpenMobile}
          className="md:hidden text-muted-foreground hover:text-white p-1.5 rounded-md hover:bg-elevated transition-colors"
          aria-label="Open sidebar navigation"
        >
          <Menu className="w-5 h-5" />
        </button>
        <h1 className="font-mono text-base sm:text-lg font-bold text-white tracking-tight">
          {pageTitle}
        </h1>
      </div>

      {/* Right: Telemetry Badge + Avatar Dropdown */}
      <div className="flex items-center gap-4">
        {/* Quick status pill on larger screens */}
        <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-md border border-border bg-elevated/50 font-mono text-xs text-muted-foreground">
          <Shield className="w-3.5 h-3.5 text-accent-cyan" />
          <span>Threat Engine: <strong className="text-emerald-400 font-normal">Active</strong></span>
        </div>

        {/* Profile Avatar Dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-2 rounded-full p-1 hover:bg-elevated transition-colors focus:outline-none focus:ring-1 focus:ring-primary"
            aria-label="User account menu"
            aria-expanded={dropdownOpen}
          >
            <Avatar className="w-8 h-8 cursor-pointer">
              <AvatarFallback>{initials}</AvatarFallback>
            </Avatar>
            <ChevronDown className="w-3.5 h-3.5 text-muted-foreground hidden sm:block" />
          </button>

          {/* Accessible Dropdown Card */}
          {dropdownOpen && (
            <div className="absolute right-0 mt-2 w-56 rounded-lg border border-border bg-elevated shadow-2xl py-1 text-xs font-mono z-50 animate-in fade-in-50 zoom-in-95">
              {/* User Header */}
              <div className="px-4 py-3 border-b border-border/80">
                <p className="font-semibold text-white truncate">
                  {user?.full_name || "Defense Analyst"}
                </p>
                <p className="text-[11px] text-muted-foreground truncate mt-0.5">
                  {user?.email || "analyst@garuda.defense"}
                </p>
                <span className="inline-block mt-1.5 px-1.5 py-0.5 rounded text-[10px] bg-primary/20 text-accent-cyan border border-primary/30">
                  Role: {user?.role || "user"}
                </span>
              </div>

              {/* Links */}
              <div className="py-1">
                <Link
                  href="/profile"
                  onClick={() => setDropdownOpen(false)}
                  className="flex items-center gap-2 px-4 py-2 text-slate-300 hover:text-white hover:bg-surface transition-colors"
                >
                  <UserIcon className="w-4 h-4 text-muted-foreground" />
                  Account Profile
                </Link>
              </div>

              {/* Logout Action */}
              <div className="pt-1 border-t border-border/80">
                <button
                  onClick={handleLogout}
                  className="flex w-full items-center gap-2 px-4 py-2 text-destructive hover:bg-destructive/10 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  Sign Out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
