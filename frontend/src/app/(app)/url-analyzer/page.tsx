"use client";

import React, { useState } from "react";
import { showDevTools } from "@/lib/dev-tools";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { LoadingState, EmptyState, ErrorState } from "@/components/ui/states";
import {
  Globe,
  ShieldCheck,
  RotateCcw,
  AlertTriangle,
  ExternalLink,
  ShieldAlert,
  Lock,
} from "lucide-react";

export default function UrlAnalyzerPage() {
  const [url, setUrl] = useState("");
  const [saveToHistory, setSaveToHistory] = useState(true);
  const [state, setState] = useState<"ready" | "analyzing" | "result" | "empty" | "error">("ready");

  const handleAnalyze = () => {
    if (!url.trim()) {
      setState("empty");
      return;
    }
    setState("analyzing");
    // MOCK: In Chunk 7B this calls POST /api/analyze/url {url, save: saveToHistory}
    setTimeout(() => {
      setState("result");
    }, 900);
  };

  const handleSample = (sample: string) => {
    setUrl(sample);
    setState("ready");
  };

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
            Zero-fetch static analysis: punycode, lookalikes, risky TLDs, and verified threat blocklists.
          </p>
        </div>

        {/* State Switcher — only visible when NEXT_PUBLIC_SHOW_DEV_TOOLS=true */}
        {showDevTools && (
          <div className="flex items-center gap-1.5 p-1 rounded-lg border border-border bg-elevated/40 text-[11px] font-mono self-start sm:self-auto">
            <span className="text-muted-foreground px-2">State:</span>
            <button
              onClick={() => setState("ready")}
              className={`px-2 py-0.5 rounded ${state === "ready" ? "bg-primary text-white" : "text-slate-400"}`}
            >
              Ready
            </button>
            <button
              onClick={() => setState("analyzing")}
              className={`px-2 py-0.5 rounded ${state === "analyzing" ? "bg-primary text-white" : "text-slate-400"}`}
            >
              Loading
            </button>
            <button
              onClick={() => setState("result")}
              className={`px-2 py-0.5 rounded ${state === "result" ? "bg-primary text-white" : "text-slate-400"}`}
            >
              Result
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

      {/* Zero Fetch Notice */}
      <div className="p-3.5 rounded-lg border border-primary/30 bg-primary/10 text-xs font-mono text-slate-300 flex items-center gap-2.5">
        <Lock className="w-4 h-4 text-accent-cyan shrink-0" />
        <span>
          <strong className="text-white">Safety Guarantee:</strong> GARUDA never connects to, fetches, or visits submitted URLs. Evaluation occurs completely in isolation via static feature extraction and local threat intelligence.
        </span>
      </div>

      {/* Input Box */}
      <div className="rounded-xl border border-border bg-surface p-5 sm:p-6 space-y-4">
        <div>
          <label htmlFor="url-input" className="block font-mono text-xs font-semibold text-slate-300 uppercase mb-2">
            Target URL or Registered Domain
          </label>
          <Input
            id="url-input"
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
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
              onClick={() => setUrl("")}
              disabled={!url}
              className="gap-1 font-mono text-xs"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Clear
            </Button>
            <Button
              onClick={handleAnalyze}
              className="gap-1.5 font-mono text-xs px-5 font-semibold"
            >
              <ShieldCheck className="w-4 h-4" />
              Analyze URL
            </Button>
          </div>
        </div>

        {/* Samples */}
        <div className="pt-3 border-t border-border/60">
          <span className="text-[11px] font-mono text-muted-foreground block mb-2">
            Try an example:
          </span>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => handleSample("http://sbi-yono-kyc.in-verify.xyz/login")}
              className="text-[11px] font-mono px-2 py-1 rounded bg-elevated hover:bg-slate-800 text-slate-300 hover:text-white border border-border"
            >
              [Phishing] sbi-yono-kyc.in-verify.xyz
            </button>
            <button
              onClick={() => handleSample("https://indian.1xbet.com/live")}
              className="text-[11px] font-mono px-2 py-1 rounded bg-elevated hover:bg-slate-800 text-slate-300 hover:text-white border border-border"
            >
              [Illegal Betting] indian.1xbet.com
            </button>
            <button
              onClick={() => handleSample("https://sbi.co.in/web/personal-banking")}
              className="text-[11px] font-mono px-2 py-1 rounded bg-elevated hover:bg-slate-800 text-slate-300 hover:text-white border border-border"
            >
              [Likely Safe] sbi.co.in
            </button>
          </div>
        </div>
      </div>

      {/* Dynamic States */}
      {state === "analyzing" && (
        <LoadingState
          message="Running Static URL Inspection..."
          description="Parsing domain structure, calculating Levenshtein distance vs Indian banks, and querying threat intelligence blocklists."
        />
      )}

      {state === "empty" && (
        <EmptyState
          title="URL Input Empty"
          description="Please specify a domain name or complete URL in the field above."
          actionLabel="Try Sample Phishing Domain"
          onAction={() => handleSample("http://sbi-yono-kyc.in-verify.xyz/login")}
        />
      )}

      {state === "error" && (
        <ErrorState
          title="URL Inspection Service Pending"
          message="FastAPI route POST /api/analyze/url is pending Chunk 7 integration."
          details="ARCHITECTURE Section 8.6: Heuristics include IP host, punycode, risky TLD, brand distance, and threat_intelligence tables."
          onRetry={() => setState("result")}
        />
      )}

      {state === "result" && (
        <div className="rounded-xl border border-border bg-surface p-6 space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-4">
            <div>
              <span className="font-mono text-xs text-muted-foreground uppercase">
                TARGET DOMAIN TELEMETRY
              </span>
              <h3 className="font-mono text-base font-bold text-white break-all">
                {url || "http://sbi-yono-kyc.in-verify.xyz/login"}
              </h3>
            </div>
            <Badge variant="high">89 High Risk</Badge>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
            <div className="p-3.5 rounded-lg border border-border bg-elevated/40">
              <span className="text-[11px] text-muted-foreground uppercase block mb-1">Lookalike Distance</span>
              <span className="text-risk-high font-bold">SBI Brand Squatting</span>
              <p className="text-[10px] text-slate-400 mt-1">Matched official target: sbi.co.in</p>
            </div>
            <div className="p-3.5 rounded-lg border border-border bg-elevated/40">
              <span className="text-[11px] text-muted-foreground uppercase block mb-1">TLD Reputation</span>
              <span className="text-amber-400 font-bold">Risky TLD (.xyz)</span>
              <p className="text-[10px] text-slate-400 mt-1">High statistical fraud prevalence</p>
            </div>
            <div className="p-3.5 rounded-lg border border-border bg-elevated/40">
              <span className="text-[11px] text-muted-foreground uppercase block mb-1">Blocklist Hit</span>
              <span className="text-risk-high font-bold">URLhaus Phishing List</span>
              <p className="text-[10px] text-slate-400 mt-1">Source: threat_intelligence table</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
