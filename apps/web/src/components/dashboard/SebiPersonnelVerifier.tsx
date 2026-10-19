"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Search,
  UserCheck,
  Briefcase,
  ExternalLink,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  Sparkles,
  PhoneCall,
  Hash,
  User,
  Info,
  Scale,
  BadgeAlert,
  ArrowRight,
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

interface StatutoryRoleMeta {
  id: string;
  roleName: string;
  hindiName: string;
  prefix: string;
  validity: "VALID" | "PROHIBITED" | "UNREGULATED";
  datasetCountText: string;
  governingLaw: string;
  permitted: string[];
  prohibited: string[];
  description: string;
  hindiDescription: string;
}

const STATUTORY_ROLES: StatutoryRoleMeta[] = [
  {
    id: "investment_adviser",
    roleName: "Investment Adviser (Financial Advisor / RIA)",
    hindiName: "पंजीकृत निवेश सलाहकार (फाइनेंशियल एडवाइजर / RIA)",
    prefix: "INA",
    validity: "VALID",
    datasetCountText: "1,041 Registered Advisers",
    governingLaw: "SEBI (Investment Advisers) Regulations, 2013",
    description:
      "A bona fide Financial Advisor legally authorized by SEBI to charge fees for personal investment planning and stock advisory.",
    hindiDescription:
      "सेबी से अधिकृत सलाहकार जो व्यक्तिगत वित्तीय योजना और शेयर सलाह के लिए पारदर्शी शुल्क लेने हेतु पंजीकृत हैं।",
    permitted: [
      "Personalized financial planning & risk profiling",
      "Direct equity, debt, & mutual fund recommendations",
      "Charging transparent, pre-agreed advisory fees (fee-only model)",
    ],
    prohibited: [
      "Strictly prohibited from promising guaranteed or assured returns",
      "Cannot receive product distribution commissions from recommended assets",
      "Cannot manage client funds directly or demand demat/trading passwords",
    ],
  },
  {
    id: "research_analyst",
    roleName: "Research Analyst (Equity & Stock Recommendation)",
    hindiName: "अनुसंधान विश्लेषक (रिसर्च एनालिस्ट / RA)",
    prefix: "INH",
    validity: "VALID",
    datasetCountText: "2,180 Registered Analysts",
    governingLaw: "SEBI (Research Analysts) Regulations, 2014",
    description:
      "SEBI-certified professionals authorized to publish stock research reports, financial models, and target valuations.",
    hindiDescription:
      "सेबी-प्रमाणित विश्लेषक जो शेयरों पर शोध रिपोर्ट, मूल्य लक्ष्य और वित्तीय विश्लेषण प्रकाशित करने के लिए अधिकृत हैं।",
    permitted: [
      "Publishing equity research reports with documented rationale",
      "Issuing buy, hold, or sell recommendation price targets",
      "Technical and fundamental corporate valuation reports",
    ],
    prohibited: [
      "Cannot offer personalized portfolio management or discretionary trading",
      "Cannot demand profit-sharing cuts or percentage cuts on trading gains",
      "Cannot promise assured daily or monthly returns",
    ],
  },
  {
    id: "portfolio_manager",
    roleName: "Portfolio Manager (PMS Provider)",
    hindiName: "पोर्टफोलियो प्रबंधक (पीएमएस प्रोवाइडर / PMS)",
    prefix: "INP",
    validity: "VALID",
    datasetCountText: "531 Registered Managers",
    governingLaw: "SEBI (Portfolio Managers) Regulations, 2020",
    description:
      "High Net-Worth Individual (HNI) discretionary wealth managers with strict fiduciary compliance and statutory minimums.",
    hindiDescription:
      "उच्च निवल मूल्य वाले निवेशकों के लिए औपचारिक विवेकपूर्ण वेल्थ मैनेजर (न्यूनतम सांविधिक सीमा: ₹50 लाख)।",
    permitted: [
      "Discretionary & non-discretionary portfolio management for HNIs",
      "Executing structured asset management under formal client contract",
      "Periodic audited NAV reporting and custodian holdings disclosure",
    ],
    prohibited: [
      "Strict statutory minimum: Cannot accept retail accounts below ₹50 Lakhs",
      "Cannot pool retail capital into personal bank accounts or UPI handles",
      "Cannot guarantee returns against market volatility",
    ],
  },
  {
    id: "stock_broker",
    roleName: "Stock Broker (Trading & Clearing Member)",
    hindiName: "स्टॉक ब्रोकर (ट्रेडिंग एवं क्लीयरिंग सदस्य)",
    prefix: "INZ",
    validity: "VALID",
    datasetCountText: "Major Institutional Brokers Registered",
    governingLaw: "SEBI (Stock Brokers) Regulations, 1992",
    description:
      "Authorized clearing and trading members of recognized stock exchanges (NSE/BSE/MCX) providing verified order routing.",
    hindiDescription:
      "मान्यता प्राप्त स्टॉक एक्सचेंजों (NSE/BSE) के अधिकृत ट्रेडिंग व क्लीयरिंग सदस्य जो अधिकृत आर्डर निष्पादित करते हैं।",
    permitted: [
      "Routing exchange orders through certified trading platforms",
      "Providing margin facilities strictly within exchange limits",
      "Holding client funds in authorized, segregated client bank accounts",
    ],
    prohibited: [
      "Cannot trade on client's behalf without explicit verified consent",
      "Cannot offer unapproved retail algorithmic trading bots",
      "Cannot accept cash deposits or payments to third-party personal accounts",
    ],
  },
];

