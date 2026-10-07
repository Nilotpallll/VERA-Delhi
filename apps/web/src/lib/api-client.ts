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
} from "@vera/contracts";

const API_BASE_URL = process.env.NEXT_PUBLIC_VERA_API_URL || "http://localhost:8000";

class VeraApiClient {
  private readonly baseUrl: string;
  private readonly versionPrefix: string;

  constructor() {
    this.baseUrl = API_BASE_URL.replace(/\/$/, "");
    this.versionPrefix = VERA_API_PREFIX;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${this.versionPrefix}${endpoint}`;
    const headers = {
      "Content-Type": "application/json",
      "Accept": "application/json",
      ...(options.headers || {}),
    };

    const response = await fetch(url, { ...options, headers });
    if (!response.ok) {
      const errorBody = await response.text();
      throw new Error(`VERA API Error [${response.status}] ${url}: ${errorBody}`);
    }

    return response.json() as Promise<T>;
  }

  /**
   * Health check contract endpoint
   */
  async getHealth(): Promise<HealthCheckResponse> {
    // Health is exposed at root and at /api/v1/health
    return this.request<HealthCheckResponse>("/health");
  }

  /**
   * Create new fraud investigation
   */
  async createInvestigation(data: InvestigationCreateRequest): Promise<InvestigationResponse> {
    return this.request<InvestigationResponse>("/investigations", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  /**
   * Retrieve investigation by ID
   */
  async getInvestigation(id: string): Promise<InvestigationResponse> {
    return this.request<InvestigationResponse>(`/investigations/${id}`);
  }
}

export const veraApi = new VeraApiClient();
