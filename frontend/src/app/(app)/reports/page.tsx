"use client";

import React, { useState } from "react";
import { showDevTools } from "@/lib/dev-tools";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { LoadingState, EmptyState, ErrorState } from "@/components/ui/states";
import {
  FileCheck2,
  ExternalLink,
  PlusCircle,
  Clock,
  ShieldAlert,
  ArrowRight,
} from "lucide-react";

// MOCK: Temporary mock reports matching ARCHITECTURE Section 6
const MOCK_REPORTS = [
  {
    id: "rep_01",
    reference_code: "GAR-2026-000001",
    title: "Fake Electricity Power Disconnection Coercion",
    category: "Utility Impersonation",
    status: "submitted",
    status_label: "Submitted to GARUDA",
    incident_date: "2026-10-06",
  },
  {
    id: "rep_02",
    reference_code: "GAR-2026-000002",
    title: "Fake ₹25 Lakh KBC Lottery Prize Advance Tax Fee",
    category: "Financial Fraud",
    status: "submitted",
    // MOCK: Status remains "Submitted to GARUDA" until an admin review feature is built
    status_label: "Submitted to GARUDA",
    incident_date: "2026-10-04",
  },
];

export default function ReportsPage() {
  const [reports, setReports] = useState(MOCK_REPORTS);
  const [state, setState] = useState<"ready" | "loading" | "empty" | "error">("ready");

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
        <div>
          <span className="font-mono text-xs uppercase text-purple-400 tracking-wider font-semibold">
            SECTOR 4: REPORTING &amp; EVIDENCE PACKAGING
          </span>
          <h2 className="font-mono text-2xl sm:text-3xl font-bold text-white mt-1 flex items-center gap-2">
            <FileCheck2 className="w-6 h-6 text-purple-400" />
            Incident Report Center
          </h2>
          <p className="text-xs sm:text-sm text-muted-foreground mt-1">
            Package scan evidence into structured GAR-2026-XXXXXX incident dossiers.
          </p>
        </div>

        {/* State Switcher — only visible when NEXT_PUBLIC_SHOW_DEV_TOOLS=true */}
        {showDevTools && (
          <div className="flex items-center gap-1.5 p-1 rounded-lg border border-border bg-elevated/40 text-[11px] font-mono self-start sm:self-auto">
            <span className="text-muted-foreground px-2">State:</span>
            <button
              onClick={() => setState("ready")}
              className={`px-2 py-0.5 rounded ${state === "ready" ? "bg-primary text-white" : "text-slate-400"}`}
            >
              Normal
            </button>
            <button
              onClick={() => setState("loading")}
              className={`px-2 py-0.5 rounded ${state === "loading" ? "bg-primary text-white" : "text-slate-400"}`}
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

      {/* Official External Resource Transparency Banner */}
      <div className="p-4 rounded-xl border border-amber-500/30 bg-amber-500/10 text-xs font-mono text-slate-300 space-y-2">
        <div className="flex items-center gap-2 font-bold text-amber-400">
          <ShieldAlert className="w-4 h-4 shrink-0" />
          <span>OFFICIAL LAW ENFORCEMENT DIRECTORY &amp; DISCLAIMER</span>
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

      {state === "loading" && (
        <LoadingState
          message="Loading Incident Dossiers..."
          description="Retrieving GARUDA incident reports from the reporting service."
        />
      )}

      {state === "error" && (
        <ErrorState
          title="Reporting Service Pending"
          message="FastAPI route GET /api/reports is pending Chunk 8 merge."
          details="ARCHITECTURE Section 6: Reports include reference sequence GAR-{year}-{seq:06d} and status history."
          onRetry={() => setState("ready")}
        />
      )}

      {state === "empty" && (
        <EmptyState
          title="No Incident Reports Logged"
          description="You have not filed any incident reports yet. When you analyze a threat, click 'Report This' to generate an evidence dossier."
          actionLabel="File Sample Report"
          onAction={() => setState("ready")}
        />
      )}

      {state === "ready" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-mono text-sm font-bold text-white uppercase tracking-wider">
              Your Incident Dossiers
            </h3>
            <Button size="sm" className="gap-1.5 font-mono text-xs">
              <PlusCircle className="w-3.5 h-3.5" />
              New Report
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {reports.map((rep) => (
              <Card key={rep.id} className="p-5 flex flex-col justify-between space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-sm font-bold text-accent-cyan">
                      {rep.reference_code}
                    </span>
                    <Badge variant="outline" className="border-purple-500/40 text-purple-300 bg-purple-500/10">
                      {rep.status_label}
                    </Badge>
                  </div>
                  <h4 className="font-semibold text-white text-sm">
                    {rep.title}
                  </h4>
                  <div className="text-xs text-muted-foreground font-mono space-y-0.5">
                    <p>Category: <span className="text-slate-300">{rep.category}</span></p>
                    <p>Incident Date: <span className="text-slate-300">{rep.incident_date}</span></p>
                  </div>
                </div>

                <div className="pt-3 border-t border-border/80 flex items-center justify-between text-xs font-mono">
                  <span className="text-muted-foreground">Status: Submitted to GARUDA</span>
                  <span className="text-primary hover:text-accent-cyan cursor-pointer inline-flex items-center gap-1 font-semibold">
                    View Dossier
                    <ArrowRight className="w-3 h-3" />
                  </span>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
