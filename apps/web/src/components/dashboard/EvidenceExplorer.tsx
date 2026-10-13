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
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-4">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <FileText className="w-4 h-4 text-indigo-400" />
            Multimodal Evidence Vault Explorer
          </h3>
          <p className="text-[11px] text-slate-400">
            Immutable SHA-256 hashed evidence items ingested into the investigation.
          </p>
        </div>

        {onUploadClick && (
          <button
            onClick={onUploadClick}
            className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition-all flex items-center gap-1.5"
          >
            + Upload New Evidence
          </button>
        )}
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-1 bg-slate-950 border border-slate-800 rounded-lg p-0.5 text-[11px]">
          {["ALL", "TEXT", "URL", "IMAGE", "VIDEO", "APK"].map((t) => (
            <button
              key={t}
              onClick={() => setSelectedType(t)}
              className={`px-2.5 py-1 rounded ${
                selectedType === t ? "bg-indigo-600 text-white font-medium" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {t}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-64">
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-2.5" />
          <input
            type="text"
            placeholder="Search payload or findings..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
        </div>
      </div>

      {/* Grid of Evidence Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {filtered.map((item) => {
          const Icon = ICONS[item.type] || FileText;
          return (
            <div
              key={item.id}
              className="p-3.5 rounded-lg bg-slate-950 border border-slate-800 hover:border-slate-700 transition-all flex flex-col justify-between space-y-3"
            >
              <div className="space-y-2">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <div className="p-1.5 rounded bg-indigo-950/70 border border-indigo-800/60 text-indigo-400">
                      <Icon className="w-4 h-4" />
                    </div>
                    <div>
                      <h4 className="text-xs font-semibold text-slate-200 truncate">{item.title}</h4>
                      <span className="text-[10px] text-slate-500 font-mono uppercase">{item.type}</span>
                    </div>
                  </div>
                  {item.confidence && (
                    <span className="text-[10px] font-mono text-indigo-400 bg-indigo-950/60 border border-indigo-900 px-1.5 py-0.5 rounded">
                      {(item.confidence * 100).toFixed(0)}%
                    </span>
                  )}
                </div>

                <div className="p-2 rounded bg-slate-900/80 border border-slate-800/80 text-[11px] font-mono text-slate-300 break-all line-clamp-3">
                  {item.payload}
                </div>

                <div className="text-[11px] text-slate-400 leading-relaxed bg-slate-900/40 p-2 rounded border border-slate-800/40">
                  <span className="text-amber-400 font-medium">Findings: </span>
                  {item.findings}
                </div>
              </div>

              <div className="space-y-2 pt-2 border-t border-slate-800/80 text-[10px]">
                {item.sha256 && (
                  <div className="flex items-center gap-1 text-slate-500 font-mono truncate" title={item.sha256}>
                    <Hash className="w-3 h-3 flex-shrink-0" />
                    <span className="truncate">{item.sha256.slice(0, 18)}...</span>
                  </div>
                )}

                <div className="flex flex-wrap gap-1">
                  {item.tags.map((tag) => (
                    <span
                      key={tag}
                      className="px-1.5 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800 text-[9px] font-mono"
                    >
                      #{tag}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
