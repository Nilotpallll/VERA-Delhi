"use client";

import React, { useState } from "react";
import { BookOpen, ExternalLink, ShieldCheck, ChevronDown } from "lucide-react";

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
  {
    id: "sebi_04",
    circularNo: "SEBI/HO/MIRSD/DOS3/CIR/P/2018/115",
    title: "Advisory on Fake Trading Portals & Stock Recommendation Groups",
    summary:
      "Investors must only execute trades through verified SEBI-registered broker portals. Never transfer investment funds to personal or unauthorized institutional escrow accounts.",
    violationType: "Phishing & Fake Broker App",
    matchedClaim: "'Verify your trading account immediately at sebi-verification.top'",
    officialSourceUrl: "https://www.sebi.gov.in",
  },
];

export function SebiGuidancePanel({
  guidanceMatches = SAMPLE_GUIDANCE,
}: {
  guidanceMatches?: SebiGuidanceItem[];
}) {
  const [expandedId, setExpandedId] = useState<string | null>("sebi_01");

  const toggleExpand = (id: string) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  return (
    <div className="w-full">
      {/* 2-Column Bento Grid of Rule Cards (radius 24, accordion expand) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {guidanceMatches.map((item, idx) => {
          const isExpanded = expandedId === item.id;
          return (
            <div
              key={item.id}
              className="vera-glass rounded-[24px] p-6 text-left flex flex-col justify-between transition-all duration-200"
            >
              <div>
                {/* Header Row */}
                <div className="flex items-center justify-between gap-2 mb-3">
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded-full bg-[var(--nav-track)] border border-[var(--border)] font-mono-tabular text-xs font-bold flex items-center justify-center text-[var(--text-primary)]">
                      {idx + 1}
                    </span>
                    <span className="font-mono-tabular text-xs text-[var(--text-muted)] font-medium truncate max-w-[200px]">
                      {item.circularNo}
                    </span>
                  </div>
                  <span className="vera-flag-badge px-2.5 py-0.5 rounded-full text-[11px] font-mono-tabular font-semibold border">
                    {item.violationType}
                  </span>
                </div>

                {/* Title */}
                <h3 className="text-base font-semibold text-[var(--text-primary)] tracking-tight leading-snug">
                  {item.title}
                </h3>

                {/* Summary / Accordion content */}
                <p className="mt-2 text-sm text-[var(--text-muted)] leading-relaxed">
                  {item.summary}
                </p>

                {/* Expandable Claim Details */}
                {isExpanded && (
                  <div className="mt-4 pt-4 border-t border-[var(--border)] space-y-3">
                    <div className="p-3 rounded-2xl bg-[var(--nav-track)] border border-[var(--border)] text-xs text-[var(--text-primary)]">
                      <span className="font-semibold block text-[var(--text-muted)] mb-1">
                        Flagged Claim Pattern:
                      </span>
                      <span className="italic font-mono-tabular">&ldquo;{item.matchedClaim}&rdquo;</span>
                    </div>

                    <div className="flex items-center justify-between text-xs pt-1">
                      <span className="flex items-center gap-1.5 text-[var(--verdict-safe)] font-medium">
                        <ShieldCheck className="w-4 h-4" />
                        <span>SEBI Enforcement Standard</span>
                      </span>
                      <a
                        href={item.officialSourceUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="font-semibold text-[var(--navy-1)] dark:text-[var(--accent)] hover:underline inline-flex items-center gap-1"
                      >
                        <span>Official Circular</span>
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    </div>
                  </div>
                )}
              </div>

              {/* Bottom Expand Toggle Bar */}
              <button
                type="button"
                onClick={() => toggleExpand(item.id)}
                className="mt-4 pt-3 border-t border-[var(--border)] w-full flex items-center justify-between text-xs font-semibold text-[var(--text-muted)] hover:text-[var(--text-primary)]"
              >
                <span>{isExpanded ? "Collapse Details" : "Expand Legal Citation"}</span>
                <ChevronDown
                  className={`w-4 h-4 transition-transform duration-200 ${
                    isExpanded ? "rotate-180" : ""
                  }`}
                />
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
