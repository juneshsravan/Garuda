import React from "react";
import { FileCheck2, ExternalLink, ShieldAlert, Clock, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";

export function ReportingSection() {
  return (
    <section id="reporting" className="py-20 sm:py-28 border-t border-border/80">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <span className="font-mono text-xs uppercase tracking-widest text-purple-400 font-semibold">
            STANDARDIZED EVIDENCE DOSSIERS
          </span>
          <h2 className="font-mono text-3xl sm:text-4xl font-bold text-white mt-3">
            Incident Packaging &amp; Verified Reporting
          </h2>
          <p className="text-sm sm:text-base text-muted-foreground mt-4 leading-relaxed">
            Transform scam messages, deceptive payment QR codes, and phishing links into structured evidence dossiers ready for official reporting.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left Column: Dossier Card */}
          <div className="lg:col-span-7 rounded-xl border border-border bg-surface p-6 shadow-xl space-y-5">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/80 pb-3">
              <div>
                <span className="font-mono text-xs text-muted-foreground uppercase block">
                  OFFICIAL GARUDA REFERENCE CODE
                </span>
                <span className="font-mono text-lg font-bold text-accent-cyan">
                  GAR-2026-000142
                </span>
              </div>
              <Badge variant="outline" className="border-purple-500/40 text-purple-300 bg-purple-500/10">
                Submitted to GARUDA
              </Badge>
            </div>

            <div className="space-y-3 font-mono text-xs">
              <div className="p-3 rounded-lg border border-border bg-elevated/40">
                <span className="text-[11px] text-muted-foreground block mb-1">INCIDENT CATEGORY</span>
                <span className="text-white font-semibold">Fake Electricity Disconnection &amp; Officer Impersonation</span>
              </div>

              <div className="p-3 rounded-lg border border-border bg-elevated/40">
                <span className="text-[11px] text-muted-foreground block mb-1">ATTACHED EVIDENCE</span>
                <span className="text-slate-300">
                  SMS text payload, verified phone number (+91 9000000001), 3 extracted indicators, and SHA-256 integrity hash.
                </span>
              </div>
            </div>

            {/* Timeline */}
            <div className="pt-2">
              <span className="font-mono text-xs text-muted-foreground uppercase block mb-3">
                STATUS LIFECYCLE
              </span>
              <div className="grid grid-cols-3 gap-2 text-center font-mono text-[11px]">
                <div className="p-2 rounded bg-purple-500/15 border border-purple-500/30 text-purple-300 font-semibold">
                  1. Submitted
                </div>
                <div className="p-2 rounded bg-elevated border border-border text-slate-400">
                  2. Under Review
                </div>
                <div className="p-2 rounded bg-elevated border border-border text-slate-400">
                  3. Packaged
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: External Law Enforcement Disclosure Card */}
          <div className="lg:col-span-5 rounded-xl border border-border bg-surface p-6 space-y-5">
            <div className="space-y-1">
              <h3 className="font-mono text-base font-bold text-white flex items-center gap-2">
                <ShieldAlert className="w-4.5 h-4.5 text-amber-400" />
                Official Indian Reporting Channels
              </h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Need to file an official FIR or report financial fraud immediately? Use India&apos;s designated national portals:
              </p>
            </div>

            <div className="space-y-3 font-mono text-xs">
              {/* Channel 1 */}
              <a
                href="https://cybercrime.gov.in"
                target="_blank"
                rel="noopener noreferrer"
                className="p-3.5 rounded-lg border border-border hover:border-slate-500 bg-elevated/50 flex items-center justify-between group transition-colors"
              >
                <div>
                  <div className="font-bold text-white group-hover:text-accent-cyan flex items-center gap-1.5">
                    cybercrime.gov.in
                    <ExternalLink className="w-3.5 h-3.5 text-muted-foreground group-hover:text-accent-cyan" />
                  </div>
                  <div className="text-[11px] text-muted-foreground mt-0.5">
                    National Cyber Crime Reporting Portal
                  </div>
                </div>
              </a>

              {/* Channel 2 */}
              <a
                href="tel:1930"
                className="p-3.5 rounded-lg border border-border hover:border-slate-500 bg-elevated/50 flex items-center justify-between group transition-colors"
              >
                <div>
                  <div className="font-bold text-white group-hover:text-accent-cyan flex items-center gap-1.5">
                    National Helpline: 1930
                    <ExternalLink className="w-3.5 h-3.5 text-muted-foreground group-hover:text-accent-cyan" />
                  </div>
                  <div className="text-[11px] text-muted-foreground mt-0.5">
                    Immediate Financial Cyber Fraud Reporting
                  </div>
                </div>
              </a>
            </div>

            {/* Crucial Honesty Warning */}
            <div className="p-3 rounded-lg border border-amber-500/30 bg-amber-500/10 text-[11px] text-slate-300 font-mono leading-relaxed">
              <strong className="text-amber-400">Transparency Disclosure:</strong> GARUDA provides structured evidence packaging and guidance. GARUDA does not submit complaints to law enforcement authorities on your behalf.
            </div>

            <Button asChild className="w-full gap-2 font-mono text-xs">
              <Link href="/reports">
                <FileCheck2 className="w-4 h-4" />
                Go to Report Center
              </Link>
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}
