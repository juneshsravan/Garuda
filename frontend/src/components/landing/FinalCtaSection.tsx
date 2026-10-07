import React from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ShieldCheck, UserPlus, ArrowRight } from "lucide-react";

export function FinalCtaSection() {
  return (
    <section className="py-20 sm:py-28 border-t border-border/80 relative overflow-hidden">
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 text-center relative z-10">
        <div className="rounded-2xl border border-primary/30 bg-gradient-to-b from-elevated/90 to-surface/90 p-8 sm:p-14 shadow-2xl">
          <span className="font-mono text-xs uppercase tracking-widest text-accent-cyan font-semibold block mb-3">
            VERIFY BEFORE YOU CLICK OR PAY
          </span>
          <h2 className="font-mono text-3xl sm:text-5xl font-extrabold text-white tracking-tight mb-4">
            Defend Against Evolving Cyber Threats
          </h2>
          <p className="mx-auto max-w-2xl text-sm sm:text-base text-muted-foreground leading-relaxed mb-8">
            Encountered a suspicious message, unfamiliar QR code, or unexpected lottery alert?
            Get an instant, transparent explanation and actionable verification steps.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Button asChild size="lg" className="w-full sm:w-auto gap-2 font-medium h-12 px-8">
              <Link href="/message-analyzer">
                <ShieldCheck className="w-5 h-5" />
                Analyze a Threat Now
                <ArrowRight className="w-4 h-4" />
              </Link>
            </Button>

            <Button asChild variant="outline" size="lg" className="w-full sm:w-auto gap-2 h-12 px-8">
              <Link href="/register">
                <UserPlus className="w-5 h-5 text-accent-cyan" />
                Create Free Account
              </Link>
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}
