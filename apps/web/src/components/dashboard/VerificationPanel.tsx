"use client";

import React from "react";
import { CheckCircle2, XCircle, AlertCircle, ShieldAlert, Cpu, Server } from "lucide-react";
import { VerificationState } from "@vera/contracts";

export interface VerificationRecord {
  entityName: string;
  entityType: "Individual Advisor" | "Corporate Broker" | "Payment Handle" | "Web Domain";
  claimedRegNumber?: string;
  registrySearched: "SEBI Registered Intermediaries" | "MCA21 Company Master" | "NPCI UPI Directory" | "Whois ICANN";
  status: VerificationState;
  details: string;
}

export interface AnalyzerStatusRecord {
  name: string;
  category: "Vision/OCR" | "Audio/STT" | "Video/Deepfake" | "APK Static" | "URL Intelligence";
  status: "ONLINE" | "FAILED" | "UNAVAILABLE" | "TIMED_OUT";
  latencyMs: number;
  safetyInterpretation: string;
}

const SAMPLE_VERIFICATIONS: VerificationRecord[] = [
  {
    entityName: "Rajesh Kumar (Alleged RA)",
    entityType: "Individual Advisor",
    claimedRegNumber: "INZ0000000",
    registrySearched: "SEBI Registered Intermediaries",
    status: VerificationState.NOT_VERIFIED,
    details: "Registration number 'INZ0000000' is fictitious and does not match SEBI active advisor records.",
  },
  {
    entityName: "Apex Capital FX",
    entityType: "Corporate Broker",
    claimedRegNumber: "U67190MH2021PTC368900",
    registrySearched: "MCA21 Company Master",
    status: VerificationState.NOT_VERIFIED,
    details: "CIN does not exist in Ministry of Corporate Affairs database. No incorporation filings found.",
  },
  {
    entityName: "apex-capital-fx.in",
    entityType: "Web Domain",
    registrySearched: "Whois ICANN",
    status: VerificationState.NOT_VERIFIED,
    details: "Domain registered recently (4 days ago); registrant identity masked via privacy proxy.",
  },
  {
    entityName: "apexinvest@icici",
    entityType: "Payment Handle",
    registrySearched: "NPCI UPI Directory",
    status: VerificationState.UNAVAILABLE,
    details: "Bank API rate limit / maintenance partition. Tri-state status UNAVAILABLE (Escalates uncertainty).",
  },
];

const SAMPLE_ANALYZERS: AnalyzerStatusRecord[] = [
  { name: "PaddleOCR Engine", category: "Vision/OCR", status: "ONLINE", latencyMs: 340, safetyInterpretation: "Signals processed" },
  { name: "faster-whisper Engine", category: "Audio/STT", status: "ONLINE", latencyMs: 510, safetyInterpretation: "Signals processed" },
  { name: "MesoNet Deepfake Detector", category: "Video/Deepfake", status: "FAILED", latencyMs: 1200, safetyInterpretation: "FAILED: Escalates risk penalty (+25). NEVER treated as safe." },
  { name: "Androguard APK Analyzer", category: "APK Static", status: "ONLINE", latencyMs: 620, safetyInterpretation: "Signals processed" },
  { name: "PhishTank & Threat Intel", category: "URL Intelligence", status: "ONLINE", latencyMs: 220, safetyInterpretation: "Signals processed" },
];

export function VerificationPanel({
  verifications = SAMPLE_VERIFICATIONS,
  analyzers = SAMPLE_ANALYZERS,
}: {
  verifications?: VerificationRecord[];
  analyzers?: AnalyzerStatusRecord[];
}) {
  return (
    <div className="space-y-4">
      {/* 1. Official Registry Tri-State Verifications */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-3">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-purple-400" />
            <h3 className="text-sm font-semibold text-slate-100">Official Registry Tri-State Verifications</h3>
          </div>
          <span className="text-[11px] font-mono text-slate-500">Rule 8 Invariant</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-500 text-left">
                <th className="pb-2">Entity / Subject</th>
                <th className="pb-2">Claimed ID</th>
                <th className="pb-2">Registry Searched</th>
                <th className="pb-2">Tri-State Result</th>
                <th className="pb-2">Audit Finding</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {verifications.map((row, i) => (
                <tr key={i} className="hover:bg-slate-800/20">
                  <td className="py-2.5 font-medium text-slate-200">
                    <div>{row.entityName}</div>
                    <span className="text-[10px] text-slate-500">{row.entityType}</span>
                  </td>
                  <td className="py-2.5 font-mono text-slate-400">{row.claimedRegNumber || "—"}</td>
                  <td className="py-2.5 text-slate-400">{row.registrySearched}</td>
                  <td className="py-2.5">
                    {row.status === VerificationState.VERIFIED ? (
                      <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 font-mono text-[10px] flex items-center gap-1 w-fit">
                        <CheckCircle2 className="w-3 h-3" /> VERIFIED
                      </span>
                    ) : row.status === VerificationState.NOT_VERIFIED ? (
                      <span className="px-2 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-800 font-mono text-[10px] flex items-center gap-1 w-fit">
                        <XCircle className="w-3 h-3" /> NOT_VERIFIED
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800 font-mono text-[10px] flex items-center gap-1 w-fit">
                        <AlertCircle className="w-3 h-3" /> UNAVAILABLE
                      </span>
                    )}
                  </td>
                  <td className="py-2.5 text-slate-400 text-[11px] max-w-xs">{row.details}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 2. Specialized Analyzer Health & Failsafe Invariant (Rule 9) */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-3">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-indigo-400" />
            <h3 className="text-sm font-semibold text-slate-100">
              Specialized Detection Engine Status &amp; Failsafe Invariant
            </h3>
          </div>
          <span className="text-[11px] font-mono text-rose-400">Rule 9: Zero-Trust Safety</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {analyzers.map((a, i) => {
            const isOk = a.status === "ONLINE";
            return (
              <div
                key={i}
                className={`p-3 rounded-lg border ${
                  isOk ? "bg-slate-950 border-slate-800" : "bg-rose-950/30 border-rose-800/60"
                } space-y-2 text-xs`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className="font-semibold text-slate-200">{a.name}</h4>
                    <span className="text-[10px] text-slate-500 font-mono">{a.category}</span>
                  </div>
                  <span
                    className={`px-2 py-0.5 rounded font-mono text-[10px] font-bold ${
                      isOk ? "bg-emerald-950 text-emerald-400 border border-emerald-800" : "bg-rose-950 text-rose-400 border border-rose-800 animate-pulse"
                    }`}
                  >
                    {a.status}
                  </span>
                </div>

                <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono">
                  <span>Latency:</span>
                  <span>{a.latencyMs}ms</span>
                </div>

                <div
                  className={`p-2 rounded text-[11px] ${
                    isOk ? "bg-slate-900 text-slate-400" : "bg-rose-950/60 text-rose-300 font-medium border border-rose-900/50"
                  }`}
                >
                  {a.safetyInterpretation}
                </div>
              </div>
            );
          })}
        </div>

        <div className="p-3 rounded-lg bg-amber-950/20 border border-amber-800/40 text-[11px] text-amber-300 flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 flex-shrink-0 text-amber-400" />
          <span>
            <strong>Safety Invariant Enforced:</strong> Under Architecture Rule 9, an analyzer error, timeout, or missing weight is NEVER displayed as &quot;safe&quot;. Failsafe logic escalates uncertainty penalties to prevent false negatives.
          </span>
        </div>
      </div>
    </div>
  );
}
