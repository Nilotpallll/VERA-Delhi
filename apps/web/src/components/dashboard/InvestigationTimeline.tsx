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
    <div className="rounded-2xl border border-[#E7E3D8] bg-white p-6 space-y-5 shadow-sm animate-fade-in">
      <div className="flex items-center justify-between border-b border-stone-200 pb-3">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-xl bg-orange-100 text-orange-600 border border-orange-200">
            <Clock className="w-4 h-4" />
          </div>
          <h3 className="text-sm font-bold text-stone-900">Investigation Execution Timeline</h3>
        </div>
        <span className="text-xs font-mono text-stone-500 font-medium">{events.length} Orchestrated Events</span>
      </div>

      <div className="relative pl-6 space-y-4 before:absolute before:left-[7px] before:top-2 before:bottom-2 before:w-0.5 before:bg-gradient-to-b before:from-orange-400 before:via-stone-300 before:to-stone-200">
        {events.map((evt, evtIdx) => {
          const isWarning = evt.status === "WARNING";
          const isFailed = evt.status === "FAILED";
          return (
            <div
              key={evt.id}
              className="relative group animate-fade-in"
              style={{ animationDelay: `${evtIdx * 0.08}s` }}
            >
              {/* Dot */}
              <div
                className={`absolute -left-6 top-1.5 w-3.5 h-3.5 rounded-full border-2 transition-all duration-300 ${
                  isFailed
                    ? "bg-rose-500 border-white shadow-md shadow-rose-500/20"
                    : isWarning
                    ? "bg-amber-500 border-white shadow-md shadow-amber-500/20"
                    : "bg-orange-500 border-white shadow-md shadow-orange-500/20"
                }`}
              />

              <div className="p-4 rounded-xl bg-[#FAF7F2] border border-[#E7E3D8] hover:border-orange-300 space-y-1.5 text-xs transition-all duration-200 card-hover shadow-sm">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-stone-900">{evt.title}</span>
                    {evt.toolName && (
                      <span className="px-2 py-0.5 rounded-md bg-orange-100 text-orange-800 font-mono text-[10px] font-bold border border-orange-200">
                        {evt.toolName}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 text-[11px] text-stone-500 font-mono">
                    <span>{evt.actor}</span>
                    <span>•</span>
                    <span>{evt.timestamp}</span>
                  </div>
                </div>

                <p className="text-stone-600 text-xs leading-relaxed">{evt.description}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
