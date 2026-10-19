"use client";

/**
 * IntroGate - wraps the /login and /register pages.
 *
 * First visit in a browser session: the cinematic intro plays ON TOP of the real page,
 * which is already rendered underneath, so the final fade reveals the actual login form
 * (no route change, no white flash). Afterwards sessionStorage remembers it, so
 * refreshing or coming back in the same session goes straight to the page.
 *
 * <ReplayIntroButton /> anywhere inside the gate plays it again.
 */
import React, { createContext, useCallback, useContext, useState, useSyncExternalStore } from "react";
import { GarudaIntro } from "./GarudaIntro";
import { hasSeenIntro, markIntroSeen, prefersReducedMotion } from "@/lib/intro";

type Mode = "checking" | "playing" | "done";

const IntroContext = createContext<{ replay: () => void } | null>(null);

const noopSubscribe = () => () => {};

function subscribeReducedMotion(cb: () => void) {
  if (typeof window === "undefined" || !window.matchMedia) return () => {};
  const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
  mq.addEventListener("change", cb);
  return () => mq.removeEventListener("change", cb);
}

export function IntroGate({ children }: { children: React.ReactNode }) {
  // Server render + first hydration frame = "checking"; then the browser value.
  const stored = useSyncExternalStore(
    noopSubscribe,
    () => (hasSeenIntro() ? "seen" : "unseen"),
    () => "checking"
  );
  const reduced = useSyncExternalStore(subscribeReducedMotion, prefersReducedMotion, () => false);

  // Set after the intro finishes or when the user hits "Replay intro"
  const [override, setOverride] = useState<Mode | null>(null);
  const [runId, setRunId] = useState(0);

  const mode: Mode =
    override ?? (stored === "checking" ? "checking" : stored === "seen" ? "done" : "playing");

  const handleFinish = useCallback(() => {
    markIntroSeen();
    setOverride("done");
  }, []);

  const replay = useCallback(() => {
    setRunId((n) => n + 1);
    setOverride("playing");
  }, []);

  return (
    <IntroContext.Provider value={{ replay }}>
      {/* inert: while the intro plays, the form underneath can't be tabbed into */}
      <div inert={mode === "playing"}>{children}</div>

      {mode === "checking" && (
        // Same colour as the intro, shown for one frame while we read sessionStorage,
        // so first-time visitors never glimpse the form before the intro starts.
        <div aria-hidden="true" style={{ position: "fixed", inset: 0, zIndex: 100, background: "#020711" }} />
      )}

      {mode === "playing" && <GarudaIntro key={runId} onFinish={handleFinish} reducedMotion={reduced} />}
    </IntroContext.Provider>
  );
}

export function ReplayIntroButton({ className = "" }: { className?: string }) {
  const ctx = useContext(IntroContext);
  if (!ctx) return null;
  return (
    <button type="button" onClick={ctx.replay} className={className}>
      ↻ Replay intro
    </button>
  );
}
