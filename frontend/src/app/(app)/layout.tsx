"use client";

import React, { useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import { useAuth } from "@/lib/auth";
import { useRouter } from "next/navigation";
import { LoadingState } from "@/components/ui/states";

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Route guard: if logged out, redirect to /login
  if (!isLoading && !user) {
    if (typeof window !== "undefined") {
      router.push("/login");
    }
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <LoadingState message="Checking security authorization..." />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      {/* Sidebar (Desktop persistent, Mobile drawer) */}
      <React.Suspense fallback={<div className="hidden md:flex md:w-64 md:fixed md:inset-y-0 bg-surface border-r border-border" />}>
        <Sidebar
          mobileOpen={mobileMenuOpen}
          onCloseMobile={() => setMobileMenuOpen(false)}
        />
      </React.Suspense>

      {/* Main Content Area */}
      <div className="md:pl-64 flex flex-col flex-1">
        <React.Suspense fallback={<div className="h-14 border-b border-border bg-surface" />}>
          <Topbar onOpenMobile={() => setMobileMenuOpen(true)} />
        </React.Suspense>
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
