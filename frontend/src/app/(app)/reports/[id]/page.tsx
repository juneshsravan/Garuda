"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  FileCheck2,
  ArrowLeft,
  Copy,
  Check,
  ShieldAlert,
  ExternalLink,
  Clock,
  Terminal,
  FileText,
  Printer,
  Share2,
} from "lucide-react";

// MOCK: Detailed report database following docs/ARCHITECTURE.md Section 6
interface ReportDetailData {
  id: string;
  reference_code: string;
  title: string;
  category: string;
  status: string;
  status_label: string;
  incident_date: string;
  created_at: string;
  description: string;
  evidence: {
    type: string;
    text: string;
    scan_id?: string;
    offender_contact?: string;
  };
  timeline: {
    timestamp: string;
    status: string;
    note: string;
  }[];
}

const MOCK_REPORTS_DATABASE: Record<string, ReportDetailData> = {
  rep_01: {
    id: "rep_01",
    reference_code: "GAR-2026-000001",
    title: "Fake Electricity Power Disconnection Coercion",
    category: "Utility Impersonation",
    status: "submitted",
    status_label: "Submitted to GARUDA",
    incident_date: "2026-10-06",
    created_at: "2026-10-06 14:22 IST",
    description:
      "Received an unprompted WhatsApp text message threatening disconnection of electricity power supply by 9:30 PM tonight unless I called an individual mobile number immediately to settle pending arrears.",
    evidence: {
      type: "SMS / WhatsApp Message",
      text: "Electricity Power will be disconnected tonight 9:30 PM due to unpaid bill. Call electricity officer immediately: 9876543210 to update bill.",
      scan_id: "scan_102",
      offender_contact: "+91 9876543210",
    },
    timeline: [
      {
        timestamp: "2026-10-06 14:22 IST",
        status: "Submitted to GARUDA",
        note: "Incident dossier registered and telemetry archived in user ledger.",
      },
      {
        timestamp: "2026-10-06 14:20 IST",
        status: "Telemetry Analyzed",
        note: "Scan scan_102 scored 88 High Risk under Utility Impersonation category.",
      },
    ],
  },
  rep_02: {
    id: "rep_02",
    reference_code: "GAR-2026-000002",
    title: "Fake ₹25 Lakh KBC Lottery Prize Advance Tax Fee",
    category: "Financial Fraud",
    status: "submitted",
    status_label: "Submitted to GARUDA",
    incident_date: "2026-10-04",
    created_at: "2026-10-04 11:15 IST",
    description:
      "Received a WhatsApp audio file and image claiming a lottery prize from Kaun Banega Crorepati (KBC), asking for an advance processing fee of ₹12,500 via UPI.",
    evidence: {
      type: "Message / Audio Scam",
      text: "Congratulations from KBC! You won 25,00,000 cash. To claim, send registration charge of 12500 to SBI account.",
      scan_id: "scan_101",
      offender_contact: "+91 9988776655",
    },
    timeline: [
      {
        timestamp: "2026-10-04 11:15 IST",
        status: "Submitted to GARUDA",
        note: "Incident dossier registered in user account.",
      },
    ],
  },
};

function getReportData(id: string): ReportDetailData {
  if (MOCK_REPORTS_DATABASE[id]) {
    return MOCK_REPORTS_DATABASE[id];
  }
  return {
    ...MOCK_REPORTS_DATABASE.rep_01,
    id,
    reference_code: "GAR-2026-000001",
    title: "Incident Report " + id,
  };
}

