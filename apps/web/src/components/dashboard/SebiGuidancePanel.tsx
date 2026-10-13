"use client";

import React from "react";
import { BookOpen, ExternalLink, AlertTriangle, ShieldCheck, FileCheck } from "lucide-react";

export interface SebiGuidanceItem {
  id: string;
  circularNo: string;
  title: string;
  summary: string;
  violationType: string;
  matchedClaim: string;
  officialSourceUrl: string;
}

const SAMPLE_GUIDANCE: SebiGuidanceItem[] = [
  {
    id: "sebi_01",
    circularNo: "SEBI/HO/MIRSD/MIRSD-PoD-1/P/CIR/2023/123",
    title: "Prohibition of Assured/Guaranteed Returns in Securities Market",
    summary:
      "Registered intermediaries and uncertified individuals are strictly prohibited from promising or offering guaranteed or fixed returns on equities, derivatives, or algorithmic trading.",
    violationType: "Guaranteed Return Prohibition",
    matchedClaim: "'Guaranteed 40% monthly returns on VIP crypto pool'",
    officialSourceUrl: "https://www.sebi.gov.in/legal/circulars/aug-2023/prohibition-of-assured-returns_75200.html",
  },
  {
    id: "sebi_02",
    circularNo: "SEBI/HO/ISD/ISD-PoD-2/P/CIR/2024/45",
    title: "Advisory Against Dealing with Unregistered Financial Influencers & Platforms",
    summary:
      "Public notice cautioning investors against unauthorized entities soliciting investments through social messaging apps (WhatsApp, Telegram, Instagram) and collecting money via personal UPI handles.",
    violationType: "Unregistered Solicitation via Social Channels",
    matchedClaim: "'Join VIP Telegram group and send payment to apexinvest@icici'",
    officialSourceUrl: "https://www.sebi.gov.in/enforcement/clarifications-on-sebi-regulations/mar-2024/advisory-against-unregistered-entities.html",
  },
  {
    id: "sebi_03",
    circularNo: "SEBI (Research Analysts) Regulations, 2014 - Reg 3",
    title: "Mandatory Registration Requirement for Research Analysts",
    summary:
      "No person shall act as a research analyst or provide recommendation services without obtaining a certificate of registration from the Board under these regulations.",
    violationType: "Unregistered Advisory Operation",
    matchedClaim: "'SEBI Registered Senior Analyst Rajesh Kumar'",
    officialSourceUrl: "https://www.sebi.gov.in/legal/regulations/sep-2014/securities-and-exchange-board-of-india-research-analysts-regulations-2014_28108.html",
  },
];

export function SebiGuidancePanel({
  guidanceMatches = SAMPLE_GUIDANCE,
}: {
  guidanceMatches?: SebiGuidanceItem[];
}) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-indigo-400" />
          <h3 className="text-sm font-semibold text-slate-100">SEBI Regulatory Guidance &amp; Circular Matches</h3>
        </div>
        <span className="text-[11px] font-mono text-slate-500">
          pgvector RAG Citations ({guidanceMatches.length} Matches)
        </span>
      </div>

      <div className="space-y-3">
        {guidanceMatches.map((item) => (
          <div
            key={item.id}
            className="p-3.5 rounded-lg bg-slate-950 border border-slate-800 space-y-2.5 text-xs"
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <span className="font-mono text-indigo-400 font-semibold text-[11px]">
                {item.circularNo}
              </span>
              <span className="px-2 py-0.5 rounded bg-rose-950/70 border border-rose-800/60 text-rose-300 font-mono text-[10px] self-start sm:self-auto">
                {item.violationType}
              </span>
            </div>

            <h4 className="font-semibold text-slate-200 text-xs">{item.title}</h4>

            <p className="text-slate-400 text-[11px] leading-relaxed">{item.summary}</p>

            <div className="p-2 rounded bg-slate-900 border border-slate-800/80 text-[11px] text-slate-300">
              <span className="text-amber-400 font-medium">Matched Suspect Claim: </span>
              <span className="italic font-serif">{item.matchedClaim}</span>
            </div>

            <div className="pt-1 flex items-center justify-between text-[11px]">
              <span className="text-slate-500 font-mono">SEBI Official Gazetted Rule</span>
              <a
                href={item.officialSourceUrl}
                target="_blank"
                rel="noreferrer"
                className="text-indigo-400 hover:text-indigo-300 flex items-center gap-1 font-medium"
              >
                <span>Read Official Circular</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
