"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import {
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  FileCheck2,
  ArrowLeft,
  Copy,
  Check,
  ExternalLink,
  Info,
  Clock,
  Terminal,
  ShieldCheck,
  Share2,
} from "lucide-react";

// MOCK: Detailed scan dossiers following docs/ARCHITECTURE.md Sections 6 and 7
interface ThreatIndicator {
  code: string;
  label: string;
  severity: "high" | "medium" | "critical" | "suspicious";
  weight: number;
  evidence: string;
}

interface LegitimacySignal {
  code: string;
  label: string;
  weight: number;
  evidence: string;
}

interface ScanDetailData {
  id: string;
  scan_type: "message" | "url" | "qr";
  created_at: string;
  sha256: string;
  raw_input: string;
  risk: {
    score: number;
    level: "safe" | "suspicious" | "medium" | "high" | "critical";
    label: string;
  };
  confidence: number;
  verification_status: string;
  category: {
    code: string;
    label: string;
  };
  summary: string;
  indicators: ThreatIndicator[];
  legitimacy_signals: LegitimacySignal[];
  recommendations: string[];
  verify_steps: string[];
  intel_status: { source: string; status: string }[];
  engine_version: string;
}

const MOCK_SCANS_DATABASE: Record<string, ScanDetailData> = {
  scan_101: {
    id: "scan_101",
    scan_type: "qr",
    created_at: "Today, 14:22",
    sha256: "7d4a98e21f6bc301a24d5e89bf234c9192837482a1e0b82f0198c3948e71b891",
    raw_input:
      "Congratulations! You won ₹500 cashback. Scan this QR immediately to claim your reward into bank account: upi://pay?pa=claim.reward92@okaxis&pn=CashDesk&am=500",
    risk: {
      score: 81,
      level: "high",
      label: "81 High Risk",
    },
    confidence: 0.89,
    verification_status: "unverified",
    category: {
      code: "qr_reward_scam",
      label: "Potential QR / Reward Scam",
    },
    summary:
      "Built only from the detected signals below: unprompted monetary incentive combined with immediate action pressure and reversed UPI payment collect vector.",
    indicators: [
      {
        code: "FIN_UNEXPECTED_REWARD",
        label: "Unexpected monetary reward lure",
        severity: "high",
        weight: 0.35,
        evidence: "You won ₹500 cashback",
      },
      {
        code: "URG_IMMEDIATE_ACTION",
        label: "Artificial temporal pressure coercion",
        severity: "medium",
        weight: 0.25,
        evidence: "immediately to claim",
      },
      {
        code: "UPI_SCAN_TO_RECEIVE",
        label: "Reversed UPI collect vector (claim money via payment request)",
        severity: "high",
        weight: 0.3,
        evidence: "Scan this QR immediately to claim your reward into bank account",
      },
    ],
    legitimacy_signals: [],
    recommendations: [
      "Do NOT scan the QR code or tap the payment URI",
      "Do NOT enter your UPI PIN (receiving money never requires a PIN)",
      "Do NOT share OTP or passwords with unverified representatives",
    ],
    verify_steps: [
      "Check your genuine banking app or official reward portal directly",
      "Verify the claimed merchant through the official registered app",
      "Remember: in UPI protocol, scanning a QR or entering a PIN only DEBITS your account",
    ],
    intel_status: [
      { source: "garuda_blocklists", status: "not_found" },
      { source: "open_threat_intel", status: "not_found" },
    ],
    engine_version: "2.0.0",
  },
  scan_102: {
    id: "scan_102",
    scan_type: "message",
    created_at: "Today, 11:05",
    sha256: "b42e71881a29304192fc01847162983749281a8b928374198273849182736451",
    raw_input:
      "Electricity Power will be disconnected tonight 9:30 PM due to unpaid bill. Call electricity officer immediately: 9876543210 to update bill.",
    risk: {
      score: 88,
      level: "high",
      label: "88 High Risk",
    },
    confidence: 0.92,
    verification_status: "unverified",
    category: {
      code: "utility_impersonation",
      label: "Utility Impersonation Coercion",
    },
    summary:
      "Synthesized from artificial utility power disconnection deadline and personal mobile redirection for immediate extortion.",
    indicators: [
      {
        code: "UTL_DISCONNECT_THREAT",
        label: "Service disconnection threat pressure",
        severity: "high",
        weight: 0.4,
        evidence: "Power will be disconnected tonight 9:30 PM",
      },
      {
        code: "CONTACT_PERSONAL_PHONE",
        label: "Redirection to personal mobile number instead of utility desk",
        severity: "high",
        weight: 0.35,
        evidence: "Call electricity officer immediately: 9876543210",
      },
    ],
    legitimacy_signals: [],
    recommendations: [
      "Do NOT call the personal mobile number provided in the message",
      "Do NOT download remote access applications (AnyDesk, TeamViewer)",
      "Do NOT make direct payments via UPI to personal VPAs",
    ],
    verify_steps: [
      "Open your state electricity board portal directly in your browser",
      "Check your consumer number payment history on the official utility bill",
      "Call the registered customer helpline listed on your physical bill",
    ],
    intel_status: [{ source: "garuda_blocklists", status: "not_found" }],
    engine_version: "2.0.0",
  },
  scan_104: {
    id: "scan_104",
    scan_type: "message",
    created_at: "Oct 05, 18:40",
    sha256: "9812739481928374829102938475618293048192837461524354657483920192",
    raw_input:
      "Your OTP for transaction of Rs 1,450.00 at AMAZON INDIA is 482910. Valid for 10 mins. Bank NEVER calls or sends SMS asking for OTP. Do NOT share OTP with anyone.",
    risk: {
      score: 8,
      level: "safe",
      label: "8 Likely Safe",
    },
    confidence: 0.95,
    verification_status: "unverified",
    category: {
      code: "legitimate_transaction_otp",
      label: "Standard Transaction OTP",
    },
    summary:
      "Built only from detected signals: carries standard transaction parameters, masked details, and official bank safety warning advisory.",
    indicators: [],
    legitimacy_signals: [
      {
        code: "LEGIT_BANK_ADVISORY",
        label: "Standard proactive bank security warning",
        weight: 0.5,
        evidence: "Bank NEVER calls or sends SMS asking for OTP",
      },
      {
        code: "LEGIT_MASKED_ACCOUNT",
        label: "Specific transaction merchant and amount without credential demand",
        weight: 0.4,
        evidence: "transaction of Rs 1,450.00 at AMAZON INDIA",
      },
    ],
    recommendations: [
      "Keep this OTP private — do not share with callers claiming to be bank staff",
      "Confirm the amount (Rs 1,450.00) matches your current active checkout",
    ],
    verify_steps: [
      "Check that you initiated this transaction yourself on Amazon India",
      "If you did not initiate this transaction, immediately freeze your card in your banking app",
    ],
    intel_status: [{ source: "garuda_blocklists", status: "not_found" }],
    engine_version: "2.0.0",
  },
};

