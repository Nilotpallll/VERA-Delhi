/**
 * VERA Frontend API Client
 * Architecture Rule 1: Frontend communicates only through API contracts.
 * Architecture Rule 2: API contracts are versioned.
 */

import {
  VERA_API_PREFIX,
  HealthCheckResponse,
  InvestigationResponse,
  InvestigationCreateRequest,
  AgentRunRequest,
  AgentRunResponse,
  AgentForensicReport,
} from "@vera/contracts";

function resolveApiBaseUrl(): string {
  if (process.env.NEXT_PUBLIC_API_URL) return process.env.NEXT_PUBLIC_API_URL;
  if (process.env.NEXT_PUBLIC_VERA_API_URL) return process.env.NEXT_PUBLIC_VERA_API_URL;
  if (typeof window !== "undefined") {
    if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
      return "http://localhost:8000";
    }
  }
  return "https://vera-delhi-ldfinal.onrender.com";
}

const API_BASE_URL = resolveApiBaseUrl();

export interface ApiClientOptions {
  apiKey?: string;
  authToken?: string;
  idempotencyKey?: string;
}

export class VeraApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly statusText: string,
    public readonly data: any,
    public readonly requestId?: string
  ) {
    super(`VERA API Error [${status}]: ${typeof data === "string" ? data : JSON.stringify(data)}`);
    this.name = "VeraApiError";
  }
}

class VeraApiClient {
  private readonly baseUrl: string;
  private readonly versionPrefix: string;
  private apiKey?: string;
  private authToken?: string;

  constructor(options?: ApiClientOptions) {
    this.baseUrl = API_BASE_URL.replace(/\/$/, "");
    this.versionPrefix = VERA_API_PREFIX;
    this.apiKey = options?.apiKey || process.env.NEXT_PUBLIC_VERA_API_KEY;
    this.authToken = options?.authToken;
  }

  public setAuthToken(token: string) {
    this.authToken = token;
  }

  public setApiKey(key: string) {
    this.apiKey = key;
  }

  private generateRequestId(): string {
    return `req_ui_${Math.random().toString(36).substring(2, 10)}`;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    customOptions?: ApiClientOptions
  ): Promise<T> {
    const url = `${this.baseUrl}${this.versionPrefix}${endpoint}`;
    const requestId = this.generateRequestId();

    const headers: Record<string, string> = {
      Accept: "application/json",
      "X-Request-ID": requestId,
      ...(options.headers as Record<string, string> || {}),
    };

    if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }

    const key = customOptions?.apiKey || this.apiKey;
    if (key) {
      headers["X-API-Key"] = key;
    }

    const token = customOptions?.authToken || this.authToken;
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    if (customOptions?.idempotencyKey) {
      headers["Idempotency-Key"] = customOptions.idempotencyKey;
    }

    const response = await fetch(url, { ...options, headers });
    const responseRequestId = response.headers.get("X-Request-ID") || requestId;

    if (!response.ok) {
      let errorBody: any;
      try {
        errorBody = await response.json();
      } catch {
        errorBody = await response.text();
      }
      throw new VeraApiError(response.status, response.statusText, errorBody, responseRequestId);
    }

    return response.json() as Promise<T>;
  }

  /**
   * Health check contract endpoint
   */
  async getHealth(): Promise<HealthCheckResponse> {
    return this.request<HealthCheckResponse>("/health");
  }

  /**
   * Create new fraud investigation
   */
  async createInvestigation(
    data: InvestigationCreateRequest,
    options?: { idempotencyKey?: string }
  ): Promise<InvestigationResponse> {
    return this.request<InvestigationResponse>(
      "/investigations",
      {
        method: "POST",
        body: JSON.stringify(data),
      },
      { idempotencyKey: options?.idempotencyKey }
    );
  }

  /**
   * Retrieve investigation by ID
   */
  async getInvestigation(id: string): Promise<InvestigationResponse> {
    return this.request<InvestigationResponse>(`/investigations/${id}`);
  }

  /**
   * Upload evidence file
   */
  async uploadFile(file: File): Promise<any> {
    const formData = new FormData();
    formData.append("file", file);

    return this.request<any>("/uploads", {
      method: "POST",
      body: formData,
    });
  }

  // ── Phase 6: Agent methods ────────────────────────────────────────────────

  /**
   * Run the VERA LangGraph investigator agent on an investigation.
   * POST /api/v1/investigations/{id}/run-agent
   */
  async runAgent(
    investigationId: string,
    data: AgentRunRequest
  ): Promise<AgentRunResponse> {
    return this.request<AgentRunResponse>(
      `/investigations/${investigationId}/run-agent`,
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    );
  }

  /**
   * Retrieve the stored VERA agent forensic report.
   * GET /api/v1/investigations/{id}/agent-report
   */
  async getAgentReport(investigationId: string): Promise<AgentForensicReport> {
    return this.request<AgentForensicReport>(
      `/investigations/${investigationId}/agent-report`
    );
  }
}

export const veraApi = new VeraApiClient();
