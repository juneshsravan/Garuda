import React from "react";
import { Badge } from "@/components/ui/badge";
import { Scale, ShieldCheck, HelpCircle, Binary, BarChart3, AlertTriangle } from "lucide-react";

const bands = [
  { range: "0 – 24", label: "Likely Safe", variant: "safe" as const, desc: "Legitimacy signals dominate, zero coercive patterns detected." },
  { range: "25 – 44", label: "Suspicious", variant: "suspicious" as const, desc: "Unusual wording, missing official advisory, or unverified link shortener." },
  { range: "45 – 64", label: "Medium Risk", variant: "medium" as const, desc: "Coercive urgency, unverified job/loan offer, or questionable origin." },
  { range: "65 – 100", label: "High Risk", variant: "high" as const, desc: "Definite predatory pattern, credential demand, or fake prize trap." },
  { range: "≥ 85 + Intel", label: "Critical Risk", variant: "critical" as const, desc: "Confirmed blocklist hit or active credential phishing/digital arrest vector." },
  { range: "Incomplete", label: "Unable to Verify", variant: "unverified" as const, desc: "Input unreadable, damaged QR, or insufficient text length." },
];

export function ExplainableRiskSection() {
  return (
    <section id="explainable-risk" className="py-20 sm:py-28 border-t border-border/80">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <span className="font-mono text-xs uppercase tracking-widest text-accent-cyan font-semibold">
            AUDITABLE SCORING LOGIC
          </span>
          <h2 className="font-mono text-3xl sm:text-4xl font-bold text-white mt-3">
            Explainable Risk, Not Black-Box AI
          </h2>
          <p className="text-sm sm:text-base text-muted-foreground mt-4 leading-relaxed">
            Every score on GARUDA is deterministic and mathematically explainable. You always see exactly which phrases added risk and which verified signals reduced it.
          </p>
        </div>

        {/* 3 Pillars of Explainability */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
          <div className="rounded-xl border border-border bg-surface p-6 space-y-3">
            <div className="w-10 h-10 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-primary">
              <Binary className="w-5 h-5" />
            </div>
            <h3 className="font-mono text-base font-bold text-white">
              Mathematical Noisy-OR Model
            </h3>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Calculates threat probability as <code className="text-accent-cyan bg-elevated px-1 py-0.5 rounded font-mono">R = 1 - ∏(1 - wᵢ)</code>. Each detected indicator contributes a calibrated weight based on empirical fraud severity.
            </p>
          </div>

          <div className="rounded-xl border border-border bg-surface p-6 space-y-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <Scale className="w-5 h-5" />
            </div>
            <h3 className="font-mono text-base font-bold text-white">
              Legitimacy Signals &amp; Anti-Gaming
            </h3>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Genuine bank advisories and masked formats apply a legitimacy discount <code className="text-emerald-400 bg-elevated px-1 py-0.5 rounded font-mono">L = 1 - ∏(1 - lⱼ)</code>. Crucially, high-severity threats immediately override all discounts.
            </p>
          </div>

          <div className="rounded-xl border border-border bg-surface p-6 space-y-3">
            <div className="w-10 h-10 rounded-lg bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
              <BarChart3 className="w-5 h-5" />
            </div>
            <h3 className="font-mono text-base font-bold text-white">
              Verbatim Evidence Snippets
            </h3>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Evidence is never vague or hallucinated. Snippets are isolated verbatim on word boundaries from the raw input payload, creating an unshakeable audit trail.
            </p>
          </div>
        </div>

        {/* Risk Bands Hierarchy */}
        <div className="rounded-xl border border-border bg-surface p-6 sm:p-8">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 border-b border-border/80 gap-2">
            <div>
              <h3 className="font-mono text-lg font-bold text-white">
                Honest Calibration &amp; Standardized Risk Bands
              </h3>
              <p className="text-xs text-muted-foreground mt-1">
                GARUDA uses honest language: &ldquo;Likely Safe&rdquo; is never claimed as absolute safety, and threats are labeled &ldquo;Detected&rdquo;, never magically &ldquo;Blocked&rdquo;.
              </p>
            </div>
            <Badge variant="outline" className="self-start sm:self-auto font-mono text-xs">
              ARCHITECTURE §7
            </Badge>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 pt-6">
            {bands.map((band) => (
              <div
                key={band.label}
                className="p-4 rounded-lg border border-border/70 bg-elevated/30 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono text-xs text-slate-400 font-bold">{band.range}</span>
                    <Badge variant={band.variant}>{band.label}</Badge>
                  </div>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    {band.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
