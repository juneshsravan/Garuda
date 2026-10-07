"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAuth } from "@/lib/auth";
import { showDevTools } from "@/lib/dev-tools";
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
  Eye,
  EyeOff,
  X,
} from "lucide-react";
import Link from "next/link";

// ─── Change Password Zod Schema ───────────────────────────────────────────────
const changePasswordSchema = z
  .object({
    current_password: z.string().min(1, "Current password is required."),
    new_password: z.string().min(8, "New password must be at least 8 characters."),
    confirm_password: z.string().min(1, "Please confirm your new password."),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: "Passwords do not match.",
    path: ["confirm_password"],
  });

type ChangePasswordFormValues = z.infer<typeof changePasswordSchema>;

// ─── Change Password Modal ────────────────────────────────────────────────────
function ChangePasswordModal({ onClose }: { onClose: () => void }) {
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ChangePasswordFormValues>({
    resolver: zodResolver(changePasswordSchema),
  });

  const onSubmit = async (data: ChangePasswordFormValues) => {
    setApiError(null);
    setSuccessMsg(null);

    // MOCK success response — replace with real POST /api/auth/change-password once Junesh's endpoint is merged
    await new Promise((resolve) => setTimeout(resolve, 700));
    /* Real call (uncomment when backend endpoint is merged):
    const res = await fetch("/api/auth/change-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        current_password: data.current_password,
        new_password: data.new_password,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      const detail = err?.detail;
      if (Array.isArray(detail)) {
        setApiError(detail.map((d: { msg: string }) => d.msg).join(" "));
      } else {
        setApiError(err?.message || "Failed to change password.");
      }
      return;
    }
    */

    // MOCK: simulate successful response
    setSuccessMsg("Password changed successfully.");
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="change-password-title"
    >
      <div className="relative w-full max-w-md rounded-2xl border border-border bg-surface p-6 shadow-2xl space-y-5">
        {/* Modal Header */}
        <div className="flex items-center justify-between">
          <h2
            id="change-password-title"
            className="font-mono text-base font-bold text-white flex items-center gap-2"
          >
            <KeyRound className="w-4 h-4 text-accent-cyan" />
            Change Password
          </h2>
          <button
            onClick={onClose}
            className="p-1 rounded text-muted-foreground hover:text-white hover:bg-elevated transition-colors"
            aria-label="Close dialog"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {successMsg ? (
          <div className="p-4 rounded-lg border border-risk-safe/40 bg-risk-safe/10 text-xs font-mono text-risk-safe flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            {successMsg}
          </div>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
            {/* API-level error */}
            {apiError && (
              <div className="p-3 rounded-lg border border-destructive/40 bg-destructive/10 text-xs font-mono text-destructive">
                {apiError}
              </div>
            )}

            {/* Current Password */}
            <div className="space-y-1">
              <label
                htmlFor="current_password"
                className="block text-xs font-mono font-semibold text-slate-300 uppercase"
              >
                Current Password
              </label>
              <div className="relative">
                <input
                  id="current_password"
                  type={showCurrent ? "text" : "password"}
                  {...register("current_password")}
                  className={`w-full rounded-md border bg-input-bg px-3 pr-10 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 transition-colors font-mono ${
                    errors.current_password
                      ? "border-destructive focus:ring-destructive"
                      : "border-input focus:border-primary focus:ring-primary"
                  }`}
                  placeholder="Enter current password"
                />
                <button
                  type="button"
                  onClick={() => setShowCurrent((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-white"
                  aria-label={showCurrent ? "Hide password" : "Show password"}
                >
                  {showCurrent ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {errors.current_password && (
                <p className="text-[11px] text-destructive font-mono">
                  {errors.current_password.message}
                </p>
              )}
            </div>

            {/* New Password */}
            <div className="space-y-1">
              <label
                htmlFor="new_password"
                className="block text-xs font-mono font-semibold text-slate-300 uppercase"
              >
                New Password
              </label>
              <div className="relative">
                <input
                  id="new_password"
                  type={showNew ? "text" : "password"}
                  {...register("new_password")}
                  className={`w-full rounded-md border bg-input-bg px-3 pr-10 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 transition-colors font-mono ${
                    errors.new_password
                      ? "border-destructive focus:ring-destructive"
                      : "border-input focus:border-primary focus:ring-primary"
                  }`}
                  placeholder="At least 8 characters"
                />
                <button
                  type="button"
                  onClick={() => setShowNew((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-white"
                  aria-label={showNew ? "Hide password" : "Show password"}
                >
                  {showNew ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {errors.new_password && (
                <p className="text-[11px] text-destructive font-mono">
                  {errors.new_password.message}
                </p>
              )}
            </div>

            {/* Confirm New Password */}
            <div className="space-y-1">
              <label
                htmlFor="confirm_password"
                className="block text-xs font-mono font-semibold text-slate-300 uppercase"
              >
                Confirm New Password
              </label>
              <div className="relative">
                <input
                  id="confirm_password"
                  type={showConfirm ? "text" : "password"}
                  {...register("confirm_password")}
                  className={`w-full rounded-md border bg-input-bg px-3 pr-10 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 transition-colors font-mono ${
                    errors.confirm_password
                      ? "border-destructive focus:ring-destructive"
                      : "border-input focus:border-primary focus:ring-primary"
                  }`}
                  placeholder="Repeat new password"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirm((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-white"
                  aria-label={showConfirm ? "Hide password" : "Show password"}
                >
                  {showConfirm ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {errors.confirm_password && (
                <p className="text-[11px] text-destructive font-mono">
                  {errors.confirm_password.message}
                </p>
              )}
            </div>

            <div className="flex items-center justify-end gap-3 pt-1">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={onClose}
                className="font-mono text-xs"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                size="sm"
                disabled={isSubmitting}
                className="font-mono text-xs gap-1.5"
              >
                {isSubmitting ? "Updating…" : "Update Password"}
              </Button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

export default function ProfilePage() {
  const router = useRouter();
  const { user, logout } = useAuth();
  const [state, setState] = useState<"ready" | "loading" | "empty" | "error">("ready");
  const [showChangePassword, setShowChangePassword] = useState(false);

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
      {/* Change Password Modal */}
      {showChangePassword && (
        <ChangePasswordModal onClose={() => setShowChangePassword(false)} />
      )}

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
            Manage your account credentials and privacy settings.
          </p>
        </div>

        {/* State Toggle — only visible when NEXT_PUBLIC_SHOW_DEV_TOOLS=true */}
        {showDevTools && (
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
        )}
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
                <Button
                  variant="outline"
                  size="sm"
                  className="text-xs"
                  onClick={() => setShowChangePassword(true)}
                >
                  Change Password
                </Button>
              </div>
            </Card>

            <Card className="p-5 space-y-3">
              <h4 className="font-bold text-white uppercase text-xs flex items-center gap-2">
                <Database className="w-4 h-4 text-primary" />
                Data Retention &amp; Privacy
              </h4>
              <p className="text-muted-foreground leading-relaxed">
                Your scans and reports are private to your account. Other users
                can&apos;t see them.
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
