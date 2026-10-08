import {
  ApiError,
  AuthResponse,
  LoginRequest,
  MessageResponse,
  RegisterRequest,
  TokenRefreshResponse,
  UserMeResponse,
} from "@/types/auth";
import {
  AnalysisResponse,
  ScanListResponse,
} from "@/types/analysis";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Access token kept strictly in memory per ARCHITECTURE Section 6
let memoryAccessToken: string | null = null;

export function setAccessToken(token: string | null): void {
  memoryAccessToken = token;
}

export function getAccessToken(): string | null {
  return memoryAccessToken;
}

export class ApiClientError extends Error {
  code: string;
  details?: Record<string, string[] | string>;
  status?: number;

  constructor(
    message: string,
    code = "UNKNOWN_ERROR",
    details?: Record<string, string[] | string>,
    status?: number
  ) {
    super(message);
    this.name = "ApiClientError";
    this.code = code;
    this.details = details;
    this.status = status;
  }
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  // If we have an in-memory access token, attach Bearer header
  if (memoryAccessToken) {
    headers["Authorization"] = `Bearer ${memoryAccessToken}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: "include", // Required for httpOnly SameSite=Lax refresh cookie
  });

  if (!response.ok) {
    let errorData: ApiError | null = null;
    try {
      errorData = await response.json();
    } catch {
      // Body is not JSON
    }

    if (errorData?.error) {
      throw new ApiClientError(
        errorData.error.message,
        errorData.error.code,
        errorData.error.details,
        response.status
      );
    }

    throw new ApiClientError(
      `Request failed with status ${response.status}`,
      `HTTP_${response.status}`,
      undefined,
      response.status
    );
  }

  return response.json();
}

/**
 * Typed API Client matching docs/ARCHITECTURE.md Section 6
 */
export const authApi = {
  register(data: RegisterRequest): Promise<AuthResponse> {
    return apiRequest<AuthResponse>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  login(data: LoginRequest): Promise<AuthResponse> {
    return apiRequest<AuthResponse>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  refresh(): Promise<TokenRefreshResponse> {
    return apiRequest<TokenRefreshResponse>("/api/auth/refresh", {
      method: "POST",
    });
  },

  logout(): Promise<MessageResponse> {
    return apiRequest<MessageResponse>("/api/auth/logout", {
      method: "POST",
    });
  },

  getMe(): Promise<UserMeResponse> {
    return apiRequest<UserMeResponse>("/api/auth/me", {
      method: "GET",
    });
  },
};

export const scanApi = {
  analyzeMessage(data: { text: string; save: boolean }): Promise<AnalysisResponse> {
    return apiRequest<AnalysisResponse>("/api/analyze/message", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  listScans(params: {
    limit?: number;
    cursor?: string | null;
    scan_type?: string | null;
    risk_level?: string | null;
  } = {}): Promise<ScanListResponse> {
    const query = new URLSearchParams();
    if (params.limit) query.set("limit", String(params.limit));
    if (params.cursor) query.set("cursor", params.cursor);
    if (params.scan_type && params.scan_type !== "all") query.set("scan_type", params.scan_type);
    if (params.risk_level && params.risk_level !== "all") query.set("risk_level", params.risk_level);

    const qs = query.toString();
    return apiRequest<ScanListResponse>(`/api/scans${qs ? `?${qs}` : ""}`, {
      method: "GET",
    });
  },

  getScan(id: string): Promise<AnalysisResponse> {
    return apiRequest<AnalysisResponse>(`/api/scans/${id}`, {
      method: "GET",
    });
  },

  deleteScan(id: string): Promise<MessageResponse> {
    return apiRequest<MessageResponse>(`/api/scans/${id}`, {
      method: "DELETE",
    });
  },
};
