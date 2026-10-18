"use client";

import React, { useState, useEffect } from "react";
import { Shield, Sparkles } from "lucide-react";

export function StartupAnimation({ onComplete }: { onComplete?: () => void }) {
  const [stage, setStage] = useState<"visible" | "fading" | "hidden">("visible");

  useEffect(() => {
    // Stage 1: Progress completes in 1.1s
    const timerFade = setTimeout(() => {
      setStage("fading");
    }, 1100);

    // Stage 2: Completely remove after fade transition
    const timerDone = setTimeout(() => {
      setStage("hidden");
      if (onComplete) onComplete();
    }, 1600);

    return () => {
      clearTimeout(timerFade);
      clearTimeout(timerDone);
    };
  }, [onComplete]);

  if (stage === "hidden") return null;

  return (
    <div
      className={`fixed inset-0 z-50 flex flex-col items-center justify-center bg-[#F8FAFC]/95 backdrop-blur-2xl transition-all duration-500 ease-out ${
        stage === "fading" ? "opacity-0 scale-105 pointer-events-none" : "opacity-100 scale-100"
      }`}
    >
      {/* Background ambient radial glow */}
      <div className="absolute w-[500px] h-[500px] rounded-full bg-gradient-to-tr from-indigo-500/15 via-blue-500/15 to-violet-500/10 blur-3xl pointer-events-none animate-pulse-glow" />

      <div className="relative z-10 flex flex-col items-center text-center space-y-5">
        {/* Animated VERA Emblem with Apple-like spring */}
        <div className="relative" style={{ animation: "splashLogo 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards" }}>
          <div className="w-20 h-20 rounded-3xl bg-gradient-to-tr from-indigo-600 via-blue-600 to-indigo-700 flex items-center justify-center text-white shadow-xl shadow-indigo-500/25 border border-white/60">
            <span className="text-3xl font-black font-sans tracking-tight">V</span>
          </div>
          <div className="absolute -top-1 -right-1 p-1.5 rounded-full bg-white shadow-sm border border-slate-100">
            <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
          </div>
        </div>

        {/* Brand Title */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-center gap-2">
            <h1 className="text-3xl font-black tracking-tight text-slate-900">
              VERA <span className="apple-gradient-text font-black">Platform</span>
            </h1>
          </div>
          <p className="text-xs font-semibold tracking-wider uppercase text-slate-500 font-mono">
            Autonomous Multimodal Forensic System
          </p>
        </div>

        {/* Minimalist Apple-like loading progress track */}
        <div className="w-48 space-y-2 pt-2">
          <div className="h-1 w-full bg-slate-200/80 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-indigo-600 to-blue-600 rounded-full"
              style={{
                animation: "splashProgress 1s cubic-bezier(0.16, 1, 0.3, 1) forwards",
              }}
            />
          </div>
          <p className="text-[11px] text-slate-400 font-medium">
            Loading verification platform...
          </p>
        </div>
      </div>
    </div>
  );
}
