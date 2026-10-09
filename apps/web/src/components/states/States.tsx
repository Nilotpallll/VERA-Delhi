"use client";

import React from "react";

export function LoadingState({ message = "Loading data..." }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center p-12 rounded-xl border border-slate-800 bg-slate-900/30 text-center">
      <div className="h-10 w-10 rounded-full border-2 border-indigo-500/20 border-t-indigo-500 animate-spin mb-4" />
      <h3 className="text-sm font-medium text-slate-300">{message}</h3>
      <p className="text-xs text-slate-500 mt-1">Connecting to VERA secure backend</p>
    </div>
  );
}

export function ErrorState({
  title = "Something went wrong",
  message,
  onRetry,
}: {
  title?: string;
  message?: string;
  onRetry?: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center p-12 rounded-xl border border-rose-900/30 bg-rose-950/10 text-center">
      <div className="h-10 w-10 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 flex items-center justify-center font-bold text-lg mb-4">
        ⚠️
      </div>
      <h3 className="text-base font-semibold text-rose-300">{title}</h3>
      {message && <p className="text-xs text-rose-400/80 mt-1 max-w-md">{message}</p>}
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-4 px-4 py-1.5 rounded-lg text-xs font-semibold bg-rose-500/20 text-rose-300 border border-rose-500/30 hover:bg-rose-500/30 transition-all"
        >
          Try Again
        </button>
      )}
    </div>
  );
}

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
        🔍
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
