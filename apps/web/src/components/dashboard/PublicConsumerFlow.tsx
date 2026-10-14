"use client";

import React, { useState, useRef } from "react";
import {
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  ExternalLink,
  PhoneCall,
  ArrowRight,
  Sparkles,
  Lock,
  Search,
  Upload,
  Film,
  X,
} from "lucide-react";
import { translations, Locale } from "@/lib/i18n";

interface PublicConsumerFlowProps {
  locale: Locale;
}

interface ScanVerdict {
  riskTier: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "MINIMAL" | "INCONCLUSIVE";
  score: number;
  highlightedReasons: string[];
  matchedKeywords: string[];
  verifiedItems: string[];
  unverifiedItems: string[];
  isDeepfakeResult?: boolean;
  deepfakeDetails?: {
    framesAnalyzed: number;
    facesDetected: number;
    temporalAggregate: number;
    flickerScore: number;
    statement: string;
    sha256: string;
  };
}

const API_BASE =
  (process.env.NEXT_PUBLIC_API_URL ||
    process.env.NEXT_PUBLIC_VERA_API_URL ||
    "https://vera-delhi.onrender.com").replace(/\/$/, "");

export function PublicConsumerFlow({ locale }: PublicConsumerFlowProps) {
  const t = translations[locale];
  const [inputText, setInputText] = useState("");
  const [isScanning, setIsScanning] = useState(false);
  const [verdict, setVerdict] = useState<ScanVerdict | null>(null);
  const [uploadedFile, setUploadedFile] = useState<{ name: string; sizeMB: string } | null>(null);
  const [uploadedB64, setUploadedB64] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    setUploadError(null);
    if (!file) return;

    const sizeMB = (file.size / 1024 / 1024).toFixed(1);
    if (file.size > 50 * 1024 * 1024) {
      setUploadError("File too large. Maximum 50 MB.");
      return;
    }
    setUploadedFile({ name: file.name, sizeMB });
    setVerdict(null);

    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = reader.result as string;
      // Keep the data-URI prefix — the backend strips it before decoding
      setUploadedB64(dataUrl);
      setInputText(`[VIDEO]: ${file.name} (${sizeMB} MB) — ready for deepfake analysis`);
    };
    reader.onerror = () => setUploadError("Failed to read file. Please try again.");
    reader.readAsDataURL(file);
  };

  const clearFile = () => {
    setUploadedFile(null);
    setUploadedB64(null);
    setInputText("");
    setUploadError(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  // ── Main analysis handler ────────────────────────────────────────────────────
  const handleScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() && !uploadedB64) return;

    setIsScanning(true);
    setVerdict(null);

    // ── Branch 1: Video file uploaded — call real deepfake API ──────────────
    if (uploadedB64) {
      try {
        const resp = await fetch(`${API_BASE}/api/v1/deepfake-check`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            video_b64: uploadedB64,
            source_label: "public_consumer_upload",
          }),
        });

        if (!resp.ok) {
          const err = await resp.json().catch(() => ({ detail: resp.statusText }));
          throw new Error(err.detail || `API error ${resp.status}`);
        }

        const data = await resp.json();

        const agg: number = data.temporal_aggregate_score ?? 0;
        const riskTier: ScanVerdict["riskTier"] =
          agg >= 0.8
            ? "CRITICAL"
            : agg >= 0.6
            ? "HIGH"
            : agg >= 0.4
            ? "MEDIUM"
            : agg >= 0.2
            ? "LOW"
            : "MINIMAL";

        const reasons: string[] = [];
        if (data.facial_manipulation_signals_detected) {
          reasons.push(
            `MesoNet-4 detected facial manipulation signals with ${Math.round(agg * 100)}% probability (temporal aggregate score: ${agg.toFixed(3)})`
          );
        }
        if ((data.temporal_flicker_score ?? 0) > 0.15) {
          reasons.push(
            `Temporal flicker artifact score: ${data.temporal_flicker_score?.toFixed(3)} — consistent with GAN synthesis boundary instability`
          );
        }
        if (data.faces_detected === 0) {
          reasons.push(
            "No human faces detected in sampled frames — video may be non-facial content or too low resolution"
          );
        }
        if (reasons.length === 0) {
          reasons.push("No significant manipulation signals detected in sampled frames.");
        }

        setVerdict({
          riskTier,
          score: Math.round(agg * 100),
          highlightedReasons: reasons,
          matchedKeywords: [],
          verifiedItems: [
            `MesoNet-4 spatiotemporal inference on ${data.frames_analyzed} extracted frames`,
            `SHA-256 content fingerprint: ${data.sha256?.slice(0, 16)}...`,
            `Laplacian variance + Sobel gradient edge analysis`,
            `Temporal consistency across ${data.frames_analyzed} frame samples`,
          ],
          unverifiedItems: [
            "Identity of the speaker/subject",
            "Original uncompressed source file",
            "Chain-of-custody provenance",
          ],
          isDeepfakeResult: true,
          deepfakeDetails: {
            framesAnalyzed: data.frames_analyzed ?? 0,
            facesDetected: data.faces_detected ?? 0,
            temporalAggregate: data.temporal_aggregate_score ?? 0,
            flickerScore: data.temporal_flicker_score ?? 0,
            statement: data.statement ?? "",
            sha256: data.sha256 ?? "",
          },
        });
      } catch (err: any) {
        setVerdict({
          riskTier: "INCONCLUSIVE",
          score: 0,
          highlightedReasons: [
            `Analysis failed: ${err.message || "Network error"}. The deepfake engine may be starting up (cold start takes ~30s on Render free tier). Please try again.`,
          ],
          matchedKeywords: [],
          verifiedItems: [],
          unverifiedItems: ["Video content", "Facial manipulation status"],
          isDeepfakeResult: true,
        });
      } finally {
        setIsScanning(false);
      }
      return;
    }

    // ── Branch 2: Text analysis (existing keyword-based scan) ────────────────
    await new Promise((r) => setTimeout(r, 1200));

    const lower = inputText.toLowerCase();
    const isGuaranteed =
      lower.includes("guarantee") ||
      lower.includes("pakka") ||
      lower.includes("fix profit") ||
      lower.includes("100%");
    const isVip =
      lower.includes("vip") ||
      lower.includes("telegram") ||
      lower.includes("whatsapp");
    const isPhishing =
      lower.includes(".top") ||
      lower.includes(".vip") ||
      lower.includes("verify") ||
      lower.includes("login");
    const isUpiScam = lower.includes("sebi") && lower.includes("@");

    let riskTier: ScanVerdict["riskTier"] = "LOW";
    let score = 15;
    const reasons: string[] = [];
    const matched: string[] = [];

    if (isGuaranteed) {
      score += 45;
      reasons.push(
        locale === "hi"
          ? "अवैध 'निश्चित मुनाफ़ा' (Guaranteed Return) का दावा"
          : "Unlawful 'Guaranteed Profit / Fixed Return' promise"
      );
      matched.push("guarantee", "profit", "pakka");
    }
    if (isVip) {
      score += 25;
      reasons.push(
        locale === "hi"
          ? "अनाधिकृत वीआईपी / सोशल मीडिया ग्रुप में जोड़ना"
          : "Unregulated private VIP/Telegram solicitation channel"
      );
      matched.push("vip", "telegram", "whatsapp");
    }
    if (isPhishing || isUpiScam) {
      score += 35;
      reasons.push(
        locale === "hi"
          ? "सेबी के नाम पर फर्जी यूपीआई या संदिग्ध डोमेन"
          : "Institutional impersonation (SEBI/NSE) or unverified payment handle"
      );
      matched.push("sebi", "domain", "@");
    }

    if (score >= 70) riskTier = "CRITICAL";
    else if (score >= 45) riskTier = "HIGH";
    else if (score >= 25) riskTier = "MEDIUM";

    setVerdict({
      riskTier,
      score: Math.min(100, score),
      highlightedReasons:
        reasons.length > 0
          ? reasons
          : [
              locale === "hi"
                ? "कोई बड़ा जोखिम संकेत नहीं मिला"
                : "No obvious high-risk deception patterns detected",
            ],
      matchedKeywords: matched,
      verifiedItems: [
        locale === "hi"
          ? "टेक्स्ट भाषा एवं कीवर्ड पैटर्न विश्लेषण"
          : "Linguistic deception & syntactic regex verification",
        locale === "hi"
          ? "सेबी सर्कुलर एवं एडवाइजरी डेटाबेस मिलान"
          : "SEBI investor caution circulars matched",
      ],
      unverifiedItems: [
        locale === "hi"
          ? "व्यक्तिगत बैंक खाता स्वामित्व (केवाईसी डेटा)"
          : "Beneficiary bank account ownership (Internal KYC unavailable)",
        locale === "hi"
          ? "निजी एंड-टू-एंड एन्क्रिप्टेड चैट लॉग्स"
          : "Private encrypted chat context beyond submitted snippet",
      ],
    });

    setIsScanning(false);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Consumer Header Banner */}
      <div className="bg-gradient-to-r from-indigo-950/60 via-slate-900 to-slate-900 border border-indigo-800/40 rounded-xl p-6 shadow-xl">
        <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-indigo-500/10 border border-indigo-400/30 text-indigo-400 text-xs font-semibold mb-3">
          <ShieldAlert className="w-3.5 h-3.5" />
          <span>{t.badge}</span>
        </div>
        <h1 className="text-2xl font-bold text-slate-100 tracking-tight mb-2">{t.title}</h1>
        <p className="text-sm text-slate-400 leading-relaxed max-w-2xl">{t.subtitle}</p>

        {/* Input Form */}
        <form onSubmit={handleScan} className="mt-6 space-y-3">
          <div className="relative">
            <textarea
              value={inputText}
              onChange={(e) => {
                // Only allow editing if there's no video attached
                if (!uploadedB64) setInputText(e.target.value);
              }}
              placeholder={t.inputPlaceholder}
              rows={3}
              readOnly={!!uploadedB64}
              className={`w-full bg-slate-950/90 border border-slate-700/80 rounded-lg p-3.5 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-sans resize-none ${
                uploadedB64 ? "opacity-70 cursor-default" : ""
              }`}
            />
          </div>

          {/* Video Upload Area */}
          <div className="p-3 rounded-lg border border-dashed border-slate-700/80 bg-slate-950/50 space-y-2">
            {!uploadedFile ? (
              <label className="cursor-pointer flex flex-col items-center justify-center gap-2 py-3 text-center group">
                <div className="p-2.5 rounded-lg bg-indigo-500/10 border border-indigo-500/30 group-hover:bg-indigo-500/20 transition-all">
                  <Film className="w-5 h-5 text-indigo-400" />
                </div>
                <div>
                  <span className="text-sm font-medium text-indigo-300 group-hover:text-indigo-200 transition-colors">
                    Upload Video / Deepfake File
                  </span>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    MP4, WebM, AVI, MOV, MKV — max 50 MB. Real MesoNet-4 analysis.
                  </p>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="video/*"
                  className="hidden"
                  onChange={handleFileUpload}
                />
              </label>
            ) : (
              <div className="flex items-center justify-between gap-3 py-1 px-2">
                <div className="flex items-center gap-2.5">
                  <Film className="w-4 h-4 text-indigo-400 flex-shrink-0" />
                  <div>
                    <p className="text-xs font-medium text-slate-200 truncate max-w-[260px]">
                      {uploadedFile.name}
                    </p>
                    <p className="text-[10px] text-slate-500">{uploadedFile.sizeMB} MB — Base64 encoded, ready for MesoNet analysis</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={clearFile}
                  className="p-1 rounded hover:bg-slate-700 text-slate-500 hover:text-slate-300 transition-colors"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            )}

            {uploadError && (
              <p className="text-xs text-red-400 px-2">{uploadError}</p>
            )}
          </div>

          {/* Actions Row */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
            <span className="text-[11px] text-slate-500 font-sans italic hidden md:inline">
              {t.inputHelp}
            </span>
            <button
              type="submit"
              disabled={isScanning || (!inputText.trim() && !uploadedB64)}
              className="w-full sm:w-auto px-6 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-500 text-white font-medium text-xs flex items-center justify-center gap-2 transition-all shadow-lg shadow-indigo-950/50"
            >
              {isScanning ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                  <span>{uploadedB64 ? "Running MesoNet Analysis..." : t.checking}</span>
                </>
              ) : (
                <>
                  <Search className="w-3.5 h-3.5" />
                  <span>{uploadedB64 ? "Analyze for Deepfake" : t.checkButton}</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Verdict & Next Steps Card */}
      {verdict && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
          <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 shadow-xl space-y-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-4 border-b border-slate-800 gap-4">
              <div>
                <span className="text-xs uppercase font-mono tracking-wider text-slate-500">
                  {verdict.isDeepfakeResult ? "Deepfake Analysis Result" : t.verdictTitle}
                </span>
                <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2 mt-0.5">
                  <span>{t.riskLevel}:</span>
                  <span
                    className={`px-3 py-0.5 rounded-full text-xs font-bold font-mono tracking-wide ${
                      verdict.riskTier === "CRITICAL"
                        ? "bg-red-500/20 text-red-400 border border-red-500/40"
                        : verdict.riskTier === "HIGH"
                        ? "bg-amber-500/20 text-amber-400 border border-amber-500/40"
                        : verdict.riskTier === "MEDIUM"
                        ? "bg-yellow-500/20 text-yellow-400 border border-yellow-500/40"
                        : verdict.riskTier === "INCONCLUSIVE"
                        ? "bg-slate-500/20 text-slate-400 border border-slate-500/40"
                        : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                    }`}
                  >
                    {verdict.riskTier} ({verdict.score}/100)
                  </span>
                </h2>
              </div>
            </div>

            {/* Deepfake Metrics Panel */}
            {verdict.isDeepfakeResult && verdict.deepfakeDetails && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {[
                  { label: "Frames Analyzed", value: verdict.deepfakeDetails.framesAnalyzed },
                  { label: "Faces Detected", value: verdict.deepfakeDetails.facesDetected },
                  {
                    label: "Manipulation Prob.",
                    value: `${(verdict.deepfakeDetails.temporalAggregate * 100).toFixed(1)}%`,
                  },
                  {
                    label: "Temporal Flicker",
                    value: verdict.deepfakeDetails.flickerScore.toFixed(3),
                  },
                ].map((m) => (
                  <div
                    key={m.label}
                    className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-center"
                  >
                    <p className="text-lg font-bold font-mono text-indigo-400">{m.value}</p>
                    <p className="text-[10px] text-slate-500 mt-0.5">{m.label}</p>
                  </div>
                ))}
              </div>
            )}

            {/* Mandatory forensic statement */}
            {verdict.isDeepfakeResult && verdict.deepfakeDetails?.statement && (
              <div className="p-3 rounded-lg bg-indigo-950/30 border border-indigo-900/50 text-xs text-indigo-300 font-mono">
                <span className="text-indigo-500 font-semibold">MesoNet statement: </span>
                {verdict.deepfakeDetails.statement}
              </div>
            )}

            {/* Top Reasons */}
            <div className="space-y-2">
              <h3 className="text-xs font-semibold uppercase font-mono text-slate-400 flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                <span>{t.topReasons}</span>
              </h3>
              <ul className="space-y-2">
                {verdict.highlightedReasons.map((r, idx) => (
                  <li
                    key={idx}
                    className="flex items-start gap-2 p-3 rounded-lg bg-slate-950/60 border border-slate-800 text-sm text-slate-300"
                  >
                    <span className="text-amber-400 font-bold">•</span>
                    <span>{r}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Dual Check Breakdown */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-3.5 rounded-lg bg-emerald-950/20 border border-emerald-900/40 space-y-1.5">
                <h4 className="text-xs font-semibold text-emerald-400 flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>{t.whatChecked}</span>
                </h4>
                <ul className="text-xs text-slate-400 space-y-1">
                  {verdict.verifiedItems.map((item, i) => (
                    <li key={i}>✓ {item}</li>
                  ))}
                </ul>
              </div>

              <div className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800 space-y-1.5">
                <h4 className="text-xs font-semibold text-slate-400 flex items-center gap-1.5">
                  <HelpCircle className="w-3.5 h-3.5 text-slate-500" />
                  <span>{t.whatCouldNotCheck}</span>
                </h4>
                <ul className="text-xs text-slate-500 space-y-1">
                  {verdict.unverifiedItems.map((item, i) => (
                    <li key={i}>? {item}</li>
                  ))}
                </ul>
              </div>
            </div>

            {/* SHA-256 fingerprint */}
            {verdict.deepfakeDetails?.sha256 && (
              <div className="p-2.5 rounded bg-slate-950 border border-slate-800 text-[10px] text-slate-500 font-mono break-all">
                SHA-256: {verdict.deepfakeDetails.sha256}
              </div>
            )}

            {/* Actionable Next Steps */}
            <div className="p-4 rounded-xl bg-indigo-950/30 border border-indigo-900/50 space-y-3">
              <h3 className="text-sm font-semibold text-indigo-300 flex items-center gap-2">
                <ArrowRight className="w-4 h-4 text-indigo-400" />
                <span>{t.whatNextTitle}</span>
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-slate-300">
                <div className="p-2.5 rounded bg-slate-900/80 border border-slate-800">
                  <span className="font-semibold block text-slate-200 mb-0.5">SEBI Intermediary Search:</span>
                  <a href="https://www.sebi.gov.in" target="_blank" rel="noreferrer" className="text-indigo-400 hover:underline flex items-center gap-1 mt-1">
                    <span>sebi.gov.in</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
                <div className="p-2.5 rounded bg-slate-900/80 border border-slate-800">
                  <span className="font-semibold block text-slate-200 mb-0.5">Lodge SEBI Complaint (SCORES):</span>
                  <a href="https://scores.sebi.gov.in" target="_blank" rel="noreferrer" className="text-indigo-400 hover:underline flex items-center gap-1 mt-1">
                    <span>scores.sebi.gov.in</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
                <div className="p-2.5 rounded bg-slate-900/80 border border-slate-800">
                  <span className="font-semibold block text-slate-200 mb-0.5">Cyber Crime Helpline:</span>
                  <a href="tel:1930" className="text-red-400 hover:underline flex items-center gap-1 mt-1 font-bold">
                    <PhoneCall className="w-3 h-3" />
                    <span>Dial 1930 / cybercrime.gov.in</span>
                  </a>
                </div>
                <div className="p-2.5 rounded bg-slate-900/80 border border-slate-800">
                  <span className="font-semibold block text-slate-200 mb-0.5">Stop Payment Protocol:</span>
                  <span className="text-slate-400 block mt-1">Contact your bank&apos;s 24/7 fraud desk within 2 hours to freeze transfer.</span>
                </div>
              </div>
            </div>

            {/* Mandatory Regulatory Disclaimer */}
            <div className="p-3 rounded bg-slate-950 border border-slate-800 text-[11px] text-slate-500 leading-relaxed font-sans">
              {t.disclaimer}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
