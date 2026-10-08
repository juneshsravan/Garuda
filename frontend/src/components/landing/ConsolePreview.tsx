import React from "react";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, ShieldAlert, CheckCircle2, Terminal, ArrowUpRight, Copy } from "lucide-react";

export function ConsolePreview() {
  return (
    <div className="relative mx-auto max-w-5xl rounded-xl border border-border bg-surface shadow-2xl overflow-hidden">
      {/* Console Window Header */}
      <div className="flex items-center justify-between border-b border-border bg-elevated/70 px-4 py-2.5">
        <div className="flex items-center gap-2">
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-red-500/80" />
            <div className="w-3 h-3 rounded-full bg-amber-500/80" />
            <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
          </div>
          <span className="ml-2 font-mono text-xs text-muted-foreground flex items-center gap-1.5">
            <Terminal className="w-3.5 h-3.5 text-primary" />
            garuda-security-console // live-telemetry-engine
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="font-mono text-[10px] uppercase tracking-wider px-2 py-0.5 rounded bg-primary/20 text-accent-cyan border border-primary/30 font-semibold">
            Example analysis
          </span>
          <span className="font-mono text-[11px] text-muted-foreground hidden sm:inline">
            ENGINE: <span className="text-accent-cyan">v2.0.0-PROD</span>
          </span>
          <span className="font-mono text-[11px] text-muted-foreground hidden md:inline">
            LATENCY: <span className="text-emerald-400">142ms</span>
          </span>
        </div>
      </div>

      {/* Main Console Content */}
      <div className="p-5 sm:p-6 space-y-6">
        {/* Input Message Preview */}
        <div className="rounded-lg border border-border bg-background/60 p-3.5 sm:p-4">
          <div className="flex items-center justify-between text-xs text-muted-foreground font-mono mb-2">
            <span>INPUT TELEMETRY: SMS / WHATSAPP PAYLOAD</span>
            <span className="text-slate-400">SHA-256: 7d4a...b891</span>
          </div>
          <p className="font-mono text-sm text-slate-200 leading-relaxed bg-[#070B14] p-3 rounded border border-border/80">
            &ldquo;Congratulations! You won ₹500 cashback. Scan this QR immediately to claim your reward into bank account: <span className="text-amber-400">upi://pay?pa=claim.reward92@okaxis&pn=CashDesk&am=500</span>&rdquo;
          </p>
        </div>

        {/* Verdict Banner */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Score Gauge */}
          <div className="rounded-lg border border-risk-high/30 bg-risk-high/10 p-4 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-muted-foreground uppercase">
                CALCULATED RISK
              </span>
              <Badge variant="high">High Risk</Badge>
            </div>
            <div className="my-3 flex items-baseline gap-2">
              <span className="font-mono text-4xl sm:text-5xl font-extrabold text-risk-high">
                81
              </span>
              <span className="text-sm font-mono text-muted-foreground">/ 100</span>
            </div>
            <div className="text-[11px] font-mono text-slate-400">
              Confidence: <span className="text-white">89%</span> · Status: <span className="text-risk-high">Unverified Source</span>
            </div>
          </div>

          {/* Classification */}
          <div className="rounded-lg border border-border bg-elevated/40 p-4 flex flex-col justify-between">
            <div>
              <span className="text-xs font-mono text-muted-foreground uppercase">
                DETECTED CLASSIFICATION
              </span>
              <h4 className="text-base font-semibold text-white mt-1.5 flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4 text-risk-high shrink-0" />
                Potential QR / Reward Scam
              </h4>
            </div>
            <p className="text-xs text-muted-foreground mt-2 leading-relaxed">
              Synthesized from predatory financial lure, artificial urgency coercion, and reversed UPI collect vectors.
            </p>
          </div>

          {/* Quick Defense Action */}
          <div className="rounded-lg border border-border bg-elevated/40 p-4 flex flex-col justify-between">
            <div>
              <span className="text-xs font-mono text-muted-foreground uppercase">
                CRITICAL ACTION
              </span>
              <h4 className="text-sm font-semibold text-risk-high mt-1.5 flex items-center gap-1.5">
                <ShieldAlert className="w-4 h-4 text-risk-high shrink-0" />
                DO NOT SCAN OR PAY
              </h4>
            </div>
            <p className="text-xs text-slate-300 mt-2 leading-relaxed">
              Receiving money never requires entering a UPI PIN or scanning any QR code.
            </p>
          </div>
        </div>

        {/* Explainable Indicators Table */}
        <div className="rounded-lg border border-border bg-background/40 overflow-hidden">
          <div className="bg-elevated/60 px-4 py-2.5 border-b border-border flex items-center justify-between">
            <span className="text-xs font-mono text-slate-300 font-semibold tracking-wide">
              THREAT INDICATORS & EVIDENCE (NOISY-OR BREAKDOWN)
            </span>
            <span className="text-[11px] font-mono text-muted-foreground">
              3 Signals Isolated
            </span>
          </div>

          <div className="divide-y divide-border/60 text-xs font-mono">
            <div className="p-3 sm:px-4 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-white">FIN_UNEXPECTED_REWARD</span>
                  <Badge variant="high" className="text-[10px] py-0 px-1.5">High Severity</Badge>
                </div>
                <div className="text-muted-foreground">
                  Evidence snippet: <span className="text-slate-200 bg-surface px-1.5 py-0.5 rounded">&ldquo;You won ₹500&rdquo;</span>
                </div>
              </div>
              <div className="text-right shrink-0">
                <span className="text-muted-foreground">Weight: </span>
                <span className="text-risk-high font-bold">+0.35</span>
              </div>
            </div>

            <div className="p-3 sm:px-4 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-white">FIN_QR_ACTION</span>
                  <Badge variant="high" className="text-[10px] py-0 px-1.5">High Severity</Badge>
                </div>
                <div className="text-muted-foreground">
                  Evidence snippet: <span className="text-slate-200 bg-surface px-1.5 py-0.5 rounded">&ldquo;Scan this QR&rdquo;</span>
                </div>
              </div>
              <div className="text-right shrink-0">
                <span className="text-muted-foreground">Weight: </span>
                <span className="text-risk-high font-bold">+0.30</span>
              </div>
            </div>

            <div className="p-3 sm:px-4 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-white">TEMP_URGENCY</span>
                  <Badge variant="medium" className="text-[10px] py-0 px-1.5">Medium Severity</Badge>
                </div>
                <div className="text-muted-foreground">
                  Evidence snippet: <span className="text-slate-200 bg-surface px-1.5 py-0.5 rounded">&ldquo;immediately to claim&rdquo;</span>
                </div>
              </div>
              <div className="text-right shrink-0">
                <span className="text-muted-foreground">Weight: </span>
                <span className="text-risk-medium font-bold">+0.25</span>
              </div>
            </div>
          </div>
        </div>

        {/* Legitimacy & Verification Steps */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
          <div className="rounded-lg border border-border bg-elevated/30 p-3.5 space-y-1.5">
            <span className="text-muted-foreground font-semibold uppercase text-[11px] block">
              Legitimacy Signals Evaluated
            </span>
            <div className="text-slate-400 space-y-1">
              <p>• Bank official safety advisory: <span className="text-slate-500">Not found (0.00)</span></p>
              <p>• Masked genuine account format: <span className="text-slate-500">Not found (0.00)</span></p>
              <p className="text-[11px] text-amber-400/90 pt-1">
                Anti-gaming rule triggered: High indicators override legitimacy discounts.
              </p>
            </div>
          </div>

          <div className="rounded-lg border border-border bg-elevated/30 p-3.5 space-y-1.5">
            <span className="text-accent-cyan font-semibold uppercase text-[11px] flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Prescribed Verification Steps
            </span>
            <ul className="text-slate-300 space-y-1">
              <li>1. Verify bank balance directly inside your authentic UPI app.</li>
              <li>2. Remember: Money credits automatically without user scans.</li>
              <li>3. Block and report sender handle to 1930 cyber helpline.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
