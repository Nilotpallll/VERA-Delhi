"use client";

import React from "react";

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
      {/* Top Header */}
      <header className="h-16 border-b border-slate-800 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50 px-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-lg bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20">
            V
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
                VERA
              </span>
              <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                Phase 1 Core
              </span>
            </div>
            <p className="text-xs text-slate-400">Investment Fraud Investigation Platform</p>
          </div>
        </div>

        <nav className="flex items-center gap-6">
          <a
            href="/"
            className="text-sm font-medium text-slate-200 hover:text-white transition-colors"
          >
            Dashboard
          </a>
          <a
            href="/investigations"
            className="text-sm font-medium text-slate-400 hover:text-white transition-colors"
          >
            Investigations
          </a>
          <a
            href="/evidence"
            className="text-sm font-medium text-slate-400 hover:text-white transition-colors"
          >
            Evidence Vault
          </a>
          <div className="h-4 w-[1px] bg-slate-800" />
          <div className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/20">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            API Online
          </div>
        </nav>
      </header>

      {/* Main App Body */}
      <div className="flex flex-1">
        {/* Sidebar */}
        <aside className="w-64 border-r border-slate-800 bg-slate-900/30 p-4 hidden md:flex flex-col gap-6">
          <div>
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider px-3 mb-2">
              Investigate
            </div>
            <div className="space-y-1">
              <a
                href="/"
                className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg bg-indigo-600/10 text-indigo-400 border border-indigo-500/20"
              >
                <span>📊</span> Overview & Health
              </a>
              <a
                href="#new"
                className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg text-slate-400 hover:bg-slate-800/50 hover:text-slate-200 transition-colors"
              >
                <span>➕</span> New Case
              </a>
              <a
                href="#history"
                className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg text-slate-400 hover:bg-slate-800/50 hover:text-slate-200 transition-colors"
              >
                <span>📂</span> Case History
              </a>
            </div>
          </div>

          <div>
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider px-3 mb-2">
              Platform
            </div>
            <div className="space-y-1">
              <div className="flex items-center justify-between px-3 py-2 text-xs text-slate-400">
                <span>Architecture</span>
                <span className="font-mono text-[10px] text-slate-500">v1.0.0</span>
              </div>
              <div className="flex items-center justify-between px-3 py-2 text-xs text-slate-400">
                <span>Scoring Engine</span>
                <span className="font-mono text-[10px] text-slate-500">Deterministic</span>
              </div>
            </div>
          </div>
        </aside>

        {/* Content Area */}
        <main className="flex-1 p-6 lg:p-8 max-w-7xl mx-auto w-full">
          {children}
        </main>
      </div>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-4 px-6 text-center text-xs text-slate-500">
        VERA Multi-Modal Fraud Detection Platform • MNC Production-Ready Architecture
      </footer>
    </div>
  );
}
