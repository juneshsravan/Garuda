import React from "react";
import { Search, Cpu, CheckCircle2, ShieldCheck, FileText } from "lucide-react";

const steps = [
  {
    step: "01",
    title: "DETECT",
    icon: Search,
    color: "text-blue-400",
    bg: "bg-blue-500/10",
    border: "border-blue-500/30",
    description:
      "Ingests suspicious text, URLs, and QR codes across 5 Indian languages. Normalizes leetspeak, homoglyphs, and hidden characters before evaluating indicators.",
  },
  {
    step: "02",
    title: "EXPLAIN",
    icon: Cpu,
    color: "text-cyan-400",
    bg: "bg-cyan-500/10",
    border: "border-cyan-500/30",
    description:
      "No black-box guesses. Scores are computed transparently via Noisy-OR logic. Every indicator and legitimacy signal is displayed with verbatim evidence snippets cut on word boundaries.",
  },
  {
    step: "03",
    title: "VERIFY",
    icon: CheckCircle2,
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/30",
    description:
      "Prescribes concrete, zero-trust verification procedures: how to check electricity board portals, verify bank alerts, or inspect genuine courier apps without clicking unknown links.",
  },
  {
    step: "04",
    title: "PROTECT",
    icon: ShieldCheck,
    color: "text-amber-400",
    bg: "bg-amber-500/10",
    border: "border-amber-500/30",
    description:
      "Immediate action protocols to prevent irreversible financial loss: enforce UPI PIN rules, block malicious sender numbers, and freeze compromised credentials.",
  },
  {
    step: "05",
    title: "REPORT",
    icon: FileText,
    color: "text-purple-400",
    bg: "bg-purple-500/10",
    border: "border-purple-500/30",
    description:
      "Generates an immutable incident dossier with a unique GAR-2026-XXXXXX reference ID. Connects directly to external reporting resources like Helpline 1930 and cybercrime.gov.in.",
  },
];

export function HowItWorksSection() {
  return (
    <section id="how-it-works" className="py-20 sm:py-28 border-t border-border/80 bg-surface/30">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <span className="font-mono text-xs uppercase tracking-widest text-accent-cyan font-semibold">
            THE 5-SECTOR DEFENSE LIFECYCLE
          </span>
          <h2 className="font-mono text-3xl sm:text-4xl font-bold text-white mt-3">
            How GARUDA Works
          </h2>
          <p className="text-sm sm:text-base text-muted-foreground mt-4 leading-relaxed">
            From initial suspicious payload to verified containment: a rigorous, explainable pipeline built specifically for Indian digital payment and messaging vectors.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {steps.map((item) => {
            const Icon = item.icon;
            return (
              <div
                key={item.step}
                className="rounded-xl border border-border bg-surface p-5 flex flex-col justify-between hover:border-slate-600 transition-all hover:bg-elevated/40"
              >
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <span className="font-mono text-xs font-bold text-muted-foreground">
                      STAGE {item.step}
                    </span>
                    <div
                      className={`w-9 h-9 rounded-lg ${item.bg} ${item.border} border flex items-center justify-center ${item.color}`}
                    >
                      <Icon className="w-4 h-4" />
                    </div>
                  </div>
                  <h3 className="font-mono text-base font-bold text-white mb-2">
                    {item.title}
                  </h3>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    {item.description}
                  </p>
                </div>

                <div className="mt-4 pt-3 border-t border-border/60 font-mono text-[11px] text-slate-400">
                  Target SLA: &lt; 3s
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
