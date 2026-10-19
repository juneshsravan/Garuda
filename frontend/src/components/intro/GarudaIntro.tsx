"use client";

/**
 * GarudaIntro - cinematic brand intro shown before /login and /register.
 *
 * Scenes (full version, ~7.5s):
 *   1. THE SIGNAL     0-2s   cyan particles fly in and form the eagle (sampled from garuda-eagle.png)
 *   2. THE PROTECTION 2-4s   shield outline draws top-down behind the eagle, tagline 1
 *   3. THE MISSION    4-6.5s mark shrinks up, GARUDA / SECURITY CONSOLE / tagline 2
 *   4. ENTER GARUDA   6.5s+  whole intro fades out, revealing the real login page underneath
 *
 * Uses CSS transitions/keyframes (garuda-intro.css, gi- prefixed classes) + one lightweight <canvas> for the particles.
 * Reduced-motion users get a ~2.5s fade-only version.
 * Sound effects are synthesised with Web Audio (introSound.ts) - no audio files.
 */
import React, { useCallback, useEffect, useRef, useState } from "react";
import { Volume2, VolumeX } from "lucide-react";
import "./garuda-intro.css";
import { createIntroSound, type IntroCue, type IntroSound } from "./introSound";

export const EAGLE_SRC = "/brand/garuda-eagle.png";
const EAGLE_W = 646;
const EAGLE_H = 387;

// Shield geometry, same as /public/brand/garuda-shield.svg (viewBox 0 0 100 112)
const SHIELD_RIGHT = "M50 3 L92 18 V54 C92 80 74 99 50 109";
const SHIELD_LEFT = "M50 3 L8 18 V54 C8 80 26 99 50 109";
const SHIELD_FULL = "M50 3 L92 18 V54 C92 80 74 99 50 109 C26 99 8 80 8 54 V18 Z";
const INNER_RIGHT = "M50 10 L85 22.5 V54 C85 76 70 92 50 101";
const INNER_LEFT = "M50 10 L15 22.5 V54 C15 76 30 92 50 101";

type Flag =
  | "s1" | "eagleOn" | "s2" | "tag1" | "tag1Hide" | "shieldDone"
  | "s3" | "name" | "sub" | "div" | "tag2" | "out" | "fast";

interface GarudaIntroProps {
  onFinish: () => void;
  reducedMotion?: boolean;
}

interface Particle {
  sx: number; sy: number; tx: number; ty: number;
  curl: number; delay: number; dur: number; size: number; tw: number; col: string;
}

