/**
 * VERA Client Observability & Performance Telemetry
 *
 * Tracks:
 * - API errors & status codes
 * - Analyzer latencies & timeouts
 * - Agent execution metrics
 * - Page load & investigation start latencies
 * - Report generation turnaround
 *
 * Security Invariant:
 * Never sends authorization tokens, credentials, or raw sensitive evidence to remote telemetry.
 */

export interface PerformanceMetrics {
  pageLoadMs?: number;
  apiLatencyMs?: number;
  investigationStartLatencyMs?: number;
  queueLatencyMs?: number;
  analyzerLatencyMs?: number;
  reportGenerationLatencyMs?: number;
}

class ClientTelemetry {
  private metrics: PerformanceMetrics = {};
  private errorLog: Array<{ timestamp: string; message: string; category: string }> = [];

  constructor() {
    if (typeof window !== "undefined") {
      this.measurePageLoad();
    }
  }

  private measurePageLoad() {
    window.addEventListener("load", () => {
      const perfEntries = performance.getEntriesByType("navigation") as PerformanceNavigationTiming[];
      if (perfEntries.length > 0) {
        this.metrics.pageLoadMs = Math.round(perfEntries[0].duration);
      }
    });
  }

  public recordMetric(metricName: keyof PerformanceMetrics, durationMs: number) {
    this.metrics[metricName] = Math.round(durationMs);
  }

  public getMetrics(): PerformanceMetrics {
    return { ...this.metrics };
  }

  public trackError(category: "API" | "ANALYZER" | "AGENT" | "QUEUE" | "DATABASE" | "FRONTEND", error: unknown) {
    const errorMsg = error instanceof Error ? error.message : String(error);
    const sanitizedMsg = this.sanitizeSensitiveData(errorMsg);

    this.errorLog.push({
      timestamp: new Date().toISOString(),
      category,
      message: sanitizedMsg,
    });

    // In production with SENTRY_DSN configured:
    // (window as any).Sentry?.captureException(new Error(`[${category}] ${sanitizedMsg}`));
  }

  private sanitizeSensitiveData(input: string): string {
    return input
      .replace(/bearer\s+[a-zA-Z0-9_\-\.]+/gi, "Bearer ***REDACTED***")
      .replace(/key=[a-zA-Z0-9_\-]+/gi, "key=***REDACTED***")
      .replace(/password=[^\s&]+/gi, "password=***REDACTED***");
  }

  public getErrors() {
    return [...this.errorLog];
  }
}

export const telemetry = new ClientTelemetry();
