"use client";

import React from "react";

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-transparent text-[var(--text-primary)] flex flex-col relative z-10 selection:bg-[var(--accent)] selection:text-[var(--accent-ink)]">
      <div className="flex-1 w-full">
        {children}
      </div>
    </div>
  );
}
