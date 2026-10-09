"use client";

import React, { useState, useEffect } from "react";
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
} from "lucide-react";
import {
  VERA_API_VERSION,
  VERA_API_PREFIX,
  VerificationState,
  RiskSeverityTier,
  EvidenceMediaType,
  InvestigationResponse,
  HealthCheckResponse,
} from "@vera/contracts";
import { veraApi, VeraApiError } from "@/lib/api-client";
import { LoadingState, ErrorState } from "@/components/states/States";

export default function Home() {
  const [health, setHealth] = useState<HealthCheckResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [isLoadingHealth, setIsLoadingHealth] = useState(true);

  // Investigation creation form state
  const [title, setTitle] = useState("Suspected High-Yield Forex Scam");
  const [targetEntityName, setTargetEntityName] = useState("Apex Quantum Wealth");
  const [primaryUrl, setPrimaryUrl] = useState("https://apex-quantum-returns.fake");
  const [summaryNote, setSummaryNote] = useState("Invited to high-yield WhatsApp group claiming 35% daily returns with unregistered crypto broker.");
  const [evidenceUrl, setEvidenceUrl] = useState("https://apex-quantum-returns.fake/deposit");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [createdCase, setCreatedCase] = useState<InvestigationResponse | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

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

  const handleCreateCase = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setSubmitError(null);

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
                <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/30">
                  Phase 1 Core
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

      {/* Live Case Initiation Console */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7 p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <div className="flex items-center gap-2 text-indigo-400">
              <Sparkles className="w-5 h-5" />
              <h2 className="font-semibold text-slate-100 text-sm">Initiate Fraud Investigation</h2>
            </div>
            <span className="text-[11px] font-mono text-slate-500">Contract v1 Compliant</span>
          </div>

          <form onSubmit={handleCreateCase} className="space-y-4 text-xs">
            <div>
              <label className="block text-slate-400 font-medium mb-1">Case Title</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-slate-400 font-medium mb-1">Target Entity / Suspect Name</label>
                <input
                  type="text"
                  value={targetEntityName}
                  onChange={(e) => setTargetEntityName(e.target.value)}
                  required
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-slate-400 font-medium mb-1">Primary URL / Web Domain</label>
                <input
                  type="url"
                  value={primaryUrl}
                  onChange={(e) => setPrimaryUrl(e.target.value)}
                  required
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-slate-400 font-medium mb-1">Initial Evidence URL / Artifact</label>
              <input
                type="text"
                value={evidenceUrl}
                onChange={(e) => setEvidenceUrl(e.target.value)}
                required
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-slate-400 font-medium mb-1">Investigator Summary / Intel Notes</label>
              <textarea
                value={summaryNote}
                onChange={(e) => setSummaryNote(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:border-indigo-500"
              />
            </div>

            {submitError && (
              <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-800/60 text-rose-300 text-[11px]">
                {submitError}
              </div>
            )}

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium shadow-lg shadow-indigo-600/20 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
            >
              {isSubmitting ? (
                <>
                  <Clock className="w-4 h-4 animate-spin" />
                  <span>Submitting to VERA Core...</span>
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  <span>Dispatch Case Investigation</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Live Case Output & Manifest Card */}
        <div className="lg:col-span-5 p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <h2 className="font-semibold text-slate-100 text-sm flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              Investigation Response
            </h2>
            <span className="text-[11px] font-mono text-slate-500">
              {createdCase ? "LIVE DISPATCHED" : "AWAITING SUBMISSION"}
            </span>
          </div>

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
                    EVIDENCE: {createdCase.evidence_count} items
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

              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1">
                <div className="text-slate-400 text-[11px] font-semibold">Deterministic Risk Assessment</div>
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-400">Initial Score:</span>
                  <span className="font-mono text-emerald-400 font-bold">{createdCase.risk_assessment?.final_score ?? createdCase.risk_assessment?.finalScore ?? 0.0} / 100</span>
                </div>
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-400">Deterministic Guard:</span>
                  <span className="text-emerald-400 font-mono">is_llm_assigned = false</span>
                </div>
              </div>

            </div>
          ) : (
            <div className="py-12 flex flex-col items-center justify-center text-center text-slate-500 space-y-2">
              <Upload className="w-8 h-8 opacity-40" />
              <p className="text-xs">Submit the form on the left to create a live investigation with cryptographic reproducibility manifest.</p>
            </div>
          )}
        </div>
      </section>

      {/* Architecture Principles Grid */}
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
            <span>Rule 6 & 7 Compliant</span>
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
            <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">
              {VerificationState.VERIFIED}
            </span>
            <span className="px-2 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-800">
              {VerificationState.NOT_VERIFIED}
            </span>
            <span className="px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800">
              {VerificationState.UNAVAILABLE}
            </span>
          </div>
          <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500 font-mono">
            <span>Rule 8 & 9 Failsafe</span>
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

      {/* Modular Layers Matrix */}
      <section className="p-6 rounded-xl bg-slate-900/40 border border-slate-800 space-y-5">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-slate-200 flex items-center gap-2">
            <Layers className="w-4 h-4 text-blue-400" />
            Architecture Boundaries & Engineering Contracts
          </h2>
          <span className="text-xs font-mono text-slate-400">MNC Tier-1 Architecture</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
          <div className="p-3.5 rounded-lg bg-slate-900/90 border border-slate-800/90 space-y-2">
            <div className="flex items-center gap-2 text-slate-300 font-medium">
              <Cpu className="w-4 h-4 text-indigo-400" />
              <span>Detection Engines</span>
            </div>
            <ul className="text-slate-400 space-y-1 text-[11px]">
              <li>- PaddleOCR (Text extraction)</li>
              <li>- faster-whisper (Audio/Speech)</li>
              <li>- MesoNet (Deepfake video)</li>
              <li>- XGBoost (Fraud classification)</li>
              <li>- Androguard / JADX (APK forensic)</li>
            </ul>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-900/90 border border-slate-800/90 space-y-2">
            <div className="flex items-center gap-2 text-slate-300 font-medium">
              <GitBranch className="w-4 h-4 text-sky-400" />
              <span>AI Providers</span>
            </div>
            <ul className="text-slate-400 space-y-1 text-[11px]">
              <li>- LLMProvider Abstract Interface</li>
              <li>- Gemini Free-Tier Provider</li>
              <li>- Ollama Local Provider</li>
              <li>- Groq Optional Fast Provider</li>
              <li>- BGE-M3 Embeddings</li>
            </ul>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-900/90 border border-slate-800/90 space-y-2">
            <div className="flex items-center gap-2 text-slate-300 font-medium">
              <Database className="w-4 h-4 text-emerald-400" />
              <span>Data & Storage</span>
            </div>
            <ul className="text-slate-400 space-y-1 text-[11px]">
              <li>- Supabase PostgreSQL + pgvector</li>
              <li>- Supabase Storage (Zero local FS)</li>
              <li>- Upstash Redis & RateLimiter</li>
              <li>- Upstash QStash (Task queuing)</li>
              <li>- Alembic Migration Engine</li>
            </ul>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-900/90 border border-slate-800/90 space-y-2">
            <div className="flex items-center gap-2 text-slate-300 font-medium">
              <Lock className="w-4 h-4 text-amber-400" />
              <span>Reproducibility</span>
            </div>
            <ul className="text-slate-400 space-y-1 text-[11px]">
              <li>- Immutable Investigation Manifest</li>
              <li>- Model weights & config digests</li>
              <li>- Rule versioning & audit logs</li>
              <li>- SHA-256 evidence hashing</li>
              <li>- Deterministic replay support</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Severity Tiers Reference */}
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

