/**
 * Cinematic sound effects for the GARUDA intro.
 *
 * Every sound is synthesised live with the Web Audio API: no audio files to download,
 * so the intro stays fast. One AudioContext, a compressor and a small generated reverb.
 *
 * Browsers only allow sound after the visitor has interacted with the site. If they
 * arrived by clicking (e.g. "Sign in" on the landing page) sound starts on its own;
 * on a direct page load the context stays suspended and the intro shows a
 * "Tap for sound" button. Cues that fire while suspended are skipped (not queued),
 * so nothing bursts out late.
 */

export type IntroCue = "tension" | "signal" | "form" | "shield" | "shieldDone" | "riser" | "brand" | "exit";

export interface IntroSound {
  /** true when audio is actually audible (context running and not muted) */
  isAudible(): boolean;
  isMuted(): boolean;
  /** Try to start audio (must be called from a click/tap/keypress to be sure to work). */
  unlock(): Promise<boolean>;
  setMuted(muted: boolean): void;
  cue(c: IntroCue): void;
  /** fade out the suspense bed (drone / heartbeat / scans), e.g. on Skip */
  stopTension(): void;
  dispose(): void;
}

const MUTE_KEY = "garuda_intro_muted";

function readMutedPref(): boolean {
  try {
    return window.localStorage.getItem(MUTE_KEY) === "1";
  } catch {
    return false;
  }
}
function writeMutedPref(m: boolean) {
  try {
    window.localStorage.setItem(MUTE_KEY, m ? "1" : "0");
  } catch {
    // ignore
  }
}

const silent: IntroSound = {
  isAudible: () => false,
  isMuted: () => true,
  unlock: async () => false,
  setMuted: () => {},
  cue: () => {},
  stopTension: () => {},
  dispose: () => {},
};

