"use client";

import React, { useState } from "react";
import Link from "next/link";
import { showDevTools } from "@/lib/dev-tools";
import { apiRequest, ApiClientError } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { LoadingState, EmptyState, ErrorState } from "@/components/ui/states";
import {
  Globe,
  ShieldCheck,
  RotateCcw,
  AlertTriangle,
  ShieldAlert,
  Lock,
  CheckCircle2,
  ListChecks,
  History,
} from "lucide-react";

/* ------------------------------------------------------------------ */
/* Shape of the answer from POST /api/analyze/url                      */
/* (same as backend/app/schemas/scan.py -> AnalysisResponse)           */
/* ------------------------------------------------------------------ */
interface UrlIndicator {
  code: string;
  label: string;
  severity: string;
  weight: number;
  evidence?: string | null;
}

interface UrlLegitimacySignal {
  code: string;
  label: string;
  weight: number;
  evidence?: string | null;
}

interface UrlAnalysisResult {
  scan_id?: string | null;
  scan_type: string;
  risk: { score: number; level: string; label: string };
  confidence: number;
  verification_status: string;
  category: { code: string; label: string };
  summary: string;
  indicators: UrlIndicator[];
  legitimacy_signals: UrlLegitimacySignal[];
  recommendations: string[];
  verify_steps: string[];
  extracted: {
    urls: { raw?: string; normalized?: string; domain?: string; source?: string }[];
  };
  engine_version: string;
}

type PageState = "ready" | "analyzing" | "result" | "empty" | "error";
type BadgeVariant = "safe" | "suspicious" | "medium" | "high" | "critical" | "unverified";

/* Risk level from the backend -> colour of the badge (badge.tsx variants) */
const LEVEL_TO_BADGE: Record<string, BadgeVariant> = {
  likely_safe: "safe",
  suspicious: "suspicious",
  medium: "medium",
  high: "high",
  critical: "critical",
  unable_to_verify: "unverified",
};

/* Indicator severity -> text colour */
const SEVERITY_COLOR: Record<string, string> = {
  critical: "text-[#EF4444]",
  high: "text-[#F97316]",
  medium: "text-[#F59E0B]",
  low: "text-[#FBBF24]",
};

/* Backend verification_status -> plain-English text */
function verificationText(status: string): string {
  if (status === "unverified") {
    return "Not found in GARUDA's lists. This result comes only from checking the address pattern.";
  }
  if (status.includes("official")) {
    return "Matches GARUDA's list of official websites.";
  }
  if (status.includes("betting")) {
    return "Matches GARUDA's list of known betting / gambling websites.";
  }
  if (status.includes("adult")) {
    return "Matches GARUDA's restricted (adult) content keywords.";
  }
  return status.replace(/_/g, " ");
}