function ReportDetailContent() {
  const params = useParams();
  const id = (params?.id as string) || "rep_01";
  const report = getReportData(id);
  const [copiedRef, setCopiedRef] = useState(false);

  const handleCopyRef = () => {
    navigator.clipboard.writeText(report.reference_code);
    setCopiedRef(true);
    setTimeout(() => setCopiedRef(false), 2000);
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-12">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-4">
        <div className="flex items-center gap-3">
          <Button asChild variant="outline" size="sm" className="gap-1.5 font-mono text-xs">
            <Link href="/reports">
              <ArrowLeft className="w-3.5 h-3.5" />
              All Reports
            </Link>
          </Button>
          <div className="h-4 w-px bg-border" />
          <span className="font-mono text-xs text-muted-foreground uppercase">
            REPORT DOSSIER: <span className="text-white font-semibold">{report.reference_code}</span>
          </span>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => window.print()}
            className="gap-1.5 font-mono text-xs"
          >
            <Printer className="w-3.5 h-3.5" />
            Print Dossier
          </Button>
        </div>
      </div>

      {/* Prominent Status Panel */}
      <Card className="border-purple-500/40 bg-surface p-6 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border/80 pb-4">
          <div>
            <span className="text-[10px] font-mono uppercase text-muted-foreground block">
              STATUS &amp; REFERENCE VERIFICATION
            </span>
            <div className="flex items-center gap-3 mt-1">
              <span className="font-mono text-2xl sm:text-3xl font-extrabold text-white tracking-wider">
                {report.reference_code}
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleCopyRef}
                className="h-7 text-xs font-mono text-muted-foreground hover:text-white"
              >
                {copiedRef ? (
                  <>
                    <Check className="w-3.5 h-3.5 mr-1 text-emerald-400" />
                    Copied
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5 mr-1" />
                    Copy
                  </>
                )}
              </Button>
            </div>
          </div>

          <div className="flex flex-col sm:items-end gap-1">
            <Badge variant="outline" className="border-purple-500/50 bg-purple-500/10 text-purple-300 font-mono text-xs px-3 py-1 self-start sm:self-auto">
              {report.status_label}
            </Badge>
            <span className="text-[11px] font-mono text-muted-foreground">
              Recorded: {report.created_at}
            </span>
          </div>
        </div>

        {/* Core Metadata Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-mono">
          <div className="p-3 rounded-lg border border-border/80 bg-elevated/40">
            <span className="text-muted-foreground block text-[10px] uppercase">Category</span>
            <span className="text-white font-semibold mt-0.5 block">{report.category}</span>
          </div>
          <div className="p-3 rounded-lg border border-border/80 bg-elevated/40">
            <span className="text-muted-foreground block text-[10px] uppercase">Incident Date</span>
            <span className="text-white font-semibold mt-0.5 block">{report.incident_date}</span>
          </div>
          <div className="p-3 rounded-lg border border-border/80 bg-elevated/40">
            <span className="text-muted-foreground block text-[10px] uppercase">Telemetry Link</span>
            {report.evidence.scan_id ? (
              <Link
                href={`/scan/${report.evidence.scan_id}`}
                className="text-accent-cyan hover:underline font-semibold mt-0.5 inline-flex items-center gap-1"
              >
                {report.evidence.scan_id}
                <ExternalLink className="w-3 h-3" />
              </Link>
            ) : (
              <span className="text-slate-400 mt-0.5 block">Direct Intake</span>
            )}
          </div>
        </div>
      </Card>

      {/* Incident Details Card */}
      <Card className="border-border bg-surface p-6 space-y-4">
        <div>
          <span className="text-[11px] font-mono text-muted-foreground uppercase block mb-1">
            INCIDENT NARRATIVE
          </span>
          <h3 className="text-lg font-bold text-white">{report.title}</h3>
        </div>

        <div className="p-4 rounded-lg border border-border/80 bg-background/50 text-xs sm:text-sm text-slate-200 leading-relaxed font-sans">
          {report.description}
        </div>
      </Card>

      {/* Attached Evidence & Telemetry Card */}
      <Card className="border-border bg-surface overflow-hidden">
        <CardHeader className="p-4 bg-elevated/40 border-b border-border flex flex-row items-center justify-between">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-purple-400" />
            <CardTitle className="font-mono text-xs uppercase text-slate-300">
              Attached Evidence ({report.evidence.type})
            </CardTitle>
          </div>
          {report.evidence.offender_contact && (
            <span className="font-mono text-[11px] text-muted-foreground">
              Offender: <span className="text-white">{report.evidence.offender_contact}</span>
            </span>
          )}
        </CardHeader>
        <CardContent className="p-4 bg-[#070B14]">
          <pre className="font-mono text-xs text-slate-200 whitespace-pre-wrap break-all leading-relaxed">
            {report.evidence.text}
          </pre>
        </CardContent>
      </Card>

      {/* Audit Timeline */}
      <Card className="border-border bg-surface p-6 space-y-3">
        <h4 className="font-mono text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <Clock className="w-4 h-4 text-accent-cyan" />
          Audit Trail &amp; Status History
        </h4>
        <div className="divide-y divide-border/60 text-xs font-mono">
          {report.timeline.map((entry, idx) => (
            <div key={idx} className="py-2.5 first:pt-0 last:pb-0 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <span className="text-purple-300 font-semibold">{entry.status}</span>
                <p className="text-slate-400 text-[11px] mt-0.5">{entry.note}</p>
              </div>
              <span className="text-muted-foreground text-[11px] shrink-0">{entry.timestamp}</span>
            </div>
          ))}
        </div>
      </Card>

      {/* Official Law Enforcement Directory Transparency Notice */}
      <div className="p-4 rounded-xl border border-amber-500/30 bg-amber-500/10 text-xs font-mono text-slate-300 space-y-2">
        <div className="flex items-center gap-2 font-bold text-amber-400">
          <ShieldAlert className="w-4 h-4 shrink-0" />
          <span>STATUTORY NOTICE &amp; LAW ENFORCEMENT REPORTING</span>
        </div>
        <p className="leading-relaxed">
          <strong>Important:</strong> GARUDA packages threat telemetry into structured dossiers for your records. GARUDA does not submit complaints to law enforcement on your behalf.
        </p>
        <div className="flex flex-wrap items-center gap-4 pt-1">
          <a
            href="https://cybercrime.gov.in"
            target="_blank"
            rel="noopener noreferrer"
            className="text-white hover:text-accent-cyan underline inline-flex items-center gap-1 font-semibold"
          >
            National Portal: cybercrime.gov.in
            <ExternalLink className="w-3 h-3" />
          </a>
          <a
            href="tel:1930"
            className="text-white hover:text-accent-cyan underline inline-flex items-center gap-1 font-semibold"
          >
            National Financial Fraud Helpline: 1930
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </div>
    </div>
  );
}

export default function ReportDetailPage() {
  return (
    <React.Suspense fallback={<div className="p-8 text-center text-muted-foreground font-mono text-xs">Loading report dossier...</div>}>
      <ReportDetailContent />
    </React.Suspense>
  );
}
