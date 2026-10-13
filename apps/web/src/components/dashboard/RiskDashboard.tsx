"use client";

import React from "react";
import {
  ShieldAlert,
  Percent,
  CheckCircle2,
  ListTodo,
  AlertTriangle,
  Info,
  Scale,
} from "lucide-react";

export interface RiskMetrics {
  riskScore: number;                // 0 - 100
  riskLevel: "LOW" | "MODERATE" | "HIGH" | "CRITICAL";
  modelConfidence: number;          // 0.0 - 1.0 (e.g. 0.88 = 88%)
  verificationStatus: "VERIFIED" | "NOT_VERIFIED" | "UNAVAILABLE" | "MIXED";
  investigationCompleteness: number;// 0 - 100%
  statusStage: "COMPLETED" | "PARTIAL" | "INSUFFICIENT_EVIDENCE" | "IN_PROGRESS";
  totalIndicators: number;
  unverifiedEntitiesCount: number;
}

export function RiskDashboard({
  metrics = {
    riskScore: 78,
    riskLevel: "CRITICAL",
    modelConfidence: 0.92,
    verificationStatus: "NOT_VERIFIED",
    investigationCompleteness: 85,
    statusStage: "COMPLETED",
    totalIndicators: 5,
    unverifiedEntitiesCount: 3,
  },
}: {
  metrics?: RiskMetrics;
}) {
  const getRiskColor = (level: string) => {
    switch (level) {
      case "CRITICAL":
        return { text: "text-red-400", bg: "bg-red-950/40", border: "border-red-700/60", bar: "bg-red-500" };
      case "HIGH":
        return { text: "text-orange-400", bg: "bg-orange-950/40", border: "border-orange-700/60", bar: "bg-orange-500" };
      case "MODERATE":
        return { text: "text-amber-400", bg: "bg-amber-950/40", border: "border-amber-700/60", bar: "bg-amber-500" };
      default:
        return { text: "text-emerald-400", bg: "bg-emerald-950/40", border: "border-emerald-700/60", bar: "bg-emerald-500" };
    }
  };

  const rc = getRiskColor(metrics.riskLevel);

  return (
    <div className="space-y-4">
      {/* 4 Distinct Architectural Pillars Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* PILLAR 1: RISK SCORE (Deterministic Rule Engine) */}
        <div className={`p-4 rounded-xl border ${rc.bg} ${rc.border} space-y-3`}>
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <ShieldAlert className="w-4 h-4 text-rose-400" />
              1. Risk Level
            </span>
            <span className={`font-mono text-xs font-bold px-2 py-0.5 rounded border ${rc.border} ${rc.text}`}>
              {metrics.riskLevel}
            </span>
          </div>

          <div>
            <div className={`text-2xl font-extrabold font-mono ${rc.text}`}>
              {metrics.riskScore.toFixed(0)} <span className="text-xs text-slate-400">/ 100</span>
            </div>
            <div className="w-full bg-slate-900 rounded-full h-2 mt-2 overflow-hidden">
              <div
                className={`h-2 rounded-full transition-all duration-700 ${rc.bar}`}
                style={{ width: `${Math.min(100, Math.max(0, metrics.riskScore))}%` }}
              />
            </div>
          </div>

          <p className="text-[10px] text-slate-400 leading-tight">
            Deterministic rule attribution. Prototype heuristic weights, NOT fraud probabilities.
          </p>
        </div>

        {/* PILLAR 2: MODEL CONFIDENCE (Feature Extraction Quality) */}
        <div className="p-4 rounded-xl border border-blue-900/40 bg-blue-950/20 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Percent className="w-4 h-4 text-blue-400" />
              2. Confidence
            </span>
            <span className="font-mono text-xs font-bold px-2 py-0.5 rounded border border-blue-700/60 text-blue-300">
              FEATURE AI
            </span>
          </div>

          <div>
            <div className="text-2xl font-extrabold font-mono text-blue-300">
              {(metrics.modelConfidence * 100).toFixed(0)}%
            </div>
            <div className="w-full bg-slate-900 rounded-full h-2 mt-2 overflow-hidden">
              <div
                className="h-2 rounded-full bg-blue-500 transition-all duration-700"
                style={{ width: `${Math.min(100, Math.max(0, metrics.modelConfidence * 100))}%` }}
              />
            </div>
          </div>

          <p className="text-[10px] text-slate-400 leading-tight">
            Confidence in claim and entity parsing from multimodal transcripts. Kept separate from risk.
          </p>
        </div>

        {/* PILLAR 3: VERIFICATION STATUS (Tri-State Regulatory Audits) */}
        <div className="p-4 rounded-xl border border-purple-900/40 bg-purple-950/20 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-purple-400" />
              3. Verification
            </span>
            <span className="font-mono text-[10px] text-slate-400">TRI-STATE</span>
          </div>

          <div>
            <div className="text-base font-bold font-mono">
              {metrics.verificationStatus === "VERIFIED" ? (
                <span className="text-emerald-400">✓ VERIFIED</span>
              ) : metrics.verificationStatus === "NOT_VERIFIED" ? (
                <span className="text-rose-400">✗ NOT VERIFIED</span>
              ) : (
                <span className="text-amber-400">? UNAVAILABLE</span>
              )}
            </div>
            <div className="text-xs text-slate-300 mt-1">
              {metrics.unverifiedEntitiesCount} entity/entities unverified in official registries
            </div>
          </div>

          <p className="text-[10px] text-slate-400 leading-tight">
            SEBI intermediary checks. Failed registry lookups never treated as safe.
          </p>
        </div>

        {/* PILLAR 4: INVESTIGATION COMPLETENESS (Missing Evidence / Analyzer Availability) */}
        <div className="p-4 rounded-xl border border-emerald-900/40 bg-emerald-950/20 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <ListTodo className="w-4 h-4 text-emerald-400" />
              4. Completeness
            </span>
            <span className="font-mono text-xs text-emerald-400 font-semibold">
              {metrics.statusStage}
            </span>
          </div>

          <div>
            <div className="text-2xl font-extrabold font-mono text-emerald-300">
              {metrics.investigationCompleteness}%
            </div>
            <div className="w-full bg-slate-900 rounded-full h-2 mt-2 overflow-hidden">
              <div
                className="h-2 rounded-full bg-emerald-500 transition-all duration-700"
                style={{ width: `${Math.min(100, Math.max(0, metrics.investigationCompleteness))}%` }}
              />
            </div>
          </div>

          <p className="text-[10px] text-slate-400 leading-tight">
            Tool coverage ratio. Incomplete investigations yield PARTIAL rather than false safety.
          </p>
        </div>
      </div>

      {/* Notice Banner */}
      <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Scale className="w-4 h-4 text-indigo-400 flex-shrink-0" />
          <span>
            <strong>Architectural Separation:</strong> Risk, Confidence, Verification, and Completeness operate under strict zero-trust boundaries (Rules 6, 8, 9).
          </span>
        </div>
        <span className="font-mono text-[10px] text-slate-500 hidden sm:inline">Engine: rules.v2.0</span>
      </div>
    </div>
  );
}
