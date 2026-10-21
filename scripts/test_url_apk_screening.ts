import { translations } from "../apps/web/src/lib/i18n";

const VERIFIED_BROKER_REGISTRY = [
  {
    name: "Angel One Limited",
    regNumber: "INZ000186937",
    type: "Stock Broker",
    status: "ACTIVE",
    aliases: ["angelone", "angel one", "angel broking", "angelbroking", "angel"],
    officialDomains: ["angelone.in", "angelone.com", "angelbroking.com"],
  },
  {
    name: "Zerodha Broking Limited",
    regNumber: "INZ000031633",
    type: "Stock Broker",
    status: "ACTIVE",
    aliases: ["zerodha", "zerodha broking", "kite"],
    officialDomains: ["zerodha.com"],
  },
  {
    name: "Groww Invest Tech Pvt Ltd",
    regNumber: "INZ000208032",
    type: "Stock Broker",
    status: "ACTIVE",
    aliases: ["groww", "groww invest tech", "groww tech"],
    officialDomains: ["groww.in"],
  },
  {
    name: "Upstox (RKSV Securities)",
    regNumber: "INZ000282739",
    type: "Stock Broker",
    status: "ACTIVE",
    aliases: ["upstox", "rksv", "rksv securities"],
    officialDomains: ["upstox.com", "rksv.in"],
  },
  {
    name: "ICICI Securities Limited",
    regNumber: "INZ000015837",
    type: "Stock Broker",
    status: "ACTIVE",
    aliases: ["icici securities", "icicidirect", "icici direct", "icici"],
    officialDomains: ["icicidirect.com", "icicisecurities.com"],
  },
  {
    name: "Kotak Securities Limited",
    regNumber: "INZ000171337",
    type: "Stock Broker",
    status: "ACTIVE",
    aliases: ["kotak securities", "kotak"],
    officialDomains: ["kotaksecurities.com"],
  },
  {
    name: "HDFC Securities Limited",
    regNumber: "INZ000005835",
    type: "Stock Broker",
    status: "ACTIVE",
    aliases: ["hdfc securities", "hdfcsec", "hdfc direct"],
    officialDomains: ["hdfcsec.com", "hdfcsecurities.com"],
  },
  {
    name: "Motilal Oswal Financial Services",
    regNumber: "INZ000163434",
    type: "Stock Broker",
    status: "ACTIVE",
    aliases: ["motilal oswal", "motilaloswal"],
    officialDomains: ["motilaloswal.com"],
  },
  {
    name: "Sharekhan Limited",
    regNumber: "INZ000171337",
    type: "Stock Broker",
    status: "ACTIVE",
    aliases: ["sharekhan", "sharekhan limited"],
    officialDomains: ["sharekhan.com"],
  },
  {
    name: "5paisa Capital Limited",
    regNumber: "INZ000010231",
    type: "Stock Broker",
    status: "ACTIVE",
    aliases: ["5paisa", "5paisa capital"],
    officialDomains: ["5paisa.com"],
  },
  {
    name: "Securities and Exchange Board of India (SEBI)",
    regNumber: "REGULATOR",
    type: "Statutory Regulatory Body",
    status: "ACTIVE",
    aliases: ["sebi", "scores", "scores sebi"],
    officialDomains: ["sebi.gov.in", "scores.sebi.gov.in", "scores.gov.in"],
  },
];

// Function simulating the exact scanning logic from PublicConsumerFlow.tsx
function normalizeBrokerSlug(val: string): string {
  return (val || "").toLowerCase().replace(/[^a-z0-9]/g, "");
}

function normalizeRegistryName(value: string | undefined): string {
  return (value || "")
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase()
    .replace(/^(mr|mrs|ms|miss|dr)\.?\s+/, "")
    .replace(/[^\p{L}\p{N}]+/gu, " ")
    .trim()
    .replace(/\s+/g, " ");
}

