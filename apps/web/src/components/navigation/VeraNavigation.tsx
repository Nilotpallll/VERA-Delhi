"use client";

import React, { useState, useEffect } from "react";
import { ShieldCheck, BookOpen, PhoneCall, Sun, Moon, Phone } from "lucide-react";
import { Locale, translations } from "@/lib/i18n";

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
        className={`vera-nav-floating hidden md:flex ${
          scrolled ? "vera-nav-scrolled" : ""
        }`}
      >
        {/* Left: Logo Mark + VERA + Fraud Intelligence */}
        <div className="flex items-center gap-2.5 flex-shrink-0 pr-2">
          <div
            className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm shadow-sm transition-colors ${
              theme === "dark"
                ? "bg-[#86E08B] text-[#04140A]"
                : "bg-[#1E3A8A] text-white"
            }`}
          >
            V
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="font-semibold text-base text-[var(--text-primary)] tracking-tight">
              VERA
            </span>
            <span className="text-[11px] text-[var(--text-muted)] font-normal hidden min-[1100px]:inline">
              Fraud Intelligence
            </span>
          </div>
        </div>

        {/* Center: 3 Pill Links (40px tall, active = filled pill) */}
        <div className="flex items-center gap-1 bg-[var(--nav-track)] p-1 rounded-full border border-[var(--border)]">
          {navLinks.map(({ id, label }) => {
            const isActive = activeTab === id;
            return (
              <button
                key={id}
                onClick={() => onTabChange(id)}
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

        {/* Right: Language toggle + Theme toggle + Helpline 1930 */}
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
              <Sun className="w-4 h-4 text-[#86E08B]" />
            ) : (
              <Moon className="w-4 h-4 text-[#1E3A8A]" />
            )}
          </button>

          {/* Helpline 1930 Pill */}
          <a
            href="tel:1930"
            className="h-9 px-3.5 rounded-full flex items-center gap-2 bg-[var(--helpline-bg)] text-[var(--helpline-text)] border border-[var(--helpline-border)] transition-transform hover:scale-[1.02] shadow-sm"
            title="National Cyber Crime Helpline"
          >
            <Phone className="w-3.5 h-3.5 flex-shrink-0" />
            <span className="text-xs font-semibold hidden min-[1100px]:inline">
              {t.cyberHelpline}
            </span>
            <span className="font-mono-tabular font-bold text-xs">1930</span>
          </a>
        </div>
      </nav>

      {/* ── MOBILE CONTROLS (< 768px) ─────────────────────────────────────── */}
      <div className="md:hidden">
        {/* Top-Left: Helpline 1930 Pinned (44px min tap target) */}
        <a
          href="tel:1930"
          className="fixed top-3 left-3 z-50 h-11 px-3.5 rounded-full flex items-center gap-1.5 bg-[var(--helpline-bg)] text-[var(--helpline-text)] border border-[var(--helpline-border)] shadow-md"
          title="Helpline 1930"
        >
          <Phone className="w-4 h-4" />
          <span className="font-mono-tabular font-bold text-xs">1930</span>
        </a>

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
              <Sun className="w-4 h-4 text-[#86E08B]" />
            ) : (
              <Moon className="w-4 h-4 text-[#1E3A8A]" />
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
