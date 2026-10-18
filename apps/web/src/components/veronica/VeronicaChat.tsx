"use client";

import React, { useEffect, useRef, useState } from "react";
import styles from "./veronica.module.css";
import { VeronicaAction, VeronicaMessage } from "./types";
import { VERONICA_STRINGS } from "./i18n";

interface VeronicaChatProps {
  messages: VeronicaMessage[];
  isThinking: boolean;
  language: "en" | "hi";
  onTriggerChip?: (chip: string) => void;
}

export const VeronicaChat: React.FC<VeronicaChatProps> = ({
  messages,
  isThinking,
  language,
  onTriggerChip,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const strings = VERONICA_STRINGS[language];

  // Auto-scroll on new message
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [messages, isThinking]);

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleActionClick = (action: VeronicaAction) => {
    if (action.type === "open_helpline") {
      window.location.href = action.payload;
    } else if (action.type === "external_link") {
      window.open(action.payload, "_blank", "noopener,noreferrer");
    } else if (action.type === "navigate") {
      if (typeof window !== "undefined") {
        window.dispatchEvent(new Event("vera:enter-app"));
      }
      setTimeout(() => {
        if (action.payload.startsWith("#")) {
          const el = document.querySelector(action.payload);
          if (el) {
            el.scrollIntoView({ behavior: "smooth" });
          } else {
            window.scrollTo({ top: 350, behavior: "smooth" });
          }
        } else {
          window.location.href = action.payload;
        }
      }, 50);
    } else if (action.type === "run_sample" && onTriggerChip) {
      onTriggerChip(action.label);
    }
  };

  const renderFormattedContent = (content: string) => {
    const lines = content.split("\n");
    return lines.map((line, idx) => {
      // Simple markdown bold replacement
      const parts = line.split(/(\*\*.*?\*\*)/g);
      const renderedLine = parts.map((part, pIdx) => {
        if (part.startsWith("**") && part.endsWith("**")) {
          return <strong key={pIdx}>{part.slice(2, -2)}</strong>;
        }
        return part;
      });

      return (
        <React.Fragment key={idx}>
          {renderedLine}
          {idx < lines.length - 1 && <br />}
        </React.Fragment>
      );
    });
  };

  return (
    <div ref={containerRef} className={styles.vrnMessagesContainer}>
      {messages.map((msg) => {
        const isUser = msg.role === "user";
        return (
          <div
            key={msg.id}
            className={`${styles.vrnMessageRow} ${
              isUser ? styles.vrnMessageRowUser : styles.vrnMessageRowAssistant
            }`}
          >
            <div
              className={`${styles.vrnBubble} ${
                isUser ? styles.vrnBubbleUser : styles.vrnBubbleAssistant
              }`}
            >
              {renderFormattedContent(msg.content)}

              {!isUser && msg.actions && msg.actions.length > 0 && (
                <div className={styles.vrnActionsGroup}>
                  {msg.actions.map((act, aIdx) => (
                    <button
                      key={`act-${aIdx}`}
                      type="button"
                      className={styles.vrnActionBtn}
                      onClick={() => handleActionClick(act)}
                    >
                      {act.label}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className={styles.vrnTimestamp}>
              {msg.timestamp}
              {!isUser && (
                <button
                  type="button"
                  onClick={() => handleCopy(msg.id, msg.content)}
                  className="ml-2 hover:underline text-[10px] text-slate-400"
                >
                  {copiedId === msg.id ? strings.copiedTooltip : strings.copyCode}
                </button>
              )}
            </div>
          </div>
        );
      })}

      {isThinking && (
        <div className={`${styles.vrnMessageRow} ${styles.vrnMessageRowAssistant}`}>
          <div className={`${styles.vrnBubble} ${styles.vrnBubbleAssistant}`}>
            <div className={styles.vrnTyping}>
              <div className={styles.vrnDot} />
              <div className={styles.vrnDot} />
              <div className={styles.vrnDot} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