export default function UrlAnalyzerPage() {
  const [url, setUrl] = useState("");
  const [saveToHistory, setSaveToHistory] = useState(true);
  const [state, setState] = useState<PageState>("ready");
  const [result, setResult] = useState<UrlAnalysisResult | null>(null);
  const [analyzedUrl, setAnalyzedUrl] = useState("");
  const [errorTitle, setErrorTitle] = useState("Could not analyze this link");
  const [errorMessage, setErrorMessage] = useState("");

  const handleAnalyze = async () => {
    const value = url.trim();
    if (!value) {
      setState("empty");
      return;
    }

    setState("analyzing");
    setResult(null);

    try {
      // REAL call to the backend (sends the login token automatically)
      const data = await apiRequest<UrlAnalysisResult>("/api/analyze/url", {
        method: "POST",
        body: JSON.stringify({ url: value, save: saveToHistory }),
      });
      setResult(data);
      setAnalyzedUrl(value);
      setState("result");
    } catch (err) {
      if (err instanceof ApiClientError) {
        if (err.code === "INVALID_URL" || err.status === 422) {
          setErrorTitle("Unable to Verify: not a valid web address");
        } else if (err.code === "SESSION_EXPIRED") {
          setErrorTitle("Session expired");
        } else if (err.code === "NETWORK_ERROR") {
          setErrorTitle("Cannot reach the GARUDA server");
        } else if (err.status === 429) {
          setErrorTitle("Too many requests");
        } else {
          setErrorTitle("Could not analyze this link");
        }
        setErrorMessage(
          err.code === "NETWORK_ERROR"
            ? "The backend is not responding. Make sure it is running on port 8000."
            : err.message
        );
      } else {
        setErrorTitle("Could not analyze this link");
        setErrorMessage("Something unexpected went wrong. Please try again.");
      }
      setState("error");
    }
  };

  const handleSample = (sample: string) => {
    setUrl(sample);
    setState("ready");
  };

  const handleClear = () => {
    setUrl("");
    setResult(null);
    setState("ready");
  };

  const badgeVariant: BadgeVariant = result
    ? LEVEL_TO_BADGE[result.risk.level] ?? "unverified"
    : "unverified";
  const domain = result?.extracted?.urls?.[0]?.domain;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
        <div>
          <span className="font-mono text-xs uppercase text-accent-cyan tracking-wider font-semibold">
            SECTOR 1: STATIC LINK HEURISTICS
          </span>
          <h2 className="font-mono text-2xl sm:text-3xl font-bold text-white mt-1 flex items-center gap-2">
            <Globe className="w-6 h-6 text-accent-cyan" />
            URL &amp; Domain Analyzer
          </h2>
          <p className="text-xs sm:text-sm text-muted-foreground mt-1">
            Static analysis of the address: fake brand names, look-alike spellings, risky endings,
            short links, and GARUDA&apos;s lists of betting and restricted sites.
          </p>
        </div>

        {/* State Switcher — only visible when NEXT_PUBLIC_SHOW_DEV_TOOLS=true */}
        {showDevTools && (
          <div className="flex items-center gap-1.5 p-1 rounded-lg border border-border bg-elevated/40 text-[11px] font-mono self-start sm:self-auto">
            <span className="text-muted-foreground px-2">State:</span>
            {(["ready", "analyzing", "empty", "error"] as PageState[]).map((s) => (
              <button
                key={s}
                onClick={() => setState(s)}
                className={`px-2 py-0.5 rounded ${state === s ? "bg-primary text-white" : "text-slate-400"}`}
              >
                {s}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Zero Fetch Notice */}
      <div className="p-3.5 rounded-lg border border-primary/30 bg-primary/10 text-xs font-mono text-slate-300 flex items-center gap-2.5">
        <Lock className="w-4 h-4 text-accent-cyan shrink-0" />
        <span>
          <strong className="text-white">Safety Guarantee:</strong> GARUDA never opens or visits
          the link you submit. It only reads the address text, so checking a dangerous link here is safe.
        </span>
      </div>

      {/* Input Box */}
      <div className="rounded-xl border border-border bg-surface p-5 sm:p-6 space-y-4">
        <div>
          <label htmlFor="url-input" className="block font-mono text-xs font-semibold text-slate-300 uppercase mb-2">
            Link or Website Address
          </label>
          <Input
            id="url-input"
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && state !== "analyzing") handleAnalyze();
            }}
            maxLength={2048}
            placeholder="e.g. sbi-yono-kyc.in-verify.xyz/login or https://indian.1xbet.com"
            className="font-mono text-sm h-11"
          />
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2 border-t border-border/80">
          <label className="flex items-center gap-2 cursor-pointer select-none text-xs font-mono text-slate-300 hover:text-white">
            <input
              type="checkbox"
              checked={saveToHistory}
              onChange={(e) => setSaveToHistory(e.target.checked)}
              className="rounded border-input bg-input-bg text-primary focus:ring-primary w-4 h-4"
            />
            <span>Save to history</span>
          </label>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleClear}
              disabled={!url || state === "analyzing"}
              className="gap-1 font-mono text-xs"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Clear
            </Button>
            <Button
              onClick={handleAnalyze}
              disabled={state === "analyzing"}
              className="gap-1.5 font-mono text-xs px-5 font-semibold"
            >
              <ShieldCheck className="w-4 h-4" />
              {state === "analyzing" ? "Analyzing..." : "Analyze URL"}
            </Button>
          </div>
        </div>

        {/* Samples */}
        <div className="pt-3 border-t border-border/60">
          <span className="text-[11px] font-mono text-muted-foreground block mb-2">
            Try an example:
          </span>
          <div className="flex flex-wrap gap-2">
            {[
              { tag: "Phishing", value: "http://sbi-yono-kyc.in-verify.xyz/login" },
              { tag: "Illegal Betting", value: "https://indian.1xbet.com/live" },
              { tag: "Short Link", value: "https://bit.ly/3abcXYZ" },
              { tag: "Official", value: "https://sbi.co.in/web/personal-banking" },
            ].map((s) => (
              <button
                key={s.value}
                onClick={() => handleSample(s.value)}
                className="text-[11px] font-mono px-2 py-1 rounded bg-elevated hover:bg-slate-800 text-slate-300 hover:text-white border border-border"
              >
                [{s.tag}] {s.value.replace(/^https?:\/\//, "").split("/")[0]}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Dynamic States */}
      {state === "analyzing" && (
        <LoadingState
          message="Checking the link..."
          description="Reading the address, finding the real domain, and comparing it with official Indian bank and brand websites."
        />
      )}

      {state === "empty" && (
        <EmptyState
          title="No link entered"
          description="Paste a website address or link in the box above."
          actionLabel="Try a sample phishing link"
          onAction={() => handleSample("http://sbi-yono-kyc.in-verify.xyz/login")}
        />
      )}

      {state === "error" && (
        <ErrorState
          title={errorTitle}
          message={errorMessage || "Please check the link and try again."}
          details="Nothing was saved to your history."
          onRetry={handleAnalyze}
        />
      )}

      {state === "result" && result && (
        <div className="rounded-xl border border-border bg-surface p-6 space-y-6">
          {/* Top: the link (plain text, NOT clickable) + risk badge */}
          <div className="flex flex-wrap items-start justify-between gap-3 border-b border-border pb-4">
            <div className="min-w-0">
              <span className="font-mono text-xs text-muted-foreground uppercase">
                Link checked (not opened)
              </span>
              <h3 className="font-mono text-base font-bold text-white break-all select-all">
                {analyzedUrl}
              </h3>
              {domain && (
                <p className="text-[11px] font-mono text-slate-400 mt-1">
                  Real domain: <span className="text-slate-200">{domain}</span>
                </p>
              )}
            </div>
            <div className="flex flex-col items-end gap-1.5">
              <Badge variant={badgeVariant} className="text-sm px-3 py-1">
                {result.risk.score} · {result.risk.label}
              </Badge>
              <span className="text-[11px] font-mono text-slate-400">
                Confidence: {Math.round(result.confidence * 100)}%
              </span>
              {(result.risk.level === "medium" ||
                result.risk.level === "high" ||
                result.risk.level === "critical" ||
                result.risk.score >= 45) && (
                <Button asChild size="sm" className="gap-1.5 font-mono text-xs bg-purple-600 hover:bg-purple-700 text-white font-semibold h-7 px-3 mt-1">
                  <Link href={result.scan_id ? `/reports?scan_id=${result.scan_id}` : `/reports`}>
                    <ShieldAlert className="w-3.5 h-3.5" />
                    Report this
                  </Link>
                </Button>
              )}
            </div>
          </div>

          {/* Category + summary */}
          <div className="space-y-2">
            <span className="text-[11px] font-mono text-muted-foreground uppercase block">Category</span>
            <p className="font-mono text-sm font-semibold text-white">{result.category.label}</p>
            <p className="text-sm text-slate-300 leading-relaxed">{result.summary}</p>
          </div>

          {/* List check status (honest: only GARUDA's own lists) */}
          <div className="p-3 rounded-lg border border-border bg-elevated/40 text-xs font-mono text-slate-300">
            <span className="text-muted-foreground uppercase text-[11px] block mb-1">List check</span>
            {verificationText(result.verification_status)}
          </div>

          {/* Warning signs */}
          {result.indicators.length > 0 && (
            <div className="space-y-2">
              <span className="text-[11px] font-mono text-muted-foreground uppercase flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5" /> Warning signs found ({result.indicators.length})
              </span>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {result.indicators.map((ind) => (
                  <div key={ind.code} className="p-3.5 rounded-lg border border-border bg-elevated/40 text-xs font-mono">
                    <div className="flex items-center justify-between gap-2">
                      <span className={`font-bold ${SEVERITY_COLOR[ind.severity] ?? "text-slate-200"}`}>
                        {ind.label}
                      </span>
                      <span className="text-[10px] uppercase text-slate-400 shrink-0">{ind.severity}</span>
                    </div>
                    {ind.evidence && (
                      <p className="text-[11px] text-slate-400 mt-1 break-all">Evidence: {ind.evidence}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Good signs */}
          {result.legitimacy_signals.length > 0 && (
            <div className="space-y-2">
              <span className="text-[11px] font-mono text-muted-foreground uppercase flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5" /> Good signs
              </span>
              {result.legitimacy_signals.map((sig) => (
                <div key={sig.code} className="p-3 rounded-lg border border-[#34D399]/30 bg-[#34D399]/10 text-xs font-mono">
                  <span className="font-bold text-[#34D399]">{sig.label}</span>
                  {sig.evidence && <p className="text-[11px] text-slate-400 mt-1 break-all">{sig.evidence}</p>}
                </div>
              ))}
            </div>
          )}

          {/* No signs at all */}
          {result.indicators.length === 0 && result.legitimacy_signals.length === 0 && (
            <div className="p-3 rounded-lg border border-border bg-elevated/40 text-xs font-mono text-slate-300">
              No warning signs were found in this address. This does not prove the website is safe,
              so still be careful before entering passwords, OTPs or card details.
            </div>
          )}

          {/* What to do */}
          {result.recommendations.length > 0 && (
            <div className="space-y-2">
              <span className="text-[11px] font-mono text-muted-foreground uppercase flex items-center gap-1.5">
                <ShieldAlert className="w-3.5 h-3.5" /> What you should do
              </span>
              <ul className="list-disc pl-5 space-y-1 text-sm text-slate-300">
                {result.recommendations.map((rec, i) => (
                  <li key={i}>{rec}</li>
                ))}
              </ul>
            </div>
          )}

          {/* How to verify */}
          {result.verify_steps.length > 0 && (
            <div className="space-y-2">
              <span className="text-[11px] font-mono text-muted-foreground uppercase flex items-center gap-1.5">
                <ListChecks className="w-3.5 h-3.5" /> How to verify it yourself
              </span>
              <ol className="list-decimal pl-5 space-y-1 text-sm text-slate-300">
                {result.verify_steps.map((step, i) => (
                  <li key={i}>{step}</li>
                ))}
              </ol>
            </div>
          )}

          {/* Footer */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-4 border-t border-border text-[11px] font-mono text-slate-400">
            <span>
              {result.scan_id ? "Saved to your history." : "Not saved (Save to history was off)."} Engine{" "}
              {result.engine_version}
            </span>
            {result.scan_id && (
              <Link href="/history" className="flex items-center gap-1 text-accent-cyan hover:underline">
                <History className="w-3.5 h-3.5" /> View history
              </Link>
            )}
          </div>
        </div>
      )}
    </div>
  );
}