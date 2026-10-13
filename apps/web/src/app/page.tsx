"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  ShieldAlert,
  Binary,
  Layers,
  Cpu,
  Database,
  Lock,
  GitBranch,
  FileCheck2,
  AlertTriangle,
  Send,
  Upload,
  CheckCircle2,
  Clock,
  Sparkles,
  Play,
  BarChart3,
  Eye,
  ListChecks,
  Users,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Shield,
  Zap,
  FileText,
  Info,
} from "lucide-react";
import {
  VERA_API_VERSION,
  VERA_API_PREFIX,
  VerificationState,
  RiskSeverityTier,
  EvidenceMediaType,
  InvestigationResponse,
  AgentRunResponse,
  AgentForensicReport,
  HealthCheckResponse,
} from "@vera/contracts";
import { veraApi, VeraApiError } from "@/lib/api-client";
import { LoadingState, ErrorState } from "@/components/states/States";

// ── Risk Level helpers ────────────────────────────────────────────────────────
const RISK_COLORS: Record<string, { bg: string; border: string; text: string; bar: string }> = {
  CRITICAL: { bg: "bg-red-950/60", border: "border-red-700", text: "text-red-300", bar: "bg-red-500" },
  HIGH:     { bg: "bg-orange-950/60", border: "border-orange-700", text: "text-orange-300", bar: "bg-orange-500" },
  MODERATE: { bg: "bg-amber-950/60", border: "border-amber-700", text: "text-amber-300", bar: "bg-amber-500" },
  LOW:      { bg: "bg-emerald-950/60", border: "border-emerald-700", text: "text-emerald-300", bar: "bg-emerald-500" },
};

function getRiskColor(level: string) {
  return RISK_COLORS[level] ?? RISK_COLORS.LOW;
}

// ── Small Section header ──────────────────────────────────────────────────────
function SectionHeader({ icon: Icon, title, sub }: { icon: any; title: string; sub?: string }) {
  return (
    <div className="flex items-center justify-between border-b border-slate-800/80 pb-3 mb-4">
      <div className="flex items-center gap-2 text-indigo-400">
        <Icon className="w-4 h-4" />
        <h2 className="font-semibold text-slate-100 text-sm">{title}</h2>
      </div>
      {sub && <span className="text-[11px] font-mono text-slate-500">{sub}</span>}
    </div>
  );
}

// ── Risk Gauge ────────────────────────────────────────────────────────────────
function RiskGauge({ score, level }: { score: number; level: string }) {
  const c = getRiskColor(level);
  return (
    <div className={`p-4 rounded-xl border ${c.bg} ${c.border} space-y-2`}>
      <div className="flex items-center justify-between">
        <span className={`text-xs font-semibold uppercase tracking-wide ${c.text}`}>Risk Level</span>
        <span className={`font-mono text-lg font-bold ${c.text}`}>{level}</span>
      </div>
      <div className="w-full bg-slate-900 rounded-full h-3 overflow-hidden">
        <div
          className={`h-3 rounded-full transition-all duration-700 ${c.bar}`}
          style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
        />
      </div>
      <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
        <span>0</span>
        <span className={`font-bold text-sm ${c.text}`}>{score.toFixed(0)} / 100</span>
        <span>100</span>
      </div>
      <p className="text-[10px] text-slate-500 mt-1">
        ⚠ Prototype heuristic weight — NOT a probability of fraud.
      </p>
    </div>
  );
}

// ── Collapsible Panel ─────────────────────────────────────────────────────────
function Collapsible({ title, count, children }: { title: string; count?: number; children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border border-slate-800 rounded-lg overflow-hidden">
      <button
        className="w-full flex items-center justify-between px-4 py-3 bg-slate-900/80 hover:bg-slate-800/50 text-left transition-colors"
        onClick={() => setOpen((o) => !o)}
      >
        <span className="text-xs font-semibold text-slate-300">
          {title}
          {count !== undefined && (
            <span className="ml-2 px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-400 text-[10px]">{count}</span>
          )}
        </span>
        {open ? <ChevronUp className="w-3.5 h-3.5 text-slate-500" /> : <ChevronDown className="w-3.5 h-3.5 text-slate-500" />}
      </button>
      {open && <div className="px-4 py-3 bg-slate-950/60 text-xs">{children}</div>}
    </div>
  );
}

