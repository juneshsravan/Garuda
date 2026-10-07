import React from "react";
import { History, Shield, Filter, Download, Trash2, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";

export function HistorySection() {
  return (
    <section id="history" className="py-20 sm:py-28 border-t border-border/80 bg-surface/30">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          {/* Left Column: Interactive Audit Log Preview */}
          <div className="lg:col-span-7 order-2 lg:order-1">
            <div className="rounded-xl border border-border bg-surface p-5 shadow-xl space-y-4">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <div className="flex items-center gap-2">
                  <History className="w-4 h-4 text-primary" />
                  <span className="font-mono text-xs font-semibold text-white uppercase">
                    Personal Scan Ledger
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-mono text-muted-foreground flex items-center gap-1">
                    <Filter className="w-3 h-3" /> Filter: All Vectors
                  </span>
                </div>
              </div>

              {/* Sample Scan Rows */}
              <div className="space-y-2.5 font-mono text-xs">
                {/* Row 1 */}
                <div className="p-3 rounded-lg border border-border/80 bg-elevated/40 flex items-center justify-between gap-3">
                  <div className="space-y-0.5 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-white font-medium truncate">Electricity Disconnection SMS</span>
                      <Badge variant="high">88 High</Badge>
                    </div>
                    <span className="text-[11px] text-muted-foreground block truncate">
                      &ldquo;Power disconnected tonight at 9:30 PM... call officer...&rdquo;
                    </span>
                  </div>
                  <span className="text-[11px] text-slate-400 shrink-0">Today, 14:22</span>
                </div>

                {/* Row 2 */}
                <div className="p-3 rounded-lg border border-border/80 bg-elevated/40 flex items-center justify-between gap-3">
                  <div className="space-y-0.5 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-white font-medium truncate">HDFC Bank Transaction OTP</span>
                      <Badge variant="safe">12 Likely Safe</Badge>
                    </div>
                    <span className="text-[11px] text-muted-foreground block truncate">
                      &ldquo;OTP for Rs 1,450.00 at AMAZON INDIA... Bank NEVER calls...&rdquo;
                    </span>
                  </div>
                  <span className="text-[11px] text-slate-400 shrink-0">Yesterday</span>
                </div>

                {/* Row 3 */}
                <div className="p-3 rounded-lg border border-border/80 bg-elevated/40 flex items-center justify-between gap-3">
                  <div className="space-y-0.5 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-white font-medium truncate">sbi-kyc-update.xyz Domain</span>
                      <Badge variant="critical">96 Critical</Badge>
                    </div>
                    <span className="text-[11px] text-muted-foreground block truncate">
                      Matched URLhaus Phishing blocklist (source: URLhaus)
                    </span>
                  </div>
                  <span className="text-[11px] text-slate-400 shrink-0">Oct 05</span>
                </div>
              </div>

              {/* Ledger Controls */}
              <div className="pt-2 flex items-center justify-between text-xs text-muted-foreground font-mono">
                <span className="text-[11px]">Encrypted at rest · Access controlled</span>
                <span className="text-accent-cyan cursor-pointer hover:underline">
                  Export CSV / JSON Dossier
                </span>
              </div>
            </div>
          </div>

          {/* Right Column: Copy & Value Proposition */}
          <div className="lg:col-span-5 order-1 lg:order-2 space-y-6">
            <span className="font-mono text-xs uppercase tracking-widest text-primary font-semibold flex items-center gap-2">
              <Shield className="w-4 h-4 text-primary" />
              PRIVATE INCIDENT RETENTION
            </span>

            <h2 className="font-mono text-3xl sm:text-4xl font-bold text-white tracking-tight">
              Personal Scan History &amp; Trend Tracking
            </h2>

            <p className="text-sm sm:text-base text-muted-foreground leading-relaxed">
              Every analysis is tied to your encrypted account session. Review previous threat evaluations, track recurring phishing campaigns against your number, or purge records on demand.
            </p>

            <ul className="space-y-3 font-mono text-xs text-slate-300">
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-accent-cyan shrink-0" />
                <span>Zero-leakage user isolation: each account only accesses their own scans.</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-accent-cyan shrink-0" />
                <span>Optional &ldquo;Save to History&rdquo; toggle for transient, zero-storage scans.</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-accent-cyan shrink-0" />
                <span>One-click full scan deletion whenever you choose.</span>
              </li>
            </ul>

            <div className="pt-2">
              <Button asChild variant="outline" className="gap-2">
                <Link href="/history">
                  View Scan Archive
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
