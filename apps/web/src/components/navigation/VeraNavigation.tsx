"use client";

import React, { useState, useEffect } from "react";
import { ShieldCheck, BookOpen, PhoneCall, Sun, Moon, ArrowLeft } from "lucide-react";
import { Locale, translations } from "@/lib/i18n";
import { VeraLogo } from "@/components/brand/VeraLogo";

export type NavTab = "CHECK" | "SEBI" | "RESOURCES";

interface VeraNavigationProps {
  activeTab: NavTab;
  onTabChange: (tab: NavTab) => void;
  locale: Locale;
  onLocaleToggle: () => void;
  theme: "light" | "dark";
  onThemeToggle: () => void;
  onOpenCover?: () => void;
}

export function VeraNavigation({
  activeTab,
  onTabChange,
  locale,
  onLocaleToggle,
  theme,
  onThemeToggle,
  onOpenCover,
}: VeraNavigationProps) {
  const [scrolled, setScrolled] = useState(false);
  const [isBrandExpanded, setIsBrandExpanded] = useState(false);
  const t = translations[locale];

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 8);
    };
    handleScroll();
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const navLinks: { id: NavTab; label: string; icon: React.ElementType }[] = [
    { id: "CHECK", label: t.navFraudCheck, icon: ShieldCheck },
    { id: "SEBI", label: t.navSebi, icon: BookOpen },
    { id: "RESOURCES", label: t.navReportHelp, icon: PhoneCall },
  ];

  return (
    <>
      {/* ── DESKTOP FLOATING GLASS PILL (>= 768px) ─────────────────────────── */}
      <nav
        aria-label="Main Navigation"
        className={`vera-nav-floating hidden md:flex ${scrolled ? "vera-nav-scrolled" : ""}`}
        onBlurCapture={(event) => {
          if (!event.currentTarget.contains(event.relatedTarget as Node | null)) {
            setIsBrandExpanded(false);
          }
        }}
      >
        {/* Left: Back Button + Logo Mark + VERA */}
        <div className="flex items-center gap-2 flex-shrink-0">
          {onOpenCover && (
            <button
              type="button"
              onClick={onOpenCover}
              className="vera-nav-back-btn group h-9 px-3 rounded-full border border-[var(--border)] bg-[var(--surface)] text-[var(--text-primary)] text-xs font-semibold hover:border-[var(--text-muted)] hover:bg-[var(--surface-solid)] transition-all flex items-center gap-1.5 shadow-sm active:scale-95"
              title={t.backToCover || "Back to Home"}
              aria-label={t.backToCover || "Back to Home"}
            >
              <ArrowLeft className="w-3.5 h-3.5 text-[var(--text-muted)] group-hover:text-[var(--text-primary)] transition-transform duration-200 ease-out group-hover:-translate-x-1" />
              <span className="font-semibold tracking-tight">{locale === "hi" ? "होम" : "Home"}</span>
            </button>
          )}

          <button
            type="button"
            className="vera-nav-brand-trigger flex items-center gap-2.5 flex-shrink-0 pr-2"
            aria-expanded={isBrandExpanded}
            aria-controls="vera-brand-popout"
            aria-label={isBrandExpanded ? "Close VERA brand details" : "Show VERA brand details"}
            onClick={() => setIsBrandExpanded((expanded) => !expanded)}
          >
            <VeraLogo className="vera-nav-logo" />
            <span className="flex items-baseline gap-1.5">
              <span className="font-semibold text-base text-[var(--text-primary)] tracking-tight">VERA</span>
              <span className="text-[11px] text-[var(--text-muted)] font-normal hidden min-[1100px]:inline">Fraud Intelligence</span>
            </span>
          </button>
        </div>

        <div id="vera-brand-popout" className={`vera-brand-popout ${isBrandExpanded ? "is-open" : ""}`} aria-hidden={!isBrandExpanded}>
          <VeraLogo className="vera-brand-popout-logo" />
          <div className="vera-brand-popout-copy">
            <strong>VERA</strong>
            <span>Verification and Evidence Based Risk Analyser</span>
            <small>Before You Invest, Let VERA Test</small>
            {onOpenCover && (
              <button
                type="button"
                onClick={() => {
                  setIsBrandExpanded(false);
                  onOpenCover();
                }}
                className="mt-2 inline-flex items-center gap-1.5 text-xs font-semibold text-amber-700 dark:text-amber-300 hover:underline group cursor-pointer"
              >
                <ArrowLeft className="w-3 h-3 group-hover:-translate-x-1 transition-transform" />
                <span>{locale === "hi" ? "होम पेज पर वापस जाएं" : "Return to Home Page"}</span>
              </button>
            )}
          </div>
        </div>

        {/* Center: 3 Pill Links (40px tall, active = filled pill) */}
        <div className="flex items-center gap-1 bg-[var(--nav-track)] p-1 rounded-full border border-[var(--border)]">
          {navLinks.map(({ id, label }) => {
            const isActive = activeTab === id;
            return (
              <button
                key={id}
                onClick={() => { setIsBrandExpanded(false); onTabChange(id); }}
                aria-pressed={isActive}
                className={`h-9 px-4 rounded-full text-sm font-medium transition-all duration-200 select-none ${
                  isActive
                    ? "bg-[var(--nav-active-pill)] text-[var(--nav-active-text)] font-semibold shadow-sm"
                    : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                }`}
              >
                {label}
              </button>
            );
          })}
        </div>

        {/* Right: Veronica AI + Language toggle + Theme toggle */}
        <div className="flex items-center gap-2 flex-shrink-0">
          {/* Veronica AI Quick Trigger */}
          <button
            type="button"
            onClick={() => {
              if (typeof window !== "undefined") {
                window.dispatchEvent(new Event("vera:toggle-veronica"));
              }
            }}
            className="h-9 pl-2 pr-3.5 rounded-full border border-amber-500/35 bg-amber-500/10 text-amber-800 dark:text-amber-200 text-xs font-semibold hover:bg-amber-500/20 transition-colors shadow-sm flex items-center gap-2 overflow-hidden"
            title="Veronica AI Forensic Assistant (Alt + V)"
            aria-label="Veronica AI Forensic Assistant"
          >
            <VeraLogo className="vera-nav-veronica-logo" />
            <span className="font-bold">Veronica AI</span>
          </button>

          {/* Language Toggle (40px pill) */}
          <button
            onClick={onLocaleToggle}
            className="h-9 px-3.5 rounded-full border border-[var(--border)] bg-[var(--surface)] text-[var(--text-primary)] text-xs font-semibold hover:border-[var(--text-muted)] transition-colors shadow-sm"
            title="Toggle language"
            aria-label="Toggle language"
            aria-pressed={locale === "hi"}
          >
            {locale === "en" ? "हिंदी" : "EN"}
          </button>

          {/* Theme Toggle (40px circle) */}
          <button
            onClick={onThemeToggle}
            className="w-9 h-9 rounded-full border border-[var(--border)] bg-[var(--surface)] text-[var(--text-primary)] flex items-center justify-center hover:border-[var(--text-muted)] transition-colors shadow-sm"
            title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
            aria-label="Toggle theme"
            aria-pressed={theme === "dark"}
          >
            {theme === "dark" ? (
              <Sun className="w-4 h-4 text-[#a9d0df]" />
            ) : (
              <Moon className="w-4 h-4 text-[#5b8594]" />
            )}
          </button>

        </div>
      </nav>

      {/* ── MOBILE CONTROLS (< 768px) ─────────────────────────────────────── */}
      <div className="md:hidden">
        {/* Top-Left: Back to Home Button */}
        {onOpenCover && (
          <button
            type="button"
            onClick={onOpenCover}
            className="vera-nav-back-btn fixed top-3 left-3 z-50 h-11 px-3.5 rounded-full border border-[var(--border)] bg-[var(--surface)] text-[var(--text-primary)] text-xs font-semibold flex items-center gap-1.5 backdrop-blur-xl shadow-md group active:scale-95 transition-all"
            title={t.backToCover || "Back to Home"}
            aria-label={t.backToCover || "Back to Home"}
          >
            <ArrowLeft className="w-4 h-4 transition-transform duration-200 ease-out group-hover:-translate-x-1" />
            <span>{locale === "hi" ? "होम" : "Home"}</span>
          </button>
        )}

        {/* Top-Right: Floating Veronica + Language + Theme Cluster (44px circles) */}
        <div className="fixed top-3 right-3 z-50 flex items-center gap-2">
          <button
            type="button"
            onClick={() => {
              if (typeof window !== "undefined") {
                window.dispatchEvent(new Event("vera:toggle-veronica"));
              }
            }}
            className="w-11 h-11 rounded-full border border-amber-500/40 bg-[var(--surface)] text-amber-700 dark:text-amber-300 text-xs font-bold flex items-center justify-center backdrop-blur-xl shadow-md"
            title="Veronica AI Assistant"
            aria-label="Veronica AI Assistant"
          >
            <VeraLogo className="vera-nav-veronica-mobile-logo" />
          </button>
          <button
            onClick={onLocaleToggle}
            className="w-11 h-11 rounded-full border border-[var(--border)] bg-[var(--surface)] text-[var(--text-primary)] text-xs font-bold flex items-center justify-center backdrop-blur-xl shadow-md"
            title="Toggle language"
            aria-label="Toggle language"
            aria-pressed={locale === "hi"}
          >
            {locale === "en" ? "हिंदी" : "EN"}
          </button>
          <button
            onClick={onThemeToggle}
            className="w-11 h-11 rounded-full border border-[var(--border)] bg-[var(--surface)] text-[var(--text-primary)] flex items-center justify-center backdrop-blur-xl shadow-md"
            title="Toggle theme"
            aria-label="Toggle theme"
            aria-pressed={theme === "dark"}
          >
            {theme === "dark" ? (
              <Sun className="w-4 h-4 text-[#a9d0df]" />
            ) : (
              <Moon className="w-4 h-4 text-[#5b8594]" />
            )}
          </button>
        </div>

        {/* Bottom: Floating Dock Pill (3 icon+label tabs, safe-area padded) */}
        <div className="fixed bottom-4 left-4 right-4 z-50 max-w-sm mx-auto">
          <nav
            aria-label="Mobile Navigation Dock"
            className="h-16 px-2 rounded-full flex items-center justify-around bg-[var(--nav-bg)] border border-[var(--border)] backdrop-blur-2xl shadow-xl"
          >
            {navLinks.map(({ id, label, icon: Icon }) => {
              const isActive = activeTab === id;
              return (
                <button
                  key={id}
                  onClick={() => onTabChange(id)}
                  aria-pressed={isActive}
                  className={`flex-1 h-12 rounded-full flex flex-col items-center justify-center transition-all ${
                    isActive
                      ? "bg-[var(--nav-active-pill)] text-[var(--nav-active-text)] font-semibold shadow-sm"
                      : "text-[var(--text-muted)]"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="text-[10px] tracking-tight mt-0.5 leading-none">
                    {label}
                  </span>
                </button>
              );
            })}
          </nav>
        </div>
      </div>
    </>
  );
}
