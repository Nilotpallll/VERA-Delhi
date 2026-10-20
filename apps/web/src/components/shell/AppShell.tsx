"use client";

import React from "react";
import { FinanceBackdrop } from "@/components/shell/FinanceBackdrop";

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-transparent text-[var(--text-primary)] flex flex-col relative z-10 selection:bg-[var(--accent)] selection:text-[var(--accent-ink)]">
      <FinanceBackdrop />
      <div className="relative z-10 flex-1 w-full">
        {children}
      </div>
    </div>
  );
}
