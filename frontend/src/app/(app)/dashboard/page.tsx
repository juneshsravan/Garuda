"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { showDevTools } from "@/lib/dev-tools";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { LoadingState, EmptyState, ErrorState } from "@/components/ui/states";
import { dashboardApi, ApiClientError } from "@/lib/api-client";
import { DashboardStatsResponse } from "@/types/dashboard";
import {
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  Activity,
  ArrowRight,
  MessageSquareText,
  Globe,
  QrCode,
  Layers,
  BarChart3,
  TrendingUp,
  Clock,
  Shield,
} from "lucide-react";

export default function DashboardPage() {
  const router = useRouter();
  const [stats, setStats] = useState<DashboardStatsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [devState, setDevState] = useState<"auto" | "loading" | "empty" | "error">("auto");

  const fetchDashboardStats = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await dashboardApi.getStats();
      setStats(data);
    } catch (err: unknown) {
      const msg =
        err instanceof ApiClientError
          ? err.message
          : err instanceof Error
          ? err.message
          : "Failed to load security telemetry.";
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardStats();
  }, [fetchDashboardStats]);

  // Format date string to display label (e.g. "Oct 8" or "10/08")
  const formatDayLabel = (dateStr: string) => {
    try {
      const parts = dateStr.split("-");
      if (parts.length === 3) {
        const d = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
        return d.toLocaleDateString("en-IN", { month: "short", day: "numeric" });
      }
      return dateStr;
    } catch {
      return dateStr;
    }
  };

  const formatRelativeTime = (isoString: string) => {
    try {
      const date = new Date(isoString);
      const diffSec = Math.floor((Date.now() - date.getTime()) / 1000);
      if (diffSec < 60) return "Just now";
      if (diffSec < 3600) return `${Math.floor(diffSec / 60)} mins ago`;
      if (diffSec < 86400) return `${Math.floor(diffSec / 3600)} hours ago`;
      if (diffSec < 172800) return "Yesterday";
      return date.toLocaleDateString("en-IN", { month: "short", day: "numeric" });
    } catch {
      return isoString;
    }
  };

  const getRiskBadgeVariant = (level: string) => {
    switch (level?.toLowerCase()) {
      case "likely_safe":
      case "safe":
        return "safe";
      case "suspicious":
        return "suspicious";
      case "medium":
        return "medium";
      case "high":
        return "high";
      case "critical":
        return "critical";
      default:
        return "unverified";
    }
  };

  // Max daily count for chart scaling
  const maxDailyCount = stats?.scans_per_day
    ? Math.max(1, ...stats.scans_per_day.map((d) => d.count))
    : 1;

  // Active state determination
  const isDevLoading = devState === "loading";
  const isDevEmpty = devState === "empty";
  const isDevError = devState === "error";

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
        <div>
          <span className="font-mono text-xs uppercase text-accent-cyan tracking-wider font-semibold">
            DEFENSE TELEMETRY OVERVIEW
          </span>
          <h2 className="font-mono text-2xl sm:text-3xl font-bold text-white mt-1">
            Security Operations Console
          </h2>
          <p className="text-xs sm:text-sm text-muted-foreground mt-1">
            Consolidated threat intelligence and personal scan metrics.
          </p>
        </div>

        {/* State Toggle for UI Testing — only visible when NEXT_PUBLIC_SHOW_DEV_TOOLS=true */}
        {showDevTools && (
          <div className="flex items-center gap-1.5 p-1 rounded-lg border border-border bg-elevated/40 text-[11px] font-mono self-start sm:self-auto">
            <span className="text-muted-foreground px-2">Dev State:</span>
            <button
              onClick={() => setDevState("auto")}
              className={`px-2.5 py-1 rounded transition-colors ${
                devState === "auto" ? "bg-primary text-white" : "text-slate-400 hover:text-white"
              }`}
            >
              Live
            </button>
            <button
              onClick={() => setDevState("loading")}
              className={`px-2.5 py-1 rounded transition-colors ${
                devState === "loading" ? "bg-primary text-white" : "text-slate-400 hover:text-white"
              }`}
            >
              Loading
            </button>
            <button
              onClick={() => setDevState("empty")}
              className={`px-2.5 py-1 rounded transition-colors ${
                devState === "empty" ? "bg-primary text-white" : "text-slate-400 hover:text-white"
              }`}
            >
              Empty
            </button>
            <button
              onClick={() => setDevState("error")}
              className={`px-2.5 py-1 rounded transition-colors ${
                devState === "error" ? "bg-primary text-white" : "text-slate-400 hover:text-white"
              }`}
            >
              Error
            </button>
          </div>
        )}
      </div>

      {/* State Renderers */}
      {(isLoading || isDevLoading) && (
        <LoadingState
          message="Querying telemetry..."
          description="Fetching personal scan metrics and risk distributions from the detection ledger."
        />
      )}

      {((!isLoading && error && devState === "auto") || isDevError) && (
        <ErrorState
          title="Telemetry Engine Error"
          message={error || "Failed to retrieve metrics from /api/dashboard/stats."}
          details="Ensure backend server is running and your authentication session is valid."
          onRetry={fetchDashboardStats}
        />
      )}

      {(!isLoading && !error && devState === "auto" && stats?.total_scans === 0) || isDevEmpty ? (
        <EmptyState
          title="No Scans Logged Yet"
          description="Your security ledger is empty. Submit a suspicious SMS, URL, or UPI QR code to populate your detection statistics."
          actionLabel="Analyze First Message"
          onAction={() => router.push("/message-analyzer")}
        />
      ) : null}

      {!isLoading && !error && devState === "auto" && stats && stats.total_scans > 0 && (
        <>
          {/* 4 Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* 1. Total Scans */}
            <Card>
              <CardHeader className="p-4 pb-2 flex flex-row items-center justify-between">
                <span className="font-mono text-xs uppercase text-muted-foreground font-semibold">
                  Total Scans
                </span>
                <Activity className="w-4 h-4 text-primary" />
              </CardHeader>
              <CardContent className="p-4 pt-1">
                <div className="font-mono text-3xl font-bold text-white">
                  {stats.total_scans}
                </div>
                <p className="text-[11px] text-muted-foreground mt-1">
                  Evaluated across all vectors
                </p>
              </CardContent>
            </Card>

            {/* 2. Threats Detected (never "Blocked") */}
            <Card className="border-risk-high/30 bg-risk-high/5">
              <CardHeader className="p-4 pb-2 flex flex-row items-center justify-between">
                <span className="font-mono text-xs uppercase text-risk-high font-semibold">
                  Threats Detected
                </span>
                <ShieldAlert className="w-4 h-4 text-risk-high" />
              </CardHeader>
              <CardContent className="p-4 pt-1">
                <div className="font-mono text-3xl font-bold text-risk-high">
                  {stats.threats_detected}
                </div>
                <p className="text-[11px] text-slate-400 mt-1">
                  High &amp; Critical severity
                </p>
              </CardContent>
            </Card>

            {/* 3. Suspicious */}
            <Card className="border-risk-suspicious/30 bg-risk-suspicious/5">
              <CardHeader className="p-4 pb-2 flex flex-row items-center justify-between">
                <span className="font-mono text-xs uppercase text-risk-suspicious font-semibold">
                  Suspicious
                </span>
                <AlertTriangle className="w-4 h-4 text-risk-suspicious" />
              </CardHeader>
              <CardContent className="p-4 pt-1">
                <div className="font-mono text-3xl font-bold text-risk-suspicious">
                  {stats.suspicious}
                </div>
                <p className="text-[11px] text-slate-400 mt-1">
                  Medium &amp; Suspicious vectors
                </p>
              </CardContent>
            </Card>

            {/* 4. Likely Safe (never "Verified Safe") */}
            <Card className="border-risk-safe/30 bg-risk-safe/5">
              <CardHeader className="p-4 pb-2 flex flex-row items-center justify-between">
                <span className="font-mono text-xs uppercase text-risk-safe font-semibold">
                  Likely Safe
                </span>
                <CheckCircle2 className="w-4 h-4 text-risk-safe" />
              </CardHeader>
              <CardContent className="p-4 pt-1">
                <div className="font-mono text-3xl font-bold text-risk-safe">
                  {stats.likely_safe}
                </div>
                <p className="text-[11px] text-slate-400 mt-1">
                  Genuine alerts &amp; advisories
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Telemetry Activity & Risk Distribution Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* 14-Day Activity Histogram (Takes 2 cols) */}
            <div className="lg:col-span-2 rounded-xl border border-border bg-surface p-5 sm:p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-border/80 pb-3">
                <h3 className="font-mono text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-accent-cyan" />
                  14-Day Scan Telemetry
                </h3>
                <span className="text-[11px] font-mono text-muted-foreground">
                  UTC Daily Volume
                </span>
              </div>

              {/* Bar Histogram */}
              <div className="h-44 flex items-end gap-1.5 sm:gap-2 pt-6 pb-2 px-1">
                {stats.scans_per_day.map((day, idx) => {
                  const heightPercent =
                    day.count > 0 ? Math.max(12, Math.round((day.count / maxDailyCount) * 100)) : 4;
                  const isToday = idx === stats.scans_per_day.length - 1;

                  return (
                    <div
                      key={day.date}
                      className="flex-1 flex flex-col items-center gap-1.5 h-full justify-end group relative"
                    >
                      {/* Tooltip on Hover */}
                      <div className="opacity-0 group-hover:opacity-100 transition-opacity absolute -top-8 px-2 py-0.5 rounded bg-elevated border border-slate-700 text-[10px] font-mono text-white whitespace-nowrap pointer-events-none z-10 shadow-lg">
                        {day.date}: {day.count} {day.count === 1 ? "scan" : "scans"}
                      </div>

                      {/* Bar */}
                      <div
                        style={{ height: `${heightPercent}%` }}
                        className={`w-full rounded-t transition-all duration-300 ${
                          day.count > 0
                            ? isToday
                              ? "bg-accent-cyan shadow-sm shadow-cyan-500/50"
                              : "bg-primary/80 hover:bg-primary"
                            : "bg-slate-800/40"
                        }`}
                      />

                      {/* Day Label (Alternating on small screens) */}
                      <span className="text-[9px] sm:text-[10px] font-mono text-muted-foreground truncate w-full text-center">
                        {idx % 2 === 0 || isToday ? formatDayLabel(day.date).split(" ")[1] : ""}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Risk Distribution Breakdown */}
            <div className="rounded-xl border border-border bg-surface p-5 sm:p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-border/80 pb-3">
                <h3 className="font-mono text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-primary" />
                  Risk Distribution
                </h3>
              </div>

              <div className="space-y-3 pt-1">
                {[
                  { key: "critical", label: "Critical", color: "bg-risk-critical text-risk-critical" },
                  { key: "high", label: "High Risk", color: "bg-risk-high text-risk-high" },
                  { key: "medium", label: "Medium Risk", color: "bg-risk-medium text-risk-medium" },
                  { key: "suspicious", label: "Suspicious", color: "bg-risk-suspicious text-risk-suspicious" },
                  { key: "likely_safe", label: "Likely Safe", color: "bg-risk-safe text-risk-safe" },
                ].map(({ key, label, color }) => {
                  const count = stats.risk_distribution[key] || 0;
                  const pct = stats.total_scans > 0 ? Math.round((count / stats.total_scans) * 100) : 0;

                  return (
                    <div key={key} className="space-y-1">
                      <div className="flex items-center justify-between text-xs font-mono">
                        <span className="text-slate-300 flex items-center gap-1.5">
                          <span className={`w-2 h-2 rounded-full ${color.split(" ")[0]}`} />
                          {label}
                        </span>
                        <span className="text-muted-foreground">
                          {count} ({pct}%)
                        </span>
                      </div>
                      <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                        <div
                          style={{ width: `${pct}%` }}
                          className={`h-full rounded-full ${color.split(" ")[0]}`}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Top Threat Categories */}
          {stats.top_categories.length > 0 && (
            <div className="rounded-xl border border-border bg-surface p-5 sm:p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-border/80 pb-3">
                <h3 className="font-mono text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Shield className="w-4 h-4 text-amber-400" />
                  Top Detected Threat Categories
                </h3>
                <span className="text-[11px] font-mono text-muted-foreground">
                  Top 5 Vector Profiles
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {stats.top_categories.map((cat, i) => (
                  <div
                    key={cat.code}
                    className="p-3 rounded-lg border border-border/80 bg-elevated/40 flex items-center justify-between gap-3 text-xs font-mono"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="text-muted-foreground text-[10px]">#{i + 1}</span>
                      <span className="text-slate-200 font-semibold truncate">{cat.label}</span>
                    </div>
                    <Badge variant="default" className="text-[11px] font-mono shrink-0">
                      {cat.count} {cat.count === 1 ? "scan" : "scans"}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Quick Launchers */}
          <div className="rounded-xl border border-border bg-surface p-5 sm:p-6 space-y-4">
            <h3 className="font-mono text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Layers className="w-4 h-4 text-accent-cyan" />
              Launch Active Analysis Engines
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <Link
                href="/message-analyzer"
                className="p-4 rounded-lg border border-border hover:border-slate-500 bg-elevated/40 hover:bg-elevated transition-colors group flex items-start gap-3"
              >
                <div className="p-2 rounded bg-primary/10 text-primary border border-primary/20 group-hover:text-accent-cyan">
                  <MessageSquareText className="w-5 h-5" />
                </div>
                <div className="space-y-1">
                  <h4 className="font-mono text-sm font-semibold text-white">
                    Message Analyzer
                  </h4>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    SMS, WhatsApp, and Telegram phrases in 5 languages.
                  </p>
                </div>
              </Link>

              <Link
                href="/url-analyzer"
                className="p-4 rounded-lg border border-border hover:border-slate-500 bg-elevated/40 hover:bg-elevated transition-colors group flex items-start gap-3"
              >
                <div className="p-2 rounded bg-cyan-500/10 text-accent-cyan border border-cyan-500/20">
                  <Globe className="w-5 h-5" />
                </div>
                <div className="space-y-1">
                  <h4 className="font-mono text-sm font-semibold text-white">
                    URL Heuristics
                  </h4>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    Static brand lookalikes and phishing domain matching.
                  </p>
                </div>
              </Link>

              <Link
                href="/qr-analyzer"
                className="p-4 rounded-lg border border-border hover:border-slate-500 bg-elevated/40 hover:bg-elevated transition-colors group flex items-start gap-3"
              >
                <div className="p-2 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
                  <QrCode className="w-5 h-5" />
                </div>
                <div className="space-y-1">
                  <h4 className="font-mono text-sm font-semibold text-white">
                    QR &amp; UPI Defense
                  </h4>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    Dissect deceptive payment requests and reward QR codes.
                  </p>
                </div>
              </Link>
            </div>
          </div>

          {/* Recent Scans Table */}
          {stats.recent_scans.length > 0 && (
            <div className="rounded-xl border border-border bg-surface overflow-hidden">
              <div className="p-4 sm:px-6 border-b border-border flex items-center justify-between">
                <div>
                  <h3 className="font-mono text-sm font-bold text-white">
                    Recent Scan Telemetry
                  </h3>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Latest threat assessments logged in this workspace session.
                  </p>
                </div>
                <Button asChild variant="outline" size="sm" className="gap-1 font-mono text-xs">
                  <Link href="/history">
                    All History
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </Button>
              </div>

              <div className="divide-y divide-border/60">
                {stats.recent_scans.map((scan) => (
                  <Link
                    key={scan.id}
                    href={`/scan/${scan.id}`}
                    className="p-4 sm:px-6 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs font-mono hover:bg-elevated/50 transition-colors block group"
                  >
                    <div className="space-y-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-slate-400 text-[11px] uppercase font-semibold">
                          [{scan.scan_type}]
                        </span>
                        <span className="text-white group-hover:text-accent-cyan transition-colors font-medium truncate">
                          {scan.preview || `Scan ${scan.id}`}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-4 shrink-0">
                      <Badge variant={getRiskBadgeVariant(scan.risk_level)}>
                        {scan.risk_label}
                      </Badge>
                      <span className="text-muted-foreground text-[11px] flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatRelativeTime(scan.created_at)}
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
