/**
 * API Client - TypeScript client for Backend API
 * Handles all API communication with error handling and retry logic
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface H3GridRequest {
  center_lat: number;
  center_lng: number;
  scale: 'neighborhood' | 'city' | 'region';
  region_name: string;
}

export interface H3Cell {
  h3_index: string;
  center_lat: number;
  center_lng: number;
  boundary: Array<[number, number]>;
}

export interface H3GridResponse {
  success: boolean;
  cells: H3Cell[];
  center: { lat: number; lng: number };
  resolution: number;
  scale: string;
}

export interface ContextSpaceAnalysisRequest {
  region_name: string;
  year_offset?: number;
  scenario?: string;
  scale?: 'neighborhood' | 'city' | 'region';
}

export interface RiskScores {
  hazard: number;
  exposure: number;
  vulnerability: number;
  total_risk: number;
}

export interface ActionRecommendation {
  id: string;
  type: string;
  icon: string;
  title: string;
  measures: string[];
  cost: number;
  timeline: string;
  co_benefits: string[];
  sources: string[];
}

export interface CellData {
  h3_index: string;
  center: { lat: number; lng: number };
  boundary: Array<[number, number]>;
  risk_scores: RiskScores;
  color: { r: number; g: number; b: number; alpha: number };
  recommendations: ActionRecommendation[];
}

export interface ContextSpaceAnalysisResponse {
  success: boolean;
  region_name: string;
  scenario: string;
  year: number;
  scale: string;
  cells: CellData[];
  center: { lat: number; lng: number };
}

class ApiClient {
  private baseUrl: string;
  private maxRetries: number = 3;
  private retryDelay: number = 1000; // ms

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async fetchWithRetry(
    url: string,
    options: RequestInit = {},
    retries: number = this.maxRetries
  ): Promise<Response> {
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      if (!response.ok) {
        if (retries > 0 && response.status >= 500) {
          // Retry on server errors
          await new Promise(resolve => setTimeout(resolve, this.retryDelay));
          return this.fetchWithRetry(url, options, retries - 1);
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return response;
    } catch (error) {
      if (retries > 0) {
        await new Promise(resolve => setTimeout(resolve, this.retryDelay));
        return this.fetchWithRetry(url, options, retries - 1);
      }
      throw error;
    }
  }

  async generateH3Grid(request: H3GridRequest): Promise<H3GridResponse> {
    const response = await this.fetchWithRetry(`${this.baseUrl}/api/h3/grid`, {
      method: 'POST',
      body: JSON.stringify(request),
    });

    return response.json();
  }

  async analyzeContextSpace(
    request: ContextSpaceAnalysisRequest
  ): Promise<ContextSpaceAnalysisResponse> {
    const response = await this.fetchWithRetry(
      `${this.baseUrl}/api/context-space/analyze`,
      {
        method: 'POST',
        body: JSON.stringify({
          year_offset: request.year_offset || 5,
          scenario: request.scenario || 'SSP2-4.5',
          scale: request.scale || 'city',
          ...request,
        }),
      }
    );

    return response.json();
  }

  async getTensor(h3Index: string, year?: number): Promise<any> {
    const url = new URL(`${this.baseUrl}/api/tensor/${h3Index}`);
    if (year) {
      url.searchParams.set('year', year.toString());
    }

    const response = await this.fetchWithRetry(url.toString());
    return response.json();
  }

  async simulateSSP(
    regionName: string,
    scenario: string = 'SSP2-4.5',
    year: number = 2050
  ): Promise<any> {
    const url = new URL(`${this.baseUrl}/api/ssp/simulate`);
    url.searchParams.set('region_name', regionName);
    url.searchParams.set('scenario', scenario);
    url.searchParams.set('year', year.toString());

    const response = await this.fetchWithRetry(url.toString());
    return response.json();
  }

  async calculateRisk(
    h3Index: string,
    scenario?: string
  ): Promise<{ success: boolean; h3_index: string; risk_scores: RiskScores }> {
    const url = new URL(`${this.baseUrl}/api/risk/calculate`);
    url.searchParams.set('h3_index', h3Index);
    if (scenario) {
      url.searchParams.set('scenario', scenario);
    }

    const response = await this.fetchWithRetry(url.toString());
    return response.json();
  }

  async recommendActions(
    h3Index: string,
    riskScore?: number
  ): Promise<{
    success: boolean;
    h3_index: string;
    recommendations: ActionRecommendation[];
  }> {
    const url = new URL(`${this.baseUrl}/api/actions/recommend`);
    url.searchParams.set('h3_index', h3Index);
    if (riskScore !== undefined) {
      url.searchParams.set('risk_score', riskScore.toString());
    }

    const response = await this.fetchWithRetry(url.toString());
    return response.json();
  }
}

export const apiClient = new ApiClient();


