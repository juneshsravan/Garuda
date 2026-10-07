import React from "react";
import { ShieldAlert, AlertOctagon, CheckCircle2, ArrowRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export function QrUpiSection() {
  return (
    <section id="qr-upi" className="py-20 sm:py-28 border-t border-border/80 bg-surface/30">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          {/* Left Column: Context & Critical Rule */}
          <div className="lg:col-span-6 space-y-6">
            <span className="font-mono text-xs uppercase tracking-widest text-risk-high font-semibold flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-risk-high" />
              SPECIALIZED INDIA PAYMENT DEFENSE
            </span>

            <h2 className="font-mono text-3xl sm:text-4xl font-bold text-white tracking-tight">
              QR Code &amp; UPI Collect Fraud Protection
            </h2>

            <p className="text-sm sm:text-base text-muted-foreground leading-relaxed">
              India&apos;s Unified Payments Interface is lightning fast, but scammers weaponize it through deceptive &ldquo;reward QR codes&rdquo; and reverse collect requests. GARUDA intercepts these before money leaves your account.
            </p>

            {/* The Golden UPI Rule Card */}
            <div className="rounded-xl border border-risk-high/40 bg-risk-high/10 p-5 space-y-2">
              <div className="flex items-center gap-2 text-risk-high font-mono text-sm font-bold">
                <AlertOctagon className="w-4 h-4 shrink-0" />
                THE GOLDEN UPI RULE
              </div>
              <p className="text-xs sm:text-sm text-slate-200 leading-relaxed font-mono">
                Receiving money <span className="text-white font-bold underline decoration-risk-high">NEVER</span> requires entering your UPI PIN, scanning any QR code, or approving a collect notification.
              </p>
            </div>

            <div className="space-y-3 pt-2">
              <div className="flex items-start gap-3">
                <CheckCircle2 className="w-4 h-4 text-accent-cyan shrink-0 mt-0.5" />
                <p className="text-xs sm:text-sm text-slate-300">
                  <strong className="text-white">Prefilled Debit Trap Detection:</strong> Flags QR codes claiming to give cashback but embedding an <code className="text-accent-cyan bg-elevated px-1 py-0.5 rounded">&am=5000</code> payment debit request.
                </p>
              </div>

              <div className="flex items-start gap-3">
                <CheckCircle2 className="w-4 h-4 text-accent-cyan shrink-0 mt-0.5" />
                <p className="text-xs sm:text-sm text-slate-300">
                  <strong className="text-white">Merchant Spoofing Intelligence:</strong> Distinguishes verified corporate payment aggregators from personal savings VPAs masquerading as electricity boards or government refund desks.
                </p>
              </div>

              <div className="flex items-start gap-3">
                <CheckCircle2 className="w-4 h-4 text-accent-cyan shrink-0 mt-0.5" />
                <p className="text-xs sm:text-sm text-slate-300">
                  <strong className="text-white">Zero Link-Traversing Architecture:</strong> Decodes and evaluates UPI deep links strictly offline. Never initiates payments or invokes third-party payment intents.
                </p>
              </div>
            </div>

            <div className="pt-2">
              <Button asChild className="gap-2">
                <Link href="/qr-analyzer">
                  Test a Suspicious QR Code
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </Button>
            </div>
          </div>

          {/* Right Column: Visual Breakdown of a Fake UPI QR Payload */}
          <div className="lg:col-span-6">
            <div className="rounded-xl border border-border bg-surface p-6 shadow-xl space-y-5">
              <div className="flex items-center justify-between border-b border-border/80 pb-3">
                <span className="font-mono text-xs text-muted-foreground uppercase">
                  DECODED UPI INTENT URI
                </span>
                <Badge variant="high">Deceptive Payload</Badge>
              </div>

              {/* Raw Payload Card */}
              <div className="bg-[#070B14] p-3.5 rounded-lg border border-border/70 font-mono text-xs text-slate-300 break-all leading-relaxed">
                upi://pay?<span className="text-accent-cyan">pa=quick.lottery.win@ybl</span>&<span className="text-emerald-400">pn=StateKBCDesk</span>&<span className="text-risk-high font-bold">am=2500</span>&<span className="text-amber-400">tn=ClaimGSTFee</span>
              </div>

              {/* Dissected Parameter Cards */}
              <div className="grid grid-cols-2 gap-3 text-xs font-mono">
                <div className="p-3 rounded-lg border border-border bg-elevated/40">
                  <span className="text-[10px] text-muted-foreground uppercase block">Payee VPA (pa)</span>
                  <span className="text-slate-200 break-all font-semibold">quick.lottery.win@ybl</span>
                  <span className="text-[10px] text-risk-high block mt-1">⚠️ Personal handle, not a merchant</span>
                </div>

                <div className="p-3 rounded-lg border border-border bg-elevated/40">
                  <span className="text-[10px] text-muted-foreground uppercase block">Payee Name (pn)</span>
                  <span className="text-slate-200 font-semibold">StateKBCDesk</span>
                  <span className="text-[10px] text-risk-high block mt-1">⚠️ Impersonating state lottery</span>
                </div>

                <div className="p-3 rounded-lg border border-border bg-elevated/40">
                  <span className="text-[10px] text-muted-foreground uppercase block">Preloaded Amount (am)</span>
                  <span className="text-risk-high font-bold text-sm">₹2,500.00</span>
                  <span className="text-[10px] text-risk-high block mt-0.5">⚠️ Will DEBIT from your bank</span>
                </div>

                <div className="p-3 rounded-lg border border-border bg-elevated/40">
                  <span className="text-[10px] text-muted-foreground uppercase block">Note / Transaction (tn)</span>
                  <span className="text-slate-200 font-semibold">ClaimGSTFee</span>
                  <span className="text-[10px] text-amber-400 block mt-1">⚠️ Coercive fee pretext</span>
                </div>
              </div>

              {/* Verdict Summary */}
              <div className="p-3.5 rounded-lg border border-risk-high/30 bg-risk-high/10 flex items-center justify-between text-xs font-mono">
                <div className="space-y-0.5">
                  <div className="font-bold text-white">GARUDA VERDICT: FRAUDULENT REVERSE DEBIT</div>
                  <div className="text-[11px] text-slate-300">Scanning this QR initiates a transfer of ₹2,500 out of your balance.</div>
                </div>
                <div className="text-right shrink-0 ml-2">
                  <span className="text-xs text-risk-high font-extrabold text-base">94/100</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
