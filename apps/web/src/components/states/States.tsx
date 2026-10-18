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
    <div className="flex flex-col items-center justify-center p-12 rounded-2xl border border-[#E7E3D8] bg-white text-center shadow-sm">
      <div className="relative mb-5">
        <div className="h-14 w-14 rounded-full border-2 border-orange-200 border-t-orange-500 animate-spin" />
        <div className="absolute inset-0 h-14 w-14 rounded-full border-2 border-transparent border-b-amber-400 animate-spin" style={{ animationDuration: '2s', animationDirection: 'reverse' }} />
        <Clock className="w-5 h-5 text-orange-600 absolute inset-0 m-auto" />
      </div>
      <h3 className="text-base font-bold text-stone-900">{message}</h3>
      <p className="text-xs text-stone-600 mt-1.5 max-w-sm leading-relaxed">
        Running multimodal analyzers, SEBI guideline retrieval, and deterministic risk scoring.
      </p>
      <div className="flex items-center gap-1.5 mt-4">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="w-2 h-2 rounded-full bg-orange-500/60"
            style={{
              animation: 'float 1.2s ease-in-out infinite',
              animationDelay: `${i * 0.2}s`,
            }}
          />
        ))}
      </div>
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
    <div className="flex flex-col items-center justify-center p-12 rounded-2xl border border-dashed border-stone-300 bg-white text-center shadow-sm animate-fade-in">
      <div className="h-14 w-14 rounded-2xl bg-orange-50 text-orange-600 border border-orange-200 flex items-center justify-center mb-5">
        <Search className="w-6 h-6" />
      </div>
      <h3 className="text-base font-bold text-stone-900">{title}</h3>
      <p className="text-xs text-stone-600 mt-1.5 max-w-sm mb-6 leading-relaxed">{description}</p>
      {onAction && (
        <button
          onClick={onAction}
          className="px-5 py-2.5 rounded-xl text-xs font-bold bg-gradient-to-r from-orange-500 to-amber-600 hover:from-orange-600 hover:to-amber-700 text-white shadow-sm transition-all duration-200"
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
    <div className="p-6 rounded-2xl border border-amber-200 bg-amber-50/90 space-y-4 shadow-sm animate-fade-in">
      <div className="flex items-center gap-3">
        <div className="p-2.5 rounded-xl bg-amber-100 text-amber-700 border border-amber-200">
          <AlertTriangle className="w-5 h-5" />
        </div>
        <div>
          <h3 className="text-sm font-bold text-amber-900">Investigation Status: PARTIAL</h3>
          <p className="text-xs text-amber-800 mt-0.5">
            One or more specialized analyzers were unavailable. Failsafe zero-trust applied: missing signals do NOT indicate safety.
          </p>
        </div>
      </div>
      <div className="bg-white p-4 rounded-xl border border-amber-200 text-xs">
        <span className="text-stone-800 font-bold">Unresolved / Unavailable Analyzers:</span>
        <ul className="mt-1.5 space-y-1 text-amber-900 list-disc list-inside font-mono text-[11px]">
          {missingAnalyzers.map((a, i) => (
            <li key={i} className="animate-fade-in" style={{ animationDelay: `${i * 0.1}s` }}>{a}</li>
          ))}
        </ul>
      </div>
      {onContinue && (
        <button
          onClick={onContinue}
          className="px-4 py-2.5 rounded-xl text-xs font-bold bg-amber-200 hover:bg-amber-300 text-amber-900 border border-amber-300 transition-all duration-200"
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
    <div className="flex flex-col items-center justify-center p-12 rounded-2xl border border-rose-200 bg-rose-50/80 text-center shadow-sm animate-fade-in">
      <div className="h-14 w-14 rounded-2xl bg-rose-100 text-rose-700 border border-rose-200 flex items-center justify-center mb-5">
        <AlertOctagon className="w-7 h-7" />
      </div>
      <h3 className="text-base font-bold text-rose-900">{title}</h3>
      <p className="text-xs text-rose-800 mt-1.5 max-w-md leading-relaxed">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-5 px-5 py-2.5 rounded-xl text-xs font-bold bg-gradient-to-r from-rose-600 to-rose-500 hover:from-rose-500 hover:to-rose-400 text-white shadow-sm transition-all duration-200 flex items-center gap-2"
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
    <div className="flex flex-col items-center justify-center p-10 rounded-2xl border border-amber-200 bg-amber-50/80 text-center space-y-4 shadow-sm animate-fade-in">
      <div className="relative">
        <div className="h-12 w-12 rounded-full border-2 border-amber-200 border-t-amber-600 animate-spin" />
      </div>
      <h3 className="text-sm font-bold text-amber-900">
        Retrying Investigation Job (Attempt {attempt} of {maxAttempts})
      </h3>
      <p className="text-xs text-amber-800 max-w-sm leading-relaxed">
        Transient dependency slowdown encountered. Applying exponential backoff delay of {delaySeconds}s before re-evaluating tool outputs.
      </p>
      <div className="w-48 h-1.5 bg-amber-200 rounded-full overflow-hidden">
        <div className="h-1.5 bg-gradient-to-r from-amber-500 to-orange-500 rounded-full" style={{ width: `${(attempt / maxAttempts) * 100}%`, transition: 'width 0.5s ease-out' }} />
      </div>
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
    <div className="p-5 rounded-2xl border border-emerald-200 bg-emerald-50/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-sm animate-fade-in">
      <div className="flex items-center gap-3">
        <div className="p-2.5 rounded-xl bg-emerald-100 text-emerald-700 border border-emerald-200">
          <CheckCircle2 className="w-5 h-5" />
        </div>
        <div>
          <h3 className="text-sm font-bold text-emerald-900">Investigation Completed</h3>
          <p className="text-xs text-emerald-800 font-mono mt-0.5">Case ID: {investigationId}</p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-xs text-stone-600 font-mono">Assigned Score:</span>
        <span className="px-3 py-1.5 rounded-xl bg-white border border-emerald-300 font-mono font-bold text-xs text-emerald-800 shadow-sm">
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
    <div className="p-6 rounded-2xl border border-[#E7E3D8] bg-white space-y-4 shadow-sm animate-fade-in">
      <div className="flex items-center gap-3">
        <div className="p-2.5 rounded-xl bg-stone-100 text-stone-600 border border-stone-200">
          <FileQuestion className="w-6 h-6" />
        </div>
        <div>
          <h3 className="text-base font-bold text-stone-900">
            Conclusion: INSUFFICIENT_EVIDENCE
          </h3>
          <p className="text-xs text-stone-600 mt-0.5">
            Input artifacts did not contain sufficient verifiable claims, registered entities, or definitive fraud signals.
          </p>
        </div>
      </div>
      <div className="p-4 rounded-xl bg-[#FAF7F2] border border-stone-200 text-xs text-stone-700 space-y-1.5">
        <div className="font-bold text-stone-900">Recommended Steps:</div>
        <div>1. Upload authentic chat exports, transaction receipts, or website screenshots.</div>
        <div>2. Provide claimed registration numbers or suspect banking / UPI identifiers.</div>
        <div>3. Failsafe rule: VERA will never invent a conclusion without verifiable citations.</div>
      </div>
      {onAddMoreEvidence && (
        <button
          onClick={onAddMoreEvidence}
          className="px-5 py-2.5 rounded-xl text-xs font-bold bg-gradient-to-r from-orange-500 to-amber-600 hover:from-orange-600 hover:to-amber-700 text-white transition-all duration-200 flex items-center gap-2 shadow-sm"
        >
          <ShieldAlert className="w-4 h-4" />
          <span>Submit Additional Evidence Items</span>
        </button>
      )}
    </div>
  );
}
