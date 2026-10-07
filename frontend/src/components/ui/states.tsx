import React from "react";
import { Loader2, AlertTriangle, Inbox, RefreshCw } from "lucide-react";
import { Button } from "./button";

interface LoadingStateProps {
  message?: string;
  description?: string;
  className?: string;
}

export function LoadingState({
  message = "Analyzing telemetry...",
  description = "Consulting local threat intelligence and legitimacy heuristics.",
  className = "",
}: LoadingStateProps) {
  return (
    <div
      className={`flex flex-col items-center justify-center p-8 text-center rounded-lg border border-border bg-surface/50 min-h-[220px] ${className}`}
    >
      <div className="relative mb-4">
        <div className="w-12 h-12 rounded-full border-2 border-primary/20 border-t-primary animate-spin flex items-center justify-center" />
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-3 h-3 rounded-full bg-accent-cyan/80 animate-ping opacity-75" />
        </div>
      </div>
      <h4 className="text-sm font-semibold text-foreground tracking-wide font-mono">
        {message}
      </h4>
      {description && (
        <p className="text-xs text-muted-foreground mt-1 max-w-sm">
          {description}
        </p>
      )}
    </div>
  );
}

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

export function EmptyState({
  icon,
  title,
  description,
  actionLabel,
  onAction,
  className = "",
}: EmptyStateProps) {
  return (
    <div
      className={`flex flex-col items-center justify-center p-8 text-center rounded-lg border border-border/80 border-dashed bg-surface/30 min-h-[240px] ${className}`}
    >
      <div className="w-12 h-12 rounded-full bg-elevated flex items-center justify-center mb-3 text-muted-foreground border border-border">
        {icon || <Inbox className="w-6 h-6" />}
      </div>
      <h4 className="text-sm font-semibold text-foreground tracking-wide mb-1">
        {title}
      </h4>
      <p className="text-xs text-muted-foreground max-w-md leading-relaxed mb-4">
        {description}
      </p>
      {actionLabel && (
        <Button size="sm" variant="outline" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </div>
  );
}

interface ErrorStateProps {
  title?: string;
  message: string;
  details?: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({
  title = "Analysis Error",
  message,
  details,
  onRetry,
  className = "",
}: ErrorStateProps) {
  return (
    <div
      className={`flex flex-col items-center justify-center p-8 text-center rounded-lg border border-destructive/30 bg-destructive/5 min-h-[220px] ${className}`}
    >
      <div className="w-12 h-12 rounded-full bg-destructive/10 text-destructive flex items-center justify-center mb-3 border border-destructive/20">
        <AlertTriangle className="w-6 h-6" />
      </div>
      <h4 className="text-sm font-semibold text-foreground tracking-wide mb-1 font-mono">
        {title}
      </h4>
      <p className="text-xs text-muted-foreground max-w-md mb-2">
        {message}
      </p>
      {details && (
        <div className="text-[11px] font-mono bg-elevated/80 border border-border text-slate-300 p-2 rounded mb-4 max-w-md break-all">
          {details}
        </div>
      )}
      {onRetry && (
        <Button size="sm" variant="outline" onClick={onRetry} className="gap-1.5">
          <RefreshCw className="w-3.5 h-3.5" />
          Retry Request
        </Button>
      )}
    </div>
  );
}