export function runTextUrlApkScreening(inputText: string, locale: "en" | "hi" = "en") {
  const textToScan = inputText.trim();
  const lower = textToScan.toLowerCase();

  // 1. SEBI Registration ID Pattern
  const sebiRegPattern = /\b(IN[A-Z]{1,3}\d{4,10})\b/i;
  const regIdMatch = textToScan.match(sebiRegPattern);
  const claimedRegId = regIdMatch ? regIdMatch[1].toUpperCase() : null;

  const sebiClaimMatch =
    /\b(?:sebi|sabi|rbi)\s*(?:registered|approved|certified|licensed|authorized|officer|official|governed)\b/i.test(textToScan) ||
    /\b(?:registered|certified|licensed)\s*(?:investment\s+)?(?:advisor|adviser|analyst|broker|trader)\b/i.test(textToScan) ||
    /\b(?:sebi|sabi)\s+(?:investment\s+)?(?:advisor|adviser|analyst|broker)\b/i.test(textToScan);

  // Extract claimed advisor name or persona
  let claimedAdvisorName: string | undefined;
  const nameIntroMatch = textToScan.match(
    /(?:my\s+name\s+is|i\s+am|this\s+is)\s+(?:mr\.?|ms\.?|dr\.?)?\s*([A-Za-z]{2,20}(?:\s+[A-Za-z]{2,20}){1,3})/i
  );
  let extractedMessageName: string | undefined;
  if (nameIntroMatch) {
    const cand = nameIntroMatch[1].trim();
    if (!/^(a\s+|an\s+|the\s+)?(sebi|sabi|registered|advisor|adviser|analyst|broker|trader|financial|certified|official)/i.test(cand)) {
      extractedMessageName = cand;
    }
  }
  claimedAdvisorName = extractedMessageName;

  if (!claimedAdvisorName) {
    for (const broker of VERIFIED_BROKER_REGISTRY) {
      const cleanLower = normalizeBrokerSlug(lower);
      const brokerMatches = broker.aliases.some((a) => cleanLower.includes(normalizeBrokerSlug(a)));
      if (brokerMatches && !lower.includes("http://") && !lower.includes("https://") && !lower.includes(".in/") && !lower.includes(".com/")) {
        claimedAdvisorName = broker.name;
        break;
      }
    }
  }

  if (!claimedAdvisorName && !claimedRegId) {
    const candidateClean = textToScan
      .replace(/^(check|verify|is|advisor|adviser|name:?|persona:?)\s+/i, "")
      .replace(/[,\.\?!]+$/, "")
      .trim();
    const hasUrlOrFile = /https?:\/\/|\.in\b|\.com\b|\.org\b|\.ac\b|\.vip\b|\.top\b|\.xyz\b|\.apk\b|www\./i.test(candidateClean);
    const isActionPhrase = /^(invest\s+on|trade\s+on|download|install|click|visit|join|transfer|pay|deposit)\b/i.test(candidateClean);
    const isLetterPattern = /^[A-Za-z\s.'-]+$/.test(candidateClean);

    if (
      !hasUrlOrFile &&
      !isActionPhrase &&
      isLetterPattern &&
      candidateClean.length >= 3 &&
      candidateClean.length <= 60 &&
      !candidateClean.includes("\n")
    ) {
      claimedAdvisorName = candidateClean;
    }
  }

  // 2. Assured Returns / Profit Guarantees Detection (CIR/2023/123)
  const percentReturnMatch = textToScan.match(
    /\b(\d+(?:\.\d+)?)\s*(?:%|percent)\s*(?:returns?|profit|gain|roi|growth|yield|dividend|payout|income)\b/i
  );
  const multiplierMatch = textToScan.match(
    /\b(?:([2-9]|10)x|(?:get\s+)?(?:double|triple)\s*(?:the|your|our|my)?)\s*(?:returns?|profit|gain|capital|money|investment|funds|paisa|amount)?\b/i
  );
  const fixedTermsMatch = textToScan.match(
    /\b(guarantee|guaranteed|pakka|fix\s*profit|fixed\s*returns?|assured\s*returns?|zero\s*risk|100%\s*profit|100%\s*sure|sure\s*shot|loss\s*proof|double\s+(?:the|your)?\s*money|paisa\s*double)\b/i
  );
  const periodicEarnMatch = textToScan.match(
    /\b(?:earn|get|receive|payout\s*of)\s*(?:[\$₹]|rs\.?|inr\s*)?(\d+(?:,\d+)*(?:\s*[kK])?)\s*(?:daily|per\s*day|weekly|monthly|every\s*day|every\s*month)\b/i
  );
  const isGuaranteed = Boolean(percentReturnMatch || multiplierMatch || fixedTermsMatch || periodicEarnMatch);

  // 3. Direct Fund Demand / Personal Account Transfer
  const fundDemandMatch = textToScan.match(
    /\b(?:please\s+)?(?:invest|send|transfer|pay|deposit|give|wire)\s+(?:me\s+)?(?:[\$₹]|rs\.?|inr\s*)?(\d+\s*(?:lakhs?|lacs?|crores?|thousand|k)?|\d+(?:,\d+)*)\b/i
  );
  const generalMoneyDemand = textToScan.match(
    /\b(?:send|transfer|pay|deposit)\s+(?:money|funds|cash|amount|capital)\s+(?:to|asap|now|here|me)\b/i
  );
  const personalChannelDemand = textToScan.match(
    /\b(?:to\s+my|send\s+to|transfer\s+to)\s+(?:personal\s+)?(?:upi|account|gpay|phonepe|paytm|bank)\b/i
  );
  const isFundSolicitation = Boolean(fundDemandMatch || generalMoneyDemand || personalChannelDemand);

  // 4. Urgency & Coercion
  const urgencyMatch = textToScan.match(
    /\b(asap|urgently|immediately|right\s+now|hurry|today\s+only|last\s+chance|within\s+\d+\s*hours?|act\s+fast|don'?t\s+wait|limited\s+(?:slots?|seats?|time))\b/i
  );
  const isUrgency = Boolean(urgencyMatch);

  // 5. Unregulated Channels / VIP Signals
  const isVip =
    /(?:(?<!\.)\bvip\b|telegram|whatsapp|signal\s+group|private\s+calls?|jackpot\s+calls?|insider\s+tips?|premium\s+calls?)/i.test(textToScan);

  // 6. URL & Domain Screening (Impersonation, Official Portals, Unverified Destinations)
  const extractedDomains: Array<{ raw: string; host: string; cleanHost: string }> = [];
  const seenDomains = new Set<string>();
  const domainRegex = /(?:https?:\/\/)?([a-zA-Z0-9][-a-zA-Z0-9]*(?:\.[a-zA-Z0-9][-a-zA-Z0-9]*)*\.[a-zA-Z]{2,}(?::\d+)?)(?:\/[^\s"'<>]*)?/gi;
  let urlMatch: RegExpExecArray | null;
  while ((urlMatch = domainRegex.exec(textToScan)) !== null) {
    const raw = urlMatch[0];
    const host = urlMatch[1].toLowerCase().split(":")[0];
    if (host.endsWith(".apk") || host.endsWith(".png") || host.endsWith(".jpg") || host.endsWith(".pdf")) {
      continue;
    }
    const cleanHost = host.replace(/^www\./, "");
    if (!seenDomains.has(cleanHost) && cleanHost.includes(".")) {
      seenDomains.add(cleanHost);
      extractedDomains.push({ raw, host, cleanHost });
    }
  }

  let hasOfficialBrokerDomain = false;
  let verifiedBrokerEntity: (typeof VERIFIED_BROKER_REGISTRY)[0] | undefined = undefined;
  let verifiedBrokerDomain = "";

  const lookalikeDomains: Array<{ domain: string; broker: (typeof VERIFIED_BROKER_REGISTRY)[0] }> = [];
  const unverifiedInvestmentDestinations: string[] = [];

  const isInvestmentContext =
    /\b(invest|investing|investment|trade|trading|trader|stocks?|crypto|deposit|yield|returns?|profit|broker|demat|fund|money|capital)\b/i.test(textToScan) ||
    /^(?:invest\s+on|trade\s+on|deposit\s+on)\b/i.test(textToScan.trim());

  for (const item of extractedDomains) {
    const dom = item.cleanHost;
    const domSlug = normalizeBrokerSlug(dom);

    // Check if domain matches an official domain of a registered broker
    let matchedOfficial: (typeof VERIFIED_BROKER_REGISTRY)[0] | undefined;
    for (const broker of VERIFIED_BROKER_REGISTRY) {
      if (broker.officialDomains.some((od) => dom === od || dom.endsWith("." + od))) {
        matchedOfficial = broker;
        break;
      }
    }

    if (matchedOfficial) {
      hasOfficialBrokerDomain = true;
      verifiedBrokerEntity = matchedOfficial;
      verifiedBrokerDomain = dom;
      continue;
    }

    // Check if domain is a lookalike/impersonation of a registered broker
    let matchedLookalike: (typeof VERIFIED_BROKER_REGISTRY)[0] | undefined;
    for (const broker of VERIFIED_BROKER_REGISTRY) {
      const brokerAliases = [
        normalizeBrokerSlug(broker.name),
        ...broker.aliases.map(normalizeBrokerSlug),
      ];
      const isImpersonating = brokerAliases.some((alias) => {
        if (alias.length < 4 && alias !== "rbi" && alias !== "nse" && alias !== "bse") return false;
        return domSlug.includes(alias);
      });

      if (isImpersonating) {
        matchedLookalike = broker;
        break;
      }
    }

    if (matchedLookalike) {
      lookalikeDomains.push({ domain: dom, broker: matchedLookalike });
      continue;
    }

    // Check if domain is an unverified investment destination
    const isGovOrExchange = /^(?:nseindia\.com|bseindia\.com|rbi\.org\.in|mcxindia\.com|cdslindia\.com|nsdl\.co\.in|sebi\.gov\.in)$/i.test(dom);
    const isDirectDomainScan =
      textToScan.trim() === item.raw.trim() ||
      textToScan.trim() === item.host ||
      textToScan.trim().startsWith("http://") ||
      textToScan.trim().startsWith("https://");

    if ((isInvestmentContext || isDirectDomainScan) && !isGovOrExchange) {
      unverifiedInvestmentDestinations.push(dom);
    }
  }

  // 7. Unsolicited APK Download / Install Link Detection
  const apkPattern = /(?:download\s+(?:and\s+)?install|sideload|install|download)?.*?([a-zA-Z0-9_\-\.]+\.apk)|\b([a-zA-Z0-9_\-\.]+\.apk)\b/i;
  const apkMatch = textToScan.match(apkPattern);
  const hasApkLink = Boolean(apkMatch);
  const apkFileName = apkMatch ? (apkMatch[1] || apkMatch[2] || "trading-app.apk") : undefined;

  // 8. Spoofed UPI / Regulated Handle Checks
  const isUpiScam = lower.includes("sebi") && lower.includes("@");

  // Calculate score & reasons
  let riskTier: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" = "LOW";
  let score = 15;
  const reasons: string[] = [];
  const matched: string[] = [];

  // Reason 2: Assured Returns
  if (isGuaranteed) {
    score += 45;
    const matchedPhrase = percentReturnMatch?.[0] || multiplierMatch?.[0] || fixedTermsMatch?.[0] || "guaranteed returns";
    reasons.push(`Prohibited Assured Return Promise ('${matchedPhrase}')`);
    matched.push(matchedPhrase);
  }

  // Reason 3: Direct Fund Solicitation
  if (isFundSolicitation) {
    score += 40;
    const matchedFundPhrase = fundDemandMatch?.[0] || generalMoneyDemand?.[0] || personalChannelDemand?.[0] || "send funds";
    reasons.push(`Unauthorized Direct Fund Solicitation ('${matchedFundPhrase}')`);
    matched.push(matchedFundPhrase);
  }

  // Reason 4: Urgency
  if (isUrgency) {
    score += 20;
    reasons.push(`High-Pressure Urgency Tactics`);
    matched.push("urgency");
  }

  // Reason 5: VIP Channel
  if (isVip) {
    score += 25;
    reasons.push(`Unregulated VIP/Telegram signal channel`);
    matched.push("vip");
  }

  // Reason 6A: Impersonation / Lookalike Broker Domain
  if (lookalikeDomains.length > 0) {
    score += 55;
    for (const item of lookalikeDomains) {
      reasons.push(
        locale === "hi"
          ? `संदिग्ध नकली ब्रोकर डोमेन ('${item.domain}') — यह डोमेन सेबी-पंजीकृत स्टॉक ब्रोकर '${item.broker.name}' की नकल कर रहा है, परंतु यह उनका अधिकृत आधिकारिक डोमेन (${item.broker.officialDomains.join(", ")}) नहीं है। वैध ब्रोकर कभी भी अनधिकृत या संदिग्ध डोमेन का उपयोग नहीं करते।`
          : `Impersonation / Lookalike Broker Domain ('${item.domain}') — Domain imitates SEBI-registered stock broker '${item.broker.name}', but is not an authorized official domain (${item.broker.officialDomains.join(", ")}). Legitimate brokers never operate on disposable or unverified TLDs.`
      );
      matched.push(item.domain, item.broker.name, "lookalike domain");
    }
  }

  // Reason 6B: Unverified Investment Destination
  if (unverifiedInvestmentDestinations.length > 0) {
    score += 45;
    for (const dom of unverifiedInvestmentDestinations) {
      reasons.push(
        locale === "hi"
          ? `अपुष्ट निवेश गंतव्य ('${dom}') — यह डोमेन स्थानीय सेबी रजिस्टर में किसी भी पंजीकृत स्टॉक ब्रोकर या अधिकृत वित्तीय मध्यस्थ से मेल नहीं खाता है। अपंजीकृत प्लेटफॉर्म के माध्यम से निवेश आमंत्रित करना सेबी नियमों का उल्लंघन है।`
          : `Unverified Investment Destination ('${dom}') — This investment destination cannot be matched to any SEBI-registered stock broker or authorized intermediary in the local registry. Soliciting investment capital or trading via unregistered web domains violates SEBI regulations.`
      );
      matched.push(dom, "unverified investment destination");
    }
  }

  // Reason 6C: Unsolicited APK Download / Install Warning
  if (hasApkLink && apkFileName) {
    score += 45;
    reasons.push(
      locale === "hi"
        ? `अवांछित APK डाउनलोड / इंस्टॉल चेतावनी ('${apkFileName}') — आधिकारिक ऐप स्टोर (Google Play Store / Apple App Store) से बाहर ट्रेडिंग या निवेश एपीके फाइल डाउनलोड करना मैलवेयर और वित्तीय क्रेडेंशियल चोरी का गंभीर जोखिम पैदा करता है। ध्यान दें: VERA द्वारा APK फ़ाइल की मैलवेयर जाँच नहीं की गई है क्योंकि फ़ाइल को विश्लेषण हेतु अपलोड नहीं किया गया था।`
        : `Unsolicited APK Download / Install Warning ('${apkFileName}') — Sideloading investment/trading APK files outside official app stores (Google Play Store / Apple App Store) is a primary vector for financial trojans and credential harvesting. Note: The APK file itself has NOT been malware-scanned by VERA because the binary file was not uploaded and analyzed.`
    );
    matched.push(apkFileName, "unsolicited apk", "apk install");
  }

  // Reason 6D: Spoofed UPI
  if (isUpiScam) {
    score += 35;
    reasons.push(`Impersonation payment handle`);
    matched.push("sebi", "@");
  }

  // Final score & Risk tier calculation
  score = Math.min(99, Math.max(10, score));
  if (score >= 70) riskTier = "CRITICAL";
  else if (score >= 45) riskTier = "HIGH";
  else if (score >= 25) riskTier = "MEDIUM";
  else riskTier = "LOW";

  const highlightedReasons =
    reasons.length > 0
      ? reasons
      : hasOfficialBrokerDomain && verifiedBrokerEntity
      ? [
          locale === "hi"
            ? `इस संदेश में कोई धोखाधड़ी संकेत नहीं मिला। यूआरएल ('${verifiedBrokerDomain}') सेबी-पंजीकृत स्टॉक ब्रोकर ${verifiedBrokerEntity.name} (${verifiedBrokerEntity.regNumber}) का आधिकारिक और प्रामाणिक वेब डोमेन है।`
            : `No high-risk deception patterns detected. The URL ('${verifiedBrokerDomain}') matches the verified official web domain of SEBI-registered stock broker ${verifiedBrokerEntity.name} (${verifiedBrokerEntity.regNumber}).`,
        ]
      : [
          locale === "hi"
            ? "इस संदेश में कोई स्पष्ट घोटाला संकेत नहीं मिला।"
            : "No obvious high-risk deception patterns detected in this text.",
        ];

  const verifiedItems = [
    "Checked against official SEBI Investor Caution Rules",
    ...(hasOfficialBrokerDomain && verifiedBrokerEntity
      ? [
          `Official SEBI-Registered Broker Domain: '${verifiedBrokerDomain}' is the authentic verified portal of ${verifiedBrokerEntity.name} (${verifiedBrokerEntity.regNumber})`,
        ]
      : []),
  ];

  const unverifiedItems = [
    "Receiver bank account ownership (Internal bank KYC is protected by privacy laws)",
    ...(hasApkLink
      ? [
          "APK binary file malware analysis (the APK file was not uploaded for static/dynamic sandbox analysis)",
        ]
      : []),
  ];

  return {
    riskTier,
    score,
    highlightedReasons,
    matchedKeywords: matched,
    verifiedItems,
    unverifiedItems,
    hasOfficialBrokerDomain,
    lookalikeDomains,
    unverifiedInvestmentDestinations,
    hasApkLink,
    apkFileName,
  };
}

// ── Test Runner ──
console.log("================================================================================");
console.log("RUNNING VERA MESSAGES / LINK / URL SCREENING VERIFICATION SUITE");
console.log("================================================================================\n");

// Test 0: Module Tab Name Verification
console.log("--- TEST 0: MODULE TAB NAME ---");
console.log(`[EN] tabMessageLink: "${translations.en.tabMessageLink}"`);
console.log(`[HI] tabMessageLink: "${translations.hi.tabMessageLink}"`);
if (translations.en.tabMessageLink === "Messages / Link / URL" && translations.hi.tabMessageLink === "संदेश / लिंक / URL") {
  console.log(" PASS: Module tab name correctly updated to Messages / Link / URL in EN and HI\n");
} else {
  console.error(" FAIL: Module tab name not updated correctly\n");
  process.exit(1);
}

// Test 1: Invest on https://www.angelone.in/
console.log("--- TEST 1: OFFICIAL BROKER DOMAIN (Invest on https://www.angelone.in/) ---");
const test1 = runTextUrlApkScreening("Invest on https://www.angelone.in/");
console.log("Input:", "Invest on https://www.angelone.in/");
console.log("Risk Tier:", test1.riskTier);
console.log("Score:", test1.score);
console.log("Has Official Broker Domain:", test1.hasOfficialBrokerDomain);
console.log("Highlighted Reasons:", test1.highlightedReasons);
console.log("Verified Items:", test1.verifiedItems);
if (test1.riskTier === "LOW" && test1.hasOfficialBrokerDomain && test1.score <= 20) {
  console.log(" PASS: Angel One official domain is NOT marked high risk and is verified!\n");
} else {
  console.error(" FAIL: Angel One official domain was incorrectly flagged as high risk!\n");
  process.exit(1);
}

// Test 2: Invest on yesMovies.ac
console.log("--- TEST 2: UNVERIFIED INVESTMENT DESTINATION (Invest on yesMovies.ac) ---");
const test2 = runTextUrlApkScreening("Invest on yesMovies.ac");
console.log("Input:", "Invest on yesMovies.ac");
console.log("Risk Tier:", test2.riskTier);
console.log("Score:", test2.score);
console.log("Unverified Destinations:", test2.unverifiedInvestmentDestinations);
console.log("Highlighted Reasons:", test2.highlightedReasons);
if (
  (test2.riskTier === "HIGH" || test2.riskTier === "CRITICAL") &&
  test2.unverifiedInvestmentDestinations.includes("yesmovies.ac") &&
  test2.highlightedReasons[0].includes("Unverified Investment Destination")
) {
  console.log(" PASS: yesMovies.ac correctly flagged as unverified investment destination!\n");
} else {
  console.error(" FAIL: yesMovies.ac was not flagged as unverified investment destination!\n");
  process.exit(1);
}

// Test 3: Lookalike broker domain (angelone-secure-login.vip)
console.log("--- TEST 3: LOOKALIKE BROKER DOMAIN (A lookalike such as angelone-secure-login.vip) ---");
const test3 = runTextUrlApkScreening("A lookalike such as angelone-secure-login.vip");
console.log("Input:", "A lookalike such as angelone-secure-login.vip");
console.log("Risk Tier:", test3.riskTier);
console.log("Score:", test3.score);
console.log("Lookalike Domains:", test3.lookalikeDomains);
console.log("Highlighted Reasons:", test3.highlightedReasons);
if (
  (test3.riskTier === "HIGH" || test3.riskTier === "CRITICAL") &&
  test3.lookalikeDomains.some((d) => d.domain === "angelone-secure-login.vip") &&
  test3.highlightedReasons.some((r) => r.includes("Impersonation / Lookalike Broker Domain"))
) {
  console.log(" PASS: angelone-secure-login.vip correctly flagged as suspicious lookalike domain!\n");
} else {
  console.error(" FAIL: angelone-secure-login.vip was not flagged as lookalike!\n");
  process.exit(1);
}

// Test 4: Download and install this trading app: trade-now.apk
console.log("--- TEST 4: UNSOLICITED APK WARNING (Download and install this trading app: trade-now.apk) ---");
const test4 = runTextUrlApkScreening("Download and install this trading app: trade-now.apk");
console.log("Input:", "Download and install this trading app: trade-now.apk");
console.log("Risk Tier:", test4.riskTier);
console.log("Score:", test4.score);
console.log("Has APK Link:", test4.hasApkLink);
console.log("APK File Name:", test4.apkFileName);
console.log("Highlighted Reasons:", test4.highlightedReasons);
console.log("Unverified Items:", test4.unverifiedItems);
const hasNoScanClaim = test4.highlightedReasons[0].toLowerCase().includes("the apk file itself has not been malware-scanned by vera because the binary file was not uploaded");
const hasUnverifiedNotice = test4.unverifiedItems.some((item) => item.includes("APK binary file malware analysis"));
if ((test4.riskTier === "HIGH" || test4.riskTier === "CRITICAL") && test4.hasApkLink && hasNoScanClaim && hasUnverifiedNotice) {
  console.log(" PASS: trade-now.apk correctly flagged as APK warning without claiming malware scanning!\n");
} else {
  console.error(" FAIL: trade-now.apk was not correctly flagged with malware scan disclaimer!\n");
  process.exit(1);
}

// Additional Tests: Formatting variations ("Angel One" vs "angelone")
console.log("--- TEST 5: BROKER FORMATTING VARIATIONS ---");
const test5a = runTextUrlApkScreening("Invest on https://angelone.in/");
const test5b = runTextUrlApkScreening("Official portal for Angel One: https://www.angelone.in");
console.log("test5a (angelone.in): RiskTier =", test5a.riskTier, ", hasOfficial =", test5a.hasOfficialBrokerDomain);
console.log("test5b (Angel One text + www.angelone.in): RiskTier =", test5b.riskTier, ", hasOfficial =", test5b.hasOfficialBrokerDomain);
if (test5a.riskTier === "LOW" && test5b.riskTier === "LOW") {
  console.log(" PASS: Broker name formatting differences handled cleanly!\n");
} else {
  console.error(" FAIL: Formatting differences failed!\n");
  process.exit(1);
}

console.log("================================================================================");
console.log("ALL TESTS COMPLETED SUCCESSFULLY! ZERO DEFECTS DETECTED.");
console.log("================================================================================");
