"use client";

import React from "react";
import styles from "./veronica.module.css";

interface VeronicaFaqChipsProps {
  chips: string[];
  onSelectChip: (question: string) => void;
  disabled?: boolean;
}

export const VeronicaFaqChips: React.FC<VeronicaFaqChipsProps> = ({
  chips,
  onSelectChip,
  disabled = false,
}) => {
  if (!chips || chips.length === 0) return null;

  return (
    <div className={styles.vrnFaqContainer}>
      {chips.map((chip, index) => (
        <button
          key={`chip-${index}`}
          type="button"
          className={styles.vrnFaqChip}
          onClick={() => onSelectChip(chip)}
          disabled={disabled}
        >
          <span>{chip}</span>
          <svg
            width="12"
            height="12"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </button>
      ))}
    </div>
  );
};
