"use client";

import React, { useState } from "react";
import {
  FileText,
  Download,
  Printer,
  ExternalLink,
  CheckCircle2,
  ShieldAlert,
  Copy,
  Check,
  Scale,
  Clock,
  ShieldCheck,
  AlertTriangle,
  Fingerprint,
} from "lucide-react";
import { SuspiciousIndicator } from "@vera/contracts";

export interface ForensicReportData {
  investigation_id: string;
  generated_at: string;
  executive_summary: string;
  risk_score: number;
  risk_level: string;
  investigation_status: string;
  model_confidence: number;
  detected_entities: Array<Record<string, unknown>>;
  claims: Array<Record<string, unknown>>;
  evidence: Array<Record<string, unknown>>;
  verification_results: Array<Record<string, unknown>>;
  sebi_guidance_matches: Array<Record<string, unknown>>;
  suspicious_indicators: SuspiciousIndicator[] | Array<{ signal_type: string; weight: number; description: string }>;
  scam_lifecycle_stage: string;
  missing_evidence: string[];
  recommended_actions: string[];
  source_citations: Array<Record<string, unknown>> | string[];
  disclaimer: string;
  ruleset_version: string;
}

export function FinalReportView({
  report,
  onExportJson,
}: {
  report: ForensicReportData;
  onExportJson?: () => void;
}) {
  const [copied, setCopied] = useState(false);

  const handlePrint = () => {
    window.print();
  };

  const handleCopySummary = () => {
    navigator.clipboard.writeText(
      `VERA FORENSIC INVESTIGATION REPORT [${report.investigation_id}]\nGenerated: ${report.generated_at}\nRisk Rating: ${report.risk_level} (${report.risk_score}/100)\nModel Confidence: ${(report.model_confidence * 100).toFixed(0)}%\nExecutive Summary: ${report.executive_summary}`
    );
    setCopied(true);
    setTimeout(() => setCopied(false), 2200);
  };

  const isCritical = report.risk_level === "CRITICAL" || report.risk_score >= 70;
  const isHigh = report.risk_level === "HIGH" || (report.risk_score >= 45 && report.risk_score < 70);

  return (
    <div className="rounded-2xl border border-[#E7E3D8] bg-white p-6 sm:p-8 space-y-6 text-xs shadow-sm print:bg-white print:text-black print:border-none print:shadow-none animate-fade-in">
      {/* ── Action Bar & Header Title ──────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-stone-200 pb-5 print:hidden">
        <div className="flex items-center gap-3.5">
          <div className="p-3 rounded-2xl bg-orange-100 text-orange-600 border border-orange-200">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base sm:text-lg font-bold text-stone-900 tracking-tight">
                Forensic Case Dossier &amp; Evidentiary Report
              </h2>
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold bg-orange-50 text-orange-800 border border-orange-200">
                Rule 13 Certified
              </span>
            </div>
            <p className="text-stone-500 font-mono text-[11px] mt-0.5">
              Case Ref: <span className="text-orange-700 font-bold">{report.investigation_id}</span> • Timestamp: {new Date(report.generated_at).toLocaleString()}
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2 flex-wrap sm:flex-nowrap">
          <button
            onClick={handleCopySummary}
            className="px-3.5 py-2 rounded-xl bg-white hover:bg-stone-50 text-stone-700 border border-stone-300 font-medium transition-all duration-200 flex items-center gap-1.5 shadow-sm text-xs"
            title="Copy Report Summary"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-600" />
                <span className="text-emerald-700 font-bold">Copied!</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5 text-stone-500" />
                <span>Copy Summary</span>
              </>
            )}
          </button>
          <button
            onClick={handlePrint}
            className="px-3.5 py-2 rounded-xl bg-white hover:bg-stone-50 text-stone-700 border border-stone-300 font-medium flex items-center gap-1.5 transition-all duration-200 shadow-sm text-xs"
          >
            <Printer className="w-3.5 h-3.5 text-stone-500" />
            <span>Print Dossier</span>
          </button>
          {onExportJson && (
            <button
              onClick={onExportJson}
              className="px-4 py-2 rounded-xl bg-gradient-to-r from-orange-500 to-amber-600 hover:from-orange-600 hover:to-amber-700 text-white font-bold flex items-center gap-1.5 transition-all duration-200 shadow-sm text-xs"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export JSON</span>
            </button>
          )}
        </div>
      </div>

      {/* ── Key Metrics 4-Column Grid ───────────────────────────────────────── */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5">
        <div className={`p-4 rounded-xl border ${
          isCritical
            ? "bg-rose-50 border-rose-200"
            : isHigh
            ? "bg-amber-50 border-amber-200"
            : "bg-emerald-50 border-emerald-200"
        }`}>
          <span className="text-[10px] text-stone-500 uppercase font-mono font-bold tracking-wider block">Risk Severity Rating</span>
          <div className={`text-lg font-black font-mono mt-1 ${
            isCritical ? "text-rose-700" : isHigh ? "text-amber-700" : "text-emerald-700"
          }`}>
            {report.risk_level} <span className="text-sm font-semibold opacity-85">({report.risk_score}/100)</span>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-[#FAF7F2] border border-[#E7E3D8]">
          <span className="text-[10px] text-stone-500 uppercase font-mono font-bold tracking-wider block">Lifecycle Stage</span>
          <div className="text-base font-bold text-stone-900 capitalize mt-1 flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-orange-600" />
            <span>{report.scam_lifecycle_stage}</span>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-[#FAF7F2] border border-[#E7E3D8]">
          <span className="text-[10px] text-stone-500 uppercase font-mono font-bold tracking-wider block">Deterministic Confidence</span>
          <div className="text-base font-bold text-stone-900 font-mono mt-1 flex items-center gap-1.5">
            <Scale className="w-3.5 h-3.5 text-orange-600" />
            <span>{(report.model_confidence * 100).toFixed(0)}%</span>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-[#FAF7F2] border border-[#E7E3D8]">
          <span className="text-[10px] text-stone-500 uppercase font-mono font-bold tracking-wider block">Ruleset Engine</span>
          <div className="text-base font-bold text-stone-900 font-mono mt-1 flex items-center gap-1.5">
            <Fingerprint className="w-3.5 h-3.5 text-orange-600" />
            <span>{report.ruleset_version}</span>
          </div>
        </div>
      </div>

      {/* ── Executive Summary ───────────────────────────────────────────────── */}
      <div className="space-y-2">
        <h3 className="text-xs font-bold uppercase tracking-wider text-stone-700 flex items-center gap-2">
          <FileText className="w-4 h-4 text-orange-600" />
          <span>Executive Forensic Summary</span>
        </h3>
        <div className="p-4 sm:p-5 rounded-xl bg-[#FAF7F2] border-l-4 border-l-orange-500 border border-[#E7E3D8] text-stone-900 leading-relaxed text-xs sm:text-sm font-sans shadow-sm">
          {report.executive_summary}
        </div>
      </div>

      {/* ── Recommended Protection Actions ───────────────────────────────────── */}
      <div className="space-y-2">
        <h3 className="text-xs font-bold uppercase tracking-wider text-stone-700 flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-rose-600" />
          <span>Mandated Protection &amp; Mitigating Actions</span>
        </h3>
        <div className="p-4 sm:p-5 rounded-xl bg-rose-50 border border-rose-200 space-y-2.5 shadow-sm">
          {report.recommended_actions.map((act, i) => (
            <div key={i} className="flex items-start gap-2.5 text-rose-900 text-xs sm:text-sm font-semibold">
              <CheckCircle2 className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
              <span>{act}</span>
            </div>
          ))}
        </div>
      </div>

      {/* ── Risk Attribution Breakdown ───────────────────────────────────────── */}
      <div className="space-y-2.5">
        <h3 className="text-xs font-bold uppercase tracking-wider text-stone-700 flex items-center gap-2">
          <Scale className="w-4 h-4 text-orange-600" />
          <span>Deterministic Risk Attribution Breakdown (Rule 7 Invariant)</span>
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          {report.suspicious_indicators.map((sig, i) => (
            <div
              key={i}
              className="p-3.5 rounded-xl bg-white border border-stone-200 flex items-start justify-between gap-3 text-xs shadow-sm hover:border-orange-300 transition-colors"
            >
              <div className="space-y-1">
                <span className="font-mono text-orange-800 font-bold block">{sig.signal_type}</span>
                <p className="text-stone-600 text-[11px] leading-relaxed">{sig.description}</p>
              </div>
              <span className="px-2.5 py-1 rounded-lg bg-orange-100 font-mono font-bold text-orange-800 border border-orange-200 flex-shrink-0">
                +{sig.weight}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* ── Official Regulatory Citations & Source Links ─────────────────────── */}
      <div className="space-y-2">
        <h3 className="text-xs font-bold uppercase tracking-wider text-stone-700 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-orange-600" />
          <span>Official Regulatory Gazetted Citations &amp; Verification Evidence</span>
        </h3>
        <div className="p-4 rounded-xl bg-[#FAF7F2] border border-[#E7E3D8] space-y-2.5 text-xs">
          {report.source_citations.map((cite, i) => {
            const citeText = typeof cite === "string" ? cite : String((cite as any).source || (cite as any).url || JSON.stringify(cite));
            return (
              <div key={i} className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-stone-800 border-b border-stone-200 pb-2 last:border-b-0 last:pb-0">
                <span className="font-mono text-orange-800 text-[11px] truncate max-w-xl font-medium">{citeText}</span>
                <a
                  href={citeText.startsWith("http") ? citeText : `https://www.sebi.gov.in/search?q=${encodeURIComponent(citeText)}`}
                  target="_blank"
                  rel="noreferrer"
                  className="text-orange-600 hover:text-orange-700 font-bold flex items-center gap-1 font-mono text-[11px] self-start sm:self-auto hover:underline"
                >
                  <span>Verify at sebi.gov.in</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── Official Legal Disclaimer ────────────────────────────────────────── */}
      <div className="p-4 rounded-xl bg-stone-100 border border-stone-200 text-xs text-stone-600 leading-relaxed">
        {report.disclaimer}
      </div>
    </div>
  );
}

