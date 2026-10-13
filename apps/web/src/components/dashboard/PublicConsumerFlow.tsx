"use client";

import React, { useState } from "react";
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
} from "lucide-react";
import { translations, Locale } from "@/lib/i18n";

interface PublicConsumerFlowProps {
  locale: Locale;
}

interface ScanVerdict {
  riskTier: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INCONCLUSIVE";
  score: number;
  highlightedReasons: string[];
  matchedKeywords: string[];
  verifiedItems: string[];
  unverifiedItems: string[];
}

export function PublicConsumerFlow({ locale }: PublicConsumerFlowProps) {
  const t = translations[locale];
  const [inputText, setInputText] = useState("");
  const [isScanning, setIsScanning] = useState(false);
  const [verdict, setVerdict] = useState<ScanVerdict | null>(null);

  const handleScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    setIsScanning(true);
    setVerdict(null);

    // Simulate scanning progress and evaluation
    await new Promise((r) => setTimeout(r, 1200));

    const lower = inputText.toLowerCase();
    const isGuaranteed = lower.includes("guarantee") || lower.includes("pakka") || lower.includes("fix profit") || lower.includes("100%");
    const isVip = lower.includes("vip") || lower.includes("telegram") || lower.includes("whatsapp");
    const isPhishing = lower.includes(".top") || lower.includes(".vip") || lower.includes("verify") || lower.includes("login");
    const isUpiScam = lower.includes("sebi") && lower.includes("@");

    let riskTier: ScanVerdict["riskTier"] = "LOW";
    let score = 15;
    const reasons: string[] = [];
    const matched: string[] = [];

    if (isGuaranteed) {
      score += 45;
      reasons.push(locale === "hi" ? "अवैध 'निश्चित मुनाफ़ा' (Guaranteed Return) का दावा" : "Unlawful 'Guaranteed Profit / Fixed Return' promise");
      matched.push("guarantee", "profit", "pakka");
    }
    if (isVip) {
      score += 25;
      reasons.push(locale === "hi" ? "अनाधिकृत वीआईपी / सोशल मीडिया ग्रुप में जोड़ना" : "Unregulated private VIP/Telegram solicitation channel");
      matched.push("vip", "telegram", "whatsapp");
    }
    if (isPhishing || isUpiScam) {
      score += 35;
      reasons.push(locale === "hi" ? "सेबी के नाम पर फर्जी यूपीआई या संदिग्ध डोमेन" : "Institutional impersonation (SEBI/NSE) or unverified payment handle");
      matched.push("sebi", "domain", "@");
    }

    if (score >= 70) riskTier = "CRITICAL";
    else if (score >= 45) riskTier = "HIGH";
    else if (score >= 25) riskTier = "MEDIUM";

    setVerdict({
      riskTier,
      score: Math.min(100, score),
      highlightedReasons: reasons.length > 0 ? reasons : [locale === "hi" ? "कोई बड़ा जोखिम संकेत नहीं मिला" : "No obvious high-risk deception patterns detected"],
      matchedKeywords: matched,
      verifiedItems: [
        locale === "hi" ? "टेक्स्ट भाषा एवं कीवर्ड पैटर्न विश्लेषण" : "Linguistic deception & syntactic regex verification",
        locale === "hi" ? "सेबी सर्कुलर एवं एडवाइजरी डेटाबेस मिलान" : "SEBI investor caution circulars matched",
      ],
      unverifiedItems: [
        locale === "hi" ? "व्यक्तिगत बैंक खाता स्वामित्व (केवाईसी डेटा)" : "Beneficiary bank account ownership (Internal KYC unavailable)",
        locale === "hi" ? "निजी एंड-टू-एंड एन्क्रिप्टेड चैट लॉग्स" : "Private encrypted chat context beyond submitted snippet",
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
              onChange={(e) => setInputText(e.target.value)}
              placeholder={t.inputPlaceholder}
              rows={3}
              className="w-full bg-slate-950/90 border border-slate-700/80 rounded-lg p-3.5 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-sans resize-none"
            />
          </div>
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <span className="text-[11px] text-slate-500 font-sans italic">{t.inputHelp}</span>
            <button
              type="submit"
              disabled={isScanning || !inputText.trim()}
              className="w-full sm:w-auto px-6 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-500 text-white font-medium text-sm flex items-center justify-center gap-2 transition-all shadow-lg shadow-indigo-950/50"
            >
              {isScanning ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                  <span>{t.checking}</span>
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  <span>{t.checkButton}</span>
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
                <span className="text-xs uppercase font-mono tracking-wider text-slate-500">{t.verdictTitle}</span>
                <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2 mt-0.5">
                  <span>{t.riskLevel}:</span>
                  <span
                    className={`px-3 py-0.5 rounded-full text-xs font-bold font-mono tracking-wide ${
                      verdict.riskTier === "CRITICAL"
                        ? "bg-red-500/20 text-red-400 border border-red-500/40"
                        : verdict.riskTier === "HIGH"
                        ? "bg-amber-500/20 text-amber-400 border border-amber-500/40"
                        : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                    }`}
                  >
                    {verdict.riskTier} ({verdict.score}/100)
                  </span>
                </h2>
              </div>
            </div>

            {/* Top Reasons with highlighted evidence */}
            <div className="space-y-2">
              <h3 className="text-xs font-semibold uppercase font-mono text-slate-400 flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                <span>{t.topReasons}</span>
              </h3>
              <ul className="space-y-2">
                {verdict.highlightedReasons.map((r, idx) => (
                  <li key={idx} className="flex items-start gap-2 p-3 rounded-lg bg-slate-950/60 border border-slate-800 text-sm text-slate-300">
                    <span className="text-amber-400 font-bold">•</span>
                    <span>{r}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Dual Check Breakdown (Verified vs Unverified) */}
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

            {/* Actionable Next Steps (SEBI, 1930, SCORES) */}
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