// Fallback generator for any arbitrary scan ID
function getScanData(id: string): ScanDetailData {
  if (MOCK_SCANS_DATABASE[id]) {
    return MOCK_SCANS_DATABASE[id];
  }
  // MOCK: Generate consistent mock scan for unseeded IDs
  return {
    ...MOCK_SCANS_DATABASE.scan_101,
    id,
    created_at: "Recent Scan",
  };
}

function ScanDetailContent() {
  const params = useParams();
  const id = (params?.id as string) || "scan_101";
  const scan = getScanData(id);
  const [copied, setCopied] = useState(false);

  const handleCopyInput = () => {
    navigator.clipboard.writeText(scan.raw_input);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Circular gauge calculations
  const radius = 54;
  const strokeWidth = 8;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (scan.risk.score / 100) * circumference;

  const getScoreColor = (score: number) => {
    if (score <= 24) return "#34D399"; // safe (Likely Safe)
    if (score <= 44) return "#FBBF24"; // suspicious
    if (score <= 64) return "#F59E0B"; // medium
    if (score <= 99) return "#F97316"; // high
    return "#EF4444"; // critical
  };

  const scoreColor = getScoreColor(scan.risk.score);

  return (
    <div className="space-y-6 pb-12 max-w-5xl mx-auto">
      {/* Top Navigation & Breadcrumbs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-4">
        <div className="flex items-center gap-3">
          <Button asChild variant="outline" size="sm" className="gap-1.5 font-mono text-xs">
            <Link href="/history">
              <ArrowLeft className="w-3.5 h-3.5" />
              History Ledger
            </Link>
          </Button>
          <div className="h-4 w-px bg-border" />
          <span className="font-mono text-xs text-muted-foreground uppercase">
            SCAN DOSSIER: <span className="text-white font-semibold">{scan.id}</span>
          </span>
        </div>

        <div className="flex items-center gap-2">
          <Button asChild size="sm" className="bg-purple-600 hover:bg-purple-700 text-white gap-1.5 font-mono text-xs">
            <Link href={`/reports/new?scan_id=${scan.id}`}>
              <FileCheck2 className="w-3.5 h-3.5" />
              Report this Threat
            </Link>
          </Button>
        </div>
      </div>

      {/* Main Verdict & Gauge Hero Section */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        {/* Risk Gauge Panel (5 cols) */}
        <div className="md:col-span-5 rounded-xl border border-border bg-surface p-6 flex flex-col items-center justify-center text-center relative overflow-hidden">
          <div className="absolute top-3 left-4 text-[10px] font-mono text-muted-foreground uppercase">
            CALCULATED RISK SCORE
          </div>

          <div className="relative my-4 flex items-center justify-center">
            {/* SVG Circular Progress Gauge */}
            <svg width="140" height="140" className="transform -rotate-90">
              <circle
                cx="70"
                cy="70"
                r={radius}
                stroke="rgba(148, 163, 184, 0.12)"
                strokeWidth={strokeWidth}
                fill="transparent"
              />
              <circle
                cx="70"
                cy="70"
                r={radius}
                stroke={scoreColor}
                strokeWidth={strokeWidth}
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
                fill="transparent"
                className="transition-all duration-1000 ease-out"
              />
            </svg>

            {/* Score Content in Center */}
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="font-mono text-4xl sm:text-5xl font-extrabold text-white tracking-tight">
                {scan.risk.score}
              </span>
              <span className="font-mono text-[11px] text-muted-foreground">
                / 100
              </span>
            </div>
          </div>

          <div className="space-y-1 mt-1">
            <Badge variant={scan.risk.level} className="text-xs px-3 py-1 font-mono">
              {scan.risk.label}
            </Badge>
            <div className="text-[11px] font-mono text-muted-foreground pt-2">
              Confidence: <span className="text-slate-200 font-semibold">{Math.round(scan.confidence * 100)}%</span>
              {" · "}
              Status: <span className="text-slate-300 capitalize">{scan.verification_status}</span>
            </div>
          </div>
        </div>

        {/* Classification & Summary Panel (7 cols) */}
        <div className="md:col-span-7 rounded-xl border border-border bg-surface p-6 flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between text-[11px] font-mono text-muted-foreground uppercase mb-2">
              <span>DETECTED CLASSIFICATION</span>
              <span>ENGINE {scan.engine_version}</span>
            </div>
            <h3 className="text-xl font-bold text-white flex items-center gap-2">
              {scan.risk.level === "safe" ? (
                <ShieldCheck className="w-5 h-5 text-risk-safe shrink-0" />
              ) : (
                <AlertTriangle className="w-5 h-5 text-risk-high shrink-0" />
              )}
              {scan.category.label}
            </h3>
            <span className="text-xs font-mono text-accent-cyan block mt-0.5">
              [{scan.category.code}]
            </span>

            <div className="mt-4 p-3.5 rounded-lg border border-border/80 bg-background/60">
              <span className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">
                EXPLANATION SUMMARY (GROUNDED IN INPUT SIGNALS)
              </span>
              <p className="text-xs sm:text-sm text-slate-200 leading-relaxed font-sans">
                {scan.summary}
              </p>
            </div>
          </div>

          <div className="pt-2 border-t border-border flex flex-wrap items-center justify-between gap-2 text-[11px] font-mono text-muted-foreground">
            <span>Vector: <span className="text-white capitalize">[{scan.scan_type}]</span></span>
            <span>Recorded: <span className="text-white">{scan.created_at}</span></span>
            <span className="truncate max-w-[200px]" title={scan.sha256}>
              SHA-256: {scan.sha256.substring(0, 12)}...
            </span>
          </div>
        </div>
      </div>

      {/* Raw Input Telemetry Box */}
      <Card className="border-border bg-surface overflow-hidden">
        <CardHeader className="p-4 bg-elevated/40 border-b border-border flex flex-row items-center justify-between">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-primary" />
            <CardTitle className="font-mono text-xs uppercase text-slate-300">
              Scanned Input Telemetry
            </CardTitle>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleCopyInput}
            className="h-7 text-xs font-mono text-muted-foreground hover:text-white"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 mr-1 text-emerald-400" />
                Copied
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5 mr-1" />
                Copy Telemetry
              </>
            )}
          </Button>
        </CardHeader>
        <CardContent className="p-4 bg-[#070B14]">
          <pre className="font-mono text-xs text-slate-200 whitespace-pre-wrap break-all leading-relaxed">
            {scan.raw_input}
          </pre>
        </CardContent>
      </Card>

      {/* Explainable Risk Signals: Indicators vs Legitimacy */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Threat Indicators Card */}
        <Card className="border-border bg-surface">
          <CardHeader className="p-4 pb-3 border-b border-border flex flex-row items-center justify-between">
            <div className="space-y-0.5">
              <CardTitle className="font-mono text-xs uppercase text-white flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-risk-high" />
                Risk Indicators ({scan.indicators.length})
              </CardTitle>
              <p className="text-[11px] text-muted-foreground font-mono">
                Noisy-OR independent probabilistic weights
              </p>
            </div>
          </CardHeader>
          <CardContent className="p-4 divide-y divide-border/60">
            {scan.indicators.length === 0 ? (
              <div className="py-6 text-center text-xs font-mono text-muted-foreground">
                No hostile threat indicators were isolated in this input.
              </div>
            ) : (
              scan.indicators.map((ind, idx) => (
                <div key={idx} className="py-3 first:pt-0 last:pb-0 space-y-1.5 text-xs font-mono">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-white">{ind.code}</span>
                    <div className="flex items-center gap-2">
                      <Badge variant={ind.severity} className="text-[10px] py-0 px-1.5 uppercase">
                        {ind.severity}
                      </Badge>
                      <span className="text-[11px] text-accent-cyan font-bold">
                        +{Math.round(ind.weight * 100)}%
                      </span>
                    </div>
                  </div>
                  <p className="text-slate-300 text-[11px]">{ind.label}</p>
                  <div className="text-muted-foreground text-[11px] bg-background/50 p-2 rounded border border-border/60">
                    Evidence: <span className="text-amber-300 font-sans">&ldquo;{ind.evidence}&rdquo;</span>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        {/* Legitimacy Signals Card */}
        <Card className="border-border bg-surface">
          <CardHeader className="p-4 pb-3 border-b border-border flex flex-row items-center justify-between">
            <div className="space-y-0.5">
              <CardTitle className="font-mono text-xs uppercase text-white flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-risk-safe" />
                Legitimacy Signals ({scan.legitimacy_signals.length})
              </CardTitle>
              <p className="text-[11px] text-muted-foreground font-mono">
                Mitigating patterns reducing composite risk
              </p>
            </div>
          </CardHeader>
          <CardContent className="p-4 divide-y divide-border/60">
            {scan.legitimacy_signals.length === 0 ? (
              <div className="py-6 text-center text-xs font-mono text-muted-foreground space-y-2">
                <p>No verified legitimacy signals isolated.</p>
                <p className="text-[10px] text-slate-500 max-w-xs mx-auto">
                  Anti-gaming rule: high-severity threat indicators suppress legitimacy discounts automatically.
                </p>
              </div>
            ) : (
              scan.legitimacy_signals.map((sig, idx) => (
                <div key={idx} className="py-3 first:pt-0 last:pb-0 space-y-1.5 text-xs font-mono">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-white">{sig.code}</span>
                    <span className="text-[11px] text-risk-safe font-bold">
                      -{Math.round(sig.weight * 100)}% discount
                    </span>
                  </div>
                  <p className="text-slate-300 text-[11px]">{sig.label}</p>
                  <div className="text-muted-foreground text-[11px] bg-background/50 p-2 rounded border border-border/60">
                    Evidence: <span className="text-emerald-300 font-sans">&ldquo;{sig.evidence}&rdquo;</span>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recommendations & Safe Verification Steps */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Protective Recommendations */}
        <div className="rounded-xl border border-border bg-surface p-5 space-y-3">
          <h4 className="font-mono text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-risk-high" />
            Protective Recommendations
          </h4>
          <ul className="space-y-2 text-xs font-mono text-slate-300">
            {scan.recommendations.map((rec, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-risk-high font-bold shrink-0">✕</span>
                <span className="leading-relaxed">{rec}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Safe Verification Steps */}
        <div className="rounded-xl border border-border bg-surface p-5 space-y-3">
          <h4 className="font-mono text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-risk-safe" />
            Independent Verification Steps
          </h4>
          <ol className="space-y-2 text-xs font-mono text-slate-300">
            {scan.verify_steps.map((step, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="w-4 h-4 rounded-full bg-primary/20 text-primary border border-primary/40 text-[10px] flex items-center justify-center shrink-0">
                  {i + 1}
                </span>
                <span className="leading-relaxed">{step}</span>
              </li>
            ))}
          </ol>
        </div>
      </div>

      {/* Action Footer */}
      <div className="p-4 rounded-xl border border-border bg-elevated/40 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="text-xs font-mono text-muted-foreground">
          Need to preserve this incident for documentation or law enforcement reporting?
        </div>
        <div className="flex items-center gap-3">
          <Button asChild variant="outline" size="sm" className="font-mono text-xs">
            <Link href="/history">Back to History</Link>
          </Button>
          <Button asChild size="sm" className="bg-purple-600 hover:bg-purple-700 text-white gap-1.5 font-mono text-xs">
            <Link href={`/reports/new?scan_id=${scan.id}`}>
              <FileCheck2 className="w-3.5 h-3.5" />
              Report this
            </Link>
          </Button>
        </div>
      </div>
    </div>
  );
}

export default function ScanDetailPage() {
  return (
    <React.Suspense fallback={<div className="p-8 text-center text-muted-foreground font-mono text-xs">Loading scan dossier...</div>}>
      <ScanDetailContent />
    </React.Suspense>
  );
}
