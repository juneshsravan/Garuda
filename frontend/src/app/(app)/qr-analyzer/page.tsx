"use client";

import React, { useState } from "react";
import { showDevTools } from "@/lib/dev-tools";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { LoadingState, EmptyState, ErrorState } from "@/components/ui/states";
import {
  QrCode,
  UploadCloud,
  ShieldCheck,
  AlertOctagon,
  HardDrive,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";

export default function QrAnalyzerPage() {
  const [payloadText, setPayloadText] = useState("");
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null);
  const [state, setState] = useState<"ready" | "analyzing" | "result" | "empty" | "error">("ready");

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFileName(file.name);
      setPayloadText("upi://pay?pa=fake.cashback@okaxis&pn=CashbackRewards&am=500&tn=ClaimNow");
      setState("ready");
    }
  };

  const handleAnalyze = () => {
    if (!payloadText.trim() && !selectedFileName) {
      setState("empty");
      return;
    }
    setState("analyzing");
    // MOCK: In Chunk 9 this calls POST /api/analyze/qr multipart or payload
    setTimeout(() => {
      setState("result");
    }, 1000);
  };

  const loadSample = () => {
    setPayloadText("upi://pay?pa=fake.cashback@okaxis&pn=CashbackRewards&am=500&tn=ClaimNow");
    setSelectedFileName("sample_fake_reward_qr.png");
    setState("ready");
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
        <div>
          <span className="font-mono text-xs uppercase text-amber-400 tracking-wider font-semibold">
            SECTOR 1: INDIA PAYMENT VECTOR
          </span>
          <h2 className="font-mono text-2xl sm:text-3xl font-bold text-white mt-1 flex items-center gap-2">
            <QrCode className="w-6 h-6 text-amber-400" />
            QR Code &amp; UPI Payee Analyzer
          </h2>
          <p className="text-xs sm:text-sm text-muted-foreground mt-1">
            In-memory payload classification: UPI intents, prefilled debits, and payee spoofing.
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

      {/* Zero Disk Storage Guarantee Banner */}
      <div className="p-3.5 rounded-lg border border-emerald-500/30 bg-emerald-500/10 text-xs font-mono text-slate-300 flex items-center gap-2.5">
        <HardDrive className="w-4 h-4 text-emerald-400 shrink-0" />
        <span>
          <strong className="text-white">Zero Disk Retention:</strong> Uploaded QR images are processed strictly in volatile RAM with OpenCV / pyzbar and immediately purged. Images are never stored on server disks or buckets.
        </span>
      </div>

      {/* Input Options: File Upload or Raw Payload */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Upload Box */}
        <div className="rounded-xl border border-dashed border-border bg-surface/50 p-6 flex flex-col items-center justify-center text-center relative hover:border-slate-500 transition-colors">
          <UploadCloud className="w-10 h-10 text-primary mb-3" />
          <h4 className="font-mono text-sm font-semibold text-white mb-1">
            Upload QR Image (PNG, JPG, WEBP)
          </h4>
          <p className="text-xs text-muted-foreground mb-4">
            Magic-byte verified · Maximum 5 MB per image
          </p>

          <input
            type="file"
            accept="image/png,image/jpeg,image/webp"
            onChange={handleFileUpload}
            id="qr-file-upload"
            className="hidden"
          />
          <label htmlFor="qr-file-upload">
            <Button asChild size="sm" variant="outline" className="cursor-pointer">
              <span>{selectedFileName || "Choose QR File"}</span>
            </Button>
          </label>
        </div>

        {/* Text Payload Box */}
        <div className="rounded-xl border border-border bg-surface p-5 flex flex-col justify-between space-y-4">
          <div>
            <label htmlFor="qr-payload-text" className="block font-mono text-xs font-semibold text-slate-300 uppercase mb-2">
              Or Paste Decoded UPI Payload / URI
            </label>
            <textarea
              id="qr-payload-text"
              rows={4}
              value={payloadText}
              onChange={(e) => setPayloadText(e.target.value)}
              placeholder="e.g. upi://pay?pa=fake.cashback@okaxis&pn=CashbackRewards&am=500&tn=ClaimNow"
              className="w-full rounded-lg border border-input bg-input-bg p-3 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary font-mono"
            />
          </div>

          <div className="flex items-center justify-between pt-2 border-t border-border">
            <Button
              variant="ghost"
              size="sm"
              onClick={loadSample}
              className="text-xs font-mono text-muted-foreground hover:text-white"
            >
              Load Fake UPI Sample
            </Button>

            <Button
              onClick={handleAnalyze}
              className="gap-1.5 font-mono text-xs px-5 font-semibold"
            >
              <ShieldCheck className="w-4 h-4" />
              Analyze QR Code
            </Button>
          </div>
        </div>
      </div>

      {/* Dynamic States */}
      {state === "analyzing" && (
        <LoadingState
          message="Decoding QR Matrix in Volatile Memory..."
          description="Classifying payload parameters, extracting payee VPA, and cross-checking reverse debit intent."
        />
      )}

      {state === "empty" && (
        <EmptyState
          title="No QR Payload Provided"
          description="Please upload a QR image or paste a decoded payment URI above."
          actionLabel="Load Fake UPI Sample"
          onAction={loadSample}
        />
      )}

      {state === "error" && (
        <ErrorState
          title="QR Decoding Service Pending"
          message="FastAPI route POST /api/analyze/qr is pending Chunk 9 integration."
          details="ARCHITECTURE Section 8.8: Uses OpenCV QRCodeDetector with pyzbar fallback and UPI parameters parsing."
          onRetry={() => setState("result")}
        />
      )}

      {state === "result" && (
        <div className="rounded-xl border border-risk-high/40 bg-surface p-6 space-y-5 shadow-xl">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-4">
            <div>
              <span className="font-mono text-xs text-muted-foreground uppercase">
                DECODED UPI VECTOR
              </span>
              <h3 className="font-mono text-base font-bold text-white">
                Deceptive Cashback Voucher Scheme
              </h3>
            </div>
            <Badge variant="high">91 High Risk</Badge>
          </div>

          <div className="p-3.5 rounded-lg border border-risk-high/30 bg-risk-high/10 flex items-start gap-3">
            <AlertOctagon className="w-5 h-5 text-risk-high shrink-0 mt-0.5" />
            <div className="space-y-1 text-xs font-mono">
              <strong className="text-white block">CRITICAL FRAUD VECTOR DETECTED</strong>
              <p className="text-slate-300">
                This QR contains a preloaded payment amount of <span className="text-risk-high font-bold">₹500.00</span>.
                Scanning and entering your UPI PIN will <span className="underline">DEBIT</span> money from your account, not credit it.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
