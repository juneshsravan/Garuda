"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { showDevTools } from "@/lib/dev-tools";
import { scanApi, ApiClientError } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { LoadingState, EmptyState, ErrorState } from "@/components/ui/states";
import { AnalysisResponse, RiskLevel } from "@/types/analysis";
import {
  QrCode,
  UploadCloud,
  Camera,
  FileText,
  ShieldCheck,
  AlertOctagon,
  HardDrive,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Copy,
  Check,
  Lock,
  ShieldAlert,
  ListChecks,
  History,
  VideoOff,
  Terminal,
  ChevronRight,
  Info,
} from "lucide-react";

type PageState = "ready" | "analyzing" | "result" | "empty" | "error";
type TabType = "paste" | "upload" | "camera";
type ScanContext = "known_payee" | "receive_money" | "stranger_request" | null;

type BadgeVariant = "safe" | "suspicious" | "medium" | "high" | "critical" | "unverified";

const LEVEL_TO_BADGE: Record<string, BadgeVariant> = {
  likely_safe: "safe",
  suspicious: "suspicious",
  medium: "medium",
  high: "high",
  critical: "critical",
  unable_to_verify: "unverified",
};

const SEVERITY_COLOR: Record<string, string> = {
  critical: "text-[#EF4444]",
  high: "text-[#F97316]",
  medium: "text-[#F59E0B]",
  low: "text-[#FBBF24]",
};

function verificationText(status: string): string {
  if (status === "no_warning_signs_found") {
    return "No threat indicators detected. Note: Standard UPI handles cannot prove payee identity. Always confirm the payee before sending funds.";
  }
  if (status === "unverified") {
    return "Not verified against official directory. Risk assessment derived from structural and context heuristics.";
  }
  if (status.includes("official")) {
    return "Matches GARUDA's verified official entity directory.";
  }
  if (status.includes("plain_text")) {
    return "Decoded as plain benign text without payment instructions.";
  }
  return status.replace(/_/g, " ");
}

