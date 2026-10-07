"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  FileCheck2,
  ArrowLeft,
  ArrowRight,
  ShieldAlert,
  CheckCircle2,
  Copy,
  Check,
  ExternalLink,
  AlertTriangle,
  UploadCloud,
  FileText,
} from "lucide-react";

// MOCK: Categories following docs/ARCHITECTURE.md
const CATEGORY_OPTIONS = [
  { value: "financial_fraud", label: "Financial Fraud / UPI Collect Scam" },
  { value: "phishing", label: "Phishing / Credential Harvesting" },
  { value: "utility_impersonation", label: "Utility Impersonation (Electricity/Gas)" },
  { value: "fake_job_investment", label: "Fake Job / Task / Investment Fraud" },
  { value: "lottery_reward", label: "Lottery / KBC / Cash Reward Lure" },
  { value: "identity_theft", label: "Government / Police Impersonation (Digital Arrest)" },
  { value: "other", label: "Other Suspicious Cyber Incident" },
];

function NewReportForm() {
  const searchParams = useSearchParams();
  const initialScanId = searchParams.get("scan_id") || "";

  // Wizard state: 1 (Details) -> 2 (Evidence) -> 3 (Review & Submit) -> 4 (Submitted Status Panel)
  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);

  // Form state
  const [formData, setFormData] = useState({
    title: initialScanId ? "Incident linked to Scan " + initialScanId : "",
    category: "financial_fraud",
    incidentDate: new Date().toISOString().split("T")[0],
    description: "",
    evidenceType: "message",
    evidenceText: "",
    scanId: initialScanId,
    offenderContact: "",
    consentAgreed: false,
  });

  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [generatedRef, setGeneratedRef] = useState("GAR-2026-000142");
  const [copiedRef, setCopiedRef] = useState(false);

  // Quick fill sample for testing
  const handleLoadSample = () => {
    setFormData({
      title: "WhatsApp Message demanding bill payment with disconnection threat",
      category: "utility_impersonation",
      incidentDate: "2026-10-07",
      description:
        "Received urgent message claiming my electricity connection would be cut off at 9:30 PM unless I called an unauthorized mobile number immediately.",
      evidenceType: "message",
      evidenceText:
        "Electricity Power will be disconnected tonight 9:30 PM due to unpaid bill. Call electricity officer immediately: 9876543210 to update bill.",
      scanId: initialScanId || "scan_102",
      offenderContact: "+91 9876543210",
      consentAgreed: true,
    });
    setFormErrors({});
  };

  const validateStep1 = () => {
    const errors: Record<string, string> = {};
    if (!formData.title.trim()) errors.title = "Report title is required";
    if (!formData.description.trim()) errors.description = "Incident description is required";
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const validateStep2 = () => {
    const errors: Record<string, string> = {};
    if (!formData.evidenceText.trim()) errors.evidenceText = "Evidence text or telemetry is required";
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleNext = () => {
    if (step === 1 && validateStep1()) {
      setStep(2);
    } else if (step === 2 && validateStep2()) {
      setStep(3);
    }
  };

  const handleSubmit = () => {
    if (!formData.consentAgreed) {
      setFormErrors({ consent: "You must acknowledge the reporting disclaimer before submitting" });
      return;
    }

    setIsSubmitting(true);
    // MOCK: Simulate API POST /api/reports response
    setTimeout(() => {
      // Generate a dynamic reference code matching GAR-{year}-{seq:06d}
      const randomSeq = Math.floor(100000 + Math.random() * 900000);
      setGeneratedRef(`GAR-2026-${randomSeq}`);
      setIsSubmitting(false);
      setStep(4);
    }, 700);
  };

  const handleCopyRef = () => {
    navigator.clipboard.writeText(generatedRef);
    setCopiedRef(true);
    setTimeout(() => setCopiedRef(false), 2000);
  };

  return (
    <div className="space-y-8 max-w-3xl mx-auto pb-12">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
        <div>
          <div className="flex items-center gap-2">
            <Button asChild variant="ghost" size="sm" className="h-7 px-2 font-mono text-xs text-muted-foreground">
              <Link href="/reports">
                <ArrowLeft className="w-3.5 h-3.5 mr-1" />
                Reports Center
              </Link>
            </Button>
          </div>
          <h2 className="font-mono text-2xl sm:text-3xl font-bold text-white mt-1 flex items-center gap-2">
            <FileCheck2 className="w-6 h-6 text-purple-400" />
            File Incident Report
          </h2>
          <p className="text-xs sm:text-sm text-muted-foreground mt-1">
            Package threat telemetry into a verified GARUDA dossier (GAR-2026-XXXXXX).
          </p>
        </div>

        {step !== 4 && (
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleLoadSample}
            className="font-mono text-xs text-slate-300 self-start sm:self-auto"
          >
            Try an example
          </Button>
        )}
      </div>

      {/* Step Progress Indicator (Steps 1 to 3) */}
      {step !== 4 && (
        <div className="grid grid-cols-3 gap-2 font-mono text-xs">
          <div
            className={`p-3 rounded-lg border text-center transition-colors ${
              step === 1
                ? "border-primary bg-primary/10 text-white font-semibold"
                : step > 1
                ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-400"
                : "border-border bg-surface text-muted-foreground"
            }`}
          >
            1. Details
          </div>
          <div
            className={`p-3 rounded-lg border text-center transition-colors ${
              step === 2
                ? "border-primary bg-primary/10 text-white font-semibold"
                : step > 2
                ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-400"
                : "border-border bg-surface text-muted-foreground"
            }`}
          >
            2. Evidence
          </div>
          <div
            className={`p-3 rounded-lg border text-center transition-colors ${
              step === 3
                ? "border-primary bg-primary/10 text-white font-semibold"
                : "border-border bg-surface text-muted-foreground"
            }`}
          >
            3. Review &amp; Submit
          </div>
        </div>
      )}

      {/* Step 1: Details */}
      {step === 1 && (
        <Card className="border-border bg-surface p-6 space-y-6">
          <div className="border-b border-border pb-3">
            <h3 className="font-mono text-sm font-bold text-white uppercase tracking-wider">
              Step 1: Incident Description &amp; Category
            </h3>
            <p className="text-xs text-muted-foreground mt-1">
              Provide context regarding how you encountered this suspicious interaction.
            </p>
          </div>

          <div className="space-y-4 text-xs font-mono">
            <div>
              <label className="text-slate-300 block mb-1.5 font-semibold">
                Report Title <span className="text-destructive">*</span>
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                placeholder="e.g. Unsolicited Telegram lottery claim requiring registration fee"
                className="w-full rounded-md border border-border bg-elevated px-3 py-2 text-white focus:outline-none focus:border-primary text-xs font-sans"
              />
              {formErrors.title && (
                <p className="text-destructive text-[11px] mt-1">{formErrors.title}</p>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-slate-300 block mb-1.5 font-semibold">
                  Incident Category <span className="text-destructive">*</span>
                </label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="w-full rounded-md border border-border bg-elevated px-3 py-2 text-white focus:outline-none focus:border-primary text-xs"
                >
                  {CATEGORY_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-slate-300 block mb-1.5 font-semibold">
                  Incident Date <span className="text-destructive">*</span>
                </label>
                <input
                  type="date"
                  value={formData.incidentDate}
                  onChange={(e) => setFormData({ ...formData, incidentDate: e.target.value })}
                  className="w-full rounded-md border border-border bg-elevated px-3 py-2 text-white focus:outline-none focus:border-primary text-xs"
                />
              </div>
            </div>

            <div>
              <label className="text-slate-300 block mb-1.5 font-semibold">
                Detailed Narrative / What Happened <span className="text-destructive">*</span>
              </label>
              <textarea
                rows={4}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Explain the background: which channel did they contact you on? What pressure or claims did they make?"
                className="w-full rounded-md border border-border bg-elevated p-3 text-white focus:outline-none focus:border-primary text-xs font-sans"
              />
              {formErrors.description && (
                <p className="text-destructive text-[11px] mt-1">{formErrors.description}</p>
              )}
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <Button onClick={handleNext} className="gap-1.5 font-mono text-xs">
              Proceed to Evidence
              <ArrowRight className="w-3.5 h-3.5" />
            </Button>
          </div>
        </Card>
      )}

      {/* Step 2: Evidence */}
      {step === 2 && (
        <Card className="border-border bg-surface p-6 space-y-6">
          <div className="border-b border-border pb-3">
            <h3 className="font-mono text-sm font-bold text-white uppercase tracking-wider">
              Step 2: Attach Telemetry &amp; Evidence
            </h3>
            <p className="text-xs text-muted-foreground mt-1">
              Paste the text, URL, UPI handle, or telemetry extracted during analysis.
            </p>
          </div>

          <div className="space-y-4 text-xs font-mono">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-slate-300 block mb-1.5 font-semibold">
                  Evidence Format
                </label>
                <select
                  value={formData.evidenceType}
                  onChange={(e) => setFormData({ ...formData, evidenceType: e.target.value })}
                  className="w-full rounded-md border border-border bg-elevated px-3 py-2 text-white focus:outline-none focus:border-primary text-xs"
                >
                  <option value="message">SMS / WhatsApp Message Text</option>
                  <option value="url">Suspicious URL / Phishing Domain</option>
                  <option value="qr">QR Code / UPI String</option>
                  <option value="text">General Telemetry Snippet</option>
                </select>
              </div>

              <div>
                <label className="text-slate-300 block mb-1.5 font-semibold">
                  Offending Contact / ID (Optional)
                </label>
                <input
                  type="text"
                  value={formData.offenderContact}
                  onChange={(e) => setFormData({ ...formData, offenderContact: e.target.value })}
                  placeholder="e.g. +91 9876543210 or sender handle"
                  className="w-full rounded-md border border-border bg-elevated px-3 py-2 text-white focus:outline-none focus:border-primary text-xs"
                />
              </div>
            </div>

            {formData.scanId && (
              <div className="p-3 rounded-lg border border-border/80 bg-background/50 flex items-center justify-between">
                <div>
                  <span className="text-[11px] text-muted-foreground block">Linked Analysis Dossier</span>
                  <span className="text-white font-semibold">{formData.scanId}</span>
                </div>
                <Badge variant="outline" className="border-primary/40 text-primary">
                  Linked
                </Badge>
              </div>
            )}

            <div>
              <label className="text-slate-300 block mb-1.5 font-semibold">
                Evidence Payload / Exact Telemetry <span className="text-destructive">*</span>
              </label>
              <textarea
                rows={5}
                value={formData.evidenceText}
                onChange={(e) => setFormData({ ...formData, evidenceText: e.target.value })}
                placeholder="Paste the verbatim text of the message, link, or decoded QR payload exactly as received."
                className="w-full rounded-md border border-border bg-[#070B14] p-3 text-slate-200 focus:outline-none focus:border-primary text-xs font-mono"
              />
              {formErrors.evidenceText && (
                <p className="text-destructive text-[11px] mt-1">{formErrors.evidenceText}</p>
              )}
            </div>
          </div>

          <div className="flex items-center justify-between pt-2">
            <Button variant="outline" onClick={() => setStep(1)} className="gap-1.5 font-mono text-xs">
              <ArrowLeft className="w-3.5 h-3.5" />
              Back
            </Button>
            <Button onClick={handleNext} className="gap-1.5 font-mono text-xs">
              Review Dossier
              <ArrowRight className="w-3.5 h-3.5" />
            </Button>
          </div>
        </Card>
      )}

      {/* Step 3: Review & Submit */}
      {step === 3 && (
        <Card className="border-border bg-surface p-6 space-y-6">
          <div className="border-b border-border pb-3">
            <h3 className="font-mono text-sm font-bold text-white uppercase tracking-wider">
              Step 3: Review Dossier &amp; Submit
            </h3>
            <p className="text-xs text-muted-foreground mt-1">
              Confirm your report contents. Upon submission, a permanent reference code will be generated.
            </p>
          </div>

          {/* Dossier Preview Summary */}
          <div className="rounded-lg border border-border bg-elevated/40 p-4 space-y-3 text-xs font-mono">
            <div>
              <span className="text-muted-foreground block">TITLE:</span>
              <span className="text-white font-semibold text-sm">{formData.title}</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 border-t border-border/80">
              <div>
                <span className="text-muted-foreground block">CATEGORY:</span>
                <span className="text-slate-200 capitalize">
                  {CATEGORY_OPTIONS.find((c) => c.value === formData.category)?.label}
                </span>
              </div>
              <div>
                <span className="text-muted-foreground block">INCIDENT DATE:</span>
                <span className="text-slate-200">{formData.incidentDate}</span>
              </div>
            </div>
            <div className="pt-2 border-t border-border/80">
              <span className="text-muted-foreground block mb-1">EVIDENCE PAYLOAD:</span>
              <pre className="bg-[#070B14] p-3 rounded text-[11px] text-slate-300 whitespace-pre-wrap break-all">
                {formData.evidenceText}
              </pre>
            </div>
          </div>

          {/* Mandatory Law Enforcement & Purpose Disclaimer */}
          <div className="p-4 rounded-xl border border-amber-500/30 bg-amber-500/10 text-xs font-mono text-slate-300 space-y-3">
            <div className="flex items-center gap-2 font-bold text-amber-400">
              <ShieldAlert className="w-4 h-4 shrink-0" />
              <span>TRANSPARENCY NOTICE &amp; SUBMISSION BOUNDARY</span>
            </div>
            <p className="leading-relaxed">
              Submitting here registers this dossier with <strong>GARUDA</strong> for your personal ledger and threat aggregation.
              <strong> GARUDA does not submit complaints to law enforcement or statutory authorities on your behalf.</strong>
            </p>
            <label className="flex items-start gap-2.5 pt-1 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.consentAgreed}
                onChange={(e) => {
                  setFormData({ ...formData, consentAgreed: e.target.checked });
                  if (formErrors.consent) setFormErrors({});
                }}
                className="mt-0.5 rounded border-border text-primary focus:ring-0"
              />
              <span className="text-slate-200 text-xs select-none">
                I understand that this incident will be recorded as <strong>&ldquo;Submitted to GARUDA&rdquo;</strong> and that external legal complaints must be submitted directly to cybercrime.gov.in or helpline 1930.
              </span>
            </label>
            {formErrors.consent && (
              <p className="text-destructive text-[11px] font-bold">{formErrors.consent}</p>
            )}
          </div>

          <div className="flex items-center justify-between pt-2">
            <Button variant="outline" onClick={() => setStep(2)} className="gap-1.5 font-mono text-xs">
              <ArrowLeft className="w-3.5 h-3.5" />
              Back
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={isSubmitting}
              className="bg-purple-600 hover:bg-purple-700 text-white gap-1.5 font-mono text-xs"
            >
              {isSubmitting ? "Generating Dossier..." : "Submit Incident Report"}
            </Button>
          </div>
        </Card>
      )}

      {/* Step 4: Status Panel (Confirmed Submission) */}
      {step === 4 && (
        <div className="space-y-6">
          {/* Confirmed Status Panel */}
          <Card className="border-purple-500/40 bg-surface p-6 sm:p-8 space-y-6 relative overflow-hidden">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                <span className="font-mono text-xs uppercase text-emerald-400 font-bold tracking-wider">
                  Dossier Generated Successfully
                </span>
              </div>
              <Badge variant="outline" className="border-purple-500/50 bg-purple-500/10 text-purple-300 font-mono text-xs px-3 py-1">
                Submitted to GARUDA
              </Badge>
            </div>

            {/* Reference Code Highlight */}
            <div className="p-5 rounded-xl border border-border bg-elevated/60 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <span className="text-[11px] font-mono text-muted-foreground uppercase block">
                  OFFICIAL INCIDENT REFERENCE
                </span>
                <span className="font-mono text-2xl sm:text-3xl font-extrabold text-white tracking-wider">
                  {generatedRef}
                </span>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={handleCopyRef}
                className="gap-1.5 font-mono text-xs shrink-0"
              >
                {copiedRef ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                    Copied
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    Copy Reference Code
                  </>
                )}
              </Button>
            </div>

            {/* Incident Summary Card */}
            <div className="space-y-2 text-xs font-mono text-slate-300">
              <div className="flex justify-between border-b border-border/80 py-2">
                <span className="text-muted-foreground">Title:</span>
                <span className="text-white font-medium text-right">{formData.title}</span>
              </div>
              <div className="flex justify-between border-b border-border/80 py-2">
                <span className="text-muted-foreground">Category:</span>
                <span className="text-white">
                  {CATEGORY_OPTIONS.find((c) => c.value === formData.category)?.label}
                </span>
              </div>
              <div className="flex justify-between border-b border-border/80 py-2">
                <span className="text-muted-foreground">Incident Date:</span>
                <span className="text-white">{formData.incidentDate}</span>
              </div>
              <div className="flex justify-between py-2">
                <span className="text-muted-foreground">Status:</span>
                <span className="text-purple-300 font-semibold">Submitted to GARUDA</span>
              </div>
            </div>

            {/* External Reporting Helpline Links */}
            <div className="p-4 rounded-xl border border-border bg-background/60 text-xs font-mono space-y-3">
              <span className="text-slate-300 font-bold block">
                Official Law Enforcement Channels (Self-Report Direct):
              </span>
              <p className="text-muted-foreground text-[11px] leading-relaxed">
                If you lost money or suffered identity harm, submit this dossier directly to official government desks. GARUDA does not submit to this channel on your behalf.
              </p>
              <div className="flex flex-wrap items-center gap-4 pt-1">
                <a
                  href="https://cybercrime.gov.in"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-accent-cyan hover:underline inline-flex items-center gap-1 font-semibold"
                >
                  National Portal: cybercrime.gov.in
                  <ExternalLink className="w-3 h-3" />
                </a>
                <a
                  href="tel:1930"
                  className="text-amber-400 hover:underline inline-flex items-center gap-1 font-semibold"
                >
                  Financial Fraud Helpline: 1930
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>

            {/* Actions */}
            <div className="pt-2 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <Button asChild variant="outline" className="font-mono text-xs">
                <Link href="/reports">View in Incident Dossier Ledger</Link>
              </Button>
              <Button
                onClick={() => {
                  setStep(1);
                  setFormData({
                    title: "",
                    category: "financial_fraud",
                    incidentDate: new Date().toISOString().split("T")[0],
                    description: "",
                    evidenceType: "message",
                    evidenceText: "",
                    scanId: "",
                    offenderContact: "",
                    consentAgreed: false,
                  });
                }}
                className="font-mono text-xs"
              >
                File Another Report
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}

export default function NewReportPage() {
  return (
    <React.Suspense fallback={<div className="p-8 text-center text-muted-foreground font-mono text-xs">Loading report wizard...</div>}>
      <NewReportForm />
    </React.Suspense>
  );
}
