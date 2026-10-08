"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { User } from "@/types/auth";
import { authApi, setAccessToken, onSessionExpired, ApiClientError } from "@/lib/api-client";

export interface AuthResult {
  success: boolean;
  user?: User;
  error?: string;
  code?: string;
  details?: Record<string, string[] | string>;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<AuthResult>;
  register: (email: string, password: string, fullName: string) => Promise<AuthResult>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Subscribe to session expiration events from api-client
  useEffect(() => {
    const unsubscribe = onSessionExpired(() => {
      setUser(null);
    });
    return unsubscribe;
  }, []);

  // Restore session on page load per ARCHITECTURE Section 6:
  // POST /api/auth/refresh to rotate/restore session, then GET /api/auth/me for user details.
  useEffect(() => {
    let isMounted = true;

    async function restoreSession() {
      try {
        const refreshRes = await authApi.refresh();
        if (refreshRes.access_token) {
          setAccessToken(refreshRes.access_token);
          const meRes = await authApi.getMe();
          if (isMounted) {
            setUser(meRes.user);
          }
        }
      } catch {
        // No valid session or expired refresh token; keep user as null
        setAccessToken(null);
        if (isMounted) {
          setUser(null);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    restoreSession();

    return () => {
      isMounted = false;
    };
  }, []);

  const login = useCallback(async (email: string, password: string): Promise<AuthResult> => {
    try {
      const res = await authApi.login({ email, password });
      setAccessToken(res.access_token);
      setUser(res.user);
      return { success: true, user: res.user };
    } catch (err: unknown) {
      if (err instanceof ApiClientError) {
        return {
          success: false,
          error: err.message,
          code: err.code,
          details: err.details,
        };
      }
      return {
        success: false,
        error: err instanceof Error ? err.message : "Failed to authenticate.",
      };
    }
  }, []);

  const register = useCallback(
    async (email: string, password: string, fullName: string): Promise<AuthResult> => {
      try {
        const res = await authApi.register({
          email,
          password,
          full_name: fullName,
        });
        setAccessToken(res.access_token);
        setUser(res.user);
        return { success: true, user: res.user };
      } catch (err: unknown) {
        if (err instanceof ApiClientError) {
          return {
            success: false,
            error: err.message,
            code: err.code,
            details: err.details,
          };
        }
        return {
          success: false,
          error: err instanceof Error ? err.message : "Failed to register account.",
        };
      }
    },
    []
  );

  const logout = useCallback(async (): Promise<void> => {
    try {
      await authApi.logout();
    } catch {
      // Ignore network errors on logout
    } finally {
      setAccessToken(null);
      setUser(null);
    }
  }, []);

  const refreshUser = useCallback(async (): Promise<void> => {
    try {
      const meRes = await authApi.getMe();
      setUser(meRes.user);
    } catch {
      // Ignore
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
