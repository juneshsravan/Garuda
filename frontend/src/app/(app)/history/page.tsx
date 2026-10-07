"use client";

import React, { useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { LoadingState, EmptyState, ErrorState } from "@/components/ui/states";
import { History, Filter, Trash2, Eye, Download, Search } from "lucide-react";

// MOCK: Temporary mock scan history matching GET /api/scans
const INITIAL_MOCK_SCANS = [
  {
    id: "scan_101",
    scan_type: "message",
    preview: "Dear SBI customer, your YONO account will be suspended today. Update PAN...",
    risk_level: "high" as const,
    risk_score: 91,
    risk_label: "91 High Risk",
    category: "Banking / KYC Suspension",
    created_at: "Today, 15:10",
  },
  {
    id: "scan_102",
    scan_type: "qr",
    preview: "Fake KBC ₹25 lakh lucky draw UPI QR with prefilled processing GST fee...",
    risk_level: "critical" as const,
    risk_score: 96,
    risk_label: "96 Critical Risk",
    category: "Lottery Advance Fee Scam",
    created_at: "Today, 11:30",
  },
  {
    id: "scan_103",
    scan_type: "url",
    preview: "http://sbi-yono-kyc.in-verify.xyz/login",
    risk_level: "high" as const,
    risk_score: 89,
    risk_label: "89 High Risk",
    category: "Phishing Domain",
    created_at: "Yesterday",
  },
  {
    id: "scan_104",
    scan_type: "message",
    preview: "Your OTP for transaction of Rs 1,450.00 at AMAZON INDIA is 482910. Bank NEVER calls...",
    risk_level: "safe" as const,
    risk_score: 8,
    risk_label: "08 Likely Safe",
    category: "Standard Transaction OTP",
    created_at: "Oct 05, 18:40",
  },
  {
    id: "scan_105",
    scan_type: "message",
    preview: "Check out the class photos: https://bit.ly/3abcXYZ",
    risk_level: "suspicious" as const,
    risk_score: 34,
    risk_label: "34 Suspicious",
    category: "Shortened Link Unverified",
    created_at: "Oct 04, 09:12",
  },
];

export default function HistoryPage() {
  const [scans, setScans] = useState(INITIAL_MOCK_SCANS);
  const [filterType, setFilterType] = useState<string>("all");
  const [filterLevel, setFilterLevel] = useState<string>("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [state, setState] = useState<"ready" | "loading" | "empty" | "error">("ready");

  const handleDelete = (id: string) => {
    // MOCK: In Chunk 4 this calls DELETE /api/scans/{id}
    setScans(scans.filter((s) => s.id !== id));
  };

  const filteredScans = scans.filter((scan) => {
    if (filterType !== "all" && scan.scan_type !== filterType) return false;
    if (filterLevel !== "all" && scan.risk_level !== filterLevel) return false;
    if (searchTerm && !scan.preview.toLowerCase().includes(searchTerm.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
        <div>
          <span className="font-mono text-xs uppercase text-primary tracking-wider font-semibold">
            SECTOR 3: PERSONAL SCAN HISTORY
          </span>
          <h2 className="font-mono text-2xl sm:text-3xl font-bold text-white mt-1 flex items-center gap-2">
            <History className="w-6 h-6 text-primary" />
            Threat History Ledger
          </h2>
          <p className="text-xs sm:text-sm text-muted-foreground mt-1">
            Browse, inspect, and delete previously evaluated payloads across all vectors.
          </p>
        </div>

        {/* State Switcher */}
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
      </div>

      {state === "loading" && (
        <LoadingState
          message="Loading Threat Records..."
          description="Querying user-scoped scans via Supabase PostgreSQL session pooler."
        />
      )}

      {state === "error" && (
        <ErrorState
          title="History Retrieval Error"
          message="FastAPI GET /api/scans failed or was not reachable."
          details="ARCHITECTURE Section 6 contract: GET /api/scans with cursor pagination and ownership check."
          onRetry={() => setState("ready")}
        />
      )}

      {state === "empty" && (
        <EmptyState
          title="No Historical Scans Found"
          description="Your scan history is empty. Scans saved with 'Save to history' enabled will appear here."
          actionLabel="Run First Analysis"
          onAction={() => setState("ready")}
        />
      )}

      {state === "ready" && (
        <div className="space-y-4">
          {/* Filter Bar */}
          <div className="rounded-xl border border-border bg-surface p-4 flex flex-col md:flex-row gap-3 items-center justify-between text-xs font-mono">
            {/* Search */}
            <div className="relative w-full md:w-72">
              <Search className="w-3.5 h-3.5 text-muted-foreground absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search history preview..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-input-bg border border-input rounded-md pl-9 pr-3 py-1.5 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary"
              />
            </div>

            {/* Filter Selects */}
            <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
              <div className="flex items-center gap-1.5 text-muted-foreground">
                <Filter className="w-3.5 h-3.5" />
                <span>Type:</span>
              </div>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="bg-elevated border border-border rounded px-2.5 py-1 text-slate-300 focus:outline-none focus:border-primary"
              >
                <option value="all">All Types</option>
                <option value="message">Messages</option>
                <option value="url">URLs</option>
                <option value="qr">QR &amp; UPI</option>
              </select>

              <div className="flex items-center gap-1.5 text-muted-foreground ml-2">
                <span>Risk:</span>
              </div>
              <select
                value={filterLevel}
                onChange={(e) => setFilterLevel(e.target.value)}
                className="bg-elevated border border-border rounded px-2.5 py-1 text-slate-300 focus:outline-none focus:border-primary"
              >
                <option value="all">All Levels</option>
                <option value="safe">Likely Safe</option>
                <option value="suspicious">Suspicious</option>
                <option value="high">High Risk</option>
                <option value="critical">Critical</option>
              </select>
            </div>
          </div>

          {/* Scans Table */}
          <div className="rounded-xl border border-border bg-surface overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-elevated/70 border-b border-border text-muted-foreground uppercase text-[11px]">
                  <tr>
                    <th className="p-3.5 sm:px-6">Vector / Preview</th>
                    <th className="p-3.5">Category</th>
                    <th className="p-3.5">Assessed Risk</th>
                    <th className="p-3.5">Logged</th>
                    <th className="p-3.5 sm:px-6 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                  {filteredScans.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="p-8 text-center text-muted-foreground">
                        No scans match the current filter criteria.
                      </td>
                    </tr>
                  ) : (
                    filteredScans.map((scan) => (
                      <tr key={scan.id} className="hover:bg-elevated/30 transition-colors">
                        <td className="p-3.5 sm:px-6 max-w-xs sm:max-w-md">
                          <span className="text-[10px] text-accent-cyan uppercase block">
                            [{scan.scan_type}]
                          </span>
                          <span className="text-white truncate block font-medium">
                            {scan.preview}
                          </span>
                        </td>
                        <td className="p-3.5 text-slate-300 whitespace-nowrap">
                          {scan.category}
                        </td>
                        <td className="p-3.5 whitespace-nowrap">
                          <Badge variant={scan.risk_level}>{scan.risk_label}</Badge>
                        </td>
                        <td className="p-3.5 text-muted-foreground whitespace-nowrap">
                          {scan.created_at}
                        </td>
                        <td className="p-3.5 sm:px-6 text-right whitespace-nowrap">
                          <button
                            onClick={() => handleDelete(scan.id)}
                            className="p-1.5 text-muted-foreground hover:text-destructive transition-colors rounded hover:bg-destructive/10"
                            title="Delete scan from ledger"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
