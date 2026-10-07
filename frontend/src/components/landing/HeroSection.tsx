import React from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, ShieldCheck, Compass, Zap, Lock, Eye } from "lucide-react";

export function HeroSection() {
  return (
    <section className="relative pt-12 pb-16 sm:pt-20 sm:pb-24 overflow-hidden">
      {/* Subtle background grid pattern */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#0d1424_1px,transparent_1px),linear-gradient(to_bottom,#0d1424_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] opacity-40 pointer-events-none" />

      <div className="relative mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 text-center">
        {/* Status Pill */}
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-border bg-surface/80 text-xs font-mono text-muted-foreground mb-6 backdrop-blur-sm">
          <span className="flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-slate-300">Garuda Defense Engine v2.0 Active</span>
          <span className="text-border">|</span>
          <span className="text-accent-cyan">India Cyber Threat Shield</span>
        </div>

        {/* Hero Title */}
        <h1 className="font-mono text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-white mb-6">
          DETECT. VERIFY. <br className="hidden sm:inline" />
          <span className="bg-gradient-to-r from-blue-400 via-primary to-cyan-400 bg-clip-text text-transparent">
            PROTECT.
          </span>
        </h1>

        {/* Hero Subtitle */}
        <p className="mx-auto max-w-2xl text-base sm:text-lg lg:text-xl text-muted-foreground leading-relaxed mb-10">
          AI-powered protection against suspicious messages, QR codes, images and links.
          Defending Indian digital consumers with transparent, explainable threat intelligence.
        </p>

        {/* Hero CTA Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
          <Button asChild size="lg" className="w-full sm:w-auto gap-2 font-medium text-base h-12 px-7">
            <Link href="/message-analyzer">
              <ShieldCheck className="w-5 h-5 text-white" />
              Analyze a Threat
              <ArrowRight className="w-4 h-4" />
            </Link>
          </Button>

          <Button asChild variant="outline" size="lg" className="w-full sm:w-auto gap-2 text-base h-12 px-7">
            <Link href="#how-it-works">
              <Compass className="w-5 h-5 text-accent-cyan" />
              Explore GARUDA
            </Link>
          </Button>
        </div>

        {/* Trust & Methodology Signals */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-border/60 text-left font-mono text-xs">
          <div className="p-3 rounded-lg border border-border/40 bg-surface/30">
            <div className="text-muted-foreground text-[11px] mb-1 flex items-center gap-1.5">
              <Eye className="w-3.5 h-3.5 text-primary" />
              DETECTION PARADIGM
            </div>
            <div className="font-semibold text-slate-200">Multimodal Heuristics</div>
          </div>
          <div className="p-3 rounded-lg border border-border/40 bg-surface/30">
            <div className="text-muted-foreground text-[11px] mb-1 flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5 text-accent-cyan" />
              ANALYSIS SPEED
            </div>
            <div className="font-semibold text-slate-200">&lt; 300ms Synchronous</div>
          </div>
          <div className="p-3 rounded-lg border border-border/40 bg-surface/30">
            <div className="text-muted-foreground text-[11px] mb-1 flex items-center gap-1.5">
              <Lock className="w-3.5 h-3.5 text-amber-400" />
              PRIVACY STANDARD
            </div>
            <div className="font-semibold text-slate-200">Zero Raw Media Storage</div>
          </div>
          <div className="p-3 rounded-lg border border-border/40 bg-surface/30">
            <div className="text-muted-foreground text-[11px] mb-1 flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              EXPLAINABILITY
            </div>
            <div className="font-semibold text-slate-200">Transparent Noisy-OR</div>
          </div>
        </div>
      </div>
    </section>
  );
}
