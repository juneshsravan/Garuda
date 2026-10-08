"use client";

import React, { useState } from "react";
import { showDevTools } from "@/lib/dev-tools";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { LoadingState, EmptyState, ErrorState } from "@/components/ui/states";
import { AnalysisDossier } from "@/components/analysis/AnalysisDossier";
import { scanApi, ApiClientError } from "@/lib/api-client";
import { AnalysisResponse } from "@/types/analysis";
import {
  MessageSquareText,
  ShieldCheck,
  RotateCcw,
  Info,
  CheckCircle2,
} from "lucide-react";
import Link from "next/link";

export default function MessageAnalyzerPage() {
  const [text, setText] = useState("");
  const [saveToHistory, setSaveToHistory] = useState(true);
  const [state, setState] = useState<"ready" | "analyzing" | "result" | "empty" | "error">("ready");
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [errorDetails, setErrorDetails] = useState<string | null>(null);

  const maxLength = 5000;
  const charCount = text.length;

  const handleSampleFill = (sampleText: string) => {
    setText(sampleText);
    setState("ready");
    setErrorDetails(null);
  };

  const handleAnalyze = async () => {
    const trimmed = text.trim();
    if (!trimmed) {
      setState("empty");
      return;
    }

    setState("analyzing");
    setErrorDetails(null);

    try {
      const response = await scanApi.analyzeMessage({
        text: trimmed,
        save: saveToHistory,
      });
      setResult(response);
      setState("result");
    } catch (err: unknown) {
      const msg = err instanceof ApiClientError ? err.message : (err instanceof Error ? err.message : "Failed to analyze message.");
      setErrorDetails(msg);
      setState("error");
    }
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
            <span className="text-muted-foreground px-2">Dev State:</span>
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
      <div className="rounded-xl border border-border bg-surface p-5 sm:p-6 space-y-4 shadow-xl">
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

        {/* Controls Bar: Char counter, Save toggle, Actions */}
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
              onClick={() => {
                setText("");
                setResult(null);
                setState("ready");
              }}
              disabled={!text}
              className="gap-1 font-mono text-xs"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Clear
            </Button>

            <Button
              onClick={handleAnalyze}
              disabled={state === "analyzing" || !text.trim()}
              className="gap-1.5 font-mono text-xs px-5 font-semibold"
            >
              <ShieldCheck className="w-4 h-4" />
              Analyze Message
            </Button>
          </div>
        </div>

        {/* Quick sample buttons */}
        <div className="pt-3 border-t border-border/60">
          <span className="text-[11px] font-mono text-muted-foreground block mb-2">
            Try a real-world example:
          </span>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => handleSampleFill("Dear SBI customer, your YONO account will be suspended today. Update PAN immediately: http://sbi-yono-kyc.in-verify.xyz")}
              className="text-[11px] font-mono px-2 py-1 rounded bg-elevated hover:bg-slate-800 text-slate-300 hover:text-white border border-border transition-colors"
            >
              [Scam] SBI YONO PAN Suspension
            </button>
            <button
              onClick={() => handleSampleFill("RBI Kehta Hai: Never share your OTP, PIN, CVV or password with anyone. Bank or RBI never asks for confidential details. For queries, visit your bank branch or check https://rbikehtahai.rbi.org.in/")}
              className="text-[11px] font-mono px-2 py-1 rounded bg-elevated hover:bg-slate-800 text-slate-300 hover:text-white border border-border transition-colors"
            >
              [Genuine] RBI Kehta Hai Advisory
            </button>
            <button
              onClick={() => handleSampleFill("Congratulations! You won ₹500 cashback. Scan this QR immediately to claim your reward into bank account: upi://pay?pa=claim.reward92@okaxis&pn=CashDesk&am=500")}
              className="text-[11px] font-mono px-2 py-1 rounded bg-elevated hover:bg-slate-800 text-slate-300 hover:text-white border border-border transition-colors"
            >
              [Scam] ₹500 QR Lottery Lure
            </button>
          </div>
        </div>
      </div>

      {/* Dynamic Results & State Views */}
      {state === "analyzing" && (
        <LoadingState
          message="Executing Noisy-OR Threat Pipeline..."
          description="Normalizing input text, extracting entities, evaluating threat rules, and computing legitimacy discounts."
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
          title="Analysis Request Failed"
          message={errorDetails || "An unexpected error occurred during message analysis."}
          details="Ensure backend server is running on port 8000 and you are authenticated."
          onRetry={handleAnalyze}
        />
      )}

      {state === "result" && result && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border/80 pb-3">
            <h3 className="font-mono text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              Analysis Results &amp; Explainability Dossier
            </h3>
            <div className="flex items-center gap-2">
              {result.scan_id && (
                <Badge variant="cyan" className="text-[10px]">
                  Saved to History
                </Badge>
              )}
              <Badge variant="default" className="text-[10px]">
                Engine v{result.engine_version}
              </Badge>
            </div>
          </div>

          {/* Real Dossier Display */}
          <AnalysisDossier analysis={result} rawInput={text} />
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
