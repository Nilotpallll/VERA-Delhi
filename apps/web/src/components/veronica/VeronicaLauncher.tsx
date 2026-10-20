"use client";

import React from "react";
import styles from "./veronica.module.css";
import { VeraLogo } from "../brand/VeraLogo";

interface VeronicaLauncherProps {
  isOpen: boolean;
  onToggle: () => void;
  language: "en" | "hi";
}

export const VeronicaLauncher: React.FC<VeronicaLauncherProps> = ({
  isOpen,
  onToggle,
  language,
}) => {
  const label = isOpen
    ? language === "hi"
      ? "वेरोनिका बंद करें"
      : "Close Veronica assistant"
    : language === "hi"
    ? "वेरोनिका एआई सहायक खोलें"
    : "Open Veronica AI assistant";

  return (
    <button
      type="button"
      id="veronica-launcher-btn"
      className={`${styles.vrnLauncher} ${isOpen ? styles.vrnLauncherOpen : ""}`}
      onClick={onToggle}
      aria-label={label}
      aria-expanded={isOpen}
      title={`${label} (Alt + V)`}
    >
      {!isOpen && <span className={styles.vrnLauncherLabel}>Talk with VERONICA</span>}
      <span className={styles.vrnLauncherIcon}>
        {!isOpen && <span className={styles.vrnLauncherPulse} />}
        {!isOpen && <span className={styles.vrnLauncherBadge} />}
        {isOpen ? (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        ) : (
          <VeraLogo className={styles.vrnLauncherLogo} />
        )}
      </span>
    </button>
  );
};
