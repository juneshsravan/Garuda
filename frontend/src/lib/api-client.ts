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
import { DashboardStatsResponse } from "@/types/dashboard";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Access token kept strictly in memory per ARCHITECTURE Section 6
let memoryAccessToken: string | null = null;

// Single in-flight refresh promise mutex (Requirement 2)
let refreshPromise: Promise<string | null> | null = null;

// Proactive refresh timer reference (Requirement 3)
let proactiveRefreshTimer: ReturnType<typeof setTimeout> | null = null;

// Session expiration subscribers (e.g. AuthProvider)
type SessionExpiredCallback = () => void;
const sessionExpiredCallbacks: Set<SessionExpiredCallback> = new Set();

export function onSessionExpired(callback: SessionExpiredCallback): () => void {
  sessionExpiredCallbacks.add(callback);
  return () => {
    sessionExpiredCallbacks.delete(callback);
  };
}

/**
 * Extracts expiration timestamp (in seconds) from a JWT without external libraries.
 */
function decodeJwtExpiry(token: string): number | null {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    const base64Url = parts[1];
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const jsonStr = decodeURIComponent(
      atob(base64)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join("")
    );
    const parsed = JSON.parse(jsonStr);
    return typeof parsed.exp === "number" ? parsed.exp : null;
  } catch {
    return null;
  }
}

/**
 * Cancels any active proactive refresh timer.
 */
function clearProactiveRefresh(): void {
  if (proactiveRefreshTimer) {
    clearTimeout(proactiveRefreshTimer);
    proactiveRefreshTimer = null;
  }
}

/**
 * Schedules a proactive session refresh about 1 minute before token expiry.
 */
function scheduleProactiveRefresh(token: string): void {
  clearProactiveRefresh();

  const expSeconds = decodeJwtExpiry(token);
  if (!expSeconds) return;

  const expMs = expSeconds * 1000;
  const now = Date.now();
  const timeUntilExp = expMs - now;

  let delayMs: number;
  if (timeUntilExp > 75_000) {
    // Standard access token (e.g., 15 mins): refresh 1 minute (60s) before expiration
    delayMs = timeUntilExp - 60_000;
  } else if (timeUntilExp > 10_000) {
    // Short-lived token (e.g., 1 min TTL for testing): refresh midway or at least 5s
    delayMs = Math.max(5_000, Math.floor(timeUntilExp / 2));
  } else if (timeUntilExp > 0) {
    // Imminent expiration (< 10 seconds): refresh almost immediately
    delayMs = 1_000;
  } else {
    // Already expired
    return;
  }

  proactiveRefreshTimer = setTimeout(async () => {
    try {
      await refreshAccessToken();
    } catch {
      // Proactive refresh failed; reactive 401 handler will handle on next request
    }
  }, delayMs);
}

export function setAccessToken(token: string | null): void {
  memoryAccessToken = token;
  if (token) {
    scheduleProactiveRefresh(token);
  } else {
    clearProactiveRefresh();
  }
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

/**
 * Handles terminal session expiration:
 * Clears token, notifies listeners, preserves typed draft message,
 * and redirects to /login with a friendly message.
 */
export function handleSessionExpired(): void {
  setAccessToken(null);

  sessionExpiredCallbacks.forEach((cb) => {
    try {
      cb();
    } catch {
      // ignore
    }
  });

  if (typeof window !== "undefined") {
    const pathname = window.location.pathname;
    // Don't redirect if already on public/auth routes
    if (pathname !== "/login" && pathname !== "/register" && pathname !== "/") {
      const returnUrl = encodeURIComponent(pathname + window.location.search);
      const friendlyMsg = encodeURIComponent("Your session expired, please sign in again");
      window.location.href = `/login?message=${friendlyMsg}&returnUrl=${returnUrl}`;
    }
  }
}

/**
 * Performs a single token refresh against POST /api/auth/refresh.
 * Mutexed with refreshPromise so simultaneous requests wait on ONE refresh call.
 */
export async function refreshAccessToken(): Promise<string | null> {
  // If a refresh is already in-flight, return the existing promise so callers wait for it
  if (refreshPromise) {
    return refreshPromise;
  }

  refreshPromise = (async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include", // required for httpOnly SameSite=Lax cookie
      });

      if (!response.ok) {
        // Refresh token itself expired or revoked
        handleSessionExpired();
        return null;
      }

      const data: TokenRefreshResponse = await response.json();
      const newToken = data.access_token || null;
      setAccessToken(newToken);
      return newToken;
    } catch {
      return null;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
  isRetry = false
): Promise<T> {
  // If analyzing a message, ensure the draft text is preserved in sessionStorage so it isn't lost
  if (typeof window !== "undefined" && endpoint === "/api/analyze/message" && options.body) {
    try {
      const parsed = JSON.parse(options.body as string);
      if (parsed?.text) {
        sessionStorage.setItem("garuda_draft_message", parsed.text);
      }
    } catch {
      // ignore
    }
  }

  const isAuthEndpoint =
    endpoint === "/api/auth/refresh" ||
    endpoint === "/api/auth/login" ||
    endpoint === "/api/auth/register";

  // If a token refresh is currently in progress and this is not an auth endpoint,
  // wait for it to complete so we use the brand-new token immediately.
  if (!isAuthEndpoint && refreshPromise) {
    await refreshPromise;
  }

  const url = `${API_BASE_URL}${endpoint}`;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  // If we have an in-memory access token, attach Bearer header
  if (memoryAccessToken) {
    headers["Authorization"] = `Bearer ${memoryAccessToken}`;
  }

  let response: Response;
  try {
    response = await fetch(url, {
      ...options,
      headers,
      credentials: "include", // Required for httpOnly SameSite=Lax refresh cookie
    });
  } catch (netErr) {
    throw new ApiClientError(
      netErr instanceof Error ? netErr.message : "Network request failed",
      "NETWORK_ERROR"
    );
  }

  // Handle 401 Unauthorized for non-auth endpoints
  if (response.status === 401 && !isRetry && !isAuthEndpoint) {
    // 1. Call POST /api/auth/refresh (single in-flight refresh)
    const newToken = await refreshAccessToken();

    if (newToken) {
      // 2. Retry the original request once with the new access token
      const retryHeaders: Record<string, string> = {
        ...(options.headers as Record<string, string>),
        "Content-Type": "application/json",
        Authorization: `Bearer ${newToken}`,
      };
      return apiRequest<T>(
        endpoint,
        {
          ...options,
          headers: retryHeaders,
        },
        true // mark as retry
      );
    } else {
      // Refresh failed (refresh token expired/revoked)
      throw new ApiClientError(
        "Your session expired, please sign in again",
        "SESSION_EXPIRED",
        undefined,
        401
      );
    }
  }

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

export const dashboardApi = {
  getStats(): Promise<DashboardStatsResponse> {
    return apiRequest<DashboardStatsResponse>("/api/dashboard/stats", {
      method: "GET",
    });
  },
};

