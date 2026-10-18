"use client";

import React, { useState } from "react";
import {
  FileText,
  Image as ImageIcon,
  Video,
  Mic,
  Globe,
  FileCode,
  Tag,
  Hash,
  ExternalLink,
  ShieldAlert,
  Search,
} from "lucide-react";

export interface EvidenceCardItem {
  id: string;
  type: "text" | "image" | "video" | "audio" | "url" | "apk";
  title: string;
  payload: string;
  source: string;
  sha256?: string;
  tags: string[];
  analyzed: boolean;
  findings: string;
  confidence?: number;
}

const SAMPLE_EVIDENCE: EvidenceCardItem[] = [
  {
    id: "ev_01",
    type: "text",
    title: "Solicitation Message Text",
    payload: "Guaranteed 40% monthly returns on crypto mining pools. DM admin for VIP access slot.",
    source: "WhatsApp Group 'Elite Wealth Signals'",
    sha256: "8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4",
    tags: ["solicitation", "guaranteed_return"],
    analyzed: true,
    findings: "Flagged +15 for guaranteed return claim under SEBI Circular SEBI/HO/MIRSD/2023.",
    confidence: 0.95,
  },
  {
    id: "ev_02",
    type: "url",
    title: "Broker Registration Link",
    payload: "https://apex-quantum-returns.fake/signup?ref=vip99",
    source: "Telegram Broadcast Message",
    sha256: "3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    tags: ["phishing", "domain_mismatch"],
    analyzed: true,
    findings: "Domain mismatch: claims SEBI intermediary status but whois created 4 days ago with privacy guard.",
    confidence: 0.88,
  },
  {
    id: "ev_03",
    type: "image",
    title: "Forged SEBI Registration Certificate",
    payload: "sebi_cert_forgery_scan.png",
    source: "Investigator Upload",
    sha256: "a1b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef0",
    tags: ["forgery", "fake_certificate"],
    analyzed: true,
    findings: "OCR extracted invalid registration string INZ0000000; signature font inconsistent with gazette.",
    confidence: 0.91,
  },
  {
    id: "ev_04",
    type: "video",
    title: "Deepfake Celebrity Endorsement",
    payload: "invest_now_ceo_video.mp4",
    source: "Instagram Sponsored Reel",
    sha256: "ef23456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
    tags: ["deepfake", "synthetic_media"],
    analyzed: true,
    findings: "Lip-sync anomaly detected with MesoNet classifier; audio pitch altered.",
    confidence: 0.84,
  },
  {
    id: "ev_05",
    type: "apk",
    title: "Trading App APK Package",
    payload: "ApexTrader_v1.04.apk",
    source: "Direct Link from Phishing Landing Page",
    sha256: "c5d6e7f8091a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c",
    tags: ["apk_malware", "sms_stealer"],
    analyzed: true,
    findings: "Static decompilation identified READ_SMS and SYSTEM_ALERT_WINDOW permissions without play protect.",
    confidence: 0.97,
  },
];

const ICONS = {
  text: FileText,
  url: Globe,
  image: ImageIcon,
  video: Video,
  audio: Mic,
  apk: FileCode,
};

export function EvidenceExplorer({
  items = SAMPLE_EVIDENCE,
  onUploadClick,
}: {
  items?: EvidenceCardItem[];
  onUploadClick?: () => void;
}) {
  const [selectedType, setSelectedType] = useState<string>("ALL");
  const [search, setSearch] = useState("");

  const filtered = items.filter((item) => {
    const matchesType = selectedType === "ALL" || item.type.toUpperCase() === selectedType;
    const matchesSearch =
      item.title.toLowerCase().includes(search.toLowerCase()) ||
      item.payload.toLowerCase().includes(search.toLowerCase()) ||
      item.findings.toLowerCase().includes(search.toLowerCase());
    return matchesType && matchesSearch;
  });

  return (
    <div className="rounded-2xl border border-[#E7E3D8] bg-white p-6 space-y-5 shadow-sm animate-fade-in">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-stone-200 pb-4">
        <div>
          <h3 className="text-base font-bold text-stone-900 flex items-center gap-2">
            <div className="p-2 rounded-xl bg-orange-100 text-orange-600 border border-orange-200">
              <FileText className="w-5 h-5" />
            </div>
            Multimodal Evidence Vault Explorer
          </h3>
          <p className="text-xs text-stone-600 mt-1">
            Immutable SHA-256 hashed evidence items ingested into the investigation.
          </p>
        </div>

        {onUploadClick && (
          <button
            onClick={onUploadClick}
            className="px-4 py-2.5 rounded-xl text-xs font-bold bg-gradient-to-r from-orange-500 to-amber-600 hover:from-orange-600 hover:to-amber-700 text-white transition-all duration-200 flex items-center gap-1.5 shadow-sm"
          >
            + Upload New Evidence
          </button>
        )}
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-1 bg-stone-100 border border-stone-200 rounded-xl p-0.5 text-xs">
          {["ALL", "TEXT", "URL", "IMAGE", "VIDEO", "APK"].map((t) => (
            <button
              key={t}
              onClick={() => setSelectedType(t)}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all duration-200 ${
                selectedType === t ? "bg-orange-500 text-white shadow-sm" : "text-stone-600 hover:text-stone-900"
              }`}
            >
              {t}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-stone-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search payload or findings..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-[#FAF7F2] border border-stone-300 rounded-xl pl-9 pr-3 py-2 text-xs text-stone-900 placeholder-stone-400 focus:outline-none focus:border-orange-500 transition-all duration-200"
          />
        </div>
      </div>

      {/* Grid of Evidence Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((item, cardIdx) => {
          const Icon = ICONS[item.type] || FileText;
          return (
            <div
              key={item.id}
              className="p-5 rounded-2xl bg-[#FAF7F2] border border-[#E7E3D8] hover:border-orange-300 transition-all duration-300 flex flex-col justify-between space-y-3 card-hover shadow-sm animate-fade-in"
              style={{ animationDelay: `${cardIdx * 0.06}s` }}
            >
              <div className="space-y-2.5">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <div className="p-2 rounded-xl bg-orange-100 border border-orange-200 text-orange-600">
                      <Icon className="w-4 h-4" />
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-stone-900 truncate">{item.title}</h4>
                      <span className="text-[10px] text-stone-500 font-mono uppercase">{item.type}</span>
                    </div>
                  </div>
                  {item.confidence && (
                    <span className="text-[11px] font-mono font-bold text-orange-800 bg-orange-100 border border-orange-200 px-2 py-0.5 rounded-lg">
                      {(item.confidence * 100).toFixed(0)}%
                    </span>
                  )}
                </div>

                <div className="p-3 rounded-xl bg-white border border-stone-200 text-xs font-mono text-stone-800 break-all line-clamp-3 shadow-sm">
                  {item.payload}
                </div>

                <div className="text-xs text-stone-700 leading-relaxed bg-white p-3 rounded-xl border border-stone-200 shadow-sm">
                  <span className="text-orange-700 font-bold">Findings: </span>
                  {item.findings}
                </div>

                {item.type === "video" && (
                  <div className="p-2.5 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-900 leading-tight">
                    <span className="font-bold block mb-0.5">⚠️ LOW-CONFIDENCE SCREENING SIGNAL</span>
                    MesoNet provides an exploratory facial artifact screening heuristic, not conclusive forensic proof.
                  </div>
                )}
              </div>

              <div className="pt-2 border-t border-stone-200 flex items-center justify-between text-[11px] text-stone-500">
                <span>Source: {item.source}</span>
                <span className="font-mono text-orange-700 font-medium">{item.tags?.join(", ")}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
