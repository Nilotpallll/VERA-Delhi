"use client";

import React, { useState } from "react";
import {
  FileText,
  Download,
  Printer,
  ExternalLink,
  CheckCircle2,
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
      `VERA FRAUD REPORT [${report.investigation_id}]\nRisk: ${report.risk_level} (${report.risk_score}/100)\nSummary: ${report.executive_summary}`
    );
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 space-y-6 text-xs print:bg-white print:text-black">
      {/* Action Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4 print:hidden">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-indigo-400" />
            Evidence Report (Forensic Fraud Investigation)
          </h2>
          <span className="text-slate-400 font-mono text-[11px]">
            Case ID: {report.investigation_id} • Rule 13 Reproducible
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleCopySummary}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-medium transition-all"
          >
            {copied ? "Copied!" : "Copy Summary"}
          </button>
          <button
            onClick={handlePrint}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-medium flex items-center gap-1.5 transition-all"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>Print Report</span>
          </button>
          {onExportJson && (
            <button
              onClick={onExportJson}
              className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium flex items-center gap-1.5 transition-all"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export JSON</span>
            </button>
          )}
        </div>
      </div>

      {/* Header Metadata */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-4 rounded-lg bg-slate-950 border border-slate-800">
        <div>
          <span className="text-[10px] text-slate-500 uppercase font-mono">Risk Rating</span>
          <div className="text-base font-bold text-rose-400 font-mono mt-0.5">
            {report.risk_level} ({report.risk_score}/100)
          </div>
        </div>
        <div>
          <span className="text-[10px] text-slate-500 uppercase font-mono">Lifecycle Stage</span>
          <div className="text-base font-bold text-slate-200 capitalize mt-0.5">
            {report.scam_lifecycle_stage}
          </div>
        </div>
        <div>
          <span className="text-[10px] text-slate-500 uppercase font-mono">Model Confidence</span>
          <div className="text-base font-bold text-blue-300 font-mono mt-0.5">
            {(report.model_confidence * 100).toFixed(0)}%
          </div>
        </div>
        <div>
          <span className="text-[10px] text-slate-500 uppercase font-mono">Ruleset Version</span>
          <div className="text-base font-bold text-slate-300 font-mono mt-0.5">
            {report.ruleset_version}
          </div>
        </div>
      </div>

      {/* Executive Summary */}
      <div className="space-y-2">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Executive Summary</h3>
        <div className="p-4 rounded-lg bg-slate-950/80 border border-slate-800 text-slate-200 leading-relaxed text-xs">
          {report.executive_summary}
        </div>
      </div>

      {/* Recommended Actions */}
      <div className="space-y-2">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          Recommended Protection Actions
        </h3>
        <div className="p-4 rounded-lg bg-rose-950/20 border border-rose-900/40 space-y-2">
          {report.recommended_actions.map((act, i) => (
            <div key={i} className="flex items-start gap-2 text-rose-200">
              <CheckCircle2 className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
              <span>{act}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Risk Attribution Breakdown */}
      <div className="space-y-2">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          Mathematical Risk Signal Breakdown
        </h3>
        <div className="space-y-1.5">
          {report.suspicious_indicators.map((sig, i) => (
            <div
              key={i}
              className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-between text-xs"
            >
              <div className="space-y-0.5">
                <span className="font-mono text-amber-300 font-semibold">{sig.signal_type}</span>
                <p className="text-slate-400 text-[11px]">{sig.description}</p>
              </div>
              <span className="px-2 py-0.5 rounded bg-slate-900 font-mono font-bold text-amber-400 border border-amber-900">
                +{sig.weight}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Official SEBI Citations & Source Links */}
      <div className="space-y-2">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          Official SEBI Regulatory Citations &amp; Source Links
        </h3>
        <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-2 text-xs">
          {report.source_citations.map((cite, i) => {
            const citeText = typeof cite === "string" ? cite : String((cite as any).source || (cite as any).url || JSON.stringify(cite));
            return (
              <div key={i} className="flex items-center justify-between text-slate-300 border-b border-slate-800/60 pb-1.5 last:border-b-0">
                <span className="font-mono text-indigo-400">{citeText}</span>
                <a
                  href={citeText.startsWith("http") ? citeText : `https://www.sebi.gov.in/search?q=${encodeURIComponent(citeText)}`}
                  target="_blank"
                  rel="noreferrer"
                  className="text-slate-400 hover:text-indigo-300 flex items-center gap-1 font-mono text-[10px]"
                >
                  <span>Verify Source</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            );
          })}
        </div>
      </div>

      {/* Disclaimer */}
      <div className="p-3 rounded-lg bg-slate-950 border border-slate-800/80 text-[10px] text-slate-500 font-mono">
        {report.disclaimer}
      </div>
    </div>
  );
}
