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
  { name: "MesoNet Deepfake Detector", category: "Video/Deepfake", status: "ONLINE", latencyMs: 480, safetyInterpretation: "Operational (Audio-visual screening & Whisper STT)" },
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
    <div className="space-y-6 animate-fade-in">
      {/* ── 1. Official Registry Tri-State Verifications ──────────────────── */}
      <div className="rounded-2xl border border-[#E7E3D8] bg-white p-6 space-y-4 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-stone-200 gap-2">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-orange-100 text-orange-600 border border-orange-200">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-stone-900 tracking-tight">
                Official Regulatory Registry Tri-State Verifications
              </h3>
              <p className="text-xs text-stone-600">
                Direct deterministic query results against SEBI, MCA21, NPCI, and ICANN registries
              </p>
            </div>
          </div>
          <span className="text-xs font-mono font-bold px-3 py-1 rounded-full bg-orange-50 text-orange-800 border border-orange-200 self-start sm:self-auto">
            Rule 8 Tri-State Invariant
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-stone-200 bg-[#FAF7F2] text-stone-600 text-left font-mono uppercase text-[10px] tracking-wider">
                <th className="py-2.5 px-3">Entity / Subject</th>
                <th className="py-2.5 px-3">Claimed ID</th>
                <th className="py-2.5 px-3">Registry Searched</th>
                <th className="py-2.5 px-3">Tri-State Result</th>
                <th className="py-2.5 px-3">Audit Finding</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-200">
              {verifications.map((row, i) => (
                <tr key={i} className="hover:bg-stone-50 transition-colors duration-150">
                  <td className="py-3 px-3 font-medium text-stone-900">
                    <div className="font-bold text-stone-900 text-sm">{row.entityName}</div>
                    <span className="text-[11px] text-stone-500 font-mono mt-0.5 block">{row.entityType}</span>
                  </td>
                  <td className="py-3 px-3 font-mono text-stone-700">{row.claimedRegNumber || "—"}</td>
                  <td className="py-3 px-3 text-stone-700 font-medium">{row.registrySearched}</td>
                  <td className="py-3 px-3">
                    {row.status === VerificationState.VERIFIED ? (
                      <span className="px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-800 border border-emerald-200 font-mono text-[11px] font-bold flex items-center gap-1.5 w-fit shadow-sm">
                        <span className="h-2 w-2 rounded-full bg-emerald-500" />
                        <CheckCircle2 className="w-3.5 h-3.5" /> VERIFIED
                      </span>
                    ) : row.status === VerificationState.NOT_VERIFIED ? (
                      <span className="px-2.5 py-1 rounded-lg bg-rose-50 text-rose-800 border border-rose-200 font-mono text-[11px] font-bold flex items-center gap-1.5 w-fit shadow-sm">
                        <span className="h-2 w-2 rounded-full bg-rose-500" />
                        <XCircle className="w-3.5 h-3.5" /> NOT_VERIFIED
                      </span>
                    ) : (
                      <span className="px-2.5 py-1 rounded-lg bg-amber-50 text-amber-800 border border-amber-200 font-mono text-[11px] font-bold flex items-center gap-1.5 w-fit shadow-sm">
                        <span className="h-2 w-2 rounded-full bg-amber-500 animate-pulse" />
                        <AlertCircle className="w-3.5 h-3.5" /> UNAVAILABLE
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-3 text-stone-600 text-xs max-w-sm leading-relaxed">{row.details}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── 2. Specialized Detection Engine Status & Failsafe Invariant ──── */}
      <div className="rounded-2xl border border-[#E7E3D8] bg-white p-6 space-y-4 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-stone-200 gap-2">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-orange-100 text-orange-600 border border-orange-200">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-stone-900 tracking-tight">
                Specialized Detection Engines &amp; Failsafe Invariant Status
              </h3>
              <p className="text-xs text-stone-600">
                Continuous health telemetry across multimodal inference pipelines
              </p>
            </div>
          </div>
          <span className="text-xs font-mono font-bold px-3 py-1 rounded-full bg-rose-50 text-rose-800 border border-rose-200 self-start sm:self-auto">
            Rule 9: Zero-Trust Safety
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
          {analyzers.map((a, i) => {
            const isOk = a.status === "ONLINE";
            return (
              <div
                key={i}
                className={`p-4 rounded-xl border transition-all duration-200 ${
                  isOk
                    ? "bg-[#FAF7F2] border-[#E7E3D8] hover:border-orange-300"
                    : "bg-rose-50/60 border-rose-200"
                } space-y-2.5 text-xs shadow-sm`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className="font-bold text-stone-900 text-sm">{a.name}</h4>
                    <span className="text-[11px] text-stone-500 font-mono mt-0.5 block">{a.category}</span>
                  </div>
                  <span
                    className={`px-2.5 py-0.5 rounded-full font-mono text-[10px] font-bold flex items-center gap-1.5 ${
                      isOk
                        ? "bg-emerald-100 text-emerald-800 border border-emerald-300"
                        : "bg-rose-100 text-rose-800 border border-rose-300 animate-pulse"
                    }`}
                  >
                    <span className={`h-1.5 w-1.5 rounded-full ${isOk ? "bg-emerald-500" : "bg-rose-500"}`} />
                    {a.status}
                  </span>
                </div>

                <div className="space-y-1">
                  <div className="flex items-center justify-between text-[11px] text-stone-600 font-mono">
                    <span>Engine Latency:</span>
                    <span className="font-bold text-stone-900">{a.latencyMs}ms</span>
                  </div>
                  <div className="h-1.5 w-full bg-stone-200 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        a.latencyMs < 300
                          ? "bg-emerald-500"
                          : a.latencyMs < 600
                          ? "bg-orange-500"
                          : "bg-amber-500"
                      }`}
                      style={{ width: `${Math.min(100, (a.latencyMs / 800) * 100)}%` }}
                    />
                  </div>
                </div>

                <div
                  className={`p-2.5 rounded-lg text-xs leading-relaxed ${
                    isOk
                      ? "bg-white text-stone-700 border border-stone-200"
                      : "bg-rose-100/70 text-rose-900 font-medium border border-rose-200"
                  }`}
                >
                  {a.safetyInterpretation}
                </div>
              </div>
            );
          })}
        </div>

        <div className="p-4 rounded-xl bg-amber-50/80 border border-amber-200 text-xs text-amber-900 flex items-start gap-3 shadow-sm">
          <ShieldAlert className="w-5 h-5 flex-shrink-0 text-amber-600 mt-0.5" />
          <div className="leading-relaxed">
            <strong className="text-amber-900 font-bold block mb-0.5">Strict Zero-Trust Failsafe Guarantee (Rule 9):</strong>
            Under VERA architecture, any analyzer offline condition, API timeout, or unverified payload NEVER evaluates as &quot;safe&quot;. Missing evidence strictly escalates uncertainty penalties to guarantee protection against false negatives.
          </div>
        </div>
      </div>
    </div>
  );
}
