"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { AnalysisResponse, RiskLevel } from "@/types/analysis";
import {
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  Copy,
  Check,
  Info,
  Clock,
  Terminal,
  ShieldCheck,
  ExternalLink,
  ChevronRight,
  Shield,
  HelpCircle,
} from "lucide-react";

interface AnalysisDossierProps {
  analysis: AnalysisResponse;
  rawInput?: string;
  showHistoryLink?: boolean;
}

export function AnalysisDossier({
  analysis,
  rawInput,
  showHistoryLink = true,
}: AnalysisDossierProps) {
  const [copied, setCopied] = useState(false);

  // Map engine risk level to UI badge variant
  const getBadgeVariant = (level: string) => {
    switch (level.toLowerCase()) {
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

  const getScoreColor = (score: number) => {
    if (score <= 24) return "#34D399"; // safe (Likely Safe)
    if (score <= 44) return "#FBBF24"; // suspicious
    if (score <= 64) return "#F59E0B"; // medium
    if (score <= 99) return "#F97316"; // high
    return "#EF4444"; // critical
  };

  const displayInput = rawInput || analysis.message?.content || "";

  const handleCopyInput = () => {
    if (!displayInput) return;
    navigator.clipboard.writeText(displayInput);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Circular gauge calculations
  const score = analysis.risk?.score ?? 0;
  const radius = 54;
  const strokeWidth = 8;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;
  const scoreColor = getScoreColor(score);
  const confidencePct = Math.round((analysis.confidence ?? 0.85) * 100);

  return (
    <div className="space-y-6">
      {/* 1. Main Verdict Banner & Gauge Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Score Gauge Card */}
        <div className="rounded-xl border border-border bg-surface p-5 flex flex-col justify-between shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-muted-foreground uppercase tracking-wider font-semibold">
              CALCULATED RISK
            </span>
            <Badge variant={getBadgeVariant(analysis.risk.level)}>
              {analysis.risk.label || analysis.risk.level}
            </Badge>
          </div>

          <div className="my-4 flex items-center justify-center">
            <div className="relative w-32 h-32 flex items-center justify-center">
              <svg className="w-full h-full -rotate-90 transform" viewBox="0 0 128 128">
                <circle
                  cx="64"
                  cy="64"
                  r={radius}
                  stroke="#121B2F"
                  strokeWidth={strokeWidth}
                  fill="transparent"
                />
                <circle
                  cx="64"
                  cy="64"
                  r={radius}
                  stroke={scoreColor}
                  strokeWidth={strokeWidth}
                  fill="transparent"
                  strokeDasharray={circumference}
                  strokeDashoffset={strokeDashoffset}
                  strokeLinecap="round"
                  className="transition-all duration-1000 ease-out"
                />
              </svg>
              <div className="absolute flex flex-col items-center justify-center text-center">
                <span className="font-mono text-3xl font-extrabold text-white tracking-tight">
                  {score}
                </span>
                <span className="text-[10px] font-mono text-muted-foreground uppercase">
                  SCORE / 100
                </span>
              </div>
            </div>
          </div>

          <div className="text-[11px] font-mono text-slate-400 border-t border-border/80 pt-2.5 flex items-center justify-between">
            <span>Confidence: <strong className="text-white font-normal">{confidencePct}%</strong></span>
            <span className="truncate max-w-[140px] text-right text-slate-400">
              {analysis.verification_status.replace(/_/g, " ")}
            </span>
          </div>
        </div>

        {/* Threat Category Card */}
        <div className="rounded-xl border border-border bg-surface p-5 flex flex-col justify-between shadow-lg">
          <div>
            <div className="flex items-center justify-between text-xs font-mono text-muted-foreground uppercase">
              <span>DETECTED CLASSIFICATION</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-elevated border border-border">
                {analysis.category?.code || "general"}
              </span>
            </div>
            <h4 className="text-base font-semibold text-white mt-2 flex items-center gap-2">
              {score >= 45 ? (
                <AlertTriangle className="w-4 h-4 text-risk-high shrink-0" />
              ) : (
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              )}
              {analysis.category?.label || "Evaluated Payload"}
            </h4>
            <p className="text-xs text-muted-foreground mt-2 leading-relaxed">
              {analysis.summary}
            </p>
          </div>

          <div className="text-[11px] font-mono text-slate-400 border-t border-border/80 pt-2.5 flex items-center justify-between">
            <span>Engine: <strong className="text-accent-cyan font-normal">v{analysis.engine_version}</strong></span>
            {analysis.extracted?.language && (
              <span>Language: <strong className="text-white font-normal uppercase">{analysis.extracted.language}</strong></span>
            )}
          </div>
        </div>

        {/* Scan Metadata & Context Card */}
        <div className="rounded-xl border border-border bg-surface p-5 flex flex-col justify-between shadow-lg">
          <div>
            <span className="text-xs font-mono text-muted-foreground uppercase">
              EVALUATION TELEMETRY
            </span>
            <div className="mt-3 space-y-2 text-xs font-mono">
              <div className="flex justify-between items-center py-1 border-b border-border/60">
                <span className="text-muted-foreground">Scan Vector</span>
                <span className="text-white uppercase font-semibold">{analysis.scan_type}</span>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-border/60">
                <span className="text-muted-foreground">Threat Indicators</span>
                <span className="text-white font-semibold">{analysis.indicators?.length || 0} found</span>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-border/60">
                <span className="text-muted-foreground">Legitimacy Signals</span>
                <span className="text-emerald-400 font-semibold">{analysis.legitimacy_signals?.length || 0} verified</span>
              </div>
              <div className="flex justify-between items-center py-1">
                <span className="text-muted-foreground">Reputation Hits</span>
                <span className="text-slate-400">{analysis.intel?.[0]?.status || "not_found"}</span>
              </div>
            </div>
          </div>

          {analysis.scan_id && showHistoryLink && (
            <div className="border-t border-border/80 pt-2.5">
              <Button asChild variant="outline" size="sm" className="w-full text-xs font-mono gap-1.5 h-8">
                <Link href={`/scan/${analysis.scan_id}`}>
                  <span>Inspect Full Dossier</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </Link>
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* 2. Pasted Message Payload Card (Keeps line breaks!) */}
      {displayInput && (
        <div className="rounded-xl border border-border bg-surface p-5 space-y-2 shadow-lg">
          <div className="flex items-center justify-between text-xs font-mono text-muted-foreground">
            <span className="flex items-center gap-1.5 uppercase font-semibold text-slate-300">
              <Terminal className="w-3.5 h-3.5 text-primary" />
              ANALYZED MESSAGE PAYLOAD
            </span>
            <button
              onClick={handleCopyInput}
              className="flex items-center gap-1 hover:text-white transition-colors text-[11px] py-1 px-2 rounded hover:bg-elevated"
              aria-label="Copy message text"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="text-emerald-400">Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  <span>Copy</span>
                </>
              )}
            </button>
          </div>

          {/* Whitespace-pre-wrap ensures all line breaks in pasted messages are preserved */}
          <div className="whitespace-pre-wrap font-mono text-xs sm:text-sm text-slate-200 leading-relaxed bg-[#070B14] p-4 rounded-lg border border-border/80 overflow-x-auto">
            {displayInput}
          </div>
        </div>
      )}

      {/* 3. Threat Indicators & Legitimacy Signals Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Threat Indicators */}
        <Card className="p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-border pb-3">
            <h4 className="font-mono text-xs sm:text-sm font-bold text-white uppercase flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-risk-high" />
              THREAT INDICATORS ({analysis.indicators?.length || 0})
            </h4>
            <span className="text-[10px] font-mono text-muted-foreground">Noisy-OR factors</span>
          </div>

          {analysis.indicators && analysis.indicators.length > 0 ? (
            <div className="space-y-3">
              {analysis.indicators.map((ind, idx) => (
                <div
                  key={`${ind.code}-${idx}`}
                  className="p-3 rounded-lg border border-border bg-background/50 space-y-2 text-xs font-mono"
                >
                  <div className="flex items-start justify-between gap-2">
                    <span className="font-semibold text-white">{ind.label}</span>
                    <div className="flex items-center gap-1.5 shrink-0">
                      <Badge variant={getBadgeVariant(ind.severity)} className="text-[10px] uppercase">
                        {ind.severity}
                      </Badge>
                      <span className="text-[10px] text-muted-foreground">w={ind.weight}</span>
                    </div>
                  </div>
                  <div className="text-[11px] text-slate-400">
                    <code>{ind.code}</code>
                  </div>
                  {ind.evidence && (
                    <div className="text-[11px] bg-red-500/10 border border-red-500/20 text-red-300 p-2 rounded">
                      <span className="text-muted-foreground font-semibold">Evidence: </span>
                      &ldquo;{ind.evidence}&rdquo;
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="p-4 rounded-lg border border-dashed border-border text-center text-xs font-mono text-muted-foreground">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 mx-auto mb-1.5" />
              No predatory threat indicators detected in input payload.
            </div>
          )}
        </Card>

        {/* Legitimacy Signals */}
        <Card className="p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-border pb-3">
            <h4 className="font-mono text-xs sm:text-sm font-bold text-white uppercase flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              LEGITIMACY SIGNALS ({analysis.legitimacy_signals?.length || 0})
            </h4>
            <span className="text-[10px] font-mono text-muted-foreground">Protective patterns</span>
          </div>

          {analysis.legitimacy_signals && analysis.legitimacy_signals.length > 0 ? (
            <div className="space-y-3">
              {analysis.legitimacy_signals.map((sig, idx) => (
                <div
                  key={`${sig.code}-${idx}`}
                  className="p-3 rounded-lg border border-border bg-background/50 space-y-2 text-xs font-mono"
                >
                  <div className="flex items-start justify-between gap-2">
                    <span className="font-semibold text-emerald-300">{sig.label}</span>
                    <span className="text-[10px] text-emerald-400 font-bold shrink-0">
                      -{Math.round(sig.weight * 100)}%
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-400">
                    <code>{sig.code}</code>
                  </div>
                  {sig.evidence && (
                    <div className="text-[11px] bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 p-2 rounded">
                      <span className="text-muted-foreground font-semibold">Pattern Match: </span>
                      &ldquo;{sig.evidence}&rdquo;
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="p-4 rounded-lg border border-dashed border-border text-center text-xs font-mono text-muted-foreground">
              <Info className="w-4 h-4 text-slate-400 mx-auto mb-1.5" />
              No authentic legitimacy signals observed (no masked A/C, bank advice, or official portal).
            </div>
          )}
        </Card>
      </div>

      {/* 4. Recommendations & Verification Steps */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Recommended Actions */}
        <Card className="p-5 space-y-3">
          <h4 className="font-mono text-xs sm:text-sm font-bold text-white uppercase border-b border-border pb-2.5 flex items-center gap-2">
            <Shield className="w-4 h-4 text-primary" />
            RECOMMENDED PROTECTIVE ACTIONS
          </h4>
          {analysis.recommendations && analysis.recommendations.length > 0 ? (
            <ul className="space-y-2 text-xs font-mono text-slate-300">
              {analysis.recommendations.map((rec, i) => (
                <li key={i} className="flex items-start gap-2 bg-elevated/40 p-2.5 rounded border border-border/60">
                  <span className="text-accent-cyan font-bold">•</span>
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs font-mono text-muted-foreground">No specific action required.</p>
          )}
        </Card>

        {/* Verification Steps */}
        <Card className="p-5 space-y-3">
          <h4 className="font-mono text-xs sm:text-sm font-bold text-white uppercase border-b border-border pb-2.5 flex items-center gap-2">
            <HelpCircle className="w-4 h-4 text-accent-cyan" />
            INDEPENDENT VERIFICATION STEPS
          </h4>
          {analysis.verify_steps && analysis.verify_steps.length > 0 ? (
            <ol className="space-y-2 text-xs font-mono text-slate-300">
              {analysis.verify_steps.map((step, i) => (
                <li key={i} className="flex items-start gap-2 bg-elevated/40 p-2.5 rounded border border-border/60">
                  <span className="text-primary font-bold">{i + 1}.</span>
                  <span>{step}</span>
                </li>
              ))}
            </ol>
          ) : (
            <p className="text-xs font-mono text-muted-foreground">Always confirm directly with your official service provider.</p>
          )}
        </Card>
      </div>
    </div>
  );
}