export default function QrAnalyzerPage() {
  const [activeTab, setActiveTab] = useState<TabType>("paste");
  const [payloadText, setPayloadText] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [filePreview, setFilePreview] = useState<string | null>(null);
  const [saveToHistory, setSaveToHistory] = useState(true);
  const [scanContext, setScanContext] = useState<ScanContext>(null);

  const [state, setState] = useState<PageState>("ready");
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [errorTitle, setErrorTitle] = useState("QR Analysis Failed");
  const [errorMessage, setErrorMessage] = useState("");
  const [copied, setCopied] = useState(false);

  // Camera states
  const [cameraActive, setCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const cameraScanIntervalRef = useRef<number | null>(null);

  // Monotonically increasing request ID to ignore late responses
  const scanRequestIdRef = useRef(0);

  // Stop camera tracks cleanly
  const stopCamera = () => {
    if (cameraScanIntervalRef.current) {
      clearInterval(cameraScanIntervalRef.current);
      cameraScanIntervalRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setCameraActive(false);
  };

  // Cleanup camera stream on unmount
  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  // Reset all state when switching tabs
  const handleTabChange = (newTab: TabType) => {
    // Invalidate any in-flight scan requests
    scanRequestIdRef.current++;
    stopCamera();

    setActiveTab(newTab);
    // Clear old result and error before entering new tab
    setResult(null);
    setErrorTitle("");
    setErrorMessage("");
    setState("ready");
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // 1. Analyze Decoded Text / URI (Paste Tab)
  const handleAnalyzeText = async () => {
    const value = payloadText.trim();
    if (!value) {
      setState("empty");
      return;
    }

    const currentReqId = ++scanRequestIdRef.current;
    setResult(null);
    setErrorTitle("");
    setErrorMessage("");
    setState("analyzing");

    try {
      const data = await scanApi.analyzeQr({
        content: value,
        save: saveToHistory,
        context: scanContext,
      });

      // Ignore late response if a newer request was dispatched
      if (scanRequestIdRef.current !== currentReqId) return;

      setResult(data);
      setState("result");
    } catch (err) {
      if (scanRequestIdRef.current !== currentReqId) return;

      if (err instanceof ApiClientError) {
        if (err.code === "INVALID_QR" || err.status === 422) {
          setErrorTitle("Invalid QR Payload");
          setErrorMessage(err.message || "This does not look like a valid QR code payload or payment URI.");
        } else if (err.code === "SESSION_EXPIRED" || err.status === 401) {
          setErrorTitle("Session Expired");
          setErrorMessage("Please sign in to analyze QR codes.");
        } else if (err.code === "NETWORK_ERROR") {
          setErrorTitle("Cannot Reach Backend");
          setErrorMessage("The backend service is unavailable. Make sure uvicorn is running on port 8000.");
        } else {
          setErrorTitle("Analysis Failed");
          setErrorMessage(err.message || "An error occurred while evaluating the QR code.");
        }
      } else {
        setErrorTitle("Unexpected Error");
        setErrorMessage("Something unexpected went wrong. Please check your network and try again.");
      }
      setState("error");
    }
  };

  // 2. Analyze Uploaded QR Image
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Invalidate in-flight and clear previous results
      scanRequestIdRef.current++;
      setSelectedFile(file);
      const url = URL.createObjectURL(file);
      setFilePreview(url);
      setResult(null);
      setErrorTitle("");
      setErrorMessage("");
      setState("ready");
    }
  };

  const handleAnalyzeFile = async () => {
    if (!selectedFile) {
      setState("empty");
      return;
    }

    const currentReqId = ++scanRequestIdRef.current;
    setResult(null);
    setErrorTitle("");
    setErrorMessage("");
    setState("analyzing");

    try {
      const data = await scanApi.analyzeQrImage({
        file: selectedFile,
        save: saveToHistory,
        context: scanContext,
      });

      if (scanRequestIdRef.current !== currentReqId) return;

      setResult(data);
      setState("result");
    } catch (err) {
      if (scanRequestIdRef.current !== currentReqId) return;

      if (err instanceof ApiClientError) {
        if (err.code === "QR_NOT_FOUND" || err.status === 422) {
          setErrorTitle("No QR Code Detected");
          setErrorMessage("Could not decode any valid QR matrix from this image. Please upload a clear, focused photo.");
        } else if (err.code === "INVALID_QR") {
          setErrorTitle("Invalid QR Image");
          setErrorMessage(err.message || "Image file format or payload is invalid.");
        } else if (err.code === "SESSION_EXPIRED" || err.status === 401) {
          setErrorTitle("Session Expired");
          setErrorMessage("Please sign in to analyze QR codes.");
        } else {
          setErrorTitle("Analysis Failed");
          setErrorMessage(err.message || "An error occurred while evaluating the uploaded image.");
        }
      } else {
        setErrorTitle("Unexpected Error");
        setErrorMessage("Something unexpected went wrong during image processing.");
      }
      setState("error");
    }
  };

  // 3. Camera Scanner
  const startCamera = async () => {
    setCameraError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment", width: { ideal: 1280 }, height: { ideal: 720 } },
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }
      setCameraActive(true);

      // Auto-scan using native BarcodeDetector if available
      if (typeof window !== "undefined" && "BarcodeDetector" in window) {
        const detector = new (window as any).BarcodeDetector({ formats: ["qr_code"] });
        cameraScanIntervalRef.current = window.setInterval(async () => {
          if (videoRef.current && videoRef.current.readyState === videoRef.current.HAVE_ENOUGH_DATA) {
            try {
              const barcodes = await detector.detect(videoRef.current);
              if (barcodes.length > 0 && barcodes[0].rawValue) {
                const detectedVal = barcodes[0].rawValue;
                stopCamera();
                setPayloadText(detectedVal);
                handleCameraScanPayload(detectedVal);
              }
            } catch {
              // Ignore frame detection failures
            }
          }
        }, 500);
      }
    } catch (err) {
      setCameraError(
        "Camera access was denied or no camera device was found. You can still upload a photo or paste the QR payload."
      );
      setCameraActive(false);
    }
  };

  const handleCaptureFrame = () => {
    if (!videoRef.current) return;
    const canvas = document.createElement("canvas");
    canvas.width = videoRef.current.videoWidth || 640;
    canvas.height = videoRef.current.videoHeight || 480;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
    canvas.toBlob((blob) => {
      if (blob) {
        stopCamera();
        handleAnalyzeBlob(blob);
      }
    }, "image/png");
  };

  const handleCameraScanPayload = async (content: string) => {
    const currentReqId = ++scanRequestIdRef.current;
    setResult(null);
    setErrorTitle("");
    setErrorMessage("");
    setState("analyzing");

    try {
      const data = await scanApi.analyzeQr({
        content,
        save: saveToHistory,
        context: scanContext,
      });

      if (scanRequestIdRef.current !== currentReqId) return;
      setResult(data);
      setState("result");
    } catch (err) {
      if (scanRequestIdRef.current !== currentReqId) return;
      setErrorTitle("Could Not Analyze Camera Scan");
      setErrorMessage(err instanceof Error ? err.message : "Error analyzing QR payload from camera.");
      setState("error");
    }
  };

  const handleAnalyzeBlob = async (blob: Blob) => {
    const currentReqId = ++scanRequestIdRef.current;
    setResult(null);
    setErrorTitle("");
    setErrorMessage("");
    setState("analyzing");

    try {
      const data = await scanApi.analyzeQrImage({
        file: blob,
        save: saveToHistory,
        context: scanContext,
      });

      if (scanRequestIdRef.current !== currentReqId) return;
      setResult(data);
      setState("result");
    } catch (err) {
      if (scanRequestIdRef.current !== currentReqId) return;
      if (err instanceof ApiClientError && err.code === "QR_NOT_FOUND") {
        setErrorTitle("No QR Code in Snapshot");
        setErrorMessage("Could not detect a QR code in the captured frame. Align the camera closer and ensure good lighting.");
      } else {
        setErrorTitle("Frame Analysis Failed");
        setErrorMessage(err instanceof Error ? err.message : "Could not decode captured camera frame.");
      }
      setState("error");
    }
  };

  // Samples
  const handleSample = (sampleText: string) => {
    scanRequestIdRef.current++;
    setPayloadText(sampleText);
    setResult(null);
    setErrorTitle("");
    setErrorMessage("");
    setState("ready");
  };

  const handleClear = () => {
    scanRequestIdRef.current++;
    setPayloadText("");
    setSelectedFile(null);
    setFilePreview(null);
    setResult(null);
    setErrorTitle("");
    setErrorMessage("");
    setState("ready");
  };

  const badgeVariant: BadgeVariant = result
    ? LEVEL_TO_BADGE[result.risk.level] ?? "unverified"
    : "unverified";

  const extractedUpi = result?.extracted?.upi;
  const extractedUrls = result?.extracted?.urls;
  const rawQrContent = result?.extracted?.qr?.content;

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
            In-memory payload classification: UPI intents, prefilled debits, payee spoofing, and malicious QR destinations.
          </p>
        </div>

        {/* State Switcher — only visible when dev tools enabled */}
        {showDevTools && (
          <div className="flex items-center gap-1.5 p-1 rounded-lg border border-border bg-elevated/40 text-[11px] font-mono self-start sm:self-auto">
            <span className="text-muted-foreground px-2">State:</span>
            {(["ready", "analyzing", "empty", "error"] as PageState[]).map((s) => (
              <button
                key={s}
                onClick={() => setState(s)}
                className={`px-2 py-0.5 rounded ${state === s ? "bg-primary text-white" : "text-slate-400"}`}
              >
                {s}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Safety & Zero Disk Retention Banner */}
      <div className="p-3.5 rounded-lg border border-emerald-500/30 bg-emerald-500/10 text-xs font-mono text-slate-300 flex items-center gap-2.5">
        <HardDrive className="w-4 h-4 text-emerald-400 shrink-0" />
        <span>
          <strong className="text-white">Zero Disk Retention:</strong> Uploaded images and camera frames are decoded strictly in volatile system RAM using OpenCV / pyzbar and immediately purged. Image files are never stored on server disks.
        </span>
      </div>

      {/* Mode Tabs: Paste | Upload | Camera */}
      <div className="flex items-center gap-2 border-b border-border pb-2">
        <button
          onClick={() => handleTabChange("paste")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-mono text-xs font-semibold transition-colors ${
            activeTab === "paste"
              ? "bg-primary text-white shadow-md"
              : "bg-surface/60 text-slate-400 hover:text-white hover:bg-elevated"
          }`}
        >
          <FileText className="w-3.5 h-3.5" />
          Paste URI / Text
        </button>

        <button
          onClick={() => handleTabChange("upload")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-mono text-xs font-semibold transition-colors ${
            activeTab === "upload"
              ? "bg-primary text-white shadow-md"
              : "bg-surface/60 text-slate-400 hover:text-white hover:bg-elevated"
          }`}
        >
          <UploadCloud className="w-3.5 h-3.5" />
          Upload QR Image
        </button>

        <button
          onClick={() => handleTabChange("camera")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-mono text-xs font-semibold transition-colors ${
            activeTab === "camera"
              ? "bg-primary text-white shadow-md"
              : "bg-surface/60 text-slate-400 hover:text-white hover:bg-elevated"
          }`}
        >
          <Camera className="w-3.5 h-3.5" />
          Camera Scanner
        </button>
      </div>

      {/* Tab 1: Paste URI / Text */}
      {activeTab === "paste" && (
        <div className="rounded-xl border border-border bg-surface p-5 sm:p-6 space-y-5">
          <div>
            <label htmlFor="qr-payload-text" className="block font-mono text-xs font-semibold text-slate-300 uppercase mb-2">
              Decoded UPI Payment URI or QR Content
            </label>
            <textarea
              id="qr-payload-text"
              rows={3}
              value={payloadText}
              onChange={(e) => setPayloadText(e.target.value)}
              placeholder="e.g. upi://pay?pa=ramesh123@oksbi&pn=Ramesh Kumar or http://sbi-kyc-update.xyz/login"
              className="w-full rounded-lg border border-input bg-input-bg p-3 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary font-mono"
            />
          </div>

          {/* Context Question (3 Radio Buttons) */}
          <div className="rounded-lg border border-border/70 bg-elevated/40 p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <label className="block font-mono text-xs font-semibold text-slate-200">
                  Why are you scanning this?
                </label>
                <p className="text-[11px] font-mono text-muted-foreground">
                  Optional context helps GARUDA identify reverse-debit and social engineering schemes.
                </p>
              </div>
              {scanContext && (
                <button
                  type="button"
                  onClick={() => setScanContext(null)}
                  className="text-[11px] font-mono text-accent-cyan hover:underline cursor-pointer"
                >
                  Clear
                </button>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5">
              <label
                className={`flex items-start gap-2.5 p-3 rounded-lg border text-xs font-mono cursor-pointer transition-colors ${
                  scanContext === "known_payee"
                    ? "border-primary bg-primary/10 text-white"
                    : "border-border bg-surface/60 text-slate-300 hover:border-slate-500"
                }`}
              >
                <input
                  type="radio"
                  name="qr-context"
                  value="known_payee"
                  checked={scanContext === "known_payee"}
                  onChange={() => setScanContext("known_payee")}
                  className="mt-0.5 text-primary focus:ring-primary"
                />
                <span className="leading-snug">Paying a shop or person I know</span>
              </label>

              <label
                className={`flex items-start gap-2.5 p-3 rounded-lg border text-xs font-mono cursor-pointer transition-colors ${
                  scanContext === "receive_money"
                    ? "border-risk-high bg-risk-high/10 text-white"
                    : "border-border bg-surface/60 text-slate-300 hover:border-slate-500"
                }`}
              >
                <input
                  type="radio"
                  name="qr-context"
                  value="receive_money"
                  checked={scanContext === "receive_money"}
                  onChange={() => setScanContext("receive_money")}
                  className="mt-0.5 text-risk-high focus:ring-risk-high"
                />
                <span className="leading-snug text-amber-300 font-semibold">
                  Someone said I will RECEIVE money, refund or prize
                </span>
              </label>

              <label
                className={`flex items-start gap-2.5 p-3 rounded-lg border text-xs font-mono cursor-pointer transition-colors ${
                  scanContext === "stranger_request"
                    ? "border-amber-500 bg-amber-500/10 text-white"
                    : "border-border bg-surface/60 text-slate-300 hover:border-slate-500"
                }`}
              >
                <input
                  type="radio"
                  name="qr-context"
                  value="stranger_request"
                  checked={scanContext === "stranger_request"}
                  onChange={() => setScanContext("stranger_request")}
                  className="mt-0.5 text-amber-500 focus:ring-amber-500"
                />
                <span className="leading-snug">A stranger or caller asked me to pay</span>
              </label>
            </div>
          </div>

          {/* Controls & Actions */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2 border-t border-border">
            <label className="flex items-center gap-2 cursor-pointer select-none text-xs font-mono text-slate-300 hover:text-white">
              <input
                type="checkbox"
                checked={saveToHistory}
                onChange={(e) => setSaveToHistory(e.target.checked)}
                className="rounded border-input bg-input-bg text-primary focus:ring-primary w-4 h-4"
              />
              <span>Save to history</span>
            </label>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleClear}
                disabled={!payloadText && !result}
                className="gap-1 font-mono text-xs"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                Clear
              </Button>

              <Button
                onClick={handleAnalyzeText}
                disabled={state === "analyzing" || !payloadText.trim()}
                className="gap-1.5 font-mono text-xs px-5 font-semibold"
              >
                <ShieldCheck className="w-4 h-4" />
                {state === "analyzing" ? "Analyzing..." : "Analyze QR Code"}
              </Button>
            </div>
          </div>

          {/* Quick Samples */}
          <div className="pt-3 border-t border-border/60">
            <span className="text-[11px] font-mono text-muted-foreground block mb-2">
              Try an example payload:
            </span>
            <div className="flex flex-wrap gap-2">
              {[
                { tag: "Safe UPI", val: "upi://pay?pa=ramesh123@oksbi&pn=Ramesh Kumar" },
                { tag: "Scam UPI", val: "upi://pay?pa=sbi.refund@ybl&pn=SBI Refund&am=4999&tn=refund received" },
                { tag: "Phishing Link", val: "http://sbi-kyc-update.xyz/login" },
              ].map((s) => (
                <button
                  key={s.tag}
                  onClick={() => handleSample(s.val)}
                  className="text-[11px] font-mono px-2 py-1 rounded bg-elevated hover:bg-slate-800 text-slate-300 hover:text-white border border-border"
                >
                  [{s.tag}] {s.val.split("&")[0]}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Upload Image */}
      {activeTab === "upload" && (
        <div className="rounded-xl border border-border bg-surface p-5 sm:p-6 space-y-5">
          <div className="rounded-xl border border-dashed border-border bg-surface/50 p-6 flex flex-col items-center justify-center text-center relative hover:border-slate-500 transition-colors">
            <UploadCloud className="w-10 h-10 text-primary mb-3" />
            <h4 className="font-mono text-sm font-semibold text-white mb-1">
              Upload QR Image (PNG, JPG, WEBP)
            </h4>
            <p className="text-xs text-muted-foreground mb-4">
              Magic-byte verified · Maximum 5 MB per image · In-memory decode
            </p>

            <input
              type="file"
              accept="image/png,image/jpeg,image/webp"
              onChange={handleFileUpload}
              id="qr-file-upload-input"
              className="hidden"
            />
            <label htmlFor="qr-file-upload-input">
              <Button asChild size="sm" variant="outline" className="cursor-pointer">
                <span>{selectedFile ? selectedFile.name : "Choose QR File"}</span>
              </Button>
            </label>

            {selectedFile && (
              <p className="text-[11px] font-mono text-accent-cyan mt-2">
                Selected: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
              </p>
            )}

            {filePreview && (
              <div className="mt-4 max-w-[200px] max-h-[200px] overflow-hidden rounded-lg border border-border">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={filePreview} alt="QR Preview" className="w-full h-full object-contain" />
              </div>
            )}
          </div>

          {/* Context Question (3 Radio Buttons) */}
          <div className="rounded-lg border border-border/70 bg-elevated/40 p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <label className="block font-mono text-xs font-semibold text-slate-200">
                  Why are you scanning this?
                </label>
                <p className="text-[11px] font-mono text-muted-foreground">
                  Optional context helps GARUDA identify reverse-debit and social engineering schemes.
                </p>
              </div>
              {scanContext && (
                <button
                  type="button"
                  onClick={() => setScanContext(null)}
                  className="text-[11px] font-mono text-accent-cyan hover:underline cursor-pointer"
                >
                  Clear
                </button>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5">
              <label
                className={`flex items-start gap-2.5 p-3 rounded-lg border text-xs font-mono cursor-pointer transition-colors ${
                  scanContext === "known_payee"
                    ? "border-primary bg-primary/10 text-white"
                    : "border-border bg-surface/60 text-slate-300 hover:border-slate-500"
                }`}
              >
                <input
                  type="radio"
                  name="qr-context-upload"
                  value="known_payee"
                  checked={scanContext === "known_payee"}
                  onChange={() => setScanContext("known_payee")}
                  className="mt-0.5 text-primary focus:ring-primary"
                />
                <span className="leading-snug">Paying a shop or person I know</span>
              </label>

              <label
                className={`flex items-start gap-2.5 p-3 rounded-lg border text-xs font-mono cursor-pointer transition-colors ${
                  scanContext === "receive_money"
                    ? "border-risk-high bg-risk-high/10 text-white"
                    : "border-border bg-surface/60 text-slate-300 hover:border-slate-500"
                }`}
              >
                <input
                  type="radio"
                  name="qr-context-upload"
                  value="receive_money"
                  checked={scanContext === "receive_money"}
                  onChange={() => setScanContext("receive_money")}
                  className="mt-0.5 text-risk-high focus:ring-risk-high"
                />
                <span className="leading-snug text-amber-300 font-semibold">
                  Someone said I will RECEIVE money, refund or prize
                </span>
              </label>

              <label
                className={`flex items-start gap-2.5 p-3 rounded-lg border text-xs font-mono cursor-pointer transition-colors ${
                  scanContext === "stranger_request"
                    ? "border-amber-500 bg-amber-500/10 text-white"
                    : "border-border bg-surface/60 text-slate-300 hover:border-slate-500"
                }`}
              >
                <input
                  type="radio"
                  name="qr-context-upload"
                  value="stranger_request"
                  checked={scanContext === "stranger_request"}
                  onChange={() => setScanContext("stranger_request")}
                  className="mt-0.5 text-amber-500 focus:ring-amber-500"
                />
                <span className="leading-snug">A stranger or caller asked me to pay</span>
              </label>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2 border-t border-border">
            <label className="flex items-center gap-2 cursor-pointer select-none text-xs font-mono text-slate-300 hover:text-white">
              <input
                type="checkbox"
                checked={saveToHistory}
                onChange={(e) => setSaveToHistory(e.target.checked)}
                className="rounded border-input bg-input-bg text-primary focus:ring-primary w-4 h-4"
              />
              <span>Save to history</span>
            </label>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleClear}
                disabled={!selectedFile && !result}
                className="gap-1 font-mono text-xs"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                Clear
              </Button>

              <Button
                onClick={handleAnalyzeFile}
                disabled={state === "analyzing" || !selectedFile}
                className="gap-1.5 font-mono text-xs px-5 font-semibold"
              >
                <ShieldCheck className="w-4 h-4" />
                {state === "analyzing" ? "Analyzing Image..." : "Analyze QR Image"}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Camera Scanner */}
      {activeTab === "camera" && (
        <div className="rounded-xl border border-border bg-surface p-5 sm:p-6 space-y-5">
          <div className="flex flex-col items-center justify-center text-center space-y-4">
            <div className="relative w-full max-w-md aspect-video bg-black rounded-lg overflow-hidden border border-border flex items-center justify-center">
              {cameraActive ? (
                <>
                  <video ref={videoRef} className="w-full h-full object-cover" autoPlay playsInline muted />
                  <div className="absolute inset-0 border-2 border-accent-cyan/60 rounded pointer-events-none m-8 animate-pulse" />
                </>
              ) : (
                <div className="flex flex-col items-center justify-center p-6 text-muted-foreground font-mono text-xs">
                  <Camera className="w-10 h-10 mb-2 text-slate-500" />
                  <span>Camera is inactive</span>
                </div>
              )}
            </div>

            {cameraError && (
              <div className="p-3 rounded-lg border border-risk-high/30 bg-risk-high/10 text-xs font-mono text-slate-300">
                {cameraError}
              </div>
            )}

            <div className="flex flex-wrap items-center gap-3">
              {!cameraActive ? (
                <Button onClick={startCamera} className="gap-2 font-mono text-xs font-semibold">
                  <Camera className="w-4 h-4" />
                  Start Live Camera
                </Button>
              ) : (
                <>
                  <Button variant="outline" onClick={stopCamera} className="gap-2 font-mono text-xs">
                    <VideoOff className="w-4 h-4" />
                    Stop Camera
                  </Button>
                  <Button onClick={handleCaptureFrame} className="gap-2 font-mono text-xs font-semibold">
                    <ShieldCheck className="w-4 h-4" />
                    Capture &amp; Analyze Frame
                  </Button>
                </>
              )}
            </div>
          </div>

          {/* Context Question (3 Radio Buttons) */}
          <div className="rounded-lg border border-border/70 bg-elevated/40 p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <label className="block font-mono text-xs font-semibold text-slate-200">
                  Why are you scanning this?
                </label>
                <p className="text-[11px] font-mono text-muted-foreground">
                  Optional context helps GARUDA identify reverse-debit and social engineering schemes.
                </p>
              </div>
              {scanContext && (
                <button
                  type="button"
                  onClick={() => setScanContext(null)}
                  className="text-[11px] font-mono text-accent-cyan hover:underline cursor-pointer"
                >
                  Clear
                </button>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5">
              <label
                className={`flex items-start gap-2.5 p-3 rounded-lg border text-xs font-mono cursor-pointer transition-colors ${
                  scanContext === "known_payee"
                    ? "border-primary bg-primary/10 text-white"
                    : "border-border bg-surface/60 text-slate-300 hover:border-slate-500"
                }`}
              >
                <input
                  type="radio"
                  name="qr-context-camera"
                  value="known_payee"
                  checked={scanContext === "known_payee"}
                  onChange={() => setScanContext("known_payee")}
                  className="mt-0.5 text-primary focus:ring-primary"
                />
                <span className="leading-snug">Paying a shop or person I know</span>
              </label>

              <label
                className={`flex items-start gap-2.5 p-3 rounded-lg border text-xs font-mono cursor-pointer transition-colors ${
                  scanContext === "receive_money"
                    ? "border-risk-high bg-risk-high/10 text-white"
                    : "border-border bg-surface/60 text-slate-300 hover:border-slate-500"
                }`}
              >
                <input
                  type="radio"
                  name="qr-context-camera"
                  value="receive_money"
                  checked={scanContext === "receive_money"}
                  onChange={() => setScanContext("receive_money")}
                  className="mt-0.5 text-risk-high focus:ring-risk-high"
                />
                <span className="leading-snug text-amber-300 font-semibold">
                  Someone said I will RECEIVE money, refund or prize
                </span>
              </label>

              <label
                className={`flex items-start gap-2.5 p-3 rounded-lg border text-xs font-mono cursor-pointer transition-colors ${
                  scanContext === "stranger_request"
                    ? "border-amber-500 bg-amber-500/10 text-white"
                    : "border-border bg-surface/60 text-slate-300 hover:border-slate-500"
                }`}
              >
                <input
                  type="radio"
                  name="qr-context-camera"
                  value="stranger_request"
                  checked={scanContext === "stranger_request"}
                  onChange={() => setScanContext("stranger_request")}
                  className="mt-0.5 text-amber-500 focus:ring-amber-500"
                />
                <span className="leading-snug">A stranger or caller asked me to pay</span>
              </label>
            </div>
          </div>
        </div>
      )}

      {/* Dynamic States */}
      {state === "analyzing" && (
        <LoadingState
          message="Decoding and Classifying QR Payload..."
          description="Parsing payment URI parameters, evaluating legitimacy signals, and cross-checking deceptive intent."
        />
      )}

      {state === "empty" && (
        <EmptyState
          title="No QR Input Provided"
          description="Please paste a UPI payment link, upload a QR image, or scan with your camera."
          actionLabel="Load Safe UPI Sample"
          onAction={() => handleSample("upi://pay?pa=ramesh123@oksbi&pn=Ramesh Kumar")}
        />
      )}

      {state === "error" && (
        <ErrorState
          title={errorTitle}
          message={errorMessage || "Could not analyze the provided QR payload."}
          details="Nothing was saved to your history."
          onRetry={activeTab === "paste" ? handleAnalyzeText : activeTab === "upload" ? handleAnalyzeFile : undefined}
        />
      )}

      {/* Result Section (Pure API Response, zero hardcoded or mock results) */}
      {state === "result" && result && (
        <div className="rounded-xl border border-border bg-surface p-6 space-y-6">
          {/* Top Banner: Decoded Type & Score */}
          <div className="flex flex-wrap items-start justify-between gap-3 border-b border-border pb-4">
            <div className="min-w-0">
              <span className="font-mono text-xs text-muted-foreground uppercase">
                Vector: {result.extracted?.qr?.type?.toUpperCase() || "QR PAYLOAD"}
              </span>
              <h3 className="font-mono text-base font-bold text-white break-all">
                {result.category.label}
              </h3>
              {rawQrContent && (
                <div className="flex items-center gap-2 mt-1">
                  <code className="text-[11px] font-mono text-slate-400 break-all bg-elevated px-2 py-0.5 rounded border border-border">
                    {rawQrContent.length > 80 ? `${rawQrContent.slice(0, 80)}...` : rawQrContent}
                  </code>
                  <button
                    onClick={() => handleCopy(rawQrContent)}
                    className="text-xs text-muted-foreground hover:text-white transition-colors"
                    title="Copy payload"
                  >
                    {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
              )}
            </div>

            <div className="flex flex-col items-end gap-1.5">
              <Badge variant={badgeVariant} className="text-sm px-3 py-1">
                {result.risk.score} · {result.risk.label}
              </Badge>
              <span className="text-[11px] font-mono text-slate-400">
                Confidence: {Math.round(result.confidence * 100)}%
              </span>
            </div>
          </div>

          {/* Extracted UPI Breakdown */}
          {extractedUpi && (
            <div className="p-4 rounded-lg border border-border bg-elevated/40 space-y-3 font-mono text-xs">
              <span className="text-muted-foreground uppercase text-[11px] block font-semibold">
                Decoded UPI Transaction Details
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                <div className="bg-surface/80 p-2.5 rounded border border-border">
                  <span className="text-muted-foreground block text-[10px]">PAYEE VPA</span>
                  <span className="text-white font-bold select-all">{extractedUpi.pa || "Not specified"}</span>
                </div>
                <div className="bg-surface/80 p-2.5 rounded border border-border">
                  <span className="text-muted-foreground block text-[10px]">PAYEE NAME</span>
                  <span className="text-white select-all">{extractedUpi.pn || "Not specified"}</span>
                </div>
                <div className="bg-surface/80 p-2.5 rounded border border-border">
                  <span className="text-muted-foreground block text-[10px]">PREFILLED AMOUNT</span>
                  <span className={`font-bold ${extractedUpi.am ? "text-amber-400" : "text-slate-300"}`}>
                    {extractedUpi.am ? `₹${extractedUpi.am}` : "None (User enters amount)"}
                  </span>
                </div>
                <div className="bg-surface/80 p-2.5 rounded border border-border">
                  <span className="text-muted-foreground block text-[10px]">TRANSACTION NOTE</span>
                  <span className="text-slate-300 select-all">{extractedUpi.tn ? `"${extractedUpi.tn}"` : "None"}</span>
                </div>
              </div>
            </div>
          )}

          {/* Extracted URL Breakdown */}
          {extractedUrls && extractedUrls.length > 0 && extractedUrls[0]?.raw && (
            <div className="p-4 rounded-lg border border-border bg-elevated/40 space-y-2 font-mono text-xs">
              <span className="text-muted-foreground uppercase text-[11px] block font-semibold">
                Decoded Destination Web Address
              </span>
              <p className="text-white break-all select-all">{extractedUrls[0].raw}</p>
              {extractedUrls[0].domain && (
                <p className="text-[11px] text-slate-400">
                  Registered domain: <span className="text-slate-200">{extractedUrls[0].domain}</span>
                </p>
              )}
            </div>
          )}

          {/* Summary */}
          <div className="space-y-1.5">
            <span className="text-[11px] font-mono text-muted-foreground uppercase block">Summary</span>
            <p className="text-sm text-slate-300 leading-relaxed font-mono">{result.summary}</p>
          </div>

          {/* Verification Status Banner */}
          <div className="p-3.5 rounded-lg border border-border bg-elevated/40 text-xs font-mono text-slate-300">
            <span className="text-muted-foreground uppercase text-[11px] block mb-1">List &amp; Integrity Status</span>
            {verificationText(result.verification_status)}
          </div>

          {/* Warning Signs (Threat Indicators) */}
          {result.indicators && result.indicators.length > 0 && (
            <div className="space-y-2">
              <span className="text-[11px] font-mono text-muted-foreground uppercase flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-risk-high" /> Warning signs found ({result.indicators.length})
              </span>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {result.indicators.map((ind) => (
                  <div key={ind.code} className="p-3.5 rounded-lg border border-border bg-elevated/40 text-xs font-mono">
                    <div className="flex items-center justify-between gap-2">
                      <span className={`font-bold ${SEVERITY_COLOR[ind.severity] ?? "text-slate-200"}`}>
                        {ind.label}
                      </span>
                      <span className="text-[10px] uppercase text-slate-400 shrink-0">{ind.severity}</span>
                    </div>
                    {ind.evidence && (
                      <p className="text-[11px] text-slate-400 mt-1 break-all">Evidence: {ind.evidence}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Good signs (Legitimacy Signals) */}
          {result.legitimacy_signals && result.legitimacy_signals.length > 0 && (
            <div className="space-y-2">
              <span className="text-[11px] font-mono text-muted-foreground uppercase flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> Legitimacy Signals
              </span>
              <div className="space-y-2">
                {result.legitimacy_signals.map((sig) => (
                  <div key={sig.code} className="p-3 rounded-lg border border-[#34D399]/30 bg-[#34D399]/10 text-xs font-mono">
                    <span className="font-bold text-[#34D399]">{sig.label}</span>
                    {sig.evidence && <p className="text-[11px] text-slate-400 mt-1 break-all">{sig.evidence}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {result.recommendations && result.recommendations.length > 0 && (
            <div className="space-y-2">
              <span className="text-[11px] font-mono text-muted-foreground uppercase flex items-center gap-1.5">
                <ShieldAlert className="w-3.5 h-3.5 text-primary" /> What you should do
              </span>
              <ul className="list-disc pl-5 space-y-1 text-sm text-slate-300 font-mono">
                {result.recommendations.map((rec, i) => (
                  <li key={i}>{rec}</li>
                ))}
              </ul>
            </div>
          )}

          {/* How to verify steps */}
          {result.verify_steps && result.verify_steps.length > 0 && (
            <div className="space-y-2">
              <span className="text-[11px] font-mono text-muted-foreground uppercase flex items-center gap-1.5">
                <ListChecks className="w-3.5 h-3.5 text-accent-cyan" /> How to verify safely
              </span>
              <ol className="list-decimal pl-5 space-y-1 text-sm text-slate-300 font-mono">
                {result.verify_steps.map((step, i) => (
                  <li key={i}>{step}</li>
                ))}
              </ol>
            </div>
          )}

          {/* Footer */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-4 border-t border-border text-[11px] font-mono text-slate-400">
            <span>
              {result.scan_id ? "Saved to your history." : "Not saved (Save to history was off)."} Engine{" "}
              {result.engine_version}
            </span>
            {result.scan_id && (
              <Link href="/history" className="flex items-center gap-1 text-accent-cyan hover:underline">
                <History className="w-3.5 h-3.5" /> View history
              </Link>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
