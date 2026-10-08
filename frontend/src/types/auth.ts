// Types matching docs/ARCHITECTURE.md Section 6

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: "user" | "admin" | string;
  is_active: boolean;
  email_verified_at: string | null;
  created_at?: string | null;
}

export interface AuthResponse {
  user: User;
  access_token: string;
  token_type: string;
}

export interface TokenRefreshResponse {
  access_token: string;
  token_type: string;
}

export interface UserMeResponse {
  user: User;
}

export interface MessageResponse {
  message: string;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Record<string, string[] | string>;
  };
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}
