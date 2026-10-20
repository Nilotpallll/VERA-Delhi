"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldCheck,
  BookOpen,
  PhoneCall,
  Phone,
  ArrowUpRight,
  AlertTriangle,
  Info,
  FileText,
  ArrowLeft,
} from "lucide-react";
import { VeraNavigation, NavTab } from "@/components/navigation/VeraNavigation";
import { PublicConsumerFlow } from "@/components/dashboard/PublicConsumerFlow";
import { SebiGuidancePanel } from "@/components/dashboard/SebiGuidancePanel";
import { VeraCover } from "@/components/landing/VeraCover";
import { ScrollEffects } from "@/components/shell/ScrollEffects";
import { translations, Locale } from "@/lib/i18n";

export default function Home() {
  const [activeTab, setActiveTab] = useState<NavTab>("CHECK");
  const [locale, setLocale] = useState<Locale>("en");
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [showCover, setShowCover] = useState(true);

  useEffect(() => {
    try {
      const storedTheme = localStorage.getItem("vera_theme") as "light" | "dark" | null;
      const initialTheme =
        storedTheme ||
        (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
      setTheme(initialTheme);
      document.documentElement.setAttribute("data-theme", initialTheme);
    } catch (_) {}
  }, []);

  const handleTabChange = (tab: NavTab) => {
    setActiveTab(tab);
    if (typeof window !== "undefined") {
      window.scrollTo({ top: 0, behavior: "instant" });
    }
  };

  const handleToggleTheme = () => {
    const next = theme === "light" ? "dark" : "light";
    setTheme(next);
    document.documentElement.setAttribute("data-theme", next);
    try {
      localStorage.setItem("vera_theme", next);
    } catch (_) {}
  };

  const handleToggleLocale = () => {
    setLocale((prev) => (prev === "en" ? "hi" : "en"));
  };

  useEffect(() => {
    const handleEnterApp = () => {
      setShowCover(false);
      if (typeof window !== "undefined") {
        window.scrollTo({ top: 0, behavior: "instant" });
      }
    };
    const handleOpenCover = () => {
      setShowCover(true);
      if (typeof window !== "undefined") {
        window.scrollTo({ top: 0, behavior: "instant" });
      }
    };

    window.addEventListener("vera:enter-app", handleEnterApp);
    window.addEventListener("vera:open-cover", handleOpenCover);
    return () => {
      window.removeEventListener("vera:enter-app", handleEnterApp);
      window.removeEventListener("vera:open-cover", handleOpenCover);
    };
  }, []);

  if (showCover) {
    return (
      <div className="vera-cover-wrapper animate-vera-fade-in w-full">
        <VeraCover
          locale={locale}
          theme={theme}
          onLocaleChange={handleToggleLocale}
          onThemeToggle={handleToggleTheme}
          onEnter={() => {
            setShowCover(false);
            window.scrollTo({ top: 0, behavior: "instant" });
          }}
        />
      </div>
    );
  }

  return (
    <div className="vera-investigation-page min-h-screen text-[var(--text-primary)] antialiased relative z-10 flex flex-col items-center animate-vera-fade-in">
      <ScrollEffects />
      {/* ── UNIFIED FLOATING NAVIGATION (Replaces sidebar & topbar) ─────────── */}
      <VeraNavigation
        activeTab={activeTab}
        onTabChange={handleTabChange}
        locale={locale}
        onLocaleToggle={handleToggleLocale}
        theme={theme}
        onThemeToggle={handleToggleTheme}
        onOpenCover={() => {
          setShowCover(true);
          window.scrollTo({ top: 0, behavior: "instant" });
        }}
      />

      {/* ── MAIN CONTENT AREA (Centered, max 1120px) ────────────────────────── */}
      <main className="w-full max-w-[1120px] mx-auto px-4 sm:px-6 pt-20 pb-24 flex flex-col items-center text-center">
        {/* TAB 1: FRAUD CHECK (HOME) */}
        {activeTab === "CHECK" && (
          <div className="w-full flex flex-col items-center">
            {/* Quick return back-pill */}
            <button
              type="button"
              onClick={() => {
                setShowCover(true);
                window.scrollTo({ top: 0, behavior: "instant" });
              }}
              className="group inline-flex items-center gap-1.5 px-3 py-1 mb-4 rounded-full border border-[var(--border)] bg-[var(--surface)] hover:bg-[var(--surface-solid)] text-[var(--text-muted)] hover:text-[var(--text-primary)] text-xs font-semibold shadow-sm transition-all duration-200 active:scale-95 cursor-pointer vera-nav-back-btn"
              aria-label={locale === "hi" ? "होम पेज पर वापस जाएं" : "Back to Home"}
            >
              <ArrowLeft className="w-3.5 h-3.5 transition-transform duration-200 ease-out group-hover:-translate-x-1" />
              <span>{locale === "hi" ? "होम पर वापस जाएं" : "Back to Home"}</span>
            </button>

            {/* H1 Title: white over navy panel in light, text color in dark */}
            <h1 className="text-fluid-h1 text-[var(--hero-h1-color)] max-w-3xl tracking-tight leading-tight">
              {locale === "hi" ? "कुछ ठीक नहीं लग रहा? जाँचें।" : "Something feels off? Check it here."}
            </h1>

            {/* Subtitle: 18px, max 560px, 70% opacity (light: white 85%) */}
            <p className="mt-3 text-lg max-w-[560px] text-[var(--hero-subtitle-color)] leading-relaxed">
              {locale === "hi"
                ? "संदेश, लिंक, स्क्रीनशॉट या वीडियो जोड़ें। VERA चेतावनी के संकेत और आगे जाँचने वाली बातें दिखाएगा।"
                : "Paste a message or link, or add a screenshot or video. VERA checks for warning signs and shows what to verify next."}
            </p>

            {/* Composer Card with Segmented Tabs, Auto-Growing Textarea, Dropzone & Floating Chips */}
            <PublicConsumerFlow locale={locale} />
          </div>
        )}

        {/* TAB 2: SEBI GUIDANCE */}
        {activeTab === "SEBI" && (
          <div className="w-full max-w-[1120px] text-left pt-2 animate-fade-in">
            <div className="text-center mb-10">
              <h2 className="text-fluid-h2 text-[var(--hero-h1-color)] tracking-tight">
                {locale === "hi" ? "निवेश के दावों के नियम समझें" : "Know the rules behind investment claims"}
              </h2>
              <p className="mt-2 text-base text-[var(--hero-subtitle-color)] max-w-xl mx-auto leading-relaxed">
                {locale === "hi"
                  ? "आसान भाषा में मार्गदर्शन पढ़ें और मूल सेबी परिपत्र देखें।"
                  : "Get plain-language guidance on common investment claims, with links to the original SEBI circulars."}
              </p>
            </div>
            <SebiGuidancePanel />
          </div>
        )}

        {/* TAB 3: REPORT & HELP */}
        {activeTab === "RESOURCES" && (
          <div className="w-full max-w-[1120px] text-left pt-2 animate-fade-in">
            {/* Header */}
            <div className="text-center mb-10">
              <h2 className="text-fluid-h2 text-[var(--hero-h1-color)] tracking-tight">
                {locale === "hi" ? "धोखाधड़ी की रिपोर्ट करनी है?" : "Need help reporting a scam?"}
              </h2>
              <p className="mt-2 text-base text-[var(--hero-subtitle-color)] max-w-xl mx-auto leading-relaxed">
                {locale === "hi"
                  ? "पैसे भेजे हैं या अपनी जानकारी साझा की है? सही जगह रिपोर्ट करने और पंजीकरण जाँचने के लिए ये आधिकारिक लिंक इस्तेमाल करें।"
                  : "If you’ve sent money or shared personal details, use these official channels to report it and check a firm’s registration."}
              </p>
            </div>

            {/* 12-Column Bento Grid */}
            <div className="grid grid-cols-12 gap-6 w-full">
              {/* CARD 1: Large Helpline 1930 Card (span 6, red-tinted, mono 56px number, tel link) */}
              <div className="vera-helpline-card col-span-12 lg:col-span-6 vera-glass rounded-[24px] p-7 sm:p-8 flex flex-col justify-between transition-transform duration-200 hover:-translate-y-0.5">
                <div>
                  <div className="flex items-center gap-3 mb-4">
                    <div className="vera-helpline-icon w-10 h-10 rounded-2xl flex items-center justify-center flex-shrink-0">
                      <PhoneCall className="w-5 h-5" />
                    </div>
                    <div>
                      <span className="vera-helpline-copy text-xs uppercase font-mono-tabular tracking-wider font-bold block">
                        {locale === "hi" ? "आपातकालीन वित्तीय हेल्पलाइन" : "Emergency Financial Helpline"}
                      </span>
                      <h3 className="text-base font-bold text-[var(--text-primary)]">
                        {locale === "hi" ? "राष्ट्रीय साइबर अपराध हेल्पलाइन" : "National Cyber Crime Helpline"}
                      </h3>
                    </div>
                  </div>

                  {/* Mono 56px Number */}
                  <div className="my-5">
                    <span className="vera-helpline-copy font-mono-tabular font-extrabold text-[56px] sm:text-[64px] tracking-tight leading-none block">
                      1930
                    </span>
                    <span className="text-xs font-mono-tabular text-[var(--text-muted)] mt-1.5 block">
                      Toll-Free • Available 24×7 across all Indian States
                    </span>
                  </div>

                  <p className="text-sm text-[var(--text-muted)] leading-relaxed mb-6">
                    {locale === "hi"
                      ? "यदि आपने धोखेबाजों को पैसे भेज दिए हैं, तो 2 घंटे (गोल्डन आवर) के भीतर 1930 पर कॉल करें। शीघ्र रिपोर्टिंग से बैंक नोडल अधिकारी संदिग्ध खातों को तुरंत फ्रीज कर पाते हैं।"
                      : "If you transferred funds to suspect entities, call 1930 immediately within the 2-hour Golden Hour. Swift reporting empowers bank nodal officers to freeze recipient escrow and UPI accounts before funds are laundered."}
                  </p>
                </div>

                <div>
                  <a
                    href="tel:1930"
                    className="vera-helpline-action w-full sm:w-auto px-8 h-12 rounded-full font-bold text-sm inline-flex items-center justify-center gap-2.5 transition-transform hover:scale-[1.02]"
                  >
                    <Phone className="w-4 h-4" />
                    <span>{locale === "hi" ? "1930 पर कॉल करें" : "Dial 1930 Helpline"}</span>
                  </a>
                </div>
              </div>

              {/* CARD 2: Official Portals Card (span 6, link rows with arrow-up-right) */}
              <div className="col-span-12 lg:col-span-6 vera-glass rounded-[24px] p-7 sm:p-8 flex flex-col justify-between transition-transform duration-200 hover:-translate-y-0.5">
                <div>
                  <div className="flex items-center gap-3 mb-5">
                    <div className="w-10 h-10 rounded-2xl bg-[var(--nav-track)] border border-[var(--border)] flex items-center justify-center text-[var(--navy-1)] dark:text-[var(--accent)] flex-shrink-0 shadow-sm">
                      <ShieldCheck className="w-5 h-5" />
                    </div>
                    <div>
                      <span className="text-xs uppercase font-mono-tabular tracking-wider font-semibold text-[var(--text-muted)] block">
                        {locale === "hi" ? "नियामक सत्यापन" : "Statutory Portals"}
                      </span>
                      <h3 className="text-base font-bold text-[var(--text-primary)]">
                        {locale === "hi" ? "आधिकारिक शिकायत एवं सत्यापन पोर्टल" : "Official Redressal & Verification Portals"}
                      </h3>
                    </div>
                  </div>

                  {/* Link Rows */}
                  <div className="space-y-3">
                    {[
                      {
                        title: locale === "hi" ? "SEBI SCORES शिकायत पोर्टल" : "SEBI SCORES Portal",
                        desc: locale === "hi"
                          ? "सेबी की ऑनलाइन शिकायत निवारण प्रणाली।"
                          : "Official investor grievance redressal portal directly managed by SEBI.",
                        href: "https://scores.sebi.gov.in",
                        icon: FileText,
                      },
                      {
                        title: locale === "hi" ? "राष्ट्रीय साइबर अपराध रिपोर्टिंग" : "CyberCrime.gov.in Portal",
                        desc: locale === "hi"
                          ? "गृह मंत्रालय का वित्तीय साइबर अपराध निवारण पोर्टल।"
                          : "Ministry of Home Affairs portal for filing cyber financial fraud FIRs.",
                        href: "https://cybercrime.gov.in",
                        icon: AlertTriangle,
                      },
                      {
                        title: locale === "hi" ? "SEBI मध्यस्थ एवं सलाहकार रजिस्टर" : "SEBI Intermediary Registry",
                        desc: locale === "hi"
                          ? "जाँचें कि क्या सलाहकार आधिकारिक रूप से पंजीकृत है।"
                          : "Verify SEBI registration numbers of brokers, analysts, and advisors.",
                        href: "https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doRecognisedFpi=yes&intmId=13",
                        icon: ShieldCheck,
                      },
                      {
                        title: locale === "hi" ? "RBI शिकायत प्रबंधन प्रणाली (CMS)" : "RBI Complaint Management System",
                        desc: locale === "hi"
                          ? "बैंक खातों या UPI लेन-देन से जुड़ी धोखाधड़ी की रिपोर्ट करें।"
                          : "File banking Ombudsman complaints for unauthorized debit and UPI fraud.",
                        href: "https://cms.rbi.org.in",
                        icon: Info,
                      },
                    ].map(({ title, desc, href, icon: Icon }) => (
                      <a
                        key={href}
                        href={href}
                        target="_blank"
                        rel="noreferrer"
                        className="p-3.5 rounded-2xl bg-[var(--nav-track)] border border-[var(--border)] hover:border-[var(--text-muted)] flex items-center justify-between gap-3 group transition-all"
                      >
                        <div className="flex items-center gap-3 min-w-0">
                          <div className="w-8 h-8 rounded-xl bg-[var(--surface-solid)] border border-[var(--border)] flex items-center justify-center text-[var(--navy-1)] dark:text-[var(--accent)] flex-shrink-0">
                            <Icon className="w-4 h-4" />
                          </div>
                          <div className="min-w-0">
                            <span className="text-xs font-bold text-[var(--text-primary)] block truncate">
                              {title}
                            </span>
                            <span className="text-[11px] text-[var(--text-muted)] block truncate">
                              {desc}
                            </span>
                          </div>
                        </div>
                        <ArrowUpRight className="w-4 h-4 text-[var(--text-muted)] group-hover:text-[var(--text-primary)] group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all flex-shrink-0" />
                      </a>
                    ))}
                  </div>
                </div>

                <div className="pt-4 border-t border-[var(--border)] mt-4">
                  <span className="text-[11px] font-mono-tabular text-[var(--text-muted)] block">
                    {locale === "hi"
                      ? "सभी लिंक सीधे भारत सरकार और सेबी के सुरक्षित डोमेन पर ले जाते हैं।"
                      : "All links point directly to official .gov.in and SEBI sovereign domains."}
                  </span>
                </div>
              </div>

              {/* CARD 3: Remaining Item - Start a Formal Investigation with SEBI (span 12) */}
              <div className="col-span-12 vera-glass rounded-[24px] p-7 sm:p-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 transition-transform duration-200 hover:-translate-y-0.5">
                <div className="space-y-1.5 max-w-2xl">
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono-tabular font-bold bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20">
                      FORMAL ACTION
                    </span>
                    <h3 className="text-base font-bold text-[var(--text-primary)]">
                      {locale === "hi"
                        ? "SEBI के साथ औपचारिक जाँच शुरू करें"
                        : "Initiate a Formal Investigation with SEBI"}
                    </h3>
                  </div>
                  <p className="text-sm text-[var(--text-muted)] leading-relaxed">
                    {locale === "hi"
                      ? "यदि किसी अनाधिकृत सलाहकार या ब्रोकर ने आपको गुमराह किया है, तो SEBI SCORES 2.0 पर शिकायत दर्ज करें। यह SEBI की जाँच विंग को सीधे नियामक जाँच शुरू करने का अधिकार देता है।"
                      : "If you have been solicited by an unregistered entity or victimized by false promises, filing a formal complaint on SEBI SCORES 2.0 triggers a case dossier that mandates an institutional review by SEBI enforcement officers."}
                  </p>
                </div>

                <a
                  href="https://scores.sebi.gov.in"
                  target="_blank"
                  rel="noreferrer"
                  className="flex-shrink-0 h-11 px-6 rounded-full bg-[var(--navy-1)] text-white dark:bg-[var(--accent)] dark:text-[var(--accent-ink)] font-bold text-xs inline-flex items-center gap-2 hover:opacity-90 shadow-md transition-all"
                >
                  <span>{locale === "hi" ? "SEBI SCORES खोलें" : "Launch SEBI SCORES 2.0"}</span>
                  <ArrowUpRight className="w-4 h-4" />
                </a>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
