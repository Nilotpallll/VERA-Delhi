"use client";

import React, { useState, useEffect } from "react";
import { ShieldCheck, BookOpen, PhoneCall, Sun, Moon } from "lucide-react";
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
}

export function VeraNavigation({
  activeTab,
  onTabChange,
  locale,
  onLocaleToggle,
  theme,
  onThemeToggle,
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
        {/* Left: Logo Mark + VERA + Fraud Intelligence */}
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

        <div id="vera-brand-popout" className={`vera-brand-popout ${isBrandExpanded ? "is-open" : ""}`} aria-hidden={!isBrandExpanded}>
          <VeraLogo className="vera-brand-popout-logo" />
          <div className="vera-brand-popout-copy">
            <strong>VERA</strong>
            <span>Verification and Evidence Based Risk Analyser</span>
            <small>Before You Invest, Let VERA Test</small>
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

        {/* Right: Language toggle + Theme toggle */}
        <div className="flex items-center gap-2 flex-shrink-0">
          {/* Language Toggle (40px pill) */}
          <button
            onClick={onLocaleToggle}
            className="h-9 px-3.5 rounded-full border border-[var(--border)] bg-[var(--surface)] text-[var(--text-primary)] text-xs font-semibold hover:border-[var(--text-muted)] transition-colors shadow-sm"
            title="Toggle language"
            aria-label="Toggle language"
          >
            {locale === "en" ? "हिंदी" : "EN"}
          </button>

          {/* Theme Toggle (40px circle) */}
          <button
            onClick={onThemeToggle}
            className="w-9 h-9 rounded-full border border-[var(--border)] bg-[var(--surface)] text-[var(--text-primary)] flex items-center justify-center hover:border-[var(--text-muted)] transition-colors shadow-sm"
            title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
            aria-label="Toggle theme"
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
        {/* Top-Right: Floating Language + Theme Cluster (44px circles) */}
        <div className="fixed top-3 right-3 z-50 flex items-center gap-2">
          <button
            onClick={onLocaleToggle}
            className="w-11 h-11 rounded-full border border-[var(--border)] bg-[var(--surface)] text-[var(--text-primary)] text-xs font-bold flex items-center justify-center backdrop-blur-xl shadow-md"
            title="Toggle language"
            aria-label="Toggle language"
          >
            {locale === "en" ? "हिंदी" : "EN"}
          </button>
          <button
            onClick={onThemeToggle}
            className="w-11 h-11 rounded-full border border-[var(--border)] bg-[var(--surface)] text-[var(--text-primary)] flex items-center justify-center backdrop-blur-xl shadow-md"
            title="Toggle theme"
            aria-label="Toggle theme"
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
