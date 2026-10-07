"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { User } from "@/types/auth";

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  register: (email: string, password: string, fullName: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// MOCK: Temporary mock user for UI testing until backend auth is connected
const MOCK_INITIAL_USER: User = {
  id: "usr_mock_001",
  email: "analyst@garuda.defense",
  full_name: "Defense Analyst",
  role: "user",
  is_active: true,
  email_verified_at: "2026-10-07T12:00:00Z",
  created_at: "2026-10-01T00:00:00Z",
};

export function AuthProvider({ children }: { children: React.ReactNode }) {
  // MOCK: Default to mock user so that app shell pages can be previewed immediately,
  // while allowing easy toggle via logout / login in the browser.
  const [user, setUser] = useState<User | null>(MOCK_INITIAL_USER);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  useEffect(() => {
    // Check local storage / session state if saved
    const savedUser = typeof window !== "undefined" ? localStorage.getItem("garuda_mock_user") : null;
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch {
        setUser(MOCK_INITIAL_USER); // MOCK
      }
    }
  }, []);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    // MOCK: Simulating API response against ARCHITECTURE Section 6 contract
    await new Promise((resolve) => setTimeout(resolve, 600));
    setIsLoading(false);

    if (password.length < 8) {
      return { success: false, error: "Password must be at least 8 characters." };
    }

    const newUser: User = {
      id: "usr_mock_" + Math.random().toString(36).substring(7),
      email,
      full_name: email.split("@")[0].toUpperCase() || "Security Officer",
      role: "user",
      is_active: true,
      email_verified_at: new Date().toISOString(),
      created_at: new Date().toISOString(),
    };

    setUser(newUser);
    if (typeof window !== "undefined") {
      localStorage.setItem("garuda_mock_user", JSON.stringify(newUser));
    }
    return { success: true };
  };

  const register = async (email: string, password: string, fullName: string) => {
    setIsLoading(true);
    // MOCK: Simulating API response against ARCHITECTURE Section 6 contract
    await new Promise((resolve) => setTimeout(resolve, 600));
    setIsLoading(false);

    if (password.length < 8) {
      return { success: false, error: "Password must be at least 8 characters." };
    }

    const newUser: User = {
      id: "usr_mock_" + Math.random().toString(36).substring(7),
      email,
      full_name: fullName,
      role: "user",
      is_active: true,
      email_verified_at: null,
      created_at: new Date().toISOString(),
    };

    setUser(newUser);
    if (typeof window !== "undefined") {
      localStorage.setItem("garuda_mock_user", JSON.stringify(newUser));
    }
    return { success: true };
  };

  const logout = async () => {
    setUser(null);
    if (typeof window !== "undefined") {
      localStorage.removeItem("garuda_mock_user");
    }
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
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