export function GarudaIntro({ onFinish, reducedMotion = false }: GarudaIntroProps) {
  const [flags, setFlags] = useState<Set<Flag>>(() => new Set());
  const markRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const hudTextRef = useRef<HTMLSpanElement>(null);
  const hudPctRef = useRef<HTMLSpanElement>(null);
  const hudBarRef = useRef<HTMLSpanElement>(null);
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);
  const finished = useRef(false);
  const soundRef = useRef<IntroSound | null>(null);
  // "locked" = browser hasn't allowed audio yet (no click on the site so far)
  const [sound, setSound] = useState<"on" | "off" | "locked">("locked");

  const cue = useCallback((c: IntroCue) => soundRef.current?.cue(c), []);

  const on = useCallback((...f: Flag[]) => {
    setFlags((prev) => {
      const next = new Set(prev);
      f.forEach((x) => next.add(x));
      return next;
    });
  }, []);

  const finish = useCallback(
    (fast: boolean) => {
      if (finished.current) return;
      finished.current = true;
      soundRef.current?.stopTension();
      cue("exit");
      timers.current.forEach(clearTimeout);
      timers.current = [];
      on(...(fast ? (["out", "fast"] as Flag[]) : (["out"] as Flag[])));
      // let the fade complete, then unmount (the login page is already rendered underneath)
      timers.current.push(setTimeout(onFinish, fast ? 380 : 950));
    },
    [on, onFinish, cue]
  );

  /* ---------------- sound ---------------- */
  useEffect(() => {
    const s = createIntroSound();
    soundRef.current = s;
    let cancelled = false;
    s.unlock().then((running) => {
      if (cancelled) return;
      setSound(running ? (s.isMuted() ? "off" : "on") : "locked");
    });
    return () => {
      cancelled = true;
      s.dispose();
      soundRef.current = null;
    };
  }, []);

  const enableSound = useCallback(async () => {
    const s = soundRef.current;
    if (!s) return;
    const running = await s.unlock();
    if (!running) return;
    s.setMuted(false);
    setSound("on");
  }, []);

  const toggleSound = useCallback(async () => {
    const s = soundRef.current;
    if (!s) return;
    if (sound === "locked" || sound === "off") return enableSound();
    s.setMuted(true);
    setSound("off");
  }, [sound, enableSound]);

  /* ---------------- timeline ---------------- */
  useEffect(() => {
    const at = (ms: number, fn: () => void) => timers.current.push(setTimeout(fn, ms));

    if (reducedMotion) {
      at(30, () => on("s1", "eagleOn", "s2", "shieldDone", "s3"));
      at(200, () => { on("name", "sub", "div", "tag2"); cue("brand"); });
      at(2200, () => finish(false));
    } else {
      at(30, () => { on("s1"); cue("tension"); cue("signal"); }); // Scene 1 - THE SIGNAL
      at(1750, () => { on("eagleOn"); cue("form"); });
      at(2000, () => { on("s2"); cue("shield"); });            // Scene 2 - THE PROTECTION
      at(2550, () => on("tag1"));
      at(3350, () => { on("shieldDone"); cue("shieldDone"); });
      at(3600, () => cue("riser"));
      at(4000, () => on("tag1Hide", "s3"));                    // Scene 3 - THE MISSION
      at(4350, () => { on("name"); cue("brand"); });
      at(4750, () => on("sub"));
      at(4950, () => on("div"));
      at(5150, () => on("tag2"));
      at(6500, () => finish(false));                // Scene 4 - ENTER GARUDA
    }

    const t = timers.current;
    return () => t.forEach(clearTimeout);
  }, [reducedMotion, on, finish, cue]);

  /* ---------------- keyboard: Esc skips ---------------- */
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") finish(true);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [finish]);

  /* ---------------- scan readout (updated via refs, no re-renders) ---------------- */
  useEffect(() => {
    if (reducedMotion) return;
    const start = performance.now();
    const id = setInterval(() => {
      const t = performance.now() - start;
      const pct = Math.min(100, Math.max(0, Math.round(((t - 200) / 3100) * 100)));
      const text =
        t < 1750 ? "ESTABLISHING SECURE SIGNAL" : t < 3350 ? "SCANNING THREAT VECTORS" : "SHIELD ARMED · SYSTEM SECURE";
      if (hudTextRef.current) hudTextRef.current.textContent = text;
      if (hudPctRef.current) hudPctRef.current.textContent = t < 3350 ? `${String(pct).padStart(2, "0")}%` : "✓";
      if (hudBarRef.current) hudBarRef.current.style.transform = `scaleX(${pct / 100})`;
      if (t > 3400) clearInterval(id);
    }, 50);
    return () => clearInterval(id);
  }, [reducedMotion]);

  /* ---------------- particles that form the eagle ---------------- */
  useEffect(() => {
    if (reducedMotion) return;
    const canvas = canvasRef.current;
    const mark = markRef.current;
    if (!canvas || !mark) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let raf = 0;
    let alive = true;
    let particles: Particle[] = [];
    const start = performance.now();

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const W = window.innerWidth;
    const H = window.innerHeight;
    canvas.width = Math.round(W * dpr);
    canvas.height = Math.round(H * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    const img = new Image();
    img.decoding = "async";
    img.src = EAGLE_SRC;

    img.onload = () => {
      if (!alive) return;
      // Rendered eagle box (CSS px) before any scene-3 transform
      const r = mark.getBoundingClientRect();
      const w = Math.max(1, Math.round(r.width));
      const h = Math.max(1, Math.round((w * EAGLE_H) / EAGLE_W));
      const off = document.createElement("canvas");
      off.width = w;
      off.height = h;
      const o = off.getContext("2d", { willReadFrequently: true });
      if (!o) return;
      o.drawImage(img, 0, 0, w, h);
      let data: Uint8ClampedArray;
      try {
        data = o.getImageData(0, 0, w, h).data;
      } catch {
        return; // can't sample - the eagle still fades in normally
      }

      // pick a step so we get roughly 1800-2200 points regardless of screen size
      let opaque = 0;
      for (let i = 3; i < data.length; i += 16) if (data[i] > 90) opaque++;
      const step = Math.max(2, Math.round(Math.sqrt((opaque * 4) / 2000)));

      const targets: { x: number; y: number; c: [number, number, number] }[] = [];
      for (let y = 0; y < h; y += step) {
        for (let x = 0; x < w; x += step) {
          const i = (y * w + x) * 4;
          if (data[i + 3] > 90) targets.push({ x: r.left + x, y: r.top + y, c: [data[i], data[i + 1], data[i + 2]] });
        }
      }

      const cx = W / 2;
      const cy = r.top + r.height / 2;
      const R = Math.max(W, H);
      particles = targets.map((t) => {
        const a = Math.random() * Math.PI * 2;
        const d = R * (0.35 + Math.random() * 0.55);
        // lift dark-blue feather colours toward cyan so they read as light
        const c = t.c.map((v, k) => Math.min(255, Math.round(v * 0.55 + [120, 225, 255][k] * 0.55)));
        return {
          sx: cx + Math.cos(a) * d,
          sy: cy + Math.sin(a) * d,
          tx: t.x,
          ty: t.y,
          curl: (Math.random() - 0.5) * 140,
          delay: 150 + Math.random() * 550,
          dur: 950 + Math.random() * 450,
          size: Math.random() < 0.15 ? 1.8 : 1.15,
          tw: Math.random() * Math.PI * 2,
          col: `${c[0]},${c[1]},${c[2]}`,
        };
      });
    };

    const easeInOut = (p: number) => (p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2);

    const frame = (now: number) => {
      if (!alive) return;
      const t = now - start;
      ctx.clearRect(0, 0, W, H);
      if (t > 2500) return; // particles have handed off to the crisp eagle image; stop the loop
      ctx.globalCompositeOperation = "lighter";
      const handoff = t > 1750 ? Math.max(0, 1 - (t - 1750) / 650) : 1;

      for (const p of particles) {
        const local = (t - p.delay) / p.dur;
        if (local <= 0) continue;
        const k = Math.min(1, local);
        const e = easeInOut(k);
        const dx = p.tx - p.sx;
        const dy = p.ty - p.sy;
        const len = Math.hypot(dx, dy) || 1;
        const bend = Math.sin(Math.PI * e) * p.curl;
        const x = p.sx + dx * e + (-dy / len) * bend;
        const y = p.sy + dy * e + (dx / len) * bend;
        let a = Math.min(1, local * 3) * handoff;
        if (k === 1) a *= 0.75 + 0.25 * Math.sin(t / 90 + p.tw);
        ctx.fillStyle = `rgba(${p.col},${a})`;
        ctx.fillRect(x, y, p.size, p.size);
        if (k < 1) {
          ctx.fillStyle = `rgba(0,217,255,${a * 0.25})`;
          ctx.fillRect(x - dx * 0.012, y - dy * 0.012, p.size, p.size);
        }
      }
      raf = requestAnimationFrame(frame);
    };
    raf = requestAnimationFrame(frame);

    return () => {
      alive = false;
      cancelAnimationFrame(raf);
    };
  }, [reducedMotion]);

  const has = (f: Flag) => flags.has(f);
  const rootClass = [
    "gi-root",
    reducedMotion && "gi-rm",
    has("s1") && "gi-s1",
    has("eagleOn") && "gi-eagleOn",
    has("s2") && "gi-s2",
    has("shieldDone") && "gi-shieldDone",
    has("s3") && "gi-s3",
    has("out") && "gi-out",
    has("fast") && "gi-fast",
  ]
    .filter(Boolean)
    .join(" ");

  const rise = (show: boolean, hide = false) =>
    ["gi-rise", show && "gi-show", hide && "gi-hide"].filter(Boolean).join(" ");

  return (
    <div
      className={rootClass}
      role="dialog"
      aria-modal="true"
      aria-label="GARUDA introduction"
      onPointerDown={() => {
        if (sound === "locked") enableSound();
      }}
    >
      <div className={`${"gi-layer"} ${"gi-ambCyan"}`} />
      <div className={`${"gi-layer"} ${"gi-ambViolet"}`} />
      <div className={`${"gi-layer"} ${"gi-dust"}`} />
      <div className={`${"gi-layer"} ${"gi-scanTexture"}`} />
      <div className={"gi-layer"} aria-hidden="true">
        <div className={"gi-scanline"} />
        <div className={"gi-scanline"} />
        <div className={"gi-scanline"} />
      </div>

      <canvas ref={canvasRef} className={"gi-canvas"} aria-hidden="true" />

      <div ref={markRef} className={"gi-mark"}>
        <div className={"gi-glow"} />
        <div className={"gi-pulseUnder"} />
        <div className={"gi-ring"} />

        {/* target-lock corner brackets around the shield */}
        <svg className={"gi-brackets"} viewBox="0 0 100 112" aria-hidden="true">
          <path d="M0 16 V0 H16" />
          <path d="M84 0 H100 V16" />
          <path d="M100 96 V112 H84" />
          <path d="M16 112 H0 V96" />
        </svg>

        <svg className={"gi-shield"} viewBox="0 0 100 112" aria-hidden="true">
          <defs>
            <linearGradient id="garudaShieldFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="rgba(0,217,255,0.10)" />
              <stop offset="100%" stopColor="rgba(128,85,255,0.06)" />
            </linearGradient>
          </defs>
          <g className={"gi-net"}>
            <path pathLength={1} d="M92 30 L108 24 L122 24" />
            <path pathLength={1} d="M92 60 L110 60 L116 54" />
            <path pathLength={1} d="M80 88 L98 98 L110 98" />
            <path pathLength={1} d="M8 30 L-8 24 L-22 24" />
            <path pathLength={1} d="M8 60 L-10 60 L-16 66" />
            <path pathLength={1} d="M20 88 L2 98 L-10 98" />
            <circle cx="122" cy="24" r="1" />
            <circle cx="116" cy="54" r="1" />
            <circle cx="110" cy="98" r="1" />
            <circle cx="-22" cy="24" r="1" />
            <circle cx="-16" cy="66" r="1" />
            <circle cx="-10" cy="98" r="1" />
          </g>
          <path className={"gi-shieldFill"} d={SHIELD_FULL} />
          {/* two halves so the outline draws from the top down both sides at once */}
          <path className={"gi-shieldLine"} pathLength={1} d={SHIELD_RIGHT} />
          <path className={"gi-shieldLine"} pathLength={1} d={SHIELD_LEFT} />
          <path className={"gi-shieldInner"} pathLength={1} d={INNER_RIGHT} />
          <path className={"gi-shieldInner"} pathLength={1} d={INNER_LEFT} />
        </svg>

        {/* eslint-disable-next-line @next/next/no-img-element -- plain img: decoded once, also sampled by the particle canvas */}
        <img
          className={"gi-eagle"}
          src={EAGLE_SRC}
          width={EAGLE_W}
          height={EAGLE_H}
          alt=""
          draggable={false}
          fetchPriority="high"
        />

        {/* laser scan beam sweeping over the eagle */}
        <div className={"gi-beam"} aria-hidden="true" />
      </div>

      <div className={"gi-hud"} aria-hidden="true">
        <div className={"gi-hudRow"}>
          <span ref={hudTextRef}>ESTABLISHING SECURE SIGNAL</span>
          <span ref={hudPctRef} className={"gi-hudPct"}>00%</span>
        </div>
        <div className={"gi-hudTrack"}>
          <span ref={hudBarRef} className={"gi-hudBar"} />
        </div>
      </div>

      <p className={`${"gi-tagline1"} ${rise(has("tag1"), has("tag1Hide"))}`}>
        Every <b>Click</b>. Every <b>Message</b>. Every <b>Threat</b>.
      </p>

      <div className={"gi-brand"}>
        <h1 className={["gi-brandName", has("name") && "gi-show"].filter(Boolean).join(" ")}>GARUDA</h1>
        <div className={`${"gi-brandSub"} ${rise(has("sub"))}`}>SECURITY CONSOLE</div>
        <div className={["gi-divider", has("div") && "gi-show"].filter(Boolean).join(" ")} />
        <p className={`${"gi-tagline2"} ${rise(has("tag2"))}`}>
          <span>Detect</span> threats. <span>Verify</span> trust. <span>Stay</span> safe.
        </p>
      </div>

      <button
        type="button"
        className={"gi-sound"}
        onClick={toggleSound}
        onPointerDown={(e) => e.stopPropagation()}
        aria-pressed={sound === "on"}
        aria-label={sound === "on" ? "Mute intro sound" : "Turn on intro sound"}
      >
        {sound === "on" ? <Volume2 size={14} /> : <VolumeX size={14} />}
        {sound === "on" ? "SOUND ON" : sound === "off" ? "SOUND OFF" : "TAP FOR SOUND"}
      </button>

      <button type="button" className={"gi-skip"} onClick={() => finish(true)}>
        SKIP INTRO →
      </button>
    </div>
  );
}
