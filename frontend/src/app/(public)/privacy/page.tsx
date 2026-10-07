import React from "react";
import Link from "next/link";
import { GarudaLogo } from "@/components/brand/GarudaLogo";
import { ArrowLeft, ShieldCheck, Lock, HardDrive, EyeOff } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-background text-foreground py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto space-y-8">
        <div className="flex items-center justify-between border-b border-border pb-6">
          <Link href="/">
            <GarudaLogo size={36} showWordmark={true} subtitle="PRIVACY &amp; SECURITY" />
          </Link>
          <Button asChild variant="outline" size="sm" className="gap-2">
            <Link href="/">
              <ArrowLeft className="w-4 h-4" />
              Back to Home
            </Link>
          </Button>
        </div>

        <div className="space-y-4">
          <h1 className="font-mono text-3xl font-bold text-white">
            Privacy Policy &amp; Data Architecture
          </h1>
          <p className="text-sm text-muted-foreground font-mono">
            Effective Date: October 2026 · Version 2.0.0
          </p>
        </div>

        <div className="space-y-6 text-sm text-slate-300 leading-relaxed font-sans">
          <section className="space-y-3 rounded-xl border border-border bg-surface p-6">
            <h2 className="font-mono text-lg font-bold text-white flex items-center gap-2">
              <HardDrive className="w-5 h-5 text-accent-cyan" />
              1. Zero Persistent Media Storage
            </h2>
            <p>
              When you upload images or QR codes to GARUDA, they are read entirely in volatile system RAM using OpenCV and pyzbar. We never write uploaded images to disk, storage buckets, or cloud object stores. Once the QR payload is extracted, the memory buffer is wiped immediately.
            </p>
          </section>

          <section className="space-y-3 rounded-xl border border-border bg-surface p-6">
            <h2 className="font-mono text-lg font-bold text-white flex items-center gap-2">
              <EyeOff className="w-5 h-5 text-primary" />
              2. Static Heuristics Without Network Crawling
            </h2>
            <p>
              GARUDA never fetches, executes, or initiates HTTP traffic to URLs submitted for inspection. All domain and link analysis is performed offline through lexical parsing, brand distance calculations, and preloaded threat blocklists. We will never accidentally trigger malicious server-side beacons or phishing counters.
            </p>
          </section>

          <section className="space-y-3 rounded-xl border border-border bg-surface p-6">
            <h2 className="font-mono text-lg font-bold text-white flex items-center gap-2">
              <Lock className="w-5 h-5 text-emerald-400" />
              3. Data Ownership &amp; Audit Logs
            </h2>
            <p>
              All scans recorded in your account are isolated via access controls and row-level isolation. You retain full authority to delete any historical scan record. You can also analyze threats in ephemeral mode with the &ldquo;Don&apos;t save this scan&rdquo; toggle.
            </p>
          </section>

          <section className="space-y-3 rounded-xl border border-amber-500/30 bg-amber-500/10 p-6 font-mono text-xs">
            <h3 className="font-bold text-amber-300 uppercase">
              Law Enforcement Disclaimer
            </h3>
            <p className="text-slate-200 mt-1 leading-relaxed">
              GARUDA is an independent defense intelligence system. GARUDA does not submit reports to law enforcement on your behalf. To file an official complaint, users must contact the National Cyber Crime Reporting Portal at cybercrime.gov.in or helpline 1930.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
