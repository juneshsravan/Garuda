"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { LoadingState, EmptyState, ErrorState } from "@/components/ui/states";
import { reportApi, scanApi, ApiClientError } from "@/lib/api-client";
import { ReportItem, ScamType } from "@/types/report";
import {
  FileCheck2,
  PhoneCall,
  ExternalLink,
  ShieldAlert,
  AlertTriangle,
  Building2,
  CheckCircle2,
  Send,
  PlusCircle,
  Clock,
  Link as LinkIcon,
  Smartphone,
  CreditCard,
  QrCode,
  RotateCcw,
} from "lucide-react";

const SCAM_TYPE_OPTIONS: { value: ScamType; label: string }[] = [
  { value: "sms", label: "SMS Scam" },
  { value: "whatsapp", label: "WhatsApp Fraud" },
  { value: "call", label: "Phone Call / Vishing" },
  { value: "link", label: "Malicious / Phishing Link" },
  { value: "qr_upi", label: "QR Code / UPI Payment Fraud" },
  { value: "email", label: "Phishing Email" },
  { value: "other", label: "Other Fraud" },
];

function ReportCenterContent() {
  const searchParams = useSearchParams();
  const scanIdParam = searchParams.get("scan_id");

  // Form State
  const [scamType, setScamType] = useState<ScamType>("sms");
  const [content, setContent] = useState("");
  const [scammerPhone, setScammerPhone] = useState("");
  const [scammerUpi, setScammerUpi] = useState("");
  const [scammerUrl, setScammerUrl] = useState("");
  const [amountLost, setAmountLost] = useState<string>("");
  const [incidentDate, setIncidentDate] = useState<string>(
    new Date().toISOString().split("T")[0]
  );
  const [linkedScanId, setLinkedScanId] = useState<string | null>(scanIdParam);

  const [formLoading, setFormLoading] = useState(false);
  const [formSuccessMessage, setFormSuccessMessage] = useState<string | null>(null);
  const [formErrorMessage, setFormErrorMessage] = useState<string | null>(null);

  // My Reports list state
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [reportsLoading, setReportsLoading] = useState(true);
  const [reportsError, setReportsError] = useState<string | null>(null);

  // Fetch reports on mount
  const fetchReports = async () => {
    try {
      setReportsLoading(true);
      setReportsError(null);
      const data = await reportApi.listReports();
      setReports(data.items || []);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setReportsError(err.message);
      } else {
        setReportsError("Could not load reports. Please try again.");
      }
    } finally {
      setReportsLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  // Prefill if scan_id param is provided
  useEffect(() => {
    if (scanIdParam) {
      setLinkedScanId(scanIdParam);
      scanApi
        .getScan(scanIdParam)
        .then((scan) => {
          if (scan.scan_type === "url") {
            setScamType("link");
            if (scan.extracted?.urls?.[0]?.raw) {
              setScammerUrl(scan.extracted.urls[0].raw);
              setContent(`Suspicious link reported: ${scan.extracted.urls[0].raw}`);
            }
          } else if (scan.scan_type === "qr") {
            setScamType("qr_upi");
            if (scan.extracted?.qr?.upi_payee) {
              setScammerUpi(scan.extracted.qr.upi_payee);
            }
            if (scan.extracted?.qr?.payload) {
              setContent(`Suspicious QR code payload: ${scan.extracted.qr.payload}`);
            }
          } else if (scan.scan_type === "message") {
            setScamType("sms");
            if (scan.message?.content) {
              setContent(scan.message.content);
            }
            if (scan.extracted?.phone?.length) {
              setScammerPhone(scan.extracted.phone[0]);
            }
            if (scan.extracted?.urls?.length && scan.extracted.urls[0]?.raw) {
              setScammerUrl(scan.extracted.urls[0].raw);
            }
          }
        })
        .catch(() => {
          // Ignore if scan cannot be fetched or not authorized
        });
    }
  }, [scanIdParam]);

  // Handle Form Submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormSuccessMessage(null);
    setFormErrorMessage(null);

    if (!content.trim() || content.trim().length < 5) {
      setFormErrorMessage("Please describe the incident (minimum 5 characters).");
      return;
    }

    try {
      setFormLoading(true);
      const payload = {
        scan_id: linkedScanId || null,
        scam_type: scamType,
        content: content.trim(),
        scammer_phone: scammerPhone.trim() || null,
        scammer_upi: scammerUpi.trim() || null,
        scammer_url: scammerUrl.trim() || null,
        amount_lost: amountLost ? parseFloat(amountLost) : null,
        incident_date: incidentDate || null,
      };

      const created = await reportApi.createReport(payload);
      setFormSuccessMessage(
        `Report submitted to GARUDA. Reference ID: ${created.id.slice(0, 8)}`
      );

      // Reset fields
      setContent("");
      setScammerPhone("");
      setScammerUpi("");
      setScammerUrl("");
      setAmountLost("");
      setLinkedScanId(null);

      // Refresh reports list
      await fetchReports();
    } catch (err) {
      if (err instanceof ApiClientError) {
        setFormErrorMessage(err.message);
      } else {
        setFormErrorMessage("Failed to submit report. Please check the fields and try again.");
      }
    } finally {
      setFormLoading(false);
    }
  };

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
        <div>
          <span className="font-mono text-xs uppercase text-purple-400 tracking-wider font-semibold">
            COMMUNITY DEFENSE &amp; INCIDENT MANAGEMENT
          </span>
          <h2 className="font-mono text-2xl sm:text-3xl font-bold text-white mt-1 flex items-center gap-2">
            <FileCheck2 className="w-6 h-6 text-purple-400" />
            Report Center
          </h2>
          <p className="text-xs sm:text-sm text-muted-foreground mt-1">
            Submit scam incidents to warn other GARUDA users and keep track of your reports.
          </p>
        </div>
      </div>

      {/* ALWAYS-VISIBLE HELP BOX */}
      <div className="rounded-xl border border-amber-500/40 bg-gradient-to-br from-amber-500/10 via-surface to-elevated/40 p-5 sm:p-6 space-y-4 shadow-lg">
        <div className="flex items-center gap-2 text-amber-400 font-mono text-sm font-bold uppercase tracking-wider">
          <ShieldAlert className="w-5 h-5 shrink-0" />
          <span>Victim Assistance &amp; Official Emergency Helplines</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 text-xs font-mono">
          {/* Action 1 */}
          <a
            href="tel:1930"
            className="p-3.5 rounded-lg border border-amber-500/30 bg-surface/80 hover:bg-amber-500/20 transition-colors flex flex-col justify-between group"
          >
            <div>
              <div className="flex items-center justify-between text-amber-300 font-bold mb-1">
                <span className="flex items-center gap-1.5">
                  <PhoneCall className="w-4 h-4 text-amber-400" />
                  Dial 1930
                </span>
                <ExternalLink className="w-3.5 h-3.5 opacity-60 group-hover:opacity-100" />
              </div>
              <p className="text-slate-300 font-semibold">Lost money? Call 1930 immediately</p>
            </div>
            <span className="text-[11px] text-muted-foreground mt-2 block">
              National Cyber Financial Fraud Helpline (Ministry of Home Affairs).
            </span>
          </a>

          {/* Action 2 */}
          <a
            href="https://cybercrime.gov.in"
            target="_blank"
            rel="noopener noreferrer"
            className="p-3.5 rounded-lg border border-border bg-surface/80 hover:bg-elevated transition-colors flex flex-col justify-between group"
          >
            <div>
              <div className="flex items-center justify-between text-accent-cyan font-bold mb-1">
                <span>cybercrime.gov.in</span>
                <ExternalLink className="w-3.5 h-3.5 opacity-60 group-hover:opacity-100" />
              </div>
              <p className="text-slate-300 font-semibold">File a complaint at cybercrime.gov.in</p>
            </div>
            <span className="text-[11px] text-muted-foreground mt-2 block">
              Official Indian National Cyber Crime Reporting Portal.
            </span>
          </a>

          {/* Action 3 */}
          <a
            href="https://sancharsaathi.gov.in"
            target="_blank"
            rel="noopener noreferrer"
            className="p-3.5 rounded-lg border border-border bg-surface/80 hover:bg-elevated transition-colors flex flex-col justify-between group"
          >
            <div>
              <div className="flex items-center justify-between text-purple-300 font-bold mb-1">
                <span>Sanchar Saathi</span>
                <ExternalLink className="w-3.5 h-3.5 opacity-60 group-hover:opacity-100" />
              </div>
              <p className="text-slate-300 font-semibold">Report fraud calls/SMS on Sanchar Saathi (Chakshu)</p>
            </div>
            <span className="text-[11px] text-muted-foreground mt-2 block">
              Department of Telecom portal to block fraudulent callers.
            </span>
          </a>

          {/* Action 4 */}
          <div className="p-3.5 rounded-lg border border-border bg-surface/80 flex flex-col justify-between">
            <div>
              <div className="text-emerald-400 font-bold mb-1 flex items-center gap-1.5">
                <Building2 className="w-4 h-4 text-emerald-400" />
                <span>Bank Helpline</span>
              </div>
              <p className="text-slate-300 font-semibold">Call your bank to block card/UPI</p>
            </div>
            <span className="text-[11px] text-muted-foreground mt-2 block">
              Immediately freeze compromised accounts, cards, and UPI IDs.
            </span>
          </div>
        </div>

        {/* Honest Wording Disclaimer */}
        <div className="p-3 rounded-lg border border-border/80 bg-background/60 text-xs font-mono text-slate-400 leading-relaxed">
          <strong className="text-slate-200">Notice: </strong>
          Submitting a report here logs it as <strong className="text-purple-300">&ldquo;Report submitted to GARUDA&rdquo;</strong> for community threat warning indicators and your personal records. GARUDA is an independent threat analysis system and <strong>does NOT file a police complaint or official government FIR on your behalf</strong>.
        </div>
      </div>

      {/* Main Grid: Report Form & My Reports */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left: Report Form */}
        <div className="lg:col-span-5 space-y-4">
          <Card className="border-border bg-surface p-5 sm:p-6 shadow-md">
            <CardHeader className="p-0 pb-4 border-b border-border">
              <div className="flex items-center justify-between">
                <CardTitle className="font-mono text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <PlusCircle className="w-4 h-4 text-purple-400" />
                  Submit Incident Report
                </CardTitle>
                {linkedScanId && (
                  <Badge variant="outline" className="border-purple-500/40 text-purple-300 bg-purple-500/10 text-[10px]">
                    Prefilled from Scan
                  </Badge>
                )}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Anonymously warn fellow users against this phone, UPI handle, or link.
              </p>
            </CardHeader>

            <form onSubmit={handleSubmit} className="space-y-4 pt-4 text-xs font-mono">
              {formSuccessMessage && (
                <div className="p-3 rounded-lg border border-emerald-500/40 bg-emerald-500/10 text-emerald-300 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
                  <span>{formSuccessMessage}</span>
                </div>
              )}

              {formErrorMessage && (
                <div className="p-3 rounded-lg border border-destructive/40 bg-destructive/10 text-destructive flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 shrink-0" />
                  <span>{formErrorMessage}</span>
                </div>
              )}

              {/* Scam Type */}
              <div>
                <label className="text-slate-300 block mb-1.5 font-semibold">
                  Scam Type <span className="text-destructive">*</span>
                </label>
                <select
                  value={scamType}
                  onChange={(e) => setScamType(e.target.value as ScamType)}
                  className="w-full rounded-md border border-border bg-elevated px-3 py-2 text-white focus:outline-none focus:border-primary text-xs"
                >
                  {SCAM_TYPE_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* What Happened / Content */}
              <div>
                <label className="text-slate-300 block mb-1.5 font-semibold">
                  Incident Details / Content <span className="text-destructive">*</span>
                </label>
                <textarea
                  rows={4}
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  placeholder="Paste the message, scam demand, or describe what happened..."
                  className="w-full rounded-md border border-border bg-[#070B14] p-3 text-slate-200 focus:outline-none focus:border-primary text-xs font-mono"
                  required
                />
              </div>

              {/* Scammer Contact Details */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-300 block mb-1.5 font-semibold flex items-center gap-1">
                    <Smartphone className="w-3.5 h-3.5 text-muted-foreground" />
                    Scammer Phone
                  </label>
                  <Input
                    type="text"
                    value={scammerPhone}
                    onChange={(e) => setScammerPhone(e.target.value)}
                    placeholder="e.g. +91 9876543210"
                    maxLength={30}
                    className="text-xs h-9 bg-elevated"
                  />
                </div>

                <div>
                  <label className="text-slate-300 block mb-1.5 font-semibold flex items-center gap-1">
                    <CreditCard className="w-3.5 h-3.5 text-muted-foreground" />
                    Scammer UPI ID
                  </label>
                  <Input
                    type="text"
                    value={scammerUpi}
                    onChange={(e) => setScammerUpi(e.target.value)}
                    placeholder="e.g. fraudster@okaxis"
                    maxLength={100}
                    className="text-xs h-9 bg-elevated"
                  />
                </div>
              </div>

              {/* Scammer URL */}
              <div>
                <label className="text-slate-300 block mb-1.5 font-semibold flex items-center gap-1">
                  <LinkIcon className="w-3.5 h-3.5 text-muted-foreground" />
                  Scammer Website / Link
                </label>
                <Input
                  type="text"
                  value={scammerUrl}
                  onChange={(e) => setScammerUrl(e.target.value)}
                  placeholder="e.g. https://sbi-fake-login.xyz"
                  maxLength={1000}
                  className="text-xs h-9 bg-elevated"
                />
              </div>

              {/* Amount Lost & Date */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-300 block mb-1.5 font-semibold">
                    Amount Lost (₹)
                  </label>
                  <Input
                    type="number"
                    min="0"
                    step="0.01"
                    value={amountLost}
                    onChange={(e) => setAmountLost(e.target.value)}
                    placeholder="0.00"
                    className="text-xs h-9 bg-elevated"
                  />
                </div>

                <div>
                  <label className="text-slate-300 block mb-1.5 font-semibold">
                    Incident Date
                  </label>
                  <Input
                    type="date"
                    value={incidentDate}
                    onChange={(e) => setIncidentDate(e.target.value)}
                    className="text-xs h-9 bg-elevated"
                  />
                </div>
              </div>

              {/* Submit Button */}
              <div className="pt-2">
                <Button
                  type="submit"
                  disabled={formLoading}
                  className="w-full gap-2 font-mono text-xs bg-purple-600 hover:bg-purple-700 text-white font-semibold h-10"
                >
                  <Send className="w-3.5 h-3.5" />
                  {formLoading ? "Submitting..." : "Submit Report to GARUDA"}
                </Button>
                <span className="text-[10px] text-muted-foreground text-center block mt-2">
                  Report submitted to GARUDA. This records evidence and alerts community scans.
                </span>
              </div>
            </form>
          </Card>
        </div>

        {/* Right: My Reports List */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between border-b border-border pb-3">
            <h3 className="font-mono text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Clock className="w-4 h-4 text-accent-cyan" />
              My Reports ({reports.length})
            </h3>
            <Button
              variant="outline"
              size="sm"
              onClick={fetchReports}
              disabled={reportsLoading}
              className="gap-1.5 font-mono text-xs h-7 px-2"
            >
              <RotateCcw className={`w-3 h-3 ${reportsLoading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          </div>

          {reportsLoading && (
            <LoadingState
              message="Loading your reports..."
              description="Retrieving reports submitted from your account."
            />
          )}

          {reportsError && !reportsLoading && (
            <ErrorState
              title="Could not load reports"
              message={reportsError}
              onRetry={fetchReports}
            />
          )}

          {!reportsLoading && !reportsError && reports.length === 0 && (
            <EmptyState
              title="No reports submitted yet"
              description="When you encounter scam messages, malicious URLs, or fraudulent UPI requests, submit them here to help safeguard the community."
            />
          )}

          {!reportsLoading && !reportsError && reports.length > 0 && (
            <div className="space-y-3">
              {reports.map((rep) => (
                <Card key={rep.id} className="p-4 bg-surface border-border hover:border-border/80 transition-all space-y-3">
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/60 pb-2.5">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="font-mono text-[11px] uppercase border-purple-500/40 text-purple-300 bg-purple-500/10">
                        {rep.scam_type.replace("_", " ")}
                      </Badge>
                      <span className="font-mono text-xs text-muted-foreground">
                        {new Date(rep.created_at).toLocaleDateString()}
                      </span>
                    </div>

                    {/* Status Badge: Honest wording */}
                    <Badge
                      variant="outline"
                      className={`font-mono text-[11px] ${
                        rep.status === "reviewed"
                          ? "border-emerald-500/40 text-emerald-300 bg-emerald-500/10"
                          : "border-purple-500/40 text-purple-300 bg-purple-500/10"
                      }`}
                    >
                      {rep.status === "reviewed"
                        ? "Reviewed by GARUDA"
                        : "Report submitted to GARUDA"}
                    </Badge>
                  </div>

                  {/* Content Preview */}
                  <p className="text-xs font-mono text-slate-200 whitespace-pre-wrap line-clamp-3 bg-[#070B14] p-2.5 rounded border border-border/80">
                    {rep.content}
                  </p>

                  {/* Attributes metadata */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] font-mono text-slate-400">
                    {rep.scammer_phone && (
                      <div className="flex items-center gap-1.5 truncate">
                        <Smartphone className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
                        <span>Phone: <strong className="text-slate-200">{rep.scammer_phone}</strong></span>
                      </div>
                    )}
                    {rep.scammer_upi && (
                      <div className="flex items-center gap-1.5 truncate">
                        <CreditCard className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
                        <span>UPI: <strong className="text-slate-200">{rep.scammer_upi}</strong></span>
                      </div>
                    )}
                    {rep.scammer_url && (
                      <div className="flex items-center gap-1.5 truncate sm:col-span-2">
                        <LinkIcon className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
                        <span className="truncate">URL: <strong className="text-slate-200">{rep.scammer_url}</strong></span>
                      </div>
                    )}
                    {rep.amount_lost !== null && rep.amount_lost !== undefined && (
                      <div className="flex items-center gap-1.5">
                        <span className="text-amber-400 font-semibold">
                          Amount Lost: ₹{Number(rep.amount_lost).toLocaleString("en-IN")}
                        </span>
                      </div>
                    )}
                    {rep.incident_date && (
                      <div className="flex items-center gap-1.5">
                        <span>Incident Date: {rep.incident_date}</span>
                      </div>
                    )}
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ReportsPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-muted-foreground font-mono text-xs">Loading Report Center...</div>}>
      <ReportCenterContent />
    </Suspense>
  );
}
