"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { LoadingState, EmptyState, ErrorState } from "@/components/ui/states";
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
} from "lucide-react";

// MOCK: Temporary mock stats for UI demonstration before Chunk 6 API is merged
const MOCK_DASHBOARD_STATS = {
  total_scans: 38,
  threats_detected: 14, // Honest wording: never "Blocked"
  suspicious_scans: 9,
  likely_safe: 15,     // Honest wording: never "Verified Safe"
};

// MOCK: Recent scan items
const MOCK_RECENT_SCANS = [
  {
    id: "scan_01",
    type: "MESSAGE",
    preview: "Electricity disconnection warning from 9000000001...",
    level: "high" as const,
    label: "88 High Risk",
    time: "10 mins ago",
  },
  {
    id: "scan_02",
    type: "QR / UPI",
    preview: "Fake KBC lottery ₹500 cashback claim QR...",
    level: "critical" as const,
    label: "94 Critical Risk",
    time: "2 hours ago",
  },
  {
    id: "scan_03",
    type: "URL",
    preview: "https://sbi.co.in/portal/web/home",
    level: "safe" as const,
    label: "14 Likely Safe",
    time: "Yesterday",
  },
  {
    id: "scan_04",
    type: "MESSAGE",
    preview: "Your OTP for Rs 1,450.00 at AMAZON INDIA...",
    level: "safe" as const,
    label: "08 Likely Safe",
    time: "2 days ago",
  },
];

export default function DashboardPage() {
  const [viewState, setViewState] = useState<"normal" | "loading" | "empty" | "error">("normal");

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

        {/* State Toggle for UI Testing */}
        <div className="flex items-center gap-1.5 p-1 rounded-lg border border-border bg-elevated/40 text-[11px] font-mono self-start sm:self-auto">
          <span className="text-muted-foreground px-2">Preview State:</span>
          <button
            onClick={() => setViewState("normal")}
            className={`px-2.5 py-1 rounded transition-colors ${
              viewState === "normal" ? "bg-primary text-white" : "text-slate-400 hover:text-white"
            }`}
          >
            Normal
          </button>
          <button
            onClick={() => setViewState("loading")}
            className={`px-2.5 py-1 rounded transition-colors ${
              viewState === "loading" ? "bg-primary text-white" : "text-slate-400 hover:text-white"
            }`}
          >
            Loading
          </button>
          <button
            onClick={() => setViewState("empty")}
            className={`px-2.5 py-1 rounded transition-colors ${
              viewState === "empty" ? "bg-primary text-white" : "text-slate-400 hover:text-white"
            }`}
          >
            Empty
          </button>
          <button
            onClick={() => setViewState("error")}
            className={`px-2.5 py-1 rounded transition-colors ${
              viewState === "error" ? "bg-primary text-white" : "text-slate-400 hover:text-white"
            }`}
          >
            Error
          </button>
        </div>
      </div>

      {/* State Renderers */}
      {viewState === "loading" && (
        <LoadingState
          message="Querying telemetry..."
          description="Fetching personal scan distribution from Supabase PostgreSQL."
        />
      )}

      {viewState === "error" && (
        <ErrorState
          title="Telemetry Engine Offline"
          message="Failed to retrieve analytics from /api/dashboard/stats."
          details="Error code: DB_POOL_TIMEOUT - Backend service pending Chunk 6 integration."
          onRetry={() => setViewState("normal")}
        />
      )}

      {viewState === "empty" && (
        <EmptyState
          title="No Scans Logged Yet"
          description="Your security ledger is empty. Submit a suspicious SMS, URL, or UPI QR code to populate your detection statistics."
          actionLabel="Analyze First Message"
          onAction={() => setViewState("normal")}
        />
      )}

      {viewState === "normal" && (
        <>
          {/* 4 Stat Cards */}
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
                  {MOCK_DASHBOARD_STATS.total_scans}
                </div>
                <p className="text-[11px] text-muted-foreground mt-1">
                  Synchronous evaluations
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
                  {MOCK_DASHBOARD_STATS.threats_detected}
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
                  {MOCK_DASHBOARD_STATS.suspicious_scans}
                </div>
                <p className="text-[11px] text-slate-400 mt-1">
                  Medium &amp; unverified vectors
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
                  {MOCK_DASHBOARD_STATS.likely_safe}
                </div>
                <p className="text-[11px] text-slate-400 mt-1">
                  Genuine bank / delivery alerts
                </p>
              </CardContent>
            </Card>
          </div>

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
              {MOCK_RECENT_SCANS.map((scan) => (
                <div
                  key={scan.id}
                  className="p-4 sm:px-6 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs font-mono hover:bg-elevated/30 transition-colors"
                >
                  <div className="space-y-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-slate-400 text-[11px] uppercase">
                        [{scan.type}]
                      </span>
                      <span className="text-white font-medium truncate">
                        {scan.preview}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 shrink-0">
                    <Badge variant={scan.level}>{scan.label}</Badge>
                    <span className="text-muted-foreground text-[11px]">
                      {scan.time}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
