import { ApiError } from "@/types/auth";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

let memoryAccessToken: string | null = null;

export function setAccessToken(token: string | null) {
  memoryAccessToken = token;
}

export function getAccessToken(): string | null {
  return memoryAccessToken;
}

export class ApiClientError extends Error {
  code: string;
  details?: Record<string, string>;

  constructor(message: string, code = "UNKNOWN_ERROR", details?: Record<string, string>) {
    super(message);
    this.name = "ApiClientError";
    this.code = code;
    this.details = details;
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

  if (memoryAccessToken) {
    headers["Authorization"] = `Bearer ${memoryAccessToken}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: "include", // for httpOnly refresh cookies
  });

  if (!response.ok) {
    let errorData: ApiError | null = null;
    try {
      errorData = await response.json();
    } catch {
      // not JSON
    }

    if (errorData?.error) {
      throw new ApiClientError(
        errorData.error.message,
        errorData.error.code,
        errorData.error.details
      );
    }

    throw new ApiClientError(
      `Request failed with status ${response.status}`,
      `HTTP_${response.status}`
    );
  }

  return response.json();
}
