"use client";

import React, { useRef, useState } from "react";
import styles from "./veronica.module.css";
import { VERONICA_STRINGS } from "./i18n";

interface VeronicaInputProps {
  onSendMessage: (text: string) => void;
  isLoading: boolean;
  language: "en" | "hi";
}

export const VeronicaInput: React.FC<VeronicaInputProps> = ({
  onSendMessage,
  isLoading,
  language,
}) => {
  const [text, setText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const strings = VERONICA_STRINGS[language];

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed || isLoading) return;
    onSendMessage(trimmed);
    setText("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value.slice(0, 500);
    setText(val);
    // Auto-grow
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 80)}px`;
    }
  };

  return (
    <div className={styles.vrnInputDock}>
      <div className={styles.vrnInputRow}>
        <textarea
          ref={textareaRef}
          rows={1}
          value={text}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder={strings.inputPlaceholder}
          className={styles.vrnTextarea}
          disabled={isLoading}
          aria-label={strings.inputPlaceholder}
        />
        <button
          type="button"
          onClick={handleSend}
          disabled={!text.trim() || isLoading}
          className={styles.vrnSendBtn}
          aria-label={strings.sendButtonLabel}
          title={strings.sendButtonLabel}
        >
          {isLoading ? (
            <div className={styles.vrnDot} style={{ width: 4, height: 4 }} />
          ) : (
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          )}
        </button>
      </div>

      <div className={styles.vrnFooterDisclaimer}>
        {strings.disclaimer}
      </div>
    </div>
  );
};