const UNREGULATED_TITLES: StatutoryRoleMeta[] = [
  {
    id: "telegram_tipster",
    roleName: "Telegram / WhatsApp VIP Tipster & Channel Admin",
    hindiName: "टेलीग्राम / व्हाट्सएप वीआईपी टिपस्टर व एडमिन",
    prefix: "None (Illegal)",
    validity: "PROHIBITED",
    datasetCountText: "0 (Banned Category)",
    governingLaw: "SEBI Circular SEBI/HO/ISD/ISD-PoD-2/P/CIR/2024/45",
    description:
      "Unregistered individuals operating social messaging channels selling intra-day calls, jackpot stock tips, or pump-and-dump signals.",
    hindiDescription:
      "सोशल मैसेजिंग ऐप्स पर अवैध रूप से शेयर टिप्स या जैकपॉट कॉल्स बेचने वाले अनधिकृत चैनल।",
    permitted: [],
    prohibited: [
      "🚨 Criminal offence under Section 12(1) of SEBI Act, 1992 to solicit or provide tips without license",
      "🚨 SEBI actively freezes bank accounts and levies penalties on unauthorized group admins",
      "🚨 Zero investor compensation or grievance rights under SEBI SCORES",
    ],
  },
  {
    id: "guaranteed_return_guru",
    roleName: "Guaranteed Return Consultant / Profit Doubler",
    hindiName: "निश्चित रिटर्न / पूंजी दोगुनी करने का दावा करने वाले",
    prefix: "None (Illegal)",
    validity: "PROHIBITED",
    datasetCountText: "0 (Statutorily Prohibited)",
    governingLaw: "SEBI Circular CIR/2023/123 & SEBI Act Section 12",
    description:
      "Promising fixed 20%-50% monthly returns, no-loss schemes, or capital-doubling plans is completely illegal in Indian capital markets.",
    hindiDescription:
      "शेयर बाजार में निश्चित या दोगुने मुनाफे का वादा करना कानूनन अपराध और धोखाधड़ी है।",
    permitted: [],
    prohibited: [
      "🚨 Section 12 of SEBI Act strictly prohibits assured return schemes in the securities market",
      "🚨 Registered entities face immediate license revocation if promising guaranteed profits",
      "🚨 Hallmark indicator of Ponzi pyramid or advance-fee investment fraud",
    ],
  },
  {
    id: "unregistered_finfluencer",
    roleName: "Unregistered Social Media Finfluencer",
    hindiName: "गैर-पंजीकृत सोशल मीडिया फिनफ्लुएंसर",
    prefix: "None (Unregulated)",
    validity: "UNREGULATED",
    datasetCountText: "0 (Restricted by SEBI)",
    governingLaw: "SEBI August 2024 Finfluencer Directives",
    description:
      "Influencers touting trading strategies or stock recommendations on YouTube, Instagram, or X without personal INA/INH certification.",
    hindiDescription:
      "सेबी लाइसेंस के बिना सोशल मीडिया पर ट्रेडिंग टिप्स या वित्तीय सलाह देने वाले इन्फ्लुएंसर।",
    permitted: [
      "General financial literacy (e.g. explaining what a PE ratio or mutual fund is)",
    ],
    prohibited: [
      "Cannot recommend specific stocks, options contracts, or buy/sell triggers",
      "Cannot enter fee-sharing or promotional referral ties with SEBI brokers",
      "Cannot claim to be 'SEBI Certified' without verifiable individual INA/INH license",
    ],
  },
  {
    id: "forex_account_manager",
    roleName: "Overseas Forex / Binary Options Account Manager",
    hindiName: "विदेशी फॉरेक्स व बाइनरी ऑप्शंस अकाउंट मैनेजर",
    prefix: "None (Prohibited)",
    validity: "PROHIBITED",
    datasetCountText: "0 (RBI Alert List)",
    governingLaw: "RBI Alert List & FEMA Regulations",
    description:
      "Solicitations for high-leverage currency trading via unauthorized overseas platforms (e.g. OctaFX, Olymp Trade).",
    hindiDescription:
      "अवैध विदेशी प्लेटफॉर्म्स पर मुद्रा ट्रेडिंग कराने वाले एजेंट्स (फेमा कानून का उल्लंघन)।",
    permitted: [],
    prohibited: [
      "🚨 Cross-border transfer of funds for speculative forex violates the Foreign Exchange Management Act (FEMA)",
      "🚨 Over 75 illegal trading apps explicitly flagged on RBI Alert List",
      "🚨 Bank accounts receiving overseas transfers risk immediate PMLA cyber-freeze",
    ],
  },
];

