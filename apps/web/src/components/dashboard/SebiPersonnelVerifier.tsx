"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  UserCheck,
  ExternalLink,
  Copy,
  Check,
  PhoneCall,
  Hash,
  User,
} from "lucide-react";
import { Locale } from "@/lib/i18n";

export interface SebiPersonnelVerifierProps {
  locale?: Locale;
  className?: string;
}

export interface RegistryRecordItem {
  registrationNumber: string;
  entityName: string;
  contactPerson: string;
  intermediaryType: string;
  validFrom: string;
  validTo: string;
}

export interface VerificationResultState {
  state: "FOUND" | "AMBIGUOUS" | "NOT_FOUND" | "NAME_NOT_FOUND" | "OUT_OF_SCOPE" | "UNAVAILABLE";
  coveredType?: string;
  asOf?: string;
  lookupBy?: string;
  nameMatchStatus?: "MATCHED" | "MISMATCH" | "NOT_CHECKED";
  records?: RegistryRecordItem[];
  queriedName?: string;
  queriedRegistration?: string;
}

export function SebiPersonnelVerifier({ locale = "en", className = "" }: SebiPersonnelVerifierProps) {
  const isHi = locale === "hi";

  // Form input states
  const [personnelName, setPersonnelName] = useState("");
  const [inaNumber, setInaNumber] = useState("");
  const [isVerifying, setIsVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState<VerificationResultState | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [registryStats, setRegistryStats] = useState<{ total: number; asOf: string } | null>(null);

  // Fetch live stats on mount
  useEffect(() => {
    fetch("/api/registry/sebi?action=roles")
      .then((r) => r.json())
      .then((data) => {
        if (data.state === "OK" && data.totalRecords) {
          setRegistryStats({ total: data.totalRecords, asOf: data.asOf || "2026-10-18" });
        }
      })
      .catch(() => {});
  }, []);

  // Handle Verify Execution
  const handleVerify = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const cleanReg = inaNumber.trim().toUpperCase().replace(/[\s-]/g, "");
    const cleanName = personnelName.trim();

    if (!cleanReg && !cleanName) return;

    setIsVerifying(true);
    try {
      const params = new URLSearchParams();
      if (cleanReg) params.set("registrationNumber", cleanReg);
      if (cleanName) params.set("name", cleanName);

      const res = await fetch(`/api/registry/sebi?${params.toString()}`);
      const data = await res.json();

      setVerificationResult({
        ...data,
        queriedName: cleanName,
        queriedRegistration: cleanReg,
      });
    } catch {
      setVerificationResult({
        state: "UNAVAILABLE",
        queriedName: cleanName,
        queriedRegistration: cleanReg,
      });
    } finally {
      setIsVerifying(false);
    }
  };

  // Quick Preset Sample Fillers
  const handleSelectSample = (sampleName: string, sampleReg: string) => {
    setPersonnelName(sampleName);
    setInaNumber(sampleReg);
    setVerificationResult(null);
  };

  const copyToClipboard = (text: string) => {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(text);
      setCopiedId(text);
      setTimeout(() => setCopiedId(null), 2000);
    }
  };

  // Compute Risk / Integrity Tier from Verification Result
  const getIntegrityVerdict = () => {
    if (!verificationResult) return null;

    const { state, nameMatchStatus } = verificationResult;

    // Case 1: Verified Authentic
    if (state === "FOUND" && (nameMatchStatus === "MATCHED" || nameMatchStatus === "NOT_CHECKED")) {
      return {
        tier: "SAFE",
        badge: isHi ? "सेबी पंजीकृत एवं प्रामाणिक" : "SEBI REGISTERED & AUTHENTIC",
        score: 0,
        riskLabel: isHi ? "न्यूनतम जोखिम (0/100)" : "MINIMAL RISK (0/100)",
        summary: isHi
          ? "यह मध्यस्थ आधिकारिक सेबी मास्टर डायरेक्टरी में वैध रूप से पंजीकृत है।"
          : "Active regulatory credentials verified against official SEBI Intermediary Registry records.",
      };
    }

    // Case 2: License Impersonation / Name Mismatch Risk
    if (state === "FOUND" && nameMatchStatus === "MISMATCH") {
      return {
        tier: "CRITICAL",
        badge: isHi ? "पहचान बेमेल चेतावनी" : "LICENSE IMPERSONATION DETECTED",
        score: 96,
        riskLabel: isHi ? "गंभीर जोखिम (96/100)" : "CRITICAL RISK (96/100)",
        summary: isHi
          ? "पंजीकरण संख्या मौजूद है, लेकिन यह पंजीकृत नाम से मेल नहीं खाती। यह नंबर चोरी या धोखाधड़ी का गंभीर संकेत है!"
          : "The registration number exists in SEBI records, but belongs to a different registered entity/individual. High risk of license spoofing!",
      };
    }

    // Case 3: Ambiguous multiple records found
    if (state === "AMBIGUOUS") {
      return {
        tier: "SUSPICIOUS",
        badge: isHi ? "एकाधिक रिकॉर्ड - विशिष्ट पहचान आवश्यक" : "MULTIPLE MATCHES FOUND",
        score: 45,
        riskLabel: isHi ? "सावधानी (45/100)" : "CAUTION (45/100)",
        summary: isHi
          ? "इस नाम से एक से अधिक पंजीकृत मध्यस्थ पाए गए। कृपया सही पहचान के लिए INA/INH संख्या दर्ज करें।"
          : "Multiple entities found with this name. Cross-verify with the specific registration number.",
      };
    }

    // Case 4: Unverified / Not Found
    return {
      tier: "HIGH_RISK",
      badge: isHi ? "गैर-पंजीकृत सलाहकार अलर्ट" : "UNVERIFIED / REGULATORY RED FLAG",
      score: 92,
      riskLabel: isHi ? "उच्च जोखिम (92/100)" : "HIGH RISK (92/100)",
      summary: isHi
        ? "सेबी के आधिकारिक रिकॉर्ड में इस नाम या पंजीकरण संख्या का कोई वैध रिकॉर्ड नहीं मिला।"
        : "No active regulatory record found in the SEBI Master Directory for these credentials.",
    };
  };

  const verdict = getIntegrityVerdict();

  return (
    <div
      className={`vera-composer text-left relative z-10 w-full max-w-[760px] mx-auto transition-all duration-200 mt-8 mb-6 ${className}`}
      id="vera-sebi-verifier"
    >
      {/* ── TOP HEADER ROW ─────────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 mb-5 pb-4 border-b border-[var(--border)]">
        <div className="flex items-start gap-3.5">
          <div className="w-10 h-10 rounded-2xl bg-[var(--nav-track)] border border-[var(--border)] flex items-center justify-center text-[var(--text-primary)] flex-shrink-0 shadow-sm">
            <UserCheck className="w-5 h-5 text-[var(--text-primary)]" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-[var(--text-primary)] tracking-tight">
              {isHi ? "सेबी कार्मिक एवं मध्यस्थ सत्यापन" : "SEBI Personnel & Entity Verification"}
            </h2>
            <p className="text-sm text-[var(--text-muted)] font-normal mt-0.5 leading-relaxed">
              {isHi
                ? "जाँचें कि क्या कोई व्यक्ति या संस्था सेबी पंजीकृत सलाहकार (INA) या मध्यस्थ है।"
                : "Verify whether an individual advisor or firm holds a genuine SEBI license before trusting advice or transferring capital."}
            </p>
          </div>
        </div>

        {/* Records Count Badge - matching neutral palette */}
        <div className="self-start sm:self-auto flex items-center gap-1.5 px-3 py-1 rounded-full bg-[var(--nav-track)] border border-[var(--border)] text-[var(--text-muted)] text-xs font-mono-tabular font-medium">
          <span className="w-1.5 h-1.5 rounded-full bg-[var(--text-muted)] opacity-60" />
          <span>{registryStats ? `${registryStats.total.toLocaleString()} Active SEBI Records` : "3,760 Active SEBI Records"}</span>
        </div>
      </div>

      {/* ── SIMPLE PERSONNEL VERIFICATION FORM ──────────────────────────────── */}
      <form onSubmit={handleVerify} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
          {/* Input 1: Claimed Personnel / Entity Name */}
          <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-solid)]/70 p-3.5">
            <label className="block text-xs font-semibold text-[var(--text-primary)] mb-1.5">
              {isHi ? "सलाहकार या संस्था का नाम" : "Personnel or Entity Name"}
            </label>
            <input
              type="text"
              value={personnelName}
              onChange={(e) => setPersonnelName(e.target.value)}
              placeholder={isHi ? "उदा. Kavitha Menon, Anand Rathi" : "Enter name, e.g. Kavitha Menon"}
              className="w-full rounded-xl px-3.5 py-2.5 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-subtle)] bg-[var(--input-bg)] border border-[var(--input-border)] focus:outline-none focus:ring-1 focus:ring-[var(--border)] focus:border-[var(--text-muted)] transition-all"
            />
            <p className="text-[11px] text-[var(--text-muted)] mt-1.5">
              {isHi ? "वैकल्पिक यदि INA संख्या ज्ञात है" : "Optional if registration number is provided"}
            </p>
          </div>

          {/* Input 2: SEBI Registration / INA Number */}
          <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-solid)]/70 p-3.5">
            <label className="block text-xs font-semibold text-[var(--text-primary)] mb-1.5">
              {isHi ? "सेबी पंजीकरण संख्या (INA / INH / INP / INZ)" : "SEBI Registration Number"}
            </label>
            <input
              type="text"
              value={inaNumber}
              onChange={(e) => setInaNumber(e.target.value.toUpperCase())}
              placeholder="e.g. INA000000037, INH000012345"
              className="w-full rounded-xl px-3.5 py-2.5 text-sm font-mono-tabular uppercase text-[var(--text-primary)] placeholder:text-[var(--text-subtle)] bg-[var(--input-bg)] border border-[var(--input-border)] focus:outline-none focus:ring-1 focus:ring-[var(--border)] focus:border-[var(--text-muted)] transition-all"
            />
            <p className="text-[11px] text-[var(--text-muted)] mt-1.5">
              {isHi ? "सेबी का 9-अंकीय कोड (उदा. INA000000037)" : "SEBI 9-digit registration code"}
            </p>
          </div>
        </div>

        {/* Quick Demo Preset Chips - neutral palette matching the above module */}
        <div className="flex items-center gap-2 flex-wrap pt-1">
          <span className="text-[11px] font-mono-tabular text-[var(--text-muted)]">
            {isHi ? "त्वरित उदाहरण:" : "Examples:"}
          </span>
          <button
            type="button"
            onClick={() => handleSelectSample("Kavitha Menon", "INA000000037")}
            className="px-3 py-1 rounded-full text-xs font-medium bg-[var(--nav-track)] hover:bg-[var(--surface-solid)] text-[var(--text-muted)] hover:text-[var(--text-primary)] border border-[var(--border)] transition-all cursor-pointer shadow-xs active:scale-95"
          >
            Kavitha Menon (INA000000037)
          </button>
          <button
            type="button"
            onClick={() => handleSelectSample("Anand Rathi", "INH000012345")}
            className="px-3 py-1 rounded-full text-xs font-medium bg-[var(--nav-track)] hover:bg-[var(--surface-solid)] text-[var(--text-muted)] hover:text-[var(--text-primary)] border border-[var(--border)] transition-all cursor-pointer shadow-xs active:scale-95"
          >
            Anand Rathi (INH000012345)
          </button>
          <button
            type="button"
            onClick={() => handleSelectSample("Vikram Crypto Guru", "INA000000037")}
            className="px-3 py-1 rounded-full text-xs font-medium bg-[var(--nav-track)] hover:bg-[var(--surface-solid)] text-[var(--text-muted)] hover:text-[var(--text-primary)] border border-[var(--border)] transition-all cursor-pointer shadow-xs active:scale-95"
            title="Real INA claimed by fake personnel name to demonstrate spoof detection"
          >
            Mismatched Name (Spoof Test)
          </button>
          <button
            type="button"
            onClick={() => handleSelectSample("Rajesh Fictitious", "INA999999999")}
            className="px-3 py-1 rounded-full text-xs font-medium bg-[var(--nav-track)] hover:bg-[var(--surface-solid)] text-[var(--text-muted)] hover:text-[var(--text-primary)] border border-[var(--border)] transition-all cursor-pointer shadow-xs active:scale-95"
          >
            Fake INA999999999
          </button>
        </div>

        {/* Submit & Reset Bar */}
        <div className="flex items-center justify-between pt-4 border-t border-[var(--border)]">
          <div>
            {verificationResult && (
              <button
                type="button"
                onClick={() => {
                  setVerificationResult(null);
                  setPersonnelName("");
                  setInaNumber("");
                }}
                className="text-xs font-semibold text-[var(--text-muted)] hover:text-[var(--text-primary)] cursor-pointer"
              >
                {isHi ? "साफ़ करें" : "Clear Query"}
              </button>
            )}
          </div>

          <button
            type="submit"
            disabled={isVerifying || (!personnelName.trim() && !inaNumber.trim())}
            className={`vera-btn-primary ${isVerifying ? "is-scanning" : ""}`}
          >
            {isVerifying ? (
              <span className="flex items-center gap-2">
                <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                <span>{isHi ? "सत्यापित किया जा रहा है..." : "Verifying with SEBI Registry..."}</span>
              </span>
            ) : (
              <span>{isHi ? "सेबी पंजीकरण सत्यापित करें" : "Verify SEBI Personnel"} &rarr;</span>
            )}
          </button>
        </div>
      </form>

      {/* ── VERIFICATION RESULT STATE (Cohesive Neutral VERA Theme) ─────────── */}
      {verificationResult && verdict && (
        <div className="mt-6 pt-6 border-t border-[var(--border)] animate-fade-in space-y-4 text-left">
          {/* Main Verdict Banner - Neutral Glass Theme */}
          <div className="rounded-2xl p-5 border border-[var(--border)] bg-[var(--surface-solid)]/70 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-start gap-3.5">
              <div className="w-10 h-10 rounded-2xl bg-[var(--nav-track)] border border-[var(--border)] flex items-center justify-center flex-shrink-0 text-[var(--text-primary)] shadow-sm">
                {verdict.tier === "SAFE" ? (
                  <ShieldCheck className="w-5 h-5 text-[var(--text-primary)]" />
                ) : verdict.tier === "CRITICAL" || verdict.tier === "HIGH_RISK" ? (
                  <ShieldAlert className="w-5 h-5 text-[var(--text-primary)]" />
                ) : (
                  <AlertTriangle className="w-5 h-5 text-[var(--text-primary)]" />
                )}
              </div>
              <div>
                <span className="text-[11px] font-mono-tabular font-bold uppercase tracking-wider text-[var(--text-muted)] block">
                  {verdict.badge}
                </span>
                <h3 className="text-base font-bold tracking-tight mt-0.5 text-[var(--text-primary)]">
                  {verdict.riskLabel}
                </h3>
                <p className="text-xs text-[var(--text-muted)] mt-1 max-w-xl leading-relaxed">
                  {verdict.summary}
                </p>
              </div>
            </div>

            {/* Score Pill */}
            <div className="self-end sm:self-center flex flex-col items-end flex-shrink-0">
              <span className="text-2xl font-extrabold font-mono-tabular text-[var(--text-primary)]">
                {verdict.score}/100
              </span>
              <span className="text-[10px] text-[var(--text-muted)] font-mono uppercase tracking-wider">
                {isHi ? "जोखिम सूचकांक" : "Risk Score"}
              </span>
            </div>
          </div>

          {/* Records Display Card */}
          {verificationResult.records && verificationResult.records.length > 0 ? (
            <div className="space-y-3">
              <h4 className="text-xs font-mono uppercase font-bold text-[var(--text-muted)] tracking-wider">
                {isHi ? "आधिकारिक सेबी रिकॉर्ड विवरण" : "OFFICIAL SEBI DIRECTORY MATCH"}
              </h4>

              {verificationResult.records.map((rec, idx) => (
                <div
                  key={idx}
                  className="rounded-2xl border border-[var(--border)] bg-[var(--surface-solid)]/70 p-4 sm:p-5 space-y-3 shadow-xs"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[var(--border)] pb-3">
                    <div>
                      <span className="text-[11px] font-mono uppercase tracking-wider text-[var(--text-muted)] block">
                        {rec.intermediaryType || "SEBI Intermediary"}
                      </span>
                      <h5 className="text-base font-bold text-[var(--text-primary)]">
                        {rec.entityName}
                      </h5>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="font-mono-tabular font-bold text-sm px-3 py-1 rounded-full bg-[var(--nav-track)] border border-[var(--border)] text-[var(--text-primary)]">
                        {rec.registrationNumber}
                      </span>
                      <button
                        type="button"
                        onClick={() => copyToClipboard(rec.registrationNumber)}
                        className="p-1.5 rounded-lg border border-[var(--border)] hover:bg-[var(--nav-track)] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors cursor-pointer"
                        title="Copy Registration Number"
                      >
                        {copiedId === rec.registrationNumber ? (
                          <Check className="w-3.5 h-3.5 text-[var(--text-primary)]" />
                        ) : (
                          <Copy className="w-3.5 h-3.5" />
                        )}
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                    <div>
                      <span className="text-[11px] text-[var(--text-muted)] block">
                        {isHi ? "नामित संपर्क व्यक्ति" : "Principal Contact Person"}:
                      </span>
                      <strong className="text-[var(--text-primary)] font-semibold">
                        {rec.contactPerson || "Not Listed"}
                      </strong>
                    </div>

                    <div>
                      <span className="text-[11px] text-[var(--text-muted)] block">
                        {isHi ? "पंजीकरण वैधता अवधि" : "Registration Validity"}:
                      </span>
                      <strong className="text-[var(--text-primary)] font-mono-tabular">
                        {rec.validFrom} &rarr; {rec.validTo || "Perpetual"}
                      </strong>
                    </div>

                    <div>
                      <span className="text-[11px] text-[var(--text-muted)] block">
                        {isHi ? "नाम मिलान स्थिति" : "Identity Verification"}:
                      </span>
                      {verificationResult.nameMatchStatus === "MATCHED" ? (
                        <span className="text-[var(--text-primary)] font-semibold flex items-center gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          {isHi ? "नाम सत्यापित" : "Name Matched"}
                        </span>
                      ) : verificationResult.nameMatchStatus === "MISMATCH" ? (
                        <span className="text-[var(--text-primary)] font-semibold flex items-center gap-1">
                          <XCircle className="w-3.5 h-3.5 text-[var(--text-muted)]" />
                          {isHi ? "नाम बेमेल" : "Name Mismatch"}
                        </span>
                      ) : (
                        <span className="text-[var(--text-muted)] font-medium">
                          {isHi ? "नाम प्रदान नहीं किया गया" : "No name queried"}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Impersonation Warning Notice */}
                  {verificationResult.nameMatchStatus === "MISMATCH" && (
                    <div className="p-3 rounded-xl bg-[var(--nav-track)] border border-[var(--border)] text-xs text-[var(--text-primary)] space-y-1">
                      <strong className="block font-bold text-[var(--text-primary)] flex items-center gap-1.5">
                        <AlertTriangle className="w-3.5 h-3.5 text-[var(--text-muted)]" />
                        <span>{isHi ? "लाइसेंस चोरी का संदेह!" : "Potential License Number Theft!"}</span>
                      </strong>
                      <p className="text-[var(--text-muted)] leading-relaxed">
                        {isHi
                          ? `आपने "${verificationResult.queriedName}" नाम की जाँच की, लेकिन सेबी के आधिकारिक रिकॉर्ड के अनुसार पंजीकरण संख्या ${rec.registrationNumber} केवल "${rec.entityName}" (संपर्क: ${rec.contactPerson}) के नाम पर है।`
                          : `You searched for "${verificationResult.queriedName}", but SEBI registration ${rec.registrationNumber} is officially issued to "${rec.entityName}" (Principal: ${rec.contactPerson}). Scammers frequently quote legitimate RIA numbers to deceive victims on WhatsApp and Telegram.`}
                      </p>
                    </div>
                  )}

                  {/* Official SEBI Direct Link */}
                  <div className="pt-2 flex items-center justify-between text-[11px] text-[var(--text-muted)] border-t border-[var(--border)]">
                    <span>
                      {isHi ? "स्रोत: सेबी आधिकारिक मध्यस्थ डायरेक्टरी" : "Source: Official SEBI Recognized Intermediary Registry"}
                    </span>
                    <a
                      href="https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doRecognisedFpi=yes&intmId=13"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[var(--text-primary)] hover:text-[var(--text-muted)] font-semibold inline-flex items-center gap-1 underline underline-offset-2"
                    >
                      <span>{isHi ? "सेबी पोर्टल पर देखें" : "View on SEBI.gov.in"}</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            /* Unverified / Not Found Flag List */
            <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-solid)]/70 p-4 sm:p-5 space-y-3">
              <h4 className="text-xs font-mono uppercase font-bold text-[var(--text-primary)] tracking-wider flex items-center gap-1.5">
                <ShieldAlert className="w-3.5 h-3.5 text-[var(--text-muted)]" />
                <span>{isHi ? "नियामक चेतावनी" : "REGULATORY RISK FLAGS"}</span>
              </h4>

              <ul className="space-y-2 text-xs text-[var(--text-primary)]">
                <li className="flex items-start gap-2">
                  <span className="text-[var(--text-muted)] font-bold">•</span>
                  <span>
                    <strong>{isHi ? "कोई सक्रिय पंजीकरण नहीं मिला" : "No Active Registration Found"}:</strong>{" "}
                    <span className="text-[var(--text-muted)]">
                      {isHi
                        ? `सेबी मास्टर डेटाबेस में "${inaNumber || personnelName}" के लिए कोई सक्रिय लाइसेंस दर्ज नहीं है।`
                        : `The credentials "${inaNumber || personnelName}" do not correspond to any active licensed intermediary in SEBI records.`}
                    </span>
                  </span>
                </li>

                <li className="flex items-start gap-2">
                  <span className="text-[var(--text-muted)] font-bold">•</span>
                  <span>
                    <strong>{isHi ? "सेबी अधिनियम की धारा 12 का उल्लंघन" : "Violation of SEBI Act Section 12(1)"}:</strong>{" "}
                    <span className="text-[var(--text-muted)]">
                      {isHi
                        ? "बिना सेबी पंजीकरण के किसी भी प्रकार की वित्तीय सलाह या स्टॉक टिप्स देना कानूनी अपराध है।"
                        : "Offering securities advice, stock recommendations, or investment management without a valid certificate is an offence under Section 12 of the SEBI Act, 1992."}
                    </span>
                  </span>
                </li>

                <li className="flex items-start gap-2">
                  <span className="text-[var(--text-muted)] font-bold">•</span>
                  <span>
                    <strong>{isHi ? "शून्य निवेशक संरक्षण" : "Zero Statutory Grievance Redressal"}:</strong>{" "}
                    <span className="text-[var(--text-muted)]">
                      {isHi
                        ? "अनधिकृत संस्थाओं को दिए गए पैसे सेबी स्कोर्स (SCORES) के दायरे में नहीं आते।"
                        : "Transactions with unregistered individuals are outside the jurisdiction of SEBI SCORES dispute resolution."}
                    </span>
                  </span>
                </li>
              </ul>

              <div className="pt-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-t border-[var(--border)] text-xs text-[var(--text-muted)]">
                <span>
                  {isHi ? "अनुशंसा: इस व्यक्ति या संस्था को कोई धनराशि न भेजें।" : "Recommended Action: Do not transfer funds or execute trades via this personnel."}
                </span>
                <a
                  href="tel:1930"
                  className="font-semibold inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[var(--nav-track)] hover:bg-[var(--surface-solid)] border border-[var(--border)] text-[var(--text-primary)] transition-colors self-start sm:self-auto"
                >
                  <PhoneCall className="w-3 h-3" />
                  <span>{isHi ? "हेल्पलाइन 1930" : "Dial Helpline 1930"}</span>
                </a>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
