"use client";

import React, { useEffect, useRef } from "react";
import styles from "./veronica.module.css";
import { VeronicaMessage } from "./types";
import { VERONICA_STRINGS } from "./i18n";
import { VeronicaChat } from "./VeronicaChat";
import { VeronicaFaqChips } from "./VeronicaFaqChips";
import { VeronicaInput } from "./VeronicaInput";
import { VeraLogo } from "../brand/VeraLogo";

interface VeronicaPanelProps {
  isOpen: boolean;
  onClose: () => void;
  messages: VeronicaMessage[];
  isThinking: boolean;
  language: "en" | "hi";
  onToggleLanguage: () => void;
  onSendMessage: (text: string) => void;
  onClearChat: () => void;
}

export const VeronicaPanel: React.FC<VeronicaPanelProps> = ({
  isOpen,
  onClose,
  messages,
  isThinking,
  language,
  onToggleLanguage,
  onSendMessage,
  onClearChat,
}) => {
  const panelRef = useRef<HTMLDivElement>(null);
  const strings = VERONICA_STRINGS[language];

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const latestAssistantMsg = [...messages].reverse().find((m) => m.role === "assistant");
  const latestSuggestedChips =
    latestAssistantMsg?.suggested_chips && latestAssistantMsg.suggested_chips.length > 0
      ? latestAssistantMsg.suggested_chips
      : messages.length <= 1
      ? strings.sampleChips
      : [];

  return (
    <div
      ref={panelRef}
      className={styles.vrnPanel}
      role="dialog"
      aria-label="Veronica Assistant"
      aria-modal="false"
      id="veronica-panel"
    >
      {/* ── Panel Header ────────────────────────────────────── */}
      <div className={styles.vrnHeader}>
        <div className={styles.vrnHeaderLeft}>
          <div className={styles.vrnAvatar}>
            <VeraLogo className={styles.vrnAvatarLogo} />
            <div className={styles.vrnAvatarDot} />
          </div>
          <div>
            <div className={styles.vrnTitle}>{strings.assistantName}</div>
            <div className={styles.vrnSubtitle}>
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              {strings.onlineBadge}
            </div>
          </div>
        </div>

        <div className={styles.vrnHeaderControls}>
          <button
            type="button"
            className={styles.vrnLangToggle}
            onClick={onToggleLanguage}
            title={strings.toggleLangTitle}
            aria-label={strings.toggleLangTitle}
          >
            {language === "en" ? "हिन्दी" : "English"}
          </button>

          <button
            type="button"
            className={styles.vrnHeaderBtn}
            onClick={onClearChat}
            title={strings.clearChatTitle}
            aria-label={strings.clearChatTitle}
          >
            {/* Trash icon */}
            <svg
              width="15"
              height="15"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <polyline points="3 6 5 6 21 6" />
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
            </svg>
          </button>

          <button
            type="button"
            className={styles.vrnHeaderBtn}
            onClick={onClose}
            title={strings.closePanelTitle}
            aria-label={strings.closePanelTitle}
          >
            {/* Close X icon */}
            <svg
              width="16"
              height="16"
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
          </button>
        </div>
      </div>

      {/* ── Message Stream ──────────────────────────────────── */}
      <VeronicaChat
        messages={messages}
        isThinking={isThinking}
        language={language}
        onTriggerChip={onSendMessage}
      />

      {/* ── Contextual Suggestion Chips (above input) ────────── */}
      {latestSuggestedChips.length > 0 && !isThinking && (
        <div style={{ padding: "0 16px 8px" }}>
          <VeronicaFaqChips
            chips={latestSuggestedChips}
            onSelectChip={onSendMessage}
            disabled={isThinking}
          />
        </div>
      )}

      {/* ── Input Dock ──────────────────────────────────────── */}
      <VeronicaInput
        onSendMessage={onSendMessage}
        isLoading={isThinking}
        language={language}
      />
    </div>
  );
};
