"use client";

import React from "react";
import { Clock, Play, Search, Link2, CheckCircle2, ShieldAlert, Cpu } from "lucide-react";

export interface TimelineEvent {
  id: string;
  timestamp: string;
  stage: "INGESTION" | "TOOL_EXECUTION" | "CORRELATION" | "RISK_ENGINE" | "REPORT_GENERATION";
  title: string;
  description: string;
  toolName?: string;
  actor: "User" | "VERA Investigator Agent" | "Deterministic Risk Engine" | "Forensic Reporter";
  status: "SUCCESS" | "WARNING" | "FAILED";
}

const SAMPLE_TIMELINE: TimelineEvent[] = [
  {
    id: "evt_1",
    timestamp: "10:14:02.120",
    stage: "INGESTION",
    title: "Case Created & Manifest Initialized",
    description: "Received investigation payload. Generated SHA-256 manifest hash and anchored Rule 13 audit trail.",
    actor: "User",
    status: "SUCCESS",
  },
  {
    id: "evt_2",
    timestamp: "10:14:03.450",
    stage: "TOOL_EXECUTION",
    title: "Tool: analyze_message",
    toolName: "analyze_message",
    description: "Extracted claims: 'Guaranteed 40% returns'. Flagged guaranteed_return signal (+15 weight).",
    actor: "VERA Investigator Agent",
    status: "SUCCESS",
  },
  {
    id: "evt_3",
    timestamp: "10:14:04.210",
    stage: "TOOL_EXECUTION",
    title: "Tool: verify_sebi_entity",
    toolName: "verify_sebi_entity",
    description: "Queried SEBI active registry for claimed RA 'Rajesh Kumar' (INZ0000000). Returned NOT_VERIFIED.",
    actor: "VERA Investigator Agent",
    status: "WARNING",
  },
  {
    id: "evt_4",
    timestamp: "10:14:05.105",
    stage: "TOOL_EXECUTION",
    title: "Tool: analyze_url",
    toolName: "analyze_url",
    description: "Scanned 'apex-capital-fx.in'. Domain age: 4 days. Detected domain mismatch with registered broker entity.",
    actor: "VERA Investigator Agent",
    status: "WARNING",
  },
  {
    id: "evt_5",
    timestamp: "10:14:06.020",
    stage: "CORRELATION",
    title: "Evidence Correlated Across Nodes",
    description: "Correlated WhatsApp admin phone, third-party UPI mule handle, and unregistered domain into unified entity graph.",
    actor: "VERA Investigator Agent",
    status: "SUCCESS",
  },
  {
    id: "evt_6",
    timestamp: "10:14:06.840",
    stage: "RISK_ENGINE",
    title: "Deterministic Risk Engine Evaluation",
    description: "Aggregated 5 signals: guaranteed_return (+15), unverified_entity (+25), domain_mismatch (+20), payment_mismatch (+20), known_indicator (+25). Normalized & capped at 100 -> CRITICAL.",
    actor: "Deterministic Risk Engine",
    status: "SUCCESS",
  },
  {
    id: "evt_7",
    timestamp: "10:14:07.150",
    stage: "REPORT_GENERATION",
    title: "Court-Ready Forensic Report Emitted",
    description: "Compiled executive summary, regulatory citations, and recommended investor protection actions under rules.v2.0.",
    actor: "Forensic Reporter",
    status: "SUCCESS",
  },
];

export function InvestigationTimeline({
  events = SAMPLE_TIMELINE,
}: {
  events?: TimelineEvent[];
}) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-indigo-400" />
          <h3 className="text-sm font-semibold text-slate-100">Investigation Execution Timeline</h3>
        </div>
        <span className="text-[11px] font-mono text-slate-500">{events.length} Orchestrated Events</span>
      </div>

      <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
        {events.map((evt) => {
          const isWarning = evt.status === "WARNING";
          const isFailed = evt.status === "FAILED";
          return (
            <div key={evt.id} className="relative group">
              {/* Dot */}
              <div
                className={`absolute -left-6 top-1 w-3.5 h-3.5 rounded-full border-2 ${
                  isFailed
                    ? "bg-rose-500 border-rose-950"
                    : isWarning
                    ? "bg-amber-500 border-amber-950"
                    : "bg-indigo-500 border-indigo-950"
                }`}
              />

              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1.5 text-xs">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-200">{evt.title}</span>
                    {evt.toolName && (
                      <span className="px-1.5 py-0.5 rounded bg-indigo-950 text-indigo-300 font-mono text-[10px] border border-indigo-800">
                        {evt.toolName}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 text-[10px] text-slate-500 font-mono">
                    <span>{evt.actor}</span>
                    <span>•</span>
                    <span>{evt.timestamp}</span>
                  </div>
                </div>

                <p className="text-slate-400 text-[11px] leading-relaxed">{evt.description}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