// ── Evidence Timeline Item ────────────────────────────────────────────────────
function EvidenceItem({ ev, index }: { ev: Record<string, unknown>; index: number }) {
  const evType = String(ev.type ?? "");
  const description = String(ev.description ?? "No description");
  const sourceRef = String(ev.source_reference ?? ev.source ?? "");
  const confidence = typeof ev.confidence === "number" ? (ev.confidence * 100).toFixed(0) + "%" : "—";

  return (
    <div className="flex gap-3 pb-3 last:pb-0">
      <div className="flex flex-col items-center">
        <div className="w-6 h-6 rounded-full bg-indigo-600/30 border border-indigo-500/40 flex items-center justify-center text-[10px] font-mono text-indigo-400 flex-shrink-0">
          {index + 1}
        </div>
        {index >= 0 && <div className="w-px flex-1 bg-slate-800/60 mt-1" />}
      </div>
      <div className="flex-1 pb-3">
        <div className="flex items-start justify-between gap-2">
          <span className="px-2 py-0.5 rounded bg-indigo-950/60 text-indigo-300 border border-indigo-800/60 text-[10px] font-mono">
            {evType || "EVIDENCE"}
          </span>
          <span className="text-[10px] text-slate-500 font-mono">conf: {confidence}</span>
        </div>
        <p className="mt-1 text-slate-300 text-[11px] leading-relaxed">{description}</p>
        {sourceRef && (
          <p className="text-[10px] text-slate-500 mt-0.5 truncate">src: {sourceRef}</p>
        )}
      </div>
    </div>
  );
}