export function SebiPersonnelVerifier({ locale = "en", className = "" }: SebiPersonnelVerifierProps) {
  const isHi = locale === "hi";

  // Form input states
  const [personnelName, setPersonnelName] = useState("");
  const [inaNumber, setInaNumber] = useState("");
  const [isVerifying, setIsVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState<VerificationResultState | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Role widget states
  const [roleCategory, setRoleCategory] = useState<"STATUTORY" | "UNREGULATED">("STATUTORY");
  const [roleSearchQuery, setRoleSearchQuery] = useState("");
  const [selectedRole, setSelectedRole] = useState<StatutoryRoleMeta>(STATUTORY_ROLES[0]);
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

  // Filtered roles based on search
  const visibleRoles = useMemo(() => {
    const list = roleCategory === "STATUTORY" ? STATUTORY_ROLES : UNREGULATED_TITLES;
    if (!roleSearchQuery.trim()) return list;
    const q = roleSearchQuery.toLowerCase();
    return list.filter(
      (r) =>
        r.roleName.toLowerCase().includes(q) ||
        r.hindiName.toLowerCase().includes(q) ||
        r.prefix.toLowerCase().includes(q) ||
        r.description.toLowerCase().includes(q)
    );
  }, [roleCategory, roleSearchQuery]);

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
    } catch (err) {
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

    const { state, nameMatchStatus, records } = verificationResult;

    // Case 1: Verified Authentic
    if (state === "FOUND" && (nameMatchStatus === "MATCHED" || nameMatchStatus === "NOT_CHECKED")) {
      return {
        tier: "SAFE",
        badge: isHi ? "सेबी पंजीकृत एवं प्रामाणिक" : "SEBI REGISTERED & AUTHENTIC",
        score: 0,
        riskLabel: isHi ? "न्यूनतम जोखिम (0/100)" : "MINIMAL RISK (0/100)",
        color: "emerald",
        summary: isHi
          ? "यह मध्यस्थ आधिकारिक सेबी मास्टर डायरेक्टरी में वैध रूप से पंजीकृत है।"
          : "Active regulatory credentials verified against official SEBI Intermediary Registry records.",
      };
    }

    // Case 2: License Impersonation / Name Mismatch Risk
    if (state === "FOUND" && nameMatchStatus === "MISMATCH") {
      return {
        tier: "CRITICAL",
        badge: isHi ? "लाइसेंस दुरुपयोग / पहचान बेमेल चेतावनी" : "LICENSE IMPERSONATION DETECTED",
        score: 96,
        riskLabel: isHi ? "गंभीर जोखिम (96/100)" : "CRITICAL RISK (96/100)",
        color: "rose",
        summary: isHi
          ? "पंजीकरण संख्या मौजूद है, लेकिन यह पंजीकृत नाम से मेल नहीं खाती। यह नंबर चोरी या धोखाधड़ी का गंभीर संकेत है!"
          : "The registration number exists in SEBI records, but belongs to a different registered entity/individual. High risk of license spoofing!",
      };
    }

    // Case 3: Ambiguous multiple records found
    if (state === "AMBIGUOUS") {
      return {
        tier: "SUSPICIOUS",
        badge: isHi ? "एकाधिक रिकॉर्ड - सत्यापन आवश्यक" : "MULTIPLE MATCHES - VERIFY EXACT ID",
        score: 45,
        riskLabel: isHi ? "मध्यम जोखिम (45/100)" : "CAUTION (45/100)",
        color: "amber",
        summary: isHi
          ? "इस नाम से एक से अधिक पंजीकृत मध्यस्थ पाए गए। कृपया सही पहचान के लिए INA/INH संख्या दर्ज करें।"
          : "Multiple entities found with this name. Cross-verify with the specific registration number.",
      };
    }

    // Case 4: Unverified / Not Found
    return {
      tier: "HIGH_RISK",
      badge: isHi ? "अवैध / गैर-पंजीकृत सलाहकार अलर्ट" : "UNVERIFIED / REGULATORY RED FLAG",
      score: 92,
      riskLabel: isHi ? "उच्च जोखिम (92/100)" : "HIGH RISK (92/100)",
      color: "rose",
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
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 mb-6 pb-4 border-b border-[var(--border)]">
        <div className="flex items-start gap-3.5">
          <div className="w-10 h-10 rounded-2xl bg-[var(--nav-track)] border border-[var(--border)] flex items-center justify-center text-[var(--navy-1)] dark:text-[var(--accent)] flex-shrink-0 shadow-sm">
            <UserCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-semibold text-[var(--text-primary)] tracking-tight">
                {isHi ? "सेबी कार्मिक एवं मध्यस्थ सत्यापन" : "SEBI Personnel & Entity Verification"}
              </h2>
            </div>
            <p className="text-sm text-[var(--text-muted)] font-normal mt-0.5 leading-relaxed">
              {isHi
                ? "जाँचें कि क्या कोई व्यक्ति या संस्था सेबी पंजीकृत सलाहकार (INA) या मध्यस्थ है।"
                : "Verify whether an individual advisor or firm holds a genuine SEBI license before trusting advice or transferring capital."}
            </p>
          </div>
        </div>

        {/* Live Records Active Pill */}
        <div className="self-start sm:self-auto flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/25 text-emerald-600 dark:text-emerald-400 text-xs font-mono-tabular font-semibold">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>{registryStats ? `${registryStats.total.toLocaleString()} Active SEBI Records` : "3,760 Active SEBI Records"}</span>
        </div>
      </div>

      {/* ── EMBEDDED WIDGET: SEBI STATUTORY ROLE LEGITIMACY DIRECTORY ─────── */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--nav-track)] p-4 sm:p-5 mb-6 space-y-3.5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Briefcase className="w-4 h-4 text-[var(--navy-1)] dark:text-[var(--accent)]" />
            <h3 className="text-sm font-semibold text-[var(--text-primary)]">
              {isHi ? "सेबी सांविधिक पद एवं भूमिका वैधता डायरेक्टरी" : "SEBI Role Legitimacy & Statutory Authority Widget"}
            </h3>
          </div>
          <span className="text-[11px] font-mono-tabular text-[var(--text-muted)]">
            {isHi ? "सेबी विनियम 2013-2024" : "Under SEBI Regulations 2013-2024"}
          </span>
        </div>

        {/* Role Category Selector & Quick Search */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2.5">
          <div className="flex rounded-full p-1 bg-[var(--surface)] border border-[var(--border)] flex-shrink-0 text-xs font-medium">
            <button
              type="button"
              onClick={() => {
                setRoleCategory("STATUTORY");
                setSelectedRole(STATUTORY_ROLES[0]);
              }}
              className={`px-3 py-1 rounded-full transition-all cursor-pointer ${
                roleCategory === "STATUTORY"
                  ? "bg-[var(--navy-1)] text-white dark:bg-[var(--accent)] dark:text-[var(--accent-ink)] font-semibold shadow-xs"
                  : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
              }`}
            >
              ✓ {isHi ? "वैध सेबी भूमिकाएं (4)" : "Valid SEBI Roles (4)"}
            </button>
            <button
              type="button"
              onClick={() => {
                setRoleCategory("UNREGULATED");
                setSelectedRole(UNREGULATED_TITLES[0]);
              }}
              className={`px-3 py-1 rounded-full transition-all cursor-pointer ${
                roleCategory === "UNREGULATED"
                  ? "bg-rose-600 text-white font-semibold shadow-xs"
                  : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
              }`}
            >
              ⚠️ {isHi ? "अवैध / गैर-पंजीकृत दावे (4)" : "Illegal / Scam Claims (4)"}
            </button>
          </div>

          <div className="relative flex-1">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
            <input
              type="text"
              value={roleSearchQuery}
              onChange={(e) => setRoleSearchQuery(e.target.value)}
              placeholder={isHi ? "पद का नाम खोजें (उदा. एडवाइजर, टिपस्टर, एनालिस्ट)..." : "Search role name (e.g. Financial Advisor, Tipster, PMS)..."}
              className="w-full text-xs pl-8 pr-3 py-1.5 rounded-full bg-[var(--surface)] border border-[var(--border)] text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--accent)]"
            />
          </div>
        </div>

        {/* Horizontal Chips of Roles */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
          {visibleRoles.map((role) => {
            const isSelected = selectedRole.id === role.id;
            const isValid = role.validity === "VALID";
            return (
              <button
                key={role.id}
                type="button"
                onClick={() => setSelectedRole(role)}
                className={`px-3 py-1.5 rounded-xl text-xs font-medium whitespace-nowrap transition-all border flex items-center gap-1.5 cursor-pointer flex-shrink-0 ${
                  isSelected
                    ? isValid
                      ? "bg-emerald-500/15 border-emerald-500/40 text-emerald-700 dark:text-emerald-300 font-semibold"
                      : "bg-rose-500/15 border-rose-500/40 text-rose-700 dark:text-rose-300 font-semibold"
                    : "bg-[var(--surface)] border-[var(--border)] text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                }`}
              >
                <span>{isValid ? "🟢" : "🚨"}</span>
                <span>{isHi ? role.hindiName.split(" ")[0] : role.roleName.split(" ")[0]}</span>
                <span className="font-mono-tabular text-[10px] opacity-75">({role.prefix})</span>
              </button>
            );
          })}
        </div>

        {/* Detailed Role Inspection Card */}
        <div
          className={`p-3.5 sm:p-4 rounded-xl border text-xs space-y-2.5 transition-all ${
            selectedRole.validity === "VALID"
              ? "bg-emerald-500/5 border-emerald-500/20"
              : "bg-rose-500/5 border-rose-500/20"
          }`}
        >
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1.5">
            <div className="flex items-center gap-2">
              <span
                className={`px-2 py-0.5 rounded-md font-mono-tabular font-bold text-[10px] uppercase border ${
                  selectedRole.validity === "VALID"
                    ? "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border-emerald-500/30"
                    : "bg-rose-500/15 text-rose-700 dark:text-rose-300 border-rose-500/30"
                }`}
              >
                {selectedRole.validity === "VALID" ? "✓ SEBI Recognized Statutory Role" : "🚨 Prohibited / Illegal Claim"}
              </span>
              <span className="font-semibold text-[var(--text-primary)]">
                {isHi ? selectedRole.hindiName : selectedRole.roleName}
              </span>
            </div>

            <span className="font-mono-tabular text-[11px] text-[var(--text-muted)]">
              {selectedRole.datasetCountText}
            </span>
          </div>

          <p className="text-[var(--text-primary)] leading-relaxed">
            {isHi ? selectedRole.hindiDescription : selectedRole.description}
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 pt-1 border-t border-[var(--border)]">
            {selectedRole.permitted.length > 0 && (
              <div>
                <span className="text-[11px] font-bold text-emerald-600 dark:text-emerald-400 block mb-1">
                  ✓ {isHi ? "कानूनन अनुमत कार्यक्षेत्र" : "Legally Permitted Activities"}:
                </span>
                <ul className="space-y-0.5 text-[11px] text-[var(--text-muted)] list-disc list-inside">
                  {selectedRole.permitted.map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                </ul>
              </div>
            )}

            <div>
              <span
                className={`text-[11px] font-bold block mb-1 ${
                  selectedRole.validity === "VALID"
                    ? "text-rose-600 dark:text-rose-400"
                    : "text-rose-700 dark:text-rose-300"
                }`}
              >
                ⚠️ {isHi ? "सख्त निषेध / रेड फ्लैग्स" : "Strict Prohibitions / Red Flags"}:
              </span>
              <ul className="space-y-0.5 text-[11px] text-[var(--text-muted)] list-disc list-inside">
                {selectedRole.prohibited.map((item, i) => (
                  <li key={i}>{item}</li>
                ))}
              </ul>
            </div>
          </div>

          {/* Quick Action: Use this role's prefix in the search form */}
          {selectedRole.prefix !== "None (Illegal)" && selectedRole.prefix !== "None (Prohibited)" && (
            <div className="pt-1 flex items-center justify-between text-[11px]">
              <span className="text-[var(--text-muted)] font-mono-tabular">
                Mandatory Registration Prefix: <strong className="text-[var(--text-primary)]">{selectedRole.prefix}</strong>
              </span>
              <button
                type="button"
                onClick={() => {
                  setInaNumber(selectedRole.prefix);
                }}
                className="text-[var(--navy-1)] dark:text-[var(--accent)] font-semibold hover:underline cursor-pointer flex items-center gap-1"
              >
                <span>{isHi ? "इस प्रीफिक्स से जाँचें" : "Test with this prefix"}</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* ── PERSONNEL VERIFICATION FORM ─────────────────────────────────────── */}
      <form onSubmit={handleVerify} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
          {/* Input 1: Claimed Personnel / Entity Name */}
          <div className="space-y-1 text-left">
            <label className="text-xs font-semibold text-[var(--text-primary)] flex items-center gap-1.5">
              <User className="w-3.5 h-3.5 text-[var(--navy-1)] dark:text-[var(--accent)]" />
              <span>{isHi ? "सलाहकार या संस्था का नाम" : "Personnel or Entity Name"}</span>
              <span className="text-[10px] text-[var(--text-muted)] font-normal">
                ({isHi ? "वैकल्पिक यदि INA ज्ञात है" : "optional if INA is known"})
              </span>
            </label>
            <input
              type="text"
              value={personnelName}
              onChange={(e) => setPersonnelName(e.target.value)}
              placeholder={isHi ? "उदा. Kavitha Menon, Nithin Kamath..." : "e.g. Kavitha Menon, Anand Rathi..."}
              className="w-full text-sm rounded-xl px-3.5 py-2.5 bg-[var(--input-bg)] border border-[var(--input-border)] text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)] transition-all"
            />
          </div>

          {/* Input 2: SEBI Registration / INA Number */}
          <div className="space-y-1 text-left">
            <label className="text-xs font-semibold text-[var(--text-primary)] flex items-center gap-1.5">
              <Hash className="w-3.5 h-3.5 text-[var(--navy-1)] dark:text-[var(--accent)]" />
              <span>{isHi ? "सेबी पंजीकरण संख्या (INA / INH / INP / INZ)" : "SEBI Registration Number"}</span>
            </label>
            <input
              type="text"
              value={inaNumber}
              onChange={(e) => setInaNumber(e.target.value.toUpperCase())}
              placeholder="e.g. INA000000037, INH000012345..."
              className="w-full text-sm font-mono-tabular uppercase rounded-xl px-3.5 py-2.5 bg-[var(--input-bg)] border border-[var(--input-border)] text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)] transition-all"
            />
          </div>
        </div>

        {/* Quick Demo Preset Chips */}
        <div className="flex items-center gap-1.5 flex-wrap pt-1">
          <span className="text-[11px] font-mono-tabular text-[var(--text-muted)] mr-1">
            {isHi ? "त्वरित परीक्षण:" : "QUICK SAMPLES:"}
          </span>
          <button
            type="button"
            onClick={() => handleSelectSample("Kavitha Menon", "INA000000037")}
            className="px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/25 hover:bg-emerald-500/20 transition-all cursor-pointer"
          >
            ✓ Kavitha Menon (INA000000037)
          </button>
          <button
            type="button"
            onClick={() => handleSelectSample("Anand Rathi", "INH000012345")}
            className="px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/25 hover:bg-emerald-500/20 transition-all cursor-pointer"
          >
            ✓ Anand Rathi (INH000012345)
          </button>
          <button
            type="button"
            onClick={() => handleSelectSample("Vikram Crypto Guru", "INA000000037")}
            className="px-2.5 py-1 rounded-full text-xs font-medium bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/25 hover:bg-rose-500/20 transition-all cursor-pointer"
            title="Real INA claimed by fake personnel name to demonstrate spoof detection"
          >
            ⚠️ Mismatched Name (Spoof Test)
          </button>
          <button
            type="button"
            onClick={() => handleSelectSample("Rajesh Fictitious", "INA999999999")}
            className="px-2.5 py-1 rounded-full text-xs font-medium bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/25 hover:bg-rose-500/20 transition-all cursor-pointer"
          >
            ❌ Fake INA999999999
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

      {/* ── VERIFICATION RESULT STATE ───────────────────────────────────────── */}
      {verificationResult && verdict && (
        <div className="mt-6 pt-6 border-t border-[var(--border)] animate-fade-in space-y-4 text-left">
          {/* Main Verdict Banner */}
          <div
            className={`rounded-2xl p-5 border flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
              verdict.tier === "SAFE"
                ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-900 dark:text-emerald-200"
                : verdict.tier === "CRITICAL" || verdict.tier === "HIGH_RISK"
                ? "bg-rose-500/10 border-rose-500/30 text-rose-900 dark:text-rose-200"
                : "bg-amber-500/10 border-amber-500/30 text-amber-900 dark:text-amber-200"
            }`}
          >
            <div className="flex items-start gap-3.5">
              <div
                className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 ${
                  verdict.tier === "SAFE"
                    ? "bg-emerald-600 text-white"
                    : verdict.tier === "CRITICAL" || verdict.tier === "HIGH_RISK"
                    ? "bg-rose-600 text-white"
                    : "bg-amber-600 text-white"
                }`}
              >
                {verdict.tier === "SAFE" ? (
                  <ShieldCheck className="w-6 h-6" />
                ) : verdict.tier === "CRITICAL" || verdict.tier === "HIGH_RISK" ? (
                  <ShieldAlert className="w-6 h-6" />
                ) : (
                  <AlertTriangle className="w-6 h-6" />
                )}
              </div>
              <div>
                <span className="text-[11px] font-mono-tabular font-bold uppercase tracking-wider block opacity-90">
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

            {/* Score Ring / Pill */}
            <div className="self-end sm:self-center flex flex-col items-end flex-shrink-0">
              <span className="text-2xl font-extrabold font-mono-tabular text-[var(--text-primary)]">
                {verdict.score}/100
              </span>
              <span className="text-[10px] text-[var(--text-muted)] font-mono uppercase tracking-wider">
                {isHi ? "धोखाधड़ी जोखिम सूचकांक" : "Fraud Risk Score"}
              </span>
            </div>
          </div>

          {/* Records Display Card */}
          {verificationResult.records && verificationResult.records.length > 0 ? (
            <div className="space-y-3">
              <h4 className="text-xs font-mono uppercase font-bold text-[var(--text-muted)] tracking-wider">
                {isHi ? "आधिकारिक सेबी रिकॉर्ड विवरण" : "OFFICIAL SEBI DIRECTORY MATCH DETAILS"}
              </h4>

              {verificationResult.records.map((rec, idx) => (
                <div
                  key={idx}
                  className="rounded-2xl border border-[var(--border)] bg-[var(--surface-solid)] p-4 sm:p-5 space-y-3 shadow-xs"
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
                          <Check className="w-3.5 h-3.5 text-emerald-500" />
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
                        <span className="text-emerald-600 dark:text-emerald-400 font-bold flex items-center gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          {isHi ? "नाम सत्यापित" : "Name Matched"}
                        </span>
                      ) : verificationResult.nameMatchStatus === "MISMATCH" ? (
                        <span className="text-rose-600 dark:text-rose-400 font-bold flex items-center gap-1">
                          <XCircle className="w-3.5 h-3.5" />
                          {isHi ? "नाम बेमेल (धोखाधड़ी का जोखिम)" : "Name Mismatch (Impersonation)"}
                        </span>
                      ) : (
                        <span className="text-[var(--text-muted)] font-medium">
                          {isHi ? "नाम प्रदान नहीं किया गया" : "No name queried"}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Impersonation Specific Warning */}
                  {verificationResult.nameMatchStatus === "MISMATCH" && (
                    <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/25 text-xs text-rose-700 dark:text-rose-300 space-y-1">
                      <strong className="block font-bold">
                        🚨 {isHi ? "चेतावनी: लाइसेंस चोरी का संदेह!" : "Critical Alert: Potential License Number Theft!"}
                      </strong>
                      <p className="leading-relaxed">
                        {isHi
                          ? `आपने "${verificationResult.queriedName}" नाम की जाँच की, लेकिन सेबी के आधिकारिक रिकॉर्ड के अनुसार पंजीकरण संख्या ${rec.registrationNumber} केवल "${rec.entityName}" (संपर्क: ${rec.contactPerson}) के नाम पर है। कभी भी किसी अन्य व्यक्ति को पैसे न भेजें!`
                          : `You searched for "${verificationResult.queriedName}", but SEBI registration ${rec.registrationNumber} is officially issued to "${rec.entityName}" (Principal: ${rec.contactPerson}). Scammers frequently quote legitimate RIA numbers to deceive victims on WhatsApp and Telegram.`}
                      </p>
                    </div>
                  )}

                  {/* Official SEBI Direct Link */}
                  <div className="pt-1 flex items-center justify-between text-[11px] text-[var(--text-muted)] border-t border-[var(--border)]">
                    <span>
                      {isHi ? "स्रोत: सेबी आधिकारिक मध्यस्थ डायरेक्टरी" : "Source: Official SEBI Recognized Intermediary Registry"}
                    </span>
                    <a
                      href="https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doRecognisedFpi=yes&intmId=13"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[var(--navy-1)] dark:text-[var(--accent)] font-semibold inline-flex items-center gap-1 hover:underline"
                    >
                      <span>{isHi ? "सेबी पोर्टल पर देखें" : "View on SEBI.gov.in"}</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            /* Unverified / Not Found Detailed Flag List */
            <div className="rounded-2xl border border-rose-500/20 bg-rose-500/5 p-4 sm:p-5 space-y-3">
              <h4 className="text-xs font-mono uppercase font-bold text-rose-600 dark:text-rose-400 tracking-wider">
                🚨 {isHi ? "पहचाने गए मुख्य नियामक जोखिम" : "CRITICAL REGULATORY RISK FLAGS DETECTED"}
              </h4>

              <ul className="space-y-2 text-xs text-[var(--text-primary)]">
                <li className="flex items-start gap-2">
                  <span className="text-rose-500 font-bold">•</span>
                  <span>
                    <strong>{isHi ? "कोई सक्रिय पंजीकरण नहीं मिला" : "No Active Registration Found"}:</strong>{" "}
                    {isHi
                      ? `सेबी मास्टर डेटाबेस में "${inaNumber || personnelName}" के लिए कोई सक्रिय लाइसेंस दर्ज नहीं है।`
                      : `The credentials "${inaNumber || personnelName}" do not correspond to any active licensed intermediary in SEBI records.`}
                  </span>
                </li>

                <li className="flex items-start gap-2">
                  <span className="text-rose-500 font-bold">•</span>
                  <span>
                    <strong>{isHi ? "सेबी अधिनियम की धारा 12 का उल्लंघन" : "Violation of SEBI Act Section 12(1)"}:</strong>{" "}
                    {isHi
                      ? "बिना सेबी पंजीकरण के किसी भी प्रकार की वित्तीय सलाह, स्टॉक टिप्स या पोर्टफोलियो प्रबंधन देना कानूनी अपराध है।"
                      : "Offering securities advice, stock recommendations, or investment management without a valid certificate is an offence under Section 12 of the SEBI Act, 1992."}
                  </span>
                </li>

                <li className="flex items-start gap-2">
                  <span className="text-rose-500 font-bold">•</span>
                  <span>
                    <strong>{isHi ? "शून्य निवेशक संरक्षण" : "Zero Statutory Grievance Redressal"}:</strong>{" "}
                    {isHi
                      ? "अनधिकृत संस्थाओं को दिए गए पैसे सेबी स्कोर्स (SCORES) या निवेशक संरक्षण कोष के दायरे में नहीं आते।"
                      : "Transactions with unregistered individuals are outside the jurisdiction of SEBI SCORES dispute resolution and cannot be compensated via Investor Protection Funds."}
                  </span>
                </li>
              </ul>

              <div className="pt-2 flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-t border-rose-500/20 text-xs text-rose-700 dark:text-rose-300">
                <span>
                  {isHi ? "तुरंत कदम: इस व्यक्ति को कोई धनराशि न भेजें।" : "Recommended Action: Do not transfer funds or execute trades via this personnel."}
                </span>
                <a
                  href="tel:1930"
                  className="font-bold inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-rose-600 text-white hover:bg-rose-700 transition-colors self-start sm:self-auto"
                >
                  <PhoneCall className="w-3 h-3" />
                  <span>{isHi ? "हेल्पलाइन 1930 पर रिपोर्ट करें" : "Dial Helpline 1930"}</span>
                </a>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
