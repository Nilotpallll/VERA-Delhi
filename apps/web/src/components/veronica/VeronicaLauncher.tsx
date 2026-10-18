"use client";

import React from "react";
import styles from "./veronica.module.css";

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
      className={styles.vrnLauncher}
      onClick={onToggle}
      aria-label={label}
      aria-expanded={isOpen}
      title={label}
    >
      {!isOpen && <div className={styles.vrnLauncherPulse} />}
      {!isOpen && <div className={styles.vrnLauncherBadge} />}

      {isOpen ? (
        // Close Icon (X)
        <svg
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      ) : (
        // Veronica Sparkle / Shield Chat Icon
        <svg
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" />
          <circle cx="12" cy="12" r="1" fill="currentColor" />
          <circle cx="8" cy="12" r="1" fill="currentColor" />
          <circle cx="16" cy="12" r="1" fill="currentColor" />
        </svg>
      )}
    </button>
  );
};