// ── Entity Table ──────────────────────────────────────────────────────────────
function EntityTable({ entities }: { entities: Array<Record<string, unknown>> }) {
  if (!entities.length) return <p className="text-slate-500 text-[11px]">No entities detected.</p>;
  return (
    <table className="w-full text-[11px]">
      <thead>
        <tr className="border-b border-slate-800 text-slate-500">
          <th className="text-left pb-2">Name</th>
          <th className="text-left pb-2">Type</th>
          <th className="text-left pb-2">Verified</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-slate-800/60">
        {entities.map((e, i) => (
          <tr key={i}>
            <td className="py-1.5 text-slate-300 font-mono">{String(e.name ?? e.value ?? "—")}</td>
            <td className="py-1.5 text-slate-400">{String(e.type ?? e.entity_type ?? "—")}</td>
            <td className="py-1.5">
              {e.verified === true ? (
                <span className="text-emerald-400">✓ VERIFIED</span>
              ) : e.verified === false ? (
                <span className="text-rose-400">✗ NOT VERIFIED</span>
              ) : (
                <span className="text-amber-400">? UNAVAILABLE</span>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

// ── Forensic Report Viewer ────────────────────────────────────────────────────
function ForensicReportViewer({ report }: { report: AgentForensicReport }) {
  const r = report.report;
  const rc = getRiskColor(r.risk_level);

  return (
    <div className="space-y-4 text-xs">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-slate-400 text-[10px] font-mono">Investigation ID</div>
          <div className="font-mono text-indigo-300 font-semibold">{r.investigation_id}</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Generated: {new Date(r.generated_at).toLocaleString()}</div>
        </div>
        <div className="flex flex-col items-end gap-1">
          <span className={`px-2.5 py-1 rounded-lg border font-mono text-[11px] font-bold ${rc.bg} ${rc.border} ${rc.text}`}>
            {r.risk_level} RISK
          </span>
          <span className="text-[10px] text-slate-500 font-mono">{r.ruleset_version}</span>
        </div>
      </div>

      {/* Risk Gauge */}
      <RiskGauge score={r.risk_score} level={r.risk_level} />

      {/* Executive Summary */}
      <div className="p-4 rounded-lg bg-slate-900/60 border border-slate-800">
        <div className="text-slate-400 text-[10px] font-semibold uppercase tracking-wide mb-2">Executive Summary</div>
        <p className="text-slate-200 leading-relaxed">{r.executive_summary}</p>
      </div>

      {/* Status Row */}
      <div className="grid grid-cols-3 gap-3">
        <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-center">
          <div className="text-[10px] text-slate-500 mb-1">Investigation</div>
          <div className="font-mono text-xs text-slate-300">{r.investigation_status}</div>
        </div>
        <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-center">
          <div className="text-[10px] text-slate-500 mb-1">Scam Stage</div>
          <div className="font-mono text-xs text-slate-300 capitalize">{r.scam_lifecycle_stage}</div>
        </div>
        <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-center">
          <div className="text-[10px] text-slate-500 mb-1">Model Confidence</div>
          <div className="font-mono text-xs text-slate-300">{(r.model_confidence * 100).toFixed(0)}%</div>
        </div>
      </div>

      {/* Suspicious Indicators */}
      <Collapsible title="Suspicious Indicators" count={r.suspicious_indicators.length}>
        {r.suspicious_indicators.length === 0 ? (
          <p className="text-slate-500">None detected.</p>
        ) : (
          <div className="space-y-2">
            {r.suspicious_indicators.map((s, i) => (
              <div key={i} className="flex items-start gap-3 p-2 rounded bg-slate-900/60 border border-slate-800/60">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <div className="flex justify-between">
                    <span className="font-mono text-amber-300">{s.signal_type}</span>
                    <span className="text-slate-500">+{s.weight}</span>
                  </div>
                  <p className="text-slate-400 text-[10px] mt-0.5">{s.description}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </Collapsible>

      {/* Entities */}
      <Collapsible title="Detected Entities" count={r.detected_entities.length}>
        <EntityTable entities={r.detected_entities as Array<Record<string, unknown>>} />
      </Collapsible>

      {/* Evidence Timeline */}
      <Collapsible title="Evidence Timeline" count={r.evidence.length}>
        {r.evidence.length === 0 ? (
          <p className="text-slate-500">No evidence items collected.</p>
        ) : (
          <div className="space-y-0">
            {(r.evidence as Array<Record<string, unknown>>).map((ev, i) => (
              <EvidenceItem key={i} ev={ev} index={i} />
            ))}
          </div>
        )}
      </Collapsible>

      {/* Recommended Actions */}
      <Collapsible title="Recommended Actions" count={r.recommended_actions.length}>
        {r.recommended_actions.length === 0 ? (
          <p className="text-slate-500">No specific recommendations.</p>
        ) : (
          <ul className="space-y-2">
            {r.recommended_actions.map((a, i) => (
              <li key={i} className="flex gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0 mt-0.5" />
                <span className="text-slate-300">{a}</span>
              </li>
            ))}
          </ul>
        )}
      </Collapsible>

      {/* Missing Evidence */}
      {r.missing_evidence.length > 0 && (
        <Collapsible title="Missing Evidence" count={r.missing_evidence.length}>
          <ul className="space-y-1">
            {r.missing_evidence.map((m, i) => (
              <li key={i} className="text-amber-400 flex gap-2">
                <Info className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
                <span>{m}</span>
              </li>
            ))}
          </ul>
        </Collapsible>
      )}

      {/* Disclaimer */}
      <div className="p-3 rounded-lg bg-slate-900/30 border border-slate-800/60 text-[10px] text-slate-500 font-mono">
        {r.disclaimer}
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function Home() {
  const [health, setHealth] = useState<HealthCheckResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [isLoadingHealth, setIsLoadingHealth] = useState(true);

  // Step 1: Investigation creation
  const [title, setTitle] = useState("Suspected High-Yield Forex Scam");
  const [targetEntityName, setTargetEntityName] = useState("Apex Quantum Wealth");
  const [primaryUrl, setPrimaryUrl] = useState("https://apex-quantum-returns.fake");
  const [summaryNote, setSummaryNote] = useState("Invited to high-yield WhatsApp group claiming 35% daily returns with unregistered crypto broker.");
  const [evidenceUrl, setEvidenceUrl] = useState("https://apex-quantum-returns.fake/deposit");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [createdCase, setCreatedCase] = useState<InvestigationResponse | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Step 2: Agent dispatch
  const [agentInputText, setAgentInputText] = useState(
    "Guaranteed 40% monthly returns on crypto investment. Register on apex-quantum-returns.fake. Pay via personal UPI to unlock VIP access."
  );
  const [isRunningAgent, setIsRunningAgent] = useState(false);
  const [agentRunResult, setAgentRunResult] = useState<AgentRunResponse | null>(null);
  const [agentRunError, setAgentRunError] = useState<string | null>(null);

  // Step 3: Forensic report retrieval
  const [forensicReport, setForensicReport] = useState<AgentForensicReport | null>(null);
  const [isLoadingReport, setIsLoadingReport] = useState(false);
  const [reportError, setReportError] = useState<string | null>(null);

  useEffect(() => {
    async function loadHealth() {
      try {
        setIsLoadingHealth(true);
        const data = await veraApi.getHealth();
        setHealth(data);
        setHealthError(null);
      } catch (err: any) {
        setHealthError(err.message || "Failed to reach VERA API backend");
      } finally {
        setIsLoadingHealth(false);
      }
    }
    loadHealth();
  }, []);

  // Step 1: Create investigation
  const handleCreateCase = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setSubmitError(null);
    setCreatedCase(null);
    setAgentRunResult(null);
    setForensicReport(null);

    try {
      const resp = await veraApi.createInvestigation(
        {
          title,
          target_entity_name: targetEntityName,
          primary_url: primaryUrl,
          summary_note: summaryNote,
          initial_evidence_items: [
            {
              media_type: EvidenceMediaType.URL,
              content_payload: evidenceUrl,
              source_origin: "Investigator Manual Entry",
              tags: ["forex_scam", "unauthorized_broker"],
            },
          ],
        },
        { idempotencyKey: `idemp_${Date.now()}` }
      );
      setCreatedCase(resp);
    } catch (err: any) {
      setSubmitError(err.message || "Failed to initiate case");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Step 2: Run agent
  const handleRunAgent = async () => {
    if (!createdCase) return;
    setIsRunningAgent(true);
    setAgentRunError(null);
    setAgentRunResult(null);
    setForensicReport(null);

    try {
      const result = await veraApi.runAgent(createdCase.id, {
        inputs: [
          { type: "text", value: agentInputText, description: "Suspect message / claim", source_label: "WhatsApp screenshot" },
          { type: "url", value: evidenceUrl, description: "Suspect domain", source_label: "Evidence URL" },
        ],
        max_iterations: 5,
      });
      setAgentRunResult(result);
    } catch (err: any) {
      setAgentRunError(err.message || "Agent investigation failed");
    } finally {
      setIsRunningAgent(false);
    }
  };

  // Step 3: Fetch forensic report
  const handleFetchReport = async () => {
    if (!createdCase) return;
    setIsLoadingReport(true);
    setReportError(null);
    try {
      const rpt = await veraApi.getAgentReport(createdCase.id);
      setForensicReport(rpt);
    } catch (err: any) {
      setReportError(err.message || "Failed to fetch forensic report");
    } finally {
      setIsLoadingReport(false);
    }
  };

  return (
    <div className="w-full max-w-6xl space-y-8">
      {/* Top Header */}
      <header className="border-b border-slate-800 pb-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-indigo-600/20 text-indigo-400 border border-indigo-500/30">
              <ShieldAlert className="w-8 h-8" />
            </div>
            <div>
              <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-white flex items-center gap-3">
                VERA Platform
                <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-violet-500/10 text-violet-400 border border-violet-500/30">
                  Phase 6 — Forensic Dashboard
                </span>
              </h1>
              <p className="text-sm text-slate-400 mt-0.5">
                MNC-Grade Agentic Investment-Fraud Investigation Platform
              </p>
            </div>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 text-xs font-mono">
          <div className="bg-slate-900 border border-slate-800 px-3.5 py-2 rounded-lg flex items-center gap-2.5">
            <span
              className={`flex h-2.5 w-2.5 rounded-full ${
                health?.status === "healthy"
                  ? "bg-emerald-500 animate-pulse"
                  : health?.status === "degraded"
                  ? "bg-amber-500"
                  : "bg-rose-500"
              }`}
            />
            <span className="text-slate-300">
              Backend: {health ? health.status.toUpperCase() : isLoadingHealth ? "CONNECTING..." : "OFFLINE"}
            </span>
          </div>
          <div className="text-slate-400 bg-slate-900 border border-slate-800 px-3.5 py-2 rounded-lg">
            API: {VERA_API_PREFIX} ({VERA_API_VERSION})
          </div>
        </div>
      </header>

      {/* ── STEP 1: Case Initiation ──────────────────────────────────────────── */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7 p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
          <SectionHeader icon={Sparkles} title="Step 1 — Initiate Fraud Investigation" sub="Contract v1 Compliant" />

          <form onSubmit={handleCreateCase} className="space-y-4 text-xs">
            <div>
              <label className="block text-slate-400 font-medium mb-1">Case Title</label>
              <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} required
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:border-indigo-500" />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-slate-400 font-medium mb-1">Target Entity / Suspect Name</label>
                <input type="text" value={targetEntityName} onChange={(e) => setTargetEntityName(e.target.value)} required
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:border-indigo-500" />
              </div>
              <div>
                <label className="block text-slate-400 font-medium mb-1">Primary URL / Web Domain</label>
                <input type="url" value={primaryUrl} onChange={(e) => setPrimaryUrl(e.target.value)} required
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:border-indigo-500" />
              </div>
            </div>

            <div>
              <label className="block text-slate-400 font-medium mb-1">Initial Evidence URL / Artifact</label>
              <input type="text" value={evidenceUrl} onChange={(e) => setEvidenceUrl(e.target.value)} required
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:border-indigo-500" />
            </div>

            <div>
              <label className="block text-slate-400 font-medium mb-1">Investigator Summary / Intel Notes</label>
              <textarea value={summaryNote} onChange={(e) => setSummaryNote(e.target.value)} rows={2}
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:border-indigo-500" />
            </div>

            {submitError && (
              <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-800/60 text-rose-300 text-[11px]">{submitError}</div>
            )}

            <button type="submit" disabled={isSubmitting}
              className="w-full py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium shadow-lg shadow-indigo-600/20 flex items-center justify-center gap-2 transition-all disabled:opacity-50">
              {isSubmitting ? (
                <><Clock className="w-4 h-4 animate-spin" /><span>Submitting to VERA Core...</span></>
              ) : (
                <><Send className="w-4 h-4" /><span>Dispatch Case Investigation</span></>
              )}
            </button>
          </form>
        </div>

        {/* Case creation response */}
        <div className="lg:col-span-5 p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
          <SectionHeader icon={CheckCircle2} title="Investigation Response" sub={createdCase ? "LIVE DISPATCHED" : "AWAITING SUBMISSION"} />

          {createdCase ? (
            <div className="space-y-4 text-xs">
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1">
                <div className="text-slate-400 text-[11px]">Case ID</div>
                <div className="font-mono text-indigo-400 font-semibold">{createdCase.id}</div>
                <div className="flex items-center gap-2 pt-1">
                  <span className="px-2 py-0.5 rounded text-[10px] bg-amber-950 text-amber-300 border border-amber-800">
                    STATUS: {createdCase.status}
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300">
                    EVIDENCE: {createdCase.evidence_count ?? createdCase.evidenceCount ?? 0} items
                  </span>
                </div>
              </div>

              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-2">
                <div className="text-slate-400 text-[11px] font-semibold">Immutable Manifest (Rule 13)</div>
                <div className="text-[11px] text-slate-400 font-mono space-y-1">
                  <div>Engine: {createdCase.manifest.engine_semver || createdCase.manifest.engineSemver}</div>
                  <div>Algorithm: {createdCase.manifest.scoring_algorithm_version || createdCase.manifest.scoringAlgorithmVersion}</div>
                  <div className="truncate">Config Digest: {(createdCase.manifest.configuration_digest || createdCase.manifest.configurationDigest || "").substring(0, 20)}...</div>
                  <div className="truncate">Input Digest: {(createdCase.manifest.input_digest || createdCase.manifest.inputDigest || "").substring(0, 20)}...</div>
                </div>
              </div>
            </div>
          ) : (
            <div className="py-12 flex flex-col items-center justify-center text-center text-slate-500 space-y-2">
              <Upload className="w-8 h-8 opacity-40" />
              <p className="text-xs">Submit the form to create a live investigation with cryptographic reproducibility manifest.</p>
            </div>
          )}
        </div>
      </section>

      {/* ── STEP 2: Run Agent ─────────────────────────────────────────────────── */}
      {createdCase && (
        <section className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
          <SectionHeader icon={Zap} title="Step 2 — Dispatch VERA Investigator Agent" sub="Phase 5 LangGraph" />

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 font-medium mb-1">Suspect Message / Evidence Text Input</label>
                <textarea
                  value={agentInputText}
                  onChange={(e) => setAgentInputText(e.target.value)}
                  rows={4}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:border-violet-500"
                />
              </div>
              <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800/60 text-[11px] text-slate-400 space-y-1">
                <div className="font-semibold text-slate-300">Agent will also investigate:</div>
                <div className="font-mono text-indigo-400">{evidenceUrl}</div>
                <div className="text-slate-500">via analyze_url + verify_domain tools</div>
              </div>

              {agentRunError && (
                <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-800/60 text-rose-300">{agentRunError}</div>
              )}

              <button
                onClick={handleRunAgent}
                disabled={isRunningAgent}
                className="w-full py-2.5 rounded-lg bg-violet-600 hover:bg-violet-500 text-white font-medium shadow-lg shadow-violet-600/20 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
              >
                {isRunningAgent ? (
                  <><RefreshCw className="w-4 h-4 animate-spin" /><span>Running VERA Agent Loop...</span></>
                ) : (
                  <><Play className="w-4 h-4" /><span>Run VERA Investigator Agent</span></>
                )}
              </button>
            </div>

            {/* Agent result */}
            <div>
              {agentRunResult ? (
                <div className="space-y-3 text-xs">
                  <RiskGauge score={agentRunResult.risk_score} level={agentRunResult.risk_level} />
                  <div className="grid grid-cols-2 gap-2">
                    {[
                      { label: "Status", val: agentRunResult.investigation_status },
                      { label: "Evidence Collected", val: String(agentRunResult.evidence_count) },
                      { label: "Entities Detected", val: String(agentRunResult.entity_count) },
                      { label: "Ruleset", val: agentRunResult.ruleset_version },
                    ].map(({ label, val }) => (
                      <div key={label} className="p-2.5 rounded-lg bg-slate-950 border border-slate-800">
                        <div className="text-[10px] text-slate-500">{label}</div>
                        <div className="font-mono text-slate-300 mt-0.5">{val}</div>
                      </div>
                    ))}
                  </div>
                  <button
                    onClick={handleFetchReport}
                    disabled={isLoadingReport}
                    className="w-full py-2 rounded-lg bg-emerald-700 hover:bg-emerald-600 text-white font-medium flex items-center justify-center gap-2 transition-all disabled:opacity-50"
                  >
                    {isLoadingReport ? (
                      <><Clock className="w-4 h-4 animate-spin" /><span>Loading Forensic Report...</span></>
                    ) : (
                      <><FileText className="w-4 h-4" /><span>Load Full Forensic Report</span></>
                    )}
                  </button>
                </div>
              ) : (
                <div className="h-full min-h-[180px] flex flex-col items-center justify-center text-center text-slate-500 space-y-2">
                  <BarChart3 className="w-8 h-8 opacity-30" />
                  <p className="text-xs">Agent results will appear here after dispatch.</p>
                </div>
              )}
              {reportError && (
                <div className="mt-3 p-3 rounded-lg bg-rose-950/40 border border-rose-800/60 text-rose-300 text-[11px]">{reportError}</div>
              )}
            </div>
          </div>
        </section>
      )}

      {/* ── STEP 3: Forensic Report ───────────────────────────────────────────── */}
      {forensicReport && (
        <section className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
          <SectionHeader icon={FileText} title="Step 3 — Full Forensic Report" sub="Rule 13 Reproducible" />
          <ForensicReportViewer report={forensicReport} />
        </section>
      )}

      {/* ── Architecture Principles Grid ───────────────────────────────────── */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 shadow-sm space-y-3">
          <div className="flex items-center gap-2.5 text-blue-400">
            <Binary className="w-5 h-5" />
            <h2 className="font-semibold text-slate-200 text-sm">Deterministic Risk Engine</h2>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Risk scores are strictly calculated via mathematical weighted aggregation. LLMs provide extracted features, but cannot directly set final risk scores.
          </p>
          <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500 font-mono">
            <span>Rule 6 &amp; 7 Compliant</span>
            <span className="text-emerald-400">Enforced</span>
          </div>
        </div>

        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 shadow-sm space-y-3">
          <div className="flex items-center gap-2.5 text-purple-400">
            <FileCheck2 className="w-5 h-5" />
            <h2 className="font-semibold text-slate-200 text-sm">Tri-State Verification</h2>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Registries and evidence distinguish explicitly between:
          </p>
          <div className="flex gap-1.5 flex-wrap font-mono text-[10px]">
            <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">{VerificationState.VERIFIED}</span>
            <span className="px-2 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-800">{VerificationState.NOT_VERIFIED}</span>
            <span className="px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800">{VerificationState.UNAVAILABLE}</span>
          </div>
          <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500 font-mono">
            <span>Rule 8 &amp; 9 Failsafe</span>
            <span className="text-emerald-400">Active</span>
          </div>
        </div>

        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 shadow-sm space-y-3">
          <div className="flex items-center gap-2.5 text-amber-400">
            <AlertTriangle className="w-5 h-5" />
            <h2 className="font-semibold text-slate-200 text-sm">Failsafe Default</h2>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Analyzer failure is never interpreted as safety. Timeouts, OCR crashes, and network partitions escalate uncertainty penalties.
          </p>
          <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500 font-mono">
            <span>Rule 9 Safety Invariant</span>
            <span className="text-emerald-400">Zero-Trust</span>
          </div>
        </div>
      </section>

      {/* ── Modular Layers Matrix ─────────────────────────────────────────────── */}
      <section className="p-6 rounded-xl bg-slate-900/40 border border-slate-800 space-y-5">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-slate-200 flex items-center gap-2">
            <Layers className="w-4 h-4 text-blue-400" />
            Architecture Boundaries &amp; Engineering Contracts
          </h2>
          <span className="text-xs font-mono text-slate-400">MNC Tier-1 Architecture</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
          <div className="p-3.5 rounded-lg bg-slate-900/90 border border-slate-800/90 space-y-2">
            <div className="flex items-center gap-2 text-slate-300 font-medium"><Cpu className="w-4 h-4 text-indigo-400" /><span>Detection Engines</span></div>
            <ul className="text-slate-400 space-y-1 text-[11px]">
              <li>- PaddleOCR (Text extraction)</li>
              <li>- faster-whisper (Audio/Speech)</li>
              <li>- MesoNet (Deepfake video)</li>
              <li>- XGBoost (Fraud classification)</li>
              <li>- Androguard / JADX (APK forensic)</li>
            </ul>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-900/90 border border-slate-800/90 space-y-2">
            <div className="flex items-center gap-2 text-slate-300 font-medium"><GitBranch className="w-4 h-4 text-sky-400" /><span>AI Providers</span></div>
            <ul className="text-slate-400 space-y-1 text-[11px]">
              <li>- LLMProvider Abstract Interface</li>
              <li>- Gemini Free-Tier Provider</li>
              <li>- Ollama Local Provider</li>
              <li>- Groq Optional Fast Provider</li>
              <li>- BGE-M3 Embeddings</li>
            </ul>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-900/90 border border-slate-800/90 space-y-2">
            <div className="flex items-center gap-2 text-slate-300 font-medium"><Database className="w-4 h-4 text-emerald-400" /><span>Data &amp; Storage</span></div>
            <ul className="text-slate-400 space-y-1 text-[11px]">
              <li>- Supabase PostgreSQL + pgvector</li>
              <li>- Supabase Storage (Zero local FS)</li>
              <li>- Upstash Redis &amp; RateLimiter</li>
              <li>- Upstash QStash (Task queuing)</li>
              <li>- Alembic Migration Engine</li>
            </ul>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-900/90 border border-slate-800/90 space-y-2">
            <div className="flex items-center gap-2 text-slate-300 font-medium"><Lock className="w-4 h-4 text-amber-400" /><span>Reproducibility</span></div>
            <ul className="text-slate-400 space-y-1 text-[11px]">
              <li>- Immutable Investigation Manifest</li>
              <li>- Model weights &amp; config digests</li>
              <li>- Rule versioning &amp; audit logs</li>
              <li>- SHA-256 evidence hashing</li>
              <li>- Deterministic replay support</li>
            </ul>
          </div>
        </div>
      </section>

      {/* ── Severity Tiers Reference ──────────────────────────────────────────── */}
      <section className="p-4 rounded-lg bg-slate-900/30 border border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs">
        <span className="text-slate-400 font-medium">Contract Severity Tiers:</span>
        <div className="flex items-center gap-2 font-mono text-[11px]">
          <span className="px-2 py-0.5 rounded bg-red-950/80 text-red-300 border border-red-900">{RiskSeverityTier.CRITICAL} (80-100)</span>
          <span className="px-2 py-0.5 rounded bg-orange-950/80 text-orange-300 border border-orange-900">{RiskSeverityTier.HIGH} (60-79)</span>
          <span className="px-2 py-0.5 rounded bg-amber-950/80 text-amber-300 border border-amber-900">{RiskSeverityTier.MEDIUM} (40-59)</span>
          <span className="px-2 py-0.5 rounded bg-blue-950/80 text-blue-300 border border-blue-900">{RiskSeverityTier.LOW} (10-39)</span>
          <span className="px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-300 border border-emerald-900">{RiskSeverityTier.SAFE} (0-9)</span>
          <span className="px-2 py-0.5 rounded bg-purple-950/80 text-purple-300 border border-purple-900">{RiskSeverityTier.INCONCLUSIVE}</span>
        </div>
      </section>
    </div>
  );
}
