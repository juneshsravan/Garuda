"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { LoadingState, EmptyState, ErrorState } from "@/components/ui/states";
import {
  User as UserIcon,
  Mail,
  Shield,
  KeyRound,
  LogOut,
  CheckCircle2,
  AlertCircle,
  Database,
} from "lucide-react";
import Link from "next/link";

export default function ProfilePage() {
  const router = useRouter();
  const { user, logout } = useAuth();
  const [state, setState] = useState<"ready" | "loading" | "empty" | "error">("ready");

  const initials = user?.full_name
    ? user.full_name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .substring(0, 2)
        .toUpperCase()
    : "DA";

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  return (
    <div className="space-y-8 max-w-4xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
        <div>
          <span className="font-mono text-xs uppercase text-primary tracking-wider font-semibold">
            DEFENSE CREDENTIALS
          </span>
          <h2 className="font-mono text-2xl sm:text-3xl font-bold text-white mt-1 flex items-center gap-2">
            <UserIcon className="w-6 h-6 text-primary" />
            Security Profile &amp; Preferences
          </h2>
          <p className="text-xs sm:text-sm text-muted-foreground mt-1">
            Manage your account telemetry, authentication keys, and privacy parameters.
          </p>
        </div>

        {/* State Toggle */}
        <div className="flex items-center gap-1.5 p-1 rounded-lg border border-border bg-elevated/40 text-[11px] font-mono self-start sm:self-auto">
          <span className="text-muted-foreground px-2">State:</span>
          <button
            onClick={() => setState("ready")}
            className={`px-2 py-0.5 rounded ${state === "ready" ? "bg-primary text-white" : "text-slate-400"}`}
          >
            Normal
          </button>
          <button
            onClick={() => setState("loading")}
            className={`px-2 py-0.5 rounded ${state === "loading" ? "bg-primary text-white" : "text-slate-400"}`}
          >
            Loading
          </button>
          <button
            onClick={() => setState("empty")}
            className={`px-2 py-0.5 rounded ${state === "empty" ? "bg-primary text-white" : "text-slate-400"}`}
          >
            Empty
          </button>
          <button
            onClick={() => setState("error")}
            className={`px-2 py-0.5 rounded ${state === "error" ? "bg-primary text-white" : "text-slate-400"}`}
          >
            Error
          </button>
        </div>
      </div>

      {state === "loading" && (
        <LoadingState
          message="Querying User Security Record..."
          description="Fetching session metadata from GET /api/auth/me."
        />
      )}

      {state === "error" && (
        <ErrorState
          title="Profile Session Desynchronized"
          message="Failed to retrieve account details."
          details="Token expired or backend auth service unavailable."
          onRetry={() => setState("ready")}
        />
      )}

      {state === "empty" && (
        <EmptyState
          title="No Profile Record Found"
          description="Your session has no active credentials."
          actionLabel="Return to Sign In"
          onAction={() => router.push("/login")}
        />
      )}

      {state === "ready" && (
        <div className="space-y-6">
          {/* User Summary Card */}
          <Card className="p-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
              <div className="flex items-center gap-4">
                <Avatar className="w-16 h-16 border-2 border-primary/30">
                  <AvatarFallback className="text-lg">{initials}</AvatarFallback>
                </Avatar>
                <div className="space-y-1">
                  <h3 className="font-mono text-lg font-bold text-white">
                    {user?.full_name || "Defense Analyst"}
                  </h3>
                  <p className="text-xs text-muted-foreground font-mono flex items-center gap-1.5">
                    <Mail className="w-3.5 h-3.5 text-slate-400" />
                    {user?.email || "analyst@garuda.defense"}
                  </p>
                  <div className="pt-1 flex items-center gap-2">
                    <Badge variant="cyan" className="text-[10px]">
                      Role: {user?.role || "user"}
                    </Badge>
                    {user?.email_verified_at ? (
                      <Badge variant="safe" className="text-[10px] gap-1">
                        <CheckCircle2 className="w-3 h-3" />
                        Verified Email
                      </Badge>
                    ) : (
                      <Badge variant="suspicious" className="text-[10px] gap-1">
                        <AlertCircle className="w-3 h-3" />
                        Unverified Email
                      </Badge>
                    )}
                  </div>
                </div>
              </div>

              <div>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={handleLogout}
                  className="gap-2 font-mono text-xs"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  Sign Out
                </Button>
              </div>
            </div>
          </Card>

          {/* Security & Cryptographic Posture */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
            <Card className="p-5 space-y-3">
              <h4 className="font-bold text-white uppercase text-xs flex items-center gap-2">
                <KeyRound className="w-4 h-4 text-accent-cyan" />
                Password &amp; Encryption
              </h4>
              <p className="text-muted-foreground leading-relaxed">
                Credentials protected via <strong>Argon2id</strong> with memory cost parameters. We never store reversible plain text.
              </p>
              <div className="pt-2">
                <Button variant="outline" size="sm" className="text-xs">
                  Change Password
                </Button>
              </div>
            </Card>

            <Card className="p-5 space-y-3">
              <h4 className="font-bold text-white uppercase text-xs flex items-center gap-2">
                <Database className="w-4 h-4 text-primary" />
                Data Retention &amp; Supabase RLS
              </h4>
              <p className="text-muted-foreground leading-relaxed">
                Your threat records are bounded by Row-Level Security in Supabase (Mumbai). No other user or API client can read your telemetry.
              </p>
              <div className="pt-2">
                <Link
                  href="/privacy"
                  className="text-xs text-primary hover:text-accent-cyan underline"
                >
                  Review Privacy Policy →
                </Link>
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
