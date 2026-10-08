"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { LoadingState, EmptyState, ErrorState } from "@/components/ui/states";
import { AnalysisDossier } from "@/components/analysis/AnalysisDossier";
import { scanApi, ApiClientError } from "@/lib/api-client";
import { AnalysisResponse } from "@/types/analysis";
import {
  ArrowLeft,
  Trash2,
  Calendar,
  AlertTriangle,
  Loader2,
  X,
} from "lucide-react";

export default function ScanDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = (params?.id as string) || "";

  const [scan, setScan] = useState<AnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isNotFound, setIsNotFound] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Deletion modal state
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const fetchScan = useCallback(async () => {
    if (!id) return;
    setIsLoading(true);
    setIsNotFound(false);
    setError(null);

    try {
      const response = await scanApi.getScan(id);
      setScan(response);
    } catch (err: unknown) {
      if (err instanceof ApiClientError && (err.status === 404 || err.code === "NOT_FOUND")) {
        setIsNotFound(true);
      } else {
        const msg =
          err instanceof ApiClientError
            ? err.message
            : err instanceof Error
            ? err.message
            : "Failed to retrieve scan.";
        setError(msg);
      }
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchScan();
  }, [fetchScan]);

  const handleDelete = async () => {
    setIsDeleting(true);
    setDeleteError(null);

    try {
      await scanApi.deleteScan(id);
      router.push("/history");
    } catch (err: unknown) {
      const msg =
        err instanceof ApiClientError
          ? err.message
          : err instanceof Error
          ? err.message
          : "Failed to delete scan.";
      setDeleteError(msg);
      setIsDeleting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="py-12 max-w-5xl mx-auto">
        <LoadingState
          message="Loading Scan Dossier..."
          description="Retrieving persistent forensic records and threat indicators from storage."
        />
      </div>
    );
  }

  if (isNotFound) {
    return (
      <div className="py-12 max-w-5xl mx-auto space-y-4">
        <Button asChild variant="outline" size="sm" className="gap-1.5 font-mono text-xs">
          <Link href="/history">
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to History
          </Link>
        </Button>
        <EmptyState
          title="Scan Not Found"
          description={`The scan with identifier "${id}" does not exist, has been deleted, or belongs to another user account.`}
          actionLabel="Return to History"
          onAction={() => router.push("/history")}
        />
      </div>
    );
  }

  if (error || !scan) {
    return (
      <div className="py-12 max-w-5xl mx-auto space-y-4">
        <Button asChild variant="outline" size="sm" className="gap-1.5 font-mono text-xs">
          <Link href="/history">
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to History
          </Link>
        </Button>
        <ErrorState
          title="Unable to Load Scan Dossier"
          message={error || "Could not retrieve the requested scan record."}
          onRetry={fetchScan}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-12 max-w-5xl mx-auto">
      {/* Top Header & Navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-4">
        <div className="flex items-center gap-3">
          <Button asChild variant="outline" size="sm" className="gap-1.5 font-mono text-xs">
            <Link href="/history">
              <ArrowLeft className="w-3.5 h-3.5" />
              History
            </Link>
          </Button>
          <div className="h-4 w-px bg-border" />
          <span className="font-mono text-xs text-muted-foreground uppercase truncate max-w-xs sm:max-w-md">
            SCAN DOSSIER: <span className="text-white font-semibold">{id}</span>
          </span>
        </div>

        <div className="flex items-center gap-2">
          {scan.created_at && (
            <span className="text-xs font-mono text-muted-foreground flex items-center gap-1.5 mr-2">
              <Calendar className="w-3.5 h-3.5 text-slate-400" />
              {new Date(scan.created_at).toLocaleString("en-IN", {
                dateStyle: "medium",
                timeStyle: "short",
              })}
            </span>
          )}

          <Button
            variant="destructive"
            size="sm"
            onClick={() => setShowDeleteConfirm(true)}
            className="gap-1.5 font-mono text-xs h-8"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Delete Record
          </Button>
        </div>
      </div>

      {/* Render Real Dossier */}
      <AnalysisDossier analysis={scan} showHistoryLink={false} />

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="delete-scan-modal-title"
        >
          <div className="relative w-full max-w-md rounded-2xl border border-destructive/40 bg-surface p-6 shadow-2xl space-y-4 font-mono">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2.5 text-destructive font-bold text-base">
                <AlertTriangle className="w-5 h-5 shrink-0" />
                <h3 id="delete-scan-modal-title">Delete Scan Permanently?</h3>
              </div>
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="text-muted-foreground hover:text-white"
                aria-label="Close dialog"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-muted-foreground leading-relaxed">
              This action will permanently purge this scan dossier and all associated
              indicators from your defense records. This operation cannot be reversed.
            </p>

            {deleteError && (
              <p className="text-xs text-destructive bg-destructive/10 p-2.5 rounded border border-destructive/20">
                {deleteError}
              </p>
            )}

            <div className="flex justify-end gap-2 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowDeleteConfirm(false)}
                disabled={isDeleting}
                className="text-xs font-mono"
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                size="sm"
                onClick={handleDelete}
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
                    Delete Dossier
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