export function createIntroSound(): IntroSound {
  if (typeof window === "undefined") return silent;
  const AC: typeof AudioContext | undefined =
    window.AudioContext ||
    (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
  if (!AC) return silent;

  let ctx: AudioContext;
  try {
    ctx = new AC();
  } catch {
    return silent;
  }

  let muted = readMutedPref();
  const VOLUME = 0.55;

  const master = ctx.createGain();
  master.gain.value = muted ? 0 : VOLUME;
  const comp = ctx.createDynamicsCompressor();
  comp.threshold.value = -16;
  comp.ratio.value = 4;
  master.connect(comp);
  comp.connect(ctx.destination);

  // generated reverb tail (decaying stereo noise)
  const reverb = ctx.createConvolver();
  {
    const len = Math.floor(ctx.sampleRate * 2.6);
    const ir = ctx.createBuffer(2, len, ctx.sampleRate);
    for (let ch = 0; ch < 2; ch++) {
      const d = ir.getChannelData(ch);
      for (let i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / len, 2.6);
    }
    reverb.buffer = ir;
  }
  const reverbOut = ctx.createGain();
  reverbOut.gain.value = 0.5;
  reverb.connect(reverbOut);
  reverbOut.connect(master);

  // shared white-noise buffer
  const noise = ctx.createBuffer(1, ctx.sampleRate * 2, ctx.sampleRate);
  {
    const d = noise.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
  }

  /** route a voice to the mix with a dry level and a reverb send */
  const route = (node: AudioNode, wet = 0.35, pan = 0) => {
    let last: AudioNode = node;
    if (pan !== 0 && ctx.createStereoPanner) {
      const p = ctx.createStereoPanner();
      p.pan.value = pan;
      node.connect(p);
      last = p;
    }
    last.connect(master);
    if (wet > 0) {
      const send = ctx.createGain();
      send.gain.value = wet;
      last.connect(send);
      send.connect(reverb);
    }
  };

  const env = (g: GainNode, t: number, peak: number, attack: number, decay: number) => {
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(peak, t + attack);
    g.gain.exponentialRampToValueAtTime(0.0001, t + attack + decay);
  };

  const tone = (
    type: OscillatorType, freq: number, t: number, peak: number, attack: number, decay: number,
    opts: { to?: number; wet?: number; pan?: number; detune?: number } = {}
  ) => {
    const o = ctx.createOscillator();
    o.type = type;
    o.frequency.setValueAtTime(freq, t);
    if (opts.to) o.frequency.exponentialRampToValueAtTime(opts.to, t + attack + decay);
    if (opts.detune) o.detune.value = opts.detune;
    const g = ctx.createGain();
    env(g, t, peak, attack, decay);
    o.connect(g);
    route(g, opts.wet ?? 0.35, opts.pan ?? 0);
    o.start(t);
    o.stop(t + attack + decay + 0.05);
  };

  const noiseSweep = (
    t: number, dur: number, peak: number, filterType: BiquadFilterType,
    fFrom: number, fTo: number, q = 1, wet = 0.3, attackFrac = 0.6
  ) => {
    const src = ctx.createBufferSource();
    src.buffer = noise;
    src.loop = true;
    const f = ctx.createBiquadFilter();
    f.type = filterType;
    f.Q.value = q;
    f.frequency.setValueAtTime(fFrom, t);
    f.frequency.exponentialRampToValueAtTime(fTo, t + dur);
    const g = ctx.createGain();
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(peak, t + dur * attackFrac);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    src.connect(f);
    f.connect(g);
    route(g, wet);
    src.start(t);
    src.stop(t + dur + 0.05);
  };

  // everything in the suspense bed goes through this bus so Skip can fade it out
  const tensionBus = ctx.createGain();
  tensionBus.connect(master);
  const tensionSend = ctx.createGain();
  tensionSend.gain.value = 0.35;
  tensionBus.connect(tensionSend);
  tensionSend.connect(reverb);

  const thump = (t: number, peak: number, from = 62, to = 38, decay = 0.28, dest: AudioNode = tensionBus) => {
    const o = ctx.createOscillator();
    o.type = "sine";
    o.frequency.setValueAtTime(from, t);
    o.frequency.exponentialRampToValueAtTime(to, t + decay);
    const g = ctx.createGain();
    env(g, t, peak, 0.006, decay);
    o.connect(g);
    g.connect(dest);
    o.start(t);
    o.stop(t + decay + 0.05);
  };

  /** band-passed noise that sweeps across the stereo field - a radar / scanner pass */
  const scanSweep = (t: number, dur: number, peak: number, leftToRight: boolean, dest: AudioNode = tensionBus) => {
    const src = ctx.createBufferSource();
    src.buffer = noise;
    src.loop = true;
    const bp = ctx.createBiquadFilter();
    bp.type = "bandpass";
    bp.Q.value = 9;
    bp.frequency.setValueAtTime(900, t);
    bp.frequency.exponentialRampToValueAtTime(4200, t + dur);
    const g = ctx.createGain();
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(peak, t + dur * 0.5);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    src.connect(bp);
    bp.connect(g);
    let last: AudioNode = g;
    if (ctx.createStereoPanner) {
      const pan = ctx.createStereoPanner();
      pan.pan.setValueAtTime(leftToRight ? -0.9 : 0.9, t);
      pan.pan.linearRampToValueAtTime(leftToRight ? 0.9 : -0.9, t + dur);
      g.connect(pan);
      last = pan;
    }
    last.connect(dest);
    src.start(t);
    src.stop(t + dur + 0.05);
  };

  const beep = (t: number, freq: number, dur: number, peak: number, type: OscillatorType = "square", pan = 0, wet = 0.25) => {
    const o = ctx.createOscillator();
    o.type = type;
    o.frequency.setValueAtTime(freq, t);
    const lp = ctx.createBiquadFilter();
    lp.type = "lowpass";
    lp.frequency.value = 5000;
    const g = ctx.createGain();
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(peak, t + 0.004);
    g.gain.setValueAtTime(peak, t + dur * 0.7);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(lp);
    lp.connect(g);
    route(g, wet, pan);
    o.start(t);
    o.stop(t + dur + 0.02);
  };

  /* ------------------------- the cues ------------------------- */

  // Suspense bed for scenes 1-2 (~6.4s): beating sub drone, quickening heartbeat,
  // sonar pings and stereo scanner sweeps.
  const tension = (t: number) => {
    const dur = 6.4;
    // drone: two close sub sines beat against each other + a filtered fifth
    const lp = ctx.createBiquadFilter();
    lp.type = "lowpass";
    lp.Q.value = 3;
    lp.frequency.setValueAtTime(120, t);
    lp.frequency.exponentialRampToValueAtTime(520, t + 3.3);
    lp.frequency.exponentialRampToValueAtTime(160, t + dur);
    const dg = ctx.createGain();
    dg.gain.setValueAtTime(0.0001, t);
    dg.gain.exponentialRampToValueAtTime(0.22, t + 1.4);
    dg.gain.setValueAtTime(0.22, t + 4.2);
    dg.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    lp.connect(dg);
    dg.connect(tensionBus);
    [
      ["sine", 41.2],
      ["sine", 41.9],
      ["sawtooth", 61.7],
      ["triangle", 82.4],
    ].forEach(([type, f]) => {
      const o = ctx.createOscillator();
      o.type = type as OscillatorType;
      o.frequency.setValueAtTime(f as number, t);
      o.frequency.exponentialRampToValueAtTime((f as number) * 1.06, t + 3.3); // creeping tension
      const g = ctx.createGain();
      g.gain.value = type === "sawtooth" ? 0.25 : 0.6;
      o.connect(g);
      g.connect(lp);
      o.start(t);
      o.stop(t + dur + 0.1);
    });

    // heartbeat: lub-dub, speeding up until the shield locks (~3.3s)
    let bt = t + 0.35;
    let gap = 0.95;
    while (bt < t + 3.2) {
      thump(bt, 0.32);
      thump(bt + 0.16, 0.2, 55, 36, 0.22);
      bt += gap;
      gap = Math.max(0.42, gap * 0.82);
    }

    // sonar pings
    [0.45, 1.65, 2.75].forEach((dt, i) => {
      const o = ctx.createOscillator();
      o.type = "sine";
      o.frequency.setValueAtTime(1174.7, t + dt);
      const g = ctx.createGain();
      env(g, t + dt, 0.07, 0.005, 1.6);
      o.connect(g);
      let last: AudioNode = g;
      if (ctx.createStereoPanner) {
        const pn = ctx.createStereoPanner();
        pn.pan.value = i % 2 ? 0.5 : -0.5;
        g.connect(pn);
        last = pn;
      }
      last.connect(tensionBus);
      const send = ctx.createGain();
      send.gain.value = 1.2; // pings live in the reverb
      last.connect(send);
      send.connect(reverb);
      o.start(t + dt);
      o.stop(t + dt + 1.7);
    });

    // scanner sweeps, alternating direction, in time with the on-screen scan lines
    for (let k = 0, st = t + 0.2; st < t + 3.2; k++, st += 0.62) scanSweep(st, 0.55, 0.06, k % 2 === 0);
  };

  // Scene 1: particles = fast digital data chatter + low whoosh
  const signal = (t: number) => {
    const notes = [1318.5, 1568, 1975.5, 2349.3, 2637, 3136, 3951];
    for (let i = 0; i < 70; i++) {
      const at = t + 0.1 + Math.random() * 1.6;
      beep(at, notes[(Math.random() * notes.length) | 0], 0.018 + Math.random() * 0.035, 0.012 + Math.random() * 0.012, "square", Math.random() * 1.6 - 0.8, 0.15);
    }
    noiseSweep(t, 1.75, 0.08, "bandpass", 250, 2600, 1.2, 0.35, 0.9);
  };

  // Eagle materialises - impact: sub hit + metallic shimmer
  const form = (t: number) => {
    thump(t, 0.75, 110, 36, 0.9, master);
    noiseSweep(t, 0.5, 0.12, "bandpass", 3200, 1200, 4, 0.5, 0.04);
    [220, 329.6, 440].forEach((f, i) => tone("triangle", f, t + 0.01 * i, 0.025, 0.2, 1.8, { wet: 0.7, detune: i % 2 ? 7 : -7 }));
  };

  // Scene 2: shield charging - rising saw + accelerating ticks
  const shield = (t: number) => {
    const dur = 1.35;
    const o = ctx.createOscillator();
    o.type = "sawtooth";
    o.frequency.setValueAtTime(70, t);
    o.frequency.exponentialRampToValueAtTime(330, t + dur);
    const lp = ctx.createBiquadFilter();
    lp.type = "lowpass";
    lp.Q.value = 9;
    lp.frequency.setValueAtTime(220, t);
    lp.frequency.exponentialRampToValueAtTime(3200, t + dur);
    const g = ctx.createGain();
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(0.07, t + dur * 0.9);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur + 0.05);
    o.connect(lp);
    lp.connect(g);
    route(g, 0.3);
    o.start(t);
    o.stop(t + dur + 0.1);
    // ticks: 5/s -> 25/s
    let tt = t + 0.05;
    let gap = 0.2;
    while (tt < t + dur) {
      beep(tt, 2400, 0.012, 0.05, "square", 0, 0.1);
      tt += gap;
      gap = Math.max(0.04, gap * 0.86);
    }
  };

  // Shield complete - LOCK: metallic clank + sub hit + two-tone "secured" beep
  const shieldDone = (t: number) => {
    noiseSweep(t, 0.22, 0.45, "bandpass", 2600, 1800, 3, 0.45, 0.03);
    beep(t, 196, 0.14, 0.09, "square", 0, 0.3);
    thump(t, 0.85, 90, 34, 0.7, master);
    beep(t + 0.14, 880, 0.09, 0.05, "square", 0, 0.3);
    beep(t + 0.26, 1318.5, 0.16, 0.05, "square", 0, 0.4);
    [1318.5, 2637].forEach((f, i) => tone("sine", f, t + 0.26, i ? 0.015 : 0.03, 0.003, 1.4, { wet: 0.7 }));
  };

  // reverse-cymbal style swell that sucks into the GARUDA hit
  const riser = (t: number) => {
    const dur = 0.75;
    const src = ctx.createBufferSource();
    src.buffer = noise;
    src.loop = true;
    const hp = ctx.createBiquadFilter();
    hp.type = "highpass";
    hp.frequency.setValueAtTime(500, t);
    hp.frequency.exponentialRampToValueAtTime(7000, t + dur);
    const g = ctx.createGain();
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(0.2, t + dur);
    g.gain.setValueAtTime(0.0001, t + dur + 0.01); // hard cut right before the hit
    src.connect(hp);
    hp.connect(g);
    route(g, 0.2);
    src.start(t);
    src.stop(t + dur + 0.02);
    tone("sine", 220, t, 0.03, dur * 0.95, 0.05, { to: 880, wet: 0.2 });
  };

  // Scene 3: GARUDA reveal - cinematic "BRAAAM" + sub boom + impact
  const brand = (t: number) => {
    const lp = ctx.createBiquadFilter();
    lp.type = "lowpass";
    lp.Q.value = 2.5;
    lp.frequency.setValueAtTime(140, t);
    lp.frequency.exponentialRampToValueAtTime(1800, t + 0.18);
    lp.frequency.exponentialRampToValueAtTime(380, t + 2.6);
    const bg = ctx.createGain();
    bg.gain.setValueAtTime(0.0001, t);
    bg.gain.exponentialRampToValueAtTime(0.75, t + 0.07);
    bg.gain.setValueAtTime(0.75, t + 0.9);
    bg.gain.exponentialRampToValueAtTime(0.0001, t + 3.4);
    lp.connect(bg);
    route(bg, 0.45);
    [55, 55.5, 82.4, 110.2, 110.9].forEach((f) => {
      const o = ctx.createOscillator();
      o.type = "sawtooth";
      o.frequency.value = f;
      const g = ctx.createGain();
      g.gain.value = 0.22;
      o.connect(g);
      g.connect(lp);
      o.start(t);
      o.stop(t + 3.5);
    });
    tone("sine", 46, t, 1.0, 0.01, 2.8, { to: 32, wet: 0.15 });
    noiseSweep(t, 0.8, 0.45, "lowpass", 2400, 90, 0.7, 0.4, 0.04);
    noiseSweep(t + 0.4, 1.6, 0.025, "bandpass", 9000, 4000, 3, 0.6, 0.4);
  };

  // Scene 4: transition to login - airy whoosh
  const exit = (t: number) => {
    noiseSweep(t, 1.0, 0.1, "highpass", 600, 5000, 0.5, 0.5, 0.7);
    tone("sine", 440, t, 0.02, 0.4, 0.9, { to: 880, wet: 0.7 });
  };

  const stopTension = () => {
    const now = ctx.currentTime;
    tensionBus.gain.cancelScheduledValues(now);
    tensionBus.gain.setValueAtTime(tensionBus.gain.value, now);
    tensionBus.gain.linearRampToValueAtTime(0, now + 0.25);
  };

  const cues: Record<IntroCue, (t: number) => void> = { tension, signal, form, shield, shieldDone, riser, brand, exit };

  return {
    isAudible: () => ctx.state === "running" && !muted,
    isMuted: () => muted,
    unlock: async () => {
      if (ctx.state !== "running") {
        // without a user gesture resume() can stay pending forever, so don't wait long
        await Promise.race([ctx.resume().catch(() => {}), new Promise((r) => setTimeout(r, 250))]);
      }
      return ctx.state === "running";
    },
    setMuted: (m: boolean) => {
      muted = m;
      writeMutedPref(m);
      const now = ctx.currentTime;
      master.gain.cancelScheduledValues(now);
      master.gain.setValueAtTime(master.gain.value, now);
      master.gain.linearRampToValueAtTime(m ? 0 : VOLUME, now + 0.15);
    },
    cue: (c: IntroCue) => {
      if (ctx.state !== "running" || muted) return; // skip, don't queue
      try {
        cues[c](ctx.currentTime + 0.01);
      } catch {
        // never let audio break the intro
      }
    },
    stopTension,
    dispose: () => {
      const now = ctx.currentTime;
      master.gain.cancelScheduledValues(now);
      master.gain.setValueAtTime(master.gain.value, now);
      // let the exit swell ring out, then release the audio device
      master.gain.linearRampToValueAtTime(0, now + 1.4);
      setTimeout(() => ctx.close().catch(() => {}), 1600);
    },
  };
}
