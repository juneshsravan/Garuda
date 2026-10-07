import React from "react";
import Link from "next/link";
import { GarudaLogo } from "@/components/brand/GarudaLogo";
import { Shield, ExternalLink } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-border bg-[#070B14] py-12 sm:py-16 text-muted-foreground text-xs font-mono">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-12">
          {/* Col 1: Brand & Tagline */}
          <div className="md:col-span-1 space-y-3">
            <GarudaLogo size={32} showWordmark={true} subtitle="DETECT. VERIFY. PROTECT." />
            <p className="text-xs text-muted-foreground font-sans leading-relaxed pt-2">
              Autonomous, transparent scam and phishing detection engineered for Indian digital payments and messaging channels.
            </p>
          </div>

          {/* Col 2: Detection Modules */}
          <div className="space-y-2.5">
            <h4 className="font-semibold text-white uppercase tracking-wider text-xs">
              Analyzers
            </h4>
            <ul className="space-y-2">
              <li>
                <Link href="/message-analyzer" className="hover:text-white transition-colors">
                  Message &amp; SMS Analyzer
                </Link>
              </li>
              <li>
                <Link href="/url-analyzer" className="hover:text-white transition-colors">
                  URL &amp; Domain Heuristics
                </Link>
              </li>
              <li>
                <Link href="/qr-analyzer" className="hover:text-white transition-colors">
                  QR &amp; UPI Payee Analyzer
                </Link>
              </li>
              <li>
                <Link href="/history" className="hover:text-white transition-colors">
                  Personal Scan History
                </Link>
              </li>
            </ul>
          </div>

          {/* Col 3: Defense & Reporting */}
          <div className="space-y-2.5">
            <h4 className="font-semibold text-white uppercase tracking-wider text-xs">
              Reporting &amp; Safety
            </h4>
            <ul className="space-y-2">
              <li>
                <Link href="/reports" className="hover:text-white transition-colors">
                  GARUDA Report Center
                </Link>
              </li>
              <li>
                <a
                  href="https://cybercrime.gov.in"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-white transition-colors inline-flex items-center gap-1"
                >
                  cybercrime.gov.in
                  <ExternalLink className="w-3 h-3" />
                </a>
              </li>
              <li>
                <a
                  href="tel:1930"
                  className="hover:text-white transition-colors inline-flex items-center gap-1"
                >
                  Helpline 1930
                  <ExternalLink className="w-3 h-3" />
                </a>
              </li>
              <li>
                <Link href="/privacy" className="hover:text-white transition-colors">
                  Privacy Policy &amp; Security
                </Link>
              </li>
            </ul>
          </div>

          {/* Col 4: Architecture & Integrity */}
          <div className="space-y-2.5">
            <h4 className="font-semibold text-white uppercase tracking-wider text-xs">
              Engine Specs
            </h4>
            <p className="text-[11px] text-slate-400 font-sans leading-relaxed">
              Detection Engine v2.0.0. Deterministic Noisy-OR probability, zero persistent image retention, and Argon2id session authentication.
            </p>
            <div className="pt-2 flex items-center gap-2 text-accent-cyan">
              <Shield className="w-4 h-4" />
              <span>Independent Cyber Defense</span>
            </div>
          </div>
        </div>

        {/* Disclaimer & Bottom Bar */}
        <div className="pt-8 border-t border-border/60 flex flex-col sm:flex-row items-center justify-between gap-4 text-center sm:text-left">
          <p className="text-[11px] text-muted-foreground font-sans">
            &copy; 2026 GARUDA. All rights reserved. Built for Indian digital safety.
          </p>

          <p className="text-[11px] text-amber-400/90 font-sans max-w-xl">
            <strong>Transparency Notice:</strong> GARUDA is an independent defense intelligence system. GARUDA does not submit reports to law enforcement on your behalf.
          </p>
        </div>
      </div>
    </footer>
  );
}
