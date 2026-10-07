import React from "react";
import {
  ShieldAlert,
  Binary,
  Layers,
  Cpu,
  Database,
  Lock,
  GitBranch,
  FileCheck2,
  AlertTriangle
} from "lucide-react";
import {
  VERA_API_VERSION,
  VERA_API_PREFIX,
  VerificationState,
  RiskSeverityTier
} from "@vera/contracts";

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-12 flex flex-col items-center">
      <div className="w-full max-w-6xl space-y-8">
        {/* Top Header */}
        <header className="border-b border-slate-800 pb-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-lg bg-blue-600/20 text-blue-400 border border-blue-500/30">
                <ShieldAlert className="w-8 h-8" />
              </div>
              <div>
                <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-white flex items-center gap-3">
                  VERA
                  <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/30">
                    Phase 0 Scaffolding
                  </span>
                </h1>
                <p className="text-sm text-slate-400 mt-0.5">
                  MNC-Grade Agentic Investment-Fraud Investigation Platform
                </p>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3 text-xs font-mono text-slate-400 bg-slate-900 border border-slate-800 px-4 py-2 rounded-lg self-start md:self-auto">
            <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>API: {VERA_API_PREFIX} ({VERA_API_VERSION})</span>
          </div>
        </header>

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
    </main>
  );
}
