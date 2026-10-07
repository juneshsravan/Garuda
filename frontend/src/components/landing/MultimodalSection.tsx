import React from "react";
import { MessageSquareText, Globe, QrCode, ScanEye, ArrowRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";

const modalities = [
  {
    icon: MessageSquareText,
    title: "Message & SMS Analyzer",
    badge: "5 Indian Languages",
    badgeVariant: "cyan" as const,
    description:
      "Context-aware phrase analysis across English, Hindi, Telugu, Romanized Telugu, and Hinglish. Distinguishes genuine transactional alerts from coercive threats.",
    features: [
      "Leetspeak folding (0TP → OTP, sh@re → share)",
      "Bank advisory legitimacy signal detection",
      "Contextual urgency matching, not single words",
      "Digital arrest and utility disconnection rules",
    ],
    actionLink: "/message-analyzer",
    actionText: "Try Message Analyzer",
  },
  {
    icon: Globe,
    title: "URL & Domain Heuristics",
    badge: "Zero Fetching Safety",
    badgeVariant: "safe" as const,
    description:
      "Static inspection engine that never visits or executes untrusted links. Detects typosquatting and checks against verified threat intelligence.",
    features: [
      "Brand lookalike matching for Indian banks & gov",
      "Subdomain trickery & punycode/IDN detection",
      "StevenBlack & URLhaus threat blocklists",
      "Curated illegal betting platform intelligence",
    ],
    actionLink: "/url-analyzer",
    actionText: "Try URL Analyzer",
  },
  {
    icon: QrCode,
    title: "QR Code & UPI Payee Analyzer",
    badge: "India Payment Vector",
    badgeVariant: "high" as const,
    description:
      "Dissects UPI intent URIs and payment QR codes in memory. Identifies counterfeit cashback schemes, prefilled amounts, and collect request manipulation.",
    features: [
      "Extracts payee VPA, merchant name, and note",
      "Enforces the rule: receiving money never needs a PIN",
      "Flags personal VPAs spoofing reputable enterprises",
      "Safe decoded payload rendering (no auto-opening)",
    ],
    actionLink: "/qr-analyzer",
    actionText: "Try QR Analyzer",
  },
  {
    icon: ScanEye,
    title: "Screenshot & Image OCR",
    badge: "Phase 2 Pipeline",
    badgeVariant: "outline" as const,
    description:
      "Extracts text from screenshots of fake bank debit alerts, fraudulent investment groups, and lottery letters with privacy-first zero storage.",
    features: [
      "Processed strictly in memory; zero disk retention",
      "Magic-byte format and size validation (≤ 5 MB)",
      "Tesseract OCR multi-language character mapping",
      "Integrated directly into the core detection engine",
    ],
    actionLink: "#how-it-works",
    actionText: "View Architecture",
  },
];

export function MultimodalSection() {
  return (
    <section id="multimodal" className="py-20 sm:py-28 border-t border-border/80">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <span className="font-mono text-xs uppercase tracking-widest text-primary font-semibold">
            COMPREHENSIVE COVERAGE
          </span>
          <h2 className="font-mono text-3xl sm:text-4xl font-bold text-white mt-3">
            Multimodal Threat Detection
          </h2>
          <p className="text-sm sm:text-base text-muted-foreground mt-4 leading-relaxed">
            Modern scammers combine SMS urgency, lookalike domains, and fraudulent UPI QR codes. GARUDA provides unified analysis across every vector.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {modalities.map((item) => {
            const Icon = item.icon;
            return (
              <div
                key={item.title}
                className="rounded-xl border border-border bg-surface p-6 sm:p-7 flex flex-col justify-between hover:border-slate-600 transition-all group"
              >
                <div>
                  <div className="flex items-start justify-between gap-3 mb-4">
                    <div className="w-11 h-11 rounded-lg bg-elevated border border-border flex items-center justify-center text-primary group-hover:text-accent-cyan transition-colors">
                      <Icon className="w-5 h-5" />
                    </div>
                    <Badge variant={item.badgeVariant}>{item.badge}</Badge>
                  </div>

                  <h3 className="font-mono text-lg font-bold text-white mb-2">
                    {item.title}
                  </h3>
                  <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed mb-5">
                    {item.description}
                  </p>

                  <ul className="space-y-2 mb-6">
                    {item.features.map((feature) => (
                      <li
                        key={feature}
                        className="text-xs text-slate-300 flex items-center gap-2 font-mono"
                      >
                        <span className="w-1.5 h-1.5 rounded-full bg-primary shrink-0" />
                        {feature}
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="pt-4 border-t border-border/60">
                  <Link
                    href={item.actionLink}
                    className="inline-flex items-center gap-1.5 text-xs font-mono font-semibold text-primary hover:text-accent-cyan transition-colors"
                  >
                    {item.actionText}
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
