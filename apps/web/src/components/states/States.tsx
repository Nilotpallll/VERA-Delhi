"use client";

import React from "react";
import {
  Clock,
  AlertTriangle,
  FileQuestion,
  RefreshCw,
  CheckCircle2,
  AlertOctagon,
  Search,
  ShieldAlert,
} from "lucide-react";

// ── 1. LOADING STATE ─────────────────────────────────────────────────────────
export function LoadingState({ message = "Executing agentic investigation..." }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center p-12 rounded-xl border border-slate-800 bg-slate-900/40 text-center animate-pulse">
      <div className="relative mb-4">
        <div className="h-12 w-12 rounded-full border-2 border-indigo-500/20 border-t-indigo-500 animate-spin" />
        <Clock className="w-5 h-5 text-indigo-400 absolute inset-0 m-auto" />
      </div>
      <h3 className="text-sm font-semibold text-slate-200">{message}</h3>
      <p className="text-xs text-slate-500 mt-1 max-w-sm">
        Running multimodal analyzers, SEBI guideline retrieval, and deterministic risk scoring.
      </p>
    </div>
  );
}

// ── 2. EMPTY STATE ───────────────────────────────────────────────────────────
export function EmptyState({
  title = "No investigations found",
  description = "Get started by creating your first investment fraud investigation case.",
  actionLabel = "Create Investigation",
  onAction,
}: {
  title?: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center p-12 rounded-xl border border-dashed border-slate-800 bg-slate-900/20 text-center">
      <div className="h-12 w-12 rounded-full bg-slate-800/60 text-slate-400 flex items-center justify-center text-xl mb-4">
        <Search className="w-6 h-6 text-slate-400" />
      </div>
      <h3 className="text-base font-semibold text-slate-200">{title}</h3>
      <p className="text-xs text-slate-400 mt-1 max-w-sm mb-6">{description}</p>
      {onAction && (
        <button
          onClick={onAction}
          className="px-4 py-2 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/20 transition-all"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}

// ── 3. PARTIAL STATE (Rule 9 / Phase Gate: UI remains useful) ────────────────
export function PartialState({
  missingAnalyzers = ["Video Deepfake Analyzer (GPU timeout)", "APK Dynamic Sandbox (Offline)"],
  onContinue,
}: {
  missingAnalyzers?: string[];
  onContinue?: () => void;
}) {
  return (
    <div className="p-6 rounded-xl border border-amber-700/60 bg-amber-950/20 space-y-3">
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-amber-600/20 text-amber-400 border border-amber-500/30">
          <AlertTriangle className="w-5 h-5" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-amber-300">Investigation Status: PARTIAL</h3>
          <p className="text-xs text-amber-400/80">
            One or more specialized analyzers were unavailable. Failsafe zero-trust applied: missing signals do NOT indicate safety.
          </p>
        </div>
      </div>
      <div className="bg-slate-950/60 p-3 rounded-lg border border-amber-900/40 text-xs">
        <span className="text-slate-400 font-medium">Unresolved / Unavailable Analyzers:</span>
        <ul className="mt-1 space-y-1 text-amber-300/90 list-disc list-inside font-mono text-[11px]">
          {missingAnalyzers.map((a, i) => (
            <li key={i}>{a}</li>
          ))}
        </ul>
      </div>
      {onContinue && (
        <button
          onClick={onContinue}
          className="px-3.5 py-1.5 rounded-lg text-xs font-medium bg-amber-600/30 hover:bg-amber-600/50 text-amber-200 border border-amber-500/30 transition-all"
        >
          Inspect Partial Forensic Output
        </button>
      )}
    </div>
  );
}

// ── 4. FAILED STATE ──────────────────────────────────────────────────────────
export function ErrorState({
  title = "Investigation Execution Failed",
  message = "An unhandled exception occurred during agent tool orchestration.",
  onRetry,
}: {
  title?: string;
  message?: string;
  onRetry?: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center p-12 rounded-xl border border-rose-900/40 bg-rose-950/20 text-center">
      <div className="h-12 w-12 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 flex items-center justify-center mb-4">
        <AlertOctagon className="w-6 h-6" />
      </div>
      <h3 className="text-base font-semibold text-rose-300">{title}</h3>
      <p className="text-xs text-rose-400/80 mt-1 max-w-md">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-4 px-4 py-2 rounded-lg text-xs font-semibold bg-rose-600 hover:bg-rose-500 text-white shadow-lg shadow-rose-600/20 transition-all flex items-center gap-2"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Retry Investigation</span>
        </button>
      )}
    </div>
  );
}

// ── 5. RETRYING STATE ────────────────────────────────────────────────────────
export function RetryingState({
  attempt = 2,
  maxAttempts = 3,
  delaySeconds = 5,
}: {
  attempt?: number;
  maxAttempts?: number;
  delaySeconds?: number;
}) {
  return (
    <div className="flex flex-col items-center justify-center p-8 rounded-xl border border-violet-800/50 bg-violet-950/20 text-center space-y-3">
      <div className="h-10 w-10 rounded-full border-2 border-violet-500/30 border-t-violet-400 animate-spin flex items-center justify-center" />
      <h3 className="text-sm font-semibold text-violet-300">
        Retrying Investigation Job (Attempt {attempt} of {maxAttempts})
      </h3>
      <p className="text-xs text-violet-400/80 max-w-sm">
        Transient dependency slowdown encountered. Applying exponential backoff delay of {delaySeconds}s before re-evaluating tool outputs.
      </p>
    </div>
  );
}

// ── 6. COMPLETED STATE ───────────────────────────────────────────────────────
export function CompletedState({
  investigationId,
  riskLevel = "HIGH",
  riskScore = 75,
}: {
  investigationId: string;
  riskLevel?: string;
  riskScore?: number;
}) {
  return (
    <div className="p-4 rounded-xl border border-emerald-800/60 bg-emerald-950/20 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
          <CheckCircle2 className="w-5 h-5" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-emerald-300">Investigation Completed</h3>
          <p className="text-xs text-emerald-400/80 font-mono">Case ID: {investigationId}</p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-xs text-slate-400 font-mono">Assigned Score:</span>
        <span className="px-2.5 py-1 rounded bg-slate-900 border border-emerald-600 font-mono font-bold text-xs text-emerald-300">
          {riskScore}/100 ({riskLevel})
        </span>
      </div>
    </div>
  );
}

// ── 7. INSUFFICIENT EVIDENCE STATE (Rule 8/9 failsafe) ───────────────────────
export function InsufficientEvidenceState({
  onAddMoreEvidence,
}: {
  onAddMoreEvidence?: () => void;
}) {
  return (
    <div className="p-6 rounded-xl border border-slate-700 bg-slate-900/60 space-y-4">
      <div className="flex items-center gap-3">
        <div className="p-2.5 rounded-lg bg-slate-800 text-slate-400 border border-slate-700">
          <FileQuestion className="w-6 h-6" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-slate-200">
            Conclusion: INSUFFICIENT_EVIDENCE
          </h3>
          <p className="text-xs text-slate-400">
            Input artifacts did not contain sufficient verifiable claims, registered entities, or definitive fraud signals.
          </p>
        </div>
      </div>
      <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-400 space-y-1">
        <div className="font-semibold text-slate-300">Recommended Steps:</div>
        <div>1. Upload authentic chat exports, transaction receipts, or website screenshots.</div>
        <div>2. Provide claimed registration numbers or suspect banking / UPI identifiers.</div>
        <div>3. Failsafe rule: VERA will never invent a conclusion without verifiable citations.</div>
      </div>
      {onAddMoreEvidence && (
        <button
          onClick={onAddMoreEvidence}
          className="px-4 py-2 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition-all flex items-center gap-2"
        >
          <ShieldAlert className="w-4 h-4" />
          <span>Submit Additional Evidence Items</span>
        </button>
      )}
    </div>
  );
}
