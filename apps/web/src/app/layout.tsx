import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "VERA | Investment-Fraud Investigation Platform",
  description: "MNC-grade agentic platform for multi-modal investment fraud analysis, forensic APK inspection, deepfake detection, and deterministic risk attribution.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased min-h-screen bg-slate-950 text-slate-100">
        {children}
      </body>
    </html>
  );
}
