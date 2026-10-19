"use client";

import React, { useEffect, useState } from "react";
import { VeronicaMessage } from "./types";
import { VERONICA_STRINGS } from "./i18n";
import { VeronicaLauncher } from "./VeronicaLauncher";
import { VeronicaPanel } from "./VeronicaPanel";

function resolveApiBaseUrl(): string {
  if (typeof window !== "undefined") {
    if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
      return "http://localhost:8000";
    }
  }
  if (process.env.NEXT_PUBLIC_API_URL) return process.env.NEXT_PUBLIC_API_URL;
  if (process.env.NEXT_PUBLIC_VERA_API_URL) return process.env.NEXT_PUBLIC_VERA_API_URL;
  return "https://vera-delhi.onrender.com";
}

const STORAGE_KEY = "vera_veronica_chat_v1";
const SESSION_ID_KEY = "vera_veronica_session_id";

function getOrCreateSessionId(): string {
  if (typeof window === "undefined") return "server-session";
  let sId = window.sessionStorage.getItem(SESSION_ID_KEY);
  if (!sId) {
    sId = `vrn_${Math.random().toString(36).substring(2, 9)}_${Date.now()}`;
    window.sessionStorage.setItem(SESSION_ID_KEY, sId);
  }
  return sId;
}

export const VeronicaWidget: React.FC = () => {
  const [mounted, setMounted] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [language, setLanguage] = useState<"en" | "hi">("en");
  const [messages, setMessages] = useState<VeronicaMessage[]>([]);
  const [isThinking, setIsThinking] = useState(false);

  // Client hydration check
  useEffect(() => {
    setMounted(true);

    // Feature flag check
    if (process.env.NEXT_PUBLIC_VERONICA_ENABLED === "false") {
      return;
    }

    // Try reading cached conversation or initialize
    try {
      const saved = window.sessionStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          setMessages(parsed);
          return;
        }
      }
    } catch (_) {
      // Storage unavailable or invalid JSON
    }

    // Default initial greeting
    const initialGreeting: VeronicaMessage = {
      id: "initial-welcome",
      role: "assistant",
      content: VERONICA_STRINGS.en.welcomeMessage,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      suggested_chips: VERONICA_STRINGS.en.sampleChips,
    };
    setMessages([initialGreeting]);
  }, []);

  // Save conversation to sessionStorage
  useEffect(() => {
    if (!mounted || messages.length === 0) return;
    try {
      window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
    } catch (_) {}
  }, [messages, mounted]);

  // Handle language switch
  const handleToggleLanguage = () => {
    const nextLang = language === "en" ? "hi" : "en";
    setLanguage(nextLang);

    // If only welcome message exists, update it to the new language
    if (messages.length <= 1) {
      setMessages([
        {
          id: "initial-welcome",
          role: "assistant",
          content: VERONICA_STRINGS[nextLang].welcomeMessage,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          suggested_chips: VERONICA_STRINGS[nextLang].sampleChips,
        },
      ]);
    }
  };

  const handleClearChat = () => {
    const initialGreeting: VeronicaMessage = {
      id: `welcome-${Date.now()}`,
      role: "assistant",
      content: VERONICA_STRINGS[language].welcomeMessage,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      suggested_chips: VERONICA_STRINGS[language].sampleChips,
    };
    setMessages([initialGreeting]);
    try {
      window.sessionStorage.removeItem(STORAGE_KEY);
    } catch (_) {}
  };

  const handleSendMessage = async (userText: string) => {
    const userMsg: VeronicaMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: userText,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    const nextMessages = [...messages, userMsg];
    setMessages(nextMessages);
    setIsThinking(true);

    try {
      const baseUrl = resolveApiBaseUrl();
      const sId = getOrCreateSessionId();

      const response = await fetch(`${baseUrl}/api/veronica/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: nextMessages.slice(-8).map((m) => ({
            role: m.role,
            content: m.content,
          })),
          language,
          session_id: sId,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      const assistantMsg: VeronicaMessage = {
        id: `asst-${Date.now()}`,
        role: "assistant",
        content: data.reply || VERONICA_STRINGS[language].errorFallback,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        actions: data.actions || [],
        suggested_chips: data.suggested_chips || [],
        source: data.source,
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      // Offline or network error fallback
      const fallbackMsg: VeronicaMessage = {
        id: `err-${Date.now()}`,
        role: "assistant",
        content:
          language === "hi"
            ? "क्षमा करें, सर्वर से संपर्क नहीं हो सका। आप मुख्य पेज पर दिए गए VERA स्कैनर से सीधे जांच कर सकते हैं, या 1930 पर कॉल करें।"
            : "I am temporarily unable to connect to the assistant server. You can still use the VERA scanner on this page for fraud screening, or call the National Cyber Crime Helpline at 1930.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        actions: [
          {
            type: "open_helpline",
            label: "📞 Call 1930 Helpline",
            payload: "tel:1930",
          },
        ],
        isError: true,
      };
      setMessages((prev) => [...prev, fallbackMsg]);
    } finally {
      setIsThinking(false);
    }
  };

  const sendMsgRef = React.useRef(handleSendMessage);
  sendMsgRef.current = handleSendMessage;

  useEffect(() => {
    const handleOpen = (e: Event) => {
      setIsOpen(true);
      const custom = e as CustomEvent<{ query?: string; language?: "en" | "hi" }>;
      if (custom.detail?.language) {
        setLanguage(custom.detail.language);
      }
      if (custom.detail?.query) {
        sendMsgRef.current(custom.detail.query);
      }
    };
    const handleToggle = () => setIsOpen((prev) => !prev);
    const handleClose = () => setIsOpen(false);

    window.addEventListener("vera:open-veronica", handleOpen);
    window.addEventListener("vera:toggle-veronica", handleToggle);
    window.addEventListener("vera:close-veronica", handleClose);
    return () => {
      window.removeEventListener("vera:open-veronica", handleOpen);
      window.removeEventListener("vera:toggle-veronica", handleToggle);
      window.removeEventListener("vera:close-veronica", handleClose);
    };
  }, []);

  if (!mounted) return null;
  if (process.env.NEXT_PUBLIC_VERONICA_ENABLED === "false") return null;

  return (
    <>
      <VeronicaLauncher
        isOpen={isOpen}
        onToggle={() => setIsOpen((prev) => !prev)}
        language={language}
      />
      <VeronicaPanel
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        messages={messages}
        isThinking={isThinking}
        language={language}
        onToggleLanguage={handleToggleLanguage}
        onSendMessage={handleSendMessage}
        onClearChat={handleClearChat}
      />
    </>
  );
};
