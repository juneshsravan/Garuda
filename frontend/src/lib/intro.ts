/**
 * Session tracking for the cinematic GARUDA intro.
 * The intro plays once per browser session (sessionStorage), before /login and /register.
 * Every access is wrapped in try/catch because sessionStorage can throw
 * (private mode, blocked storage) - in that case we simply play the intro.
 */
export const INTRO_SEEN_KEY = "garuda_intro_seen";

export function hasSeenIntro(): boolean {
  if (typeof window === "undefined") return false;
  try {
    return window.sessionStorage.getItem(INTRO_SEEN_KEY) === "1";
  } catch {
    return false;
  }
}

export function markIntroSeen(): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.setItem(INTRO_SEEN_KEY, "1");
  } catch {
    // ignore
  }
}

export function prefersReducedMotion(): boolean {
  if (typeof window === "undefined" || !window.matchMedia) return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}
