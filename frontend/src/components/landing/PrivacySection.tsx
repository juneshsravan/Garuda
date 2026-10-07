import React from "react";
import { Lock, EyeOff, ShieldCheck, Database, HardDrive, KeyRound } from "lucide-react";

const safeguards = [
  {
    icon: HardDrive,
    title: "Zero Raw Image Retention",
    desc: "Uploaded QR codes and screenshots are validated by magic bytes, decoded strictly in RAM, and immediately discarded. Images never touch physical disk storage.",
  },
  {
    icon: EyeOff,
    title: "No Outbound URL Crawling",
    desc: "GARUDA never fetches or navigates to analyzed URLs. Inspection is conducted completely offline via static lexical heuristics and local blocklist matches.",
  },
  {
    icon: Database,
    title: "Row-Level Security (RLS)",
    desc: "All database tables in Supabase enforce strict RLS without public API exposure. Every query verifies tenant identity with zero risk of cross-user IDOR.",
  },
  {
    icon: KeyRound,
    title: "Argon2id & Rotated Cookies",
    desc: "Passwords hashed via memory-hard Argon2id. Short-lived 15-minute JWTs live in client memory, while refresh tokens reside in secure httpOnly cookies.",
  },
  {
    icon: ShieldCheck,
    title: "Optional Ephemeral Mode",
    desc: "Want quick zero-trace analysis? Toggle 'Don't save this scan' and nothing is persisted to the database, leaving zero telemetry behind.",
  },
  {
    icon: Lock,
    title: "User Data Sovereignty",
    desc: "You retain unconditional ownership of your scan archive. Delete any individual scan or clear your entire ledger at any time with a single click.",
  },
];

export function PrivacySection() {
  return (
    <section id="privacy" className="py-20 sm:py-28 border-t border-border/80 bg-surface/30">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <span className="font-mono text-xs uppercase tracking-widest text-emerald-400 font-semibold">
            DEFENSE-GRADE PRIVACY
          </span>
          <h2 className="font-mono text-3xl sm:text-4xl font-bold text-white mt-3">
            Privacy &amp; Security Architecture
          </h2>
          <p className="text-sm sm:text-base text-muted-foreground mt-4 leading-relaxed">
            Protecting users from fraud means treating user data with utmost confidentiality. GARUDA is engineered from the ground up for minimal data exposure.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {safeguards.map((item) => {
            const Icon = item.icon;
            return (
              <div
                key={item.title}
                className="rounded-xl border border-border bg-surface p-6 space-y-3 hover:border-slate-600 transition-colors"
              >
                <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                  <Icon className="w-5 h-5" />
                </div>
                <h3 className="font-mono text-base font-bold text-white">
                  {item.title}
                </h3>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {item.desc}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
