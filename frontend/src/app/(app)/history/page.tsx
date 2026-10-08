"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { showDevTools } from "@/lib/dev-tools";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { LoadingState, EmptyState, ErrorState } from "@/components/ui/states";
import { scanApi, ApiClientError } from "@/lib/api-client";
import { ScanListItem } from "@/types/analysis";
import {
  History,
  Filter,
  Trash2,
  ExternalLink,
  Search,
  AlertTriangle,
  RotateCcw,
  Loader2,
  Calendar,
  Layers,
  ChevronRight,
  X,
} from "lucide-react";

export default function HistoryPage() {
  const router = useRouter();
  const [scans, setScans] = useState<ScanListItem[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [filterType, setFilterType] = useState<string>("all");
  const [filterLevel, setFilterLevel] = useState<string>("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Deletion modal state
  const [deleteTarget, setDeleteTarget] = useState<ScanListItem | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const fetchScans = useCallback(
    async (cursor: string | null = null, append = false) => {
      if (append) {
        setIsLoadingMore(true);
      } else {
        setIsLoading(true);
      }
      setError(null);

      try {
        const response = await scanApi.listScans({
          limit: 20,
          cursor,
          scan_type: filterType,
          risk_level: filterLevel,
        });

        if (append) {
          setScans((prev) => [...prev, ...response.items]);
        } else {
          setScans(response.items);
        }

        setNextCursor(response.next_cursor || null);
        setHasMore(response.has_more);
      } catch (err: unknown) {
        const msg =
          err instanceof ApiClientError
            ? err.message
            : err instanceof Error
            ? err.message
            : "Failed to load scan history.";
        setError(msg);
      } finally {
        setIsLoading(false);
        setIsLoadingMore(false);
      }
    },
    [filterType, filterLevel]
  );

  // Re-fetch on filter change
  useEffect(() => {
    fetchScans(null, false);
  }, [fetchScans]);

  const handleLoadMore = () => {
    if (nextCursor && !isLoadingMore) {
      fetchScans(nextCursor, true);
    }
  };

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;
    setIsDeleting(true);
    setDeleteError(null);

    try {
      await scanApi.deleteScan(String(deleteTarget.id));
      setScans((prev) => prev.filter((s) => s.id !== deleteTarget.id));
      setDeleteTarget(null);
    } catch (err: unknown) {
      const msg =
        err instanceof ApiClientError
          ? err.message
          : err instanceof Error
          ? err.message
          : "Failed to delete scan record.";
      setDeleteError(msg);
    } finally {
      setIsDeleting(false);
    }
  };

  // Helper for badge variant
  const getBadgeVariant = (level: string) => {
    switch (level?.toLowerCase()) {
      case "likely_safe":
      case "safe":
        return "safe";
      case "suspicious":
        return "suspicious";
      case "medium":
        return "medium";
      case "high":
        return "high";
      case "critical":
        return "critical";
      default:
        return "unverified";
    }
  };

  // Client-side search filtering on loaded preview text
  const displayedScans = scans.filter((scan) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    const preview = (scan.content_preview || scan.summary || "").toLowerCase();
    const cat = (scan.category?.label || "").toLowerCase();
    return preview.includes(term) || cat.includes(term) || String(scan.id).includes(term);
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

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => fetchScans(null, false)}
            disabled={isLoading}
            className="gap-1.5 font-mono text-xs"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Button asChild size="sm" className="font-mono text-xs">
            <Link href="/message-analyzer">New Scan</Link>
          </Button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="rounded-xl border border-border bg-surface p-4 space-y-3 shadow-md">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {/* Search Input */}
          <div className="relative">
            <Search className="w-4 h-4 text-muted-foreground absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search history by content or category..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3 py-2 rounded-lg border border-input bg-input-bg text-xs font-mono placeholder:text-muted-foreground focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary"
            />
          </div>

          {/* Type Filter */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-muted-foreground shrink-0">Vector:</span>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-input bg-input-bg text-xs font-mono text-foreground focus:outline-none focus:border-primary"
            >
              <option value="all">All Vectors</option>
              <option value="message">Message / SMS</option>
              <option value="url">URL / Domain</option>
              <option value="qr">QR / UPI</option>
              <option value="image">Image / OCR</option>
            </select>
          </div>

          {/* Risk Level Filter */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-muted-foreground shrink-0">Risk:</span>
            <select
              value={filterLevel}
              onChange={(e) => setFilterLevel(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-input bg-input-bg text-xs font-mono text-foreground focus:outline-none focus:border-primary"
            >
              <option value="all">All Risk Levels</option>
              <option value="likely_safe">Likely Safe</option>
              <option value="suspicious">Suspicious</option>
              <option value="medium">Medium Risk</option>
              <option value="high">High Risk</option>
              <option value="critical">Critical Risk</option>
              <option value="unable_to_verify">Unable to Verify</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      {isLoading ? (
        <LoadingState
          message="Loading Threat Records..."
          description="Querying your persistent scan ledger from the backend database."
        />
      ) : error ? (
        <ErrorState
          title="Failed to Load History"
          message={error}
          onRetry={() => fetchScans(null, false)}
        />
      ) : displayedScans.length === 0 ? (
        <EmptyState
          title="No Scans Recorded"
          description={
            searchTerm || filterType !== "all" || filterLevel !== "all"
              ? "No scan records match your active filters or search query."
              : "You have not performed or saved any scans yet. Analyze your first message to build your defense ledger."
          }
          actionLabel="Analyze Message"
          onAction={() => router.push("/message-analyzer")}
        />
      ) : (
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs font-mono text-muted-foreground px-1">
            <span>
              Showing {displayedScans.length} recorded scan{displayedScans.length === 1 ? "" : "s"}
            </span>
            <span>Sorted newest first</span>
          </div>

          {/* List of Scans */}
          <div className="space-y-3">
            {displayedScans.map((scan) => (
              <div
                key={String(scan.id)}
                className="group rounded-xl border border-border bg-surface p-4 sm:p-5 hover:border-primary/50 transition-all shadow-sm hover:shadow-md flex flex-col sm:flex-row sm:items-center justify-between gap-4"
              >
                {/* Left: Metadata & Preview */}
                <div className="space-y-2 flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
                    <Badge variant="default" className="text-[10px] uppercase font-bold tracking-wider">
                      {scan.scan_type}
                    </Badge>
                    <Badge variant={getBadgeVariant(scan.risk?.level)}>
                      {scan.risk?.label || scan.risk?.level || "Evaluated"}
                    </Badge>
                    <span className="text-[11px] text-muted-foreground">
                      Score: <strong className="text-white">{scan.risk?.score}</strong>/100
                    </span>
                    <span className="text-muted-foreground">•</span>
                    <span className="text-[11px] text-muted-foreground flex items-center gap-1">
                      <Calendar className="w-3 h-3 text-slate-400" />
                      {new Date(scan.created_at).toLocaleString("en-IN", {
                        dateStyle: "medium",
                        timeStyle: "short",
                      })}
                    </span>
                  </div>

                  {/* Message Content Preview */}
                  <p className="font-mono text-xs sm:text-sm text-slate-200 line-clamp-2 leading-relaxed bg-background/50 p-2.5 rounded border border-border/60">
                    {scan.content_preview || scan.summary || "No preview text available"}
                  </p>

                  <div className="flex items-center gap-2 text-[11px] font-mono text-muted-foreground">
                    <span className="text-slate-400">Category:</span>
                    <span className="text-white font-medium">
                      {scan.category?.label || "General Scam Evaluation"}
                    </span>
                  </div>
                </div>

                {/* Right: Actions */}
                <div className="flex items-center gap-2 sm:self-center shrink-0 pt-2 sm:pt-0 border-t sm:border-t-0 border-border/80">
                  <Button asChild variant="outline" size="sm" className="font-mono text-xs gap-1.5 h-9">
                    <Link href={`/scan/${scan.id}`}>
                      <span>Inspect Dossier</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </Link>
                  </Button>

                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => setDeleteTarget(scan)}
                    className="font-mono text-xs h-9 px-3 gap-1"
                    title="Delete Scan Record"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </Button>
                </div>
              </div>
            ))}
          </div>

          {/* Cursor Pagination: Load More */}
          {hasMore && (
            <div className="pt-4 text-center">
              <Button
                variant="outline"
                onClick={handleLoadMore}
                disabled={isLoadingMore}
                className="font-mono text-xs px-8 h-10 gap-2"
              >
                {isLoadingMore ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Loading More Scans...
                  </>
                ) : (
                  "Load More Records"
                )}
              </Button>
            </div>
          )}
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      {deleteTarget && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="delete-dialog-title"
        >
          <div className="relative w-full max-w-md rounded-2xl border border-destructive/40 bg-surface p-6 shadow-2xl space-y-4 font-mono">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2.5 text-destructive font-bold text-base">
                <AlertTriangle className="w-5 h-5 shrink-0" />
                <h3 id="delete-dialog-title">Confirm Scan Deletion</h3>
              </div>
              <button
                onClick={() => setDeleteTarget(null)}
                className="text-muted-foreground hover:text-white"
                aria-label="Close dialog"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-muted-foreground leading-relaxed">
              Are you sure you want to permanently delete this scan record?
              All associated telemetry, indicators, and analysis results will be removed immediately.
            </p>

            <div className="text-xs bg-background p-3 rounded border border-border text-slate-300 line-clamp-2">
              &ldquo;{deleteTarget.content_preview || deleteTarget.summary || String(deleteTarget.id)}&rdquo;
            </div>

            {deleteError && (
              <p className="text-xs text-destructive bg-destructive/10 p-2.5 rounded border border-destructive/20">
                {deleteError}
              </p>
            )}

            <div className="flex justify-end gap-2 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setDeleteTarget(null)}
                disabled={isDeleting}
                className="text-xs font-mono"
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                size="sm"
                onClick={handleConfirmDelete}
                disabled={isDeleting}
                className="text-xs font-mono gap-1.5"
              >
                {isDeleting ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    Deleting...
                  </>
                ) : (
                  <>
                    <Trash2 className="w-3.5 h-3.5" />
                    Delete Scan
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
