"use client";

import React, { useState } from "react";
import { showDevTools } from "@/lib/dev-tools";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { LoadingState, EmptyState, ErrorState } from "@/components/ui/states";
import { ConsolePreview } from "@/components/landing/ConsolePreview";
import {
  MessageSquareText,
  ShieldCheck,
  RotateCcw,
  Sparkles,
  Info,
} from "lucide-react";

export default function MessageAnalyzerPage() {
  const [text, setText] = useState("");
  const [saveToHistory, setSaveToHistory] = useState(true);
  const [state, setState] = useState<"ready" | "analyzing" | "result" | "empty" | "error">("ready");

  const maxLength = 5000;
  const charCount = text.length;

  const handleSampleFill = (sampleText: string) => {
    setText(sampleText);
    setState("ready");
  };

  const handleAnalyze = () => {
    if (!text.trim()) {
      setState("empty");
      return;
    }
    setState("analyzing");
    // MOCK: In Chunk 6 this calls POST /api/analyze/message {text, save: saveToHistory}
    setTimeout(() => {
      setState("result");
    }, 1000);
  };

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
        <div>
          <span className="font-mono text-xs uppercase text-primary tracking-wider font-semibold">
            SECTOR 1: DETECTION ENGINE
          </span>
          <h2 className="font-mono text-2xl sm:text-3xl font-bold text-white mt-1 flex items-center gap-2">
            <MessageSquareText className="w-6 h-6 text-primary" />
            Message &amp; SMS Threat Analyzer
          </h2>
          <p className="text-xs sm:text-sm text-muted-foreground mt-1">
            Context-aware phrase analysis across English, Hindi, Telugu, Romanized Telugu, and Hinglish.
          </p>
        </div>

        {/* State Toggle — only visible when NEXT_PUBLIC_SHOW_DEV_TOOLS=true */}
        {showDevTools && (
          <div className="flex items-center gap-1.5 p-1 rounded-lg border border-border bg-elevated/40 text-[11px] font-mono self-start sm:self-auto">
            <span className="text-muted-foreground px-2">State:</span>
            <button
              onClick={() => setState("ready")}
              className={`px-2 py-0.5 rounded ${state === "ready" ? "bg-primary text-white" : "text-slate-400"}`}
            >
              Ready
            </button>
            <button
              onClick={() => setState("analyzing")}
              className={`px-2 py-0.5 rounded ${state === "analyzing" ? "bg-primary text-white" : "text-slate-400"}`}
            >
              Loading
            </button>
            <button
              onClick={() => setState("result")}
              className={`px-2 py-0.5 rounded ${state === "result" ? "bg-primary text-white" : "text-slate-400"}`}
            >
              Result
            </button>
            <button
              onClick={() => setState("empty")}
              className={`px-2 py-0.5 rounded ${state === "empty" ? "bg-primary text-white" : "text-slate-400"}`}
            >
              Empty
            </button>
            <button
              onClick={() => setState("error")}
              className={`px-2 py-0.5 rounded ${state === "error" ? "bg-primary text-white" : "text-slate-400"}`}
            >
              Error
            </button>
          </div>
        )}
      </div>

      {/* Main Analysis Input Card */}
      <div className="rounded-xl border border-border bg-surface p-5 sm:p-6 space-y-4">
        <div>
          <label htmlFor="message-input" className="block font-mono text-xs font-semibold text-slate-300 uppercase mb-2">
            Paste Suspicious Message Text
          </label>
          <textarea
            id="message-input"
            rows={5}
            value={text}
            onChange={(e) => setText(e.target.value)}
            maxLength={maxLength}
            placeholder="Paste raw SMS, WhatsApp, Telegram, or email notification text here (e.g., 'Dear SBI customer, your YONO account will be suspended today. Update PAN immediately: http://...')..."
            className="w-full rounded-lg border border-input bg-input-bg p-3.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary font-mono transition-colors"
          />
        </div>

        {/* Controls Bar: Char counter, Save toggle, Quick presets */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2 border-t border-border/80">
          <div className="flex flex-wrap items-center gap-4 text-xs font-mono">
            {/* Character counter */}
            <span className={`${charCount > 4500 ? "text-amber-400" : "text-muted-foreground"}`}>
              {charCount} / {maxLength} characters
            </span>

            {/* Save to history checkbox */}
            <label className="flex items-center gap-2 cursor-pointer select-none text-slate-300 hover:text-white">
              <input
                type="checkbox"
                checked={saveToHistory}
                onChange={(e) => setSaveToHistory(e.target.checked)}
                className="rounded border-input bg-input-bg text-primary focus:ring-primary w-4 h-4 cursor-pointer"
              />
              <span>Save to history</span>
            </label>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setText("")}
              disabled={!text}
              className="gap-1 font-mono text-xs"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Clear
            </Button>

            <Button
              onClick={handleAnalyze}
              className="gap-1.5 font-mono text-xs px-5 font-semibold"
            >
              <ShieldCheck className="w-4 h-4" />
              Analyze Message
            </Button>
          </div>
        </div>

        {/* Quick sample links */}
        <div className="pt-3 border-t border-border/60">
          <span className="text-[11px] font-mono text-muted-foreground block mb-2">
            Try an example:
          </span>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => handleSampleFill("Dear SBI customer, your YONO account will be suspended today. Update PAN immediately: http://sbi-yono-kyc.in-verify.xyz")}
              className="text-[11px] font-mono px-2 py-1 rounded bg-elevated hover:bg-slate-800 text-slate-300 hover:text-white border border-border"
            >
              [Scam] SBI YONO PAN Suspension
            </button>
            <button
              onClick={() => handleSampleFill("Your OTP for transaction of Rs 1,450.00 at AMAZON INDIA is 482910. Valid for 10 mins. Do NOT share OTP or password with anyone. Bank NEVER calls for OTP - HDFC Bank")}
              className="text-[11px] font-mono px-2 py-1 rounded bg-elevated hover:bg-slate-800 text-slate-300 hover:text-white border border-border"
            >
              [Safe] HDFC Amazon OTP Alert
            </button>
            <button
              onClick={() => handleSampleFill("Congratulations! You won ₹500. Scan this QR immediately to claim your reward.")}
              className="text-[11px] font-mono px-2 py-1 rounded bg-elevated hover:bg-slate-800 text-slate-300 hover:text-white border border-border"
            >
              [Scam] ₹500 QR Lottery Lure
            </button>
          </div>
        </div>
      </div>

      {/* Dynamic Results & States */}
      {state === "analyzing" && (
        <LoadingState
          message="Executing Noisy-OR Threat Pipeline..."
          description="Parsing text on word boundaries, normalizing leetspeak, and evaluating legitimacy discounts."
        />
      )}

      {state === "empty" && (
        <EmptyState
          title="Input Payload Empty"
          description="Please enter or paste message text into the console above to execute threat analysis."
          actionLabel="Load Sample Message"
          onAction={() => handleSampleFill("Dear consumer, your electricity power will be disconnected tonight at 9:30 PM because previous month bill was not updated. Call our officer 9000000001 immediately.")}
        />
      )}

      {state === "error" && (
        <ErrorState
          title="Analysis API Unavailable"
          message="FastAPI backend /api/analyze/message is pending Chunk 4 merge."
          details="ARCHITECTURE Section 6 contract: POST /api/analyze/message { text: string, save: boolean }"
          onRetry={() => setState("result")}
        />
      )}

      {state === "result" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-mono text-sm font-bold text-white uppercase tracking-wider">
              Analysis Results &amp; Explainability Dossier
            </h3>
            <Badge variant="cyan">Real-time Evaluation</Badge>
          </div>
          {/* Detailed results view matching ARCHITECTURE Section 6 */}
          <ConsolePreview />
        </div>
      )}

      {state === "ready" && (
        <div className="rounded-xl border border-dashed border-border p-8 text-center text-xs font-mono text-muted-foreground space-y-1">
          <Info className="w-5 h-5 mx-auto mb-2 text-primary" />
          <p className="text-slate-300 font-semibold">Engine Standing By</p>
          <p>Paste any message above and click &ldquo;Analyze Message&rdquo; to compute risk score and legitimacy signals.</p>
        </div>
      )}
    </div>
  );
}
