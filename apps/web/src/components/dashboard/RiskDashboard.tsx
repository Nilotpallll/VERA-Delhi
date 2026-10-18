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
  const getRiskStyle = (level: string) => {
    switch (level) {
      case "CRITICAL":
        return {
          text: "text-rose-700",
          bg: "bg-rose-50/80",
          border: "border-rose-200",
          badgeBg: "bg-rose-100 text-rose-800 border-rose-300",
          bar: "bg-gradient-to-r from-rose-500 to-rose-600",
        };
      case "HIGH":
        return {
          text: "text-orange-700",
          bg: "bg-orange-50/80",
          border: "border-orange-200",
          badgeBg: "bg-orange-100 text-orange-800 border-orange-300",
          bar: "bg-gradient-to-r from-orange-500 to-orange-600",
        };
      case "MODERATE":
        return {
          text: "text-amber-700",
          bg: "bg-amber-50/80",
          border: "border-amber-200",
          badgeBg: "bg-amber-100 text-amber-800 border-amber-300",
          bar: "bg-gradient-to-r from-amber-500 to-amber-600",
        };
      default:
        return {
          text: "text-emerald-700",
          bg: "bg-emerald-50/80",
          border: "border-emerald-200",
          badgeBg: "bg-emerald-100 text-emerald-800 border-emerald-300",
          bar: "bg-gradient-to-r from-emerald-500 to-emerald-600",
        };
    }
  };

  const rs = getRiskStyle(metrics.riskLevel);

  return (
    <div className="space-y-4">
      {/* 4 Distinct Architectural Pillars Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* PILLAR 1: RISK SCORE (Deterministic Rule Engine) */}
        <div className={`p-5 rounded-2xl bg-white border ${rs.border} shadow-sm space-y-3 card-hover transition-all duration-200 relative overflow-hidden`}>
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-stone-600 flex items-center gap-1.5">
              <ShieldAlert className="w-4 h-4 text-rose-600" />
              1. Risk Level
            </span>
            <span className={`font-mono text-xs font-bold px-2.5 py-0.5 rounded-full border ${rs.badgeBg}`}>
              {metrics.riskLevel}
            </span>
          </div>

          <div className="mt-2">
            <div className={`text-3xl font-extrabold font-mono ${rs.text} animate-count-up`}>
              {metrics.riskScore.toFixed(0)} <span className="text-sm font-normal text-stone-600">/ 100</span>
            </div>
            <div className="w-full bg-stone-100 rounded-full h-2.5 mt-3 overflow-hidden border border-stone-200">
              <div
                className={`h-2.5 rounded-full transition-all duration-1000 ease-out ${rs.bar}`}
                style={{ width: `${Math.min(100, Math.max(0, metrics.riskScore))}%` }}
              />
            </div>
          </div>

          <p className="text-[11px] text-stone-600 leading-tight mt-2">
            Deterministic rule attribution. Prototype heuristic weights, NOT fraud probabilities.
          </p>
        </div>

        {/* PILLAR 2: MODEL CONFIDENCE (Feature Extraction Quality) */}
        <div className="p-5 rounded-2xl bg-white border border-[#E7E3D8] shadow-sm space-y-3 card-hover transition-all duration-200 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-stone-600 flex items-center gap-1.5">
              <Percent className="w-4 h-4 text-blue-600" />
              2. Confidence
            </span>
            <span className="font-mono text-xs font-bold px-2.5 py-0.5 rounded-full border border-blue-200 bg-blue-50 text-blue-800">
              FEATURE AI
            </span>
          </div>

          <div className="mt-2">
            <div className="text-3xl font-extrabold font-mono text-stone-900 animate-count-up">
              {(metrics.modelConfidence * 100).toFixed(0)}%
            </div>
            <div className="w-full bg-stone-100 rounded-full h-2.5 mt-3 overflow-hidden border border-stone-200">
              <div
                className="h-2.5 rounded-full bg-gradient-to-r from-blue-500 to-indigo-600 transition-all duration-1000 ease-out"
                style={{ width: `${Math.min(100, Math.max(0, metrics.modelConfidence * 100))}%` }}
              />
            </div>
          </div>

          <p className="text-[11px] text-stone-600 leading-tight mt-2">
            Confidence in claim and entity parsing from multimodal transcripts. Kept separate from risk.
          </p>
        </div>

        {/* PILLAR 3: VERIFICATION STATUS (Tri-State Regulatory Audits) */}
        <div className="p-5 rounded-2xl bg-white border border-[#E7E3D8] shadow-sm space-y-3 card-hover transition-all duration-200 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-stone-600 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-purple-600" />
              3. Verification
            </span>
            <span className="font-mono text-[10px] font-semibold text-stone-600 px-2 py-0.5 rounded-full bg-stone-100 border border-stone-200">TRI-STATE</span>
          </div>

          <div className="mt-2">
            <div className="text-base font-bold font-mono">
              {metrics.verificationStatus === "VERIFIED" ? (
                <span className="text-emerald-700 bg-emerald-50 px-2 py-1 rounded-lg border border-emerald-200">✓ VERIFIED</span>
              ) : metrics.verificationStatus === "NOT_VERIFIED" ? (
                <span className="text-rose-700 bg-rose-50 px-2 py-1 rounded-lg border border-rose-200">✗ NOT VERIFIED</span>
              ) : (
                <span className="text-amber-700 bg-amber-50 px-2 py-1 rounded-lg border border-amber-200">? UNAVAILABLE</span>
              )}
            </div>
            <div className="text-xs text-stone-600 mt-2 font-medium">
              {metrics.unverifiedEntitiesCount} entity/entities unverified in official registries
            </div>
          </div>

          <p className="text-[11px] text-stone-600 leading-tight mt-2">
            SEBI intermediary checks. Failed registry lookups never treated as safe.
          </p>
        </div>

        {/* PILLAR 4: INVESTIGATION COMPLETENESS */}
        <div className="p-5 rounded-2xl bg-white border border-[#E7E3D8] shadow-sm space-y-3 card-hover transition-all duration-200 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-stone-600 flex items-center gap-1.5">
              <ListTodo className="w-4 h-4 text-emerald-600" />
              4. Completeness
            </span>
            <span className="font-mono text-xs text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200 font-bold">
              {metrics.statusStage}
            </span>
          </div>

          <div className="mt-2">
            <div className="text-3xl font-extrabold font-mono text-stone-900 animate-count-up">
              {metrics.investigationCompleteness}%
            </div>
            <div className="w-full bg-stone-100 rounded-full h-2.5 mt-3 overflow-hidden border border-stone-200">
              <div
                className="h-2.5 rounded-full bg-gradient-to-r from-emerald-500 to-teal-600 transition-all duration-1000 ease-out"
                style={{ width: `${Math.min(100, Math.max(0, metrics.investigationCompleteness))}%` }}
              />
            </div>
          </div>

          <p className="text-[11px] text-stone-600 leading-tight mt-2">
            Tool coverage ratio. Incomplete investigations yield PARTIAL rather than false safety.
          </p>
        </div>
      </div>

      {/* Notice Banner */}
      <div className="p-3.5 rounded-xl bg-[#FAF7F2] border border-[#E7E3D8] text-xs text-stone-700 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Scale className="w-4 h-4 text-orange-600 flex-shrink-0" />
          <span>
            <strong className="text-stone-900">Zero-Trust Architecture:</strong> Risk, Confidence, Verification, and Completeness operate under strict independent boundaries.
          </span>
        </div>
        <span className="font-mono text-[10px] text-stone-600 self-start sm:self-auto px-2 py-0.5 rounded bg-white border border-stone-200">Engine: rules.v2.0</span>
      </div>
    </div>
  );
}
