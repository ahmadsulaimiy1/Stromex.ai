"use client";

import { create } from "zustand";

import { api } from "@/lib/api";
import { clearTokens, getAccessToken, getRefreshToken, setTokens } from "@/lib/auth-storage";
import type { TokenPair, UserRead } from "@/lib/types";

interface AuthState {
  user: UserRead | null;
  status: "idle" | "loading" | "authenticated" | "unauthenticated";
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, displayName: string) => Promise<void>;
  loginAsGuest: () => Promise<void>;
  upgradeGuest: (email: string, password: string, displayName: string) => Promise<void>;
  adoptSession: (accessToken: string, refreshToken: string) => Promise<void>;
  logout: () => Promise<void>;
  logoutAllDevices: () => Promise<void>;
  deleteAccount: (password?: string) => Promise<void>;
  hydrate: () => Promise<void>;
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  status: "idle",

  async login(email, password) {
    set({ status: "loading" });
    const pair = await api.post<TokenPair>("/api/v1/auth/login", { email, password }, false);
    setTokens(pair.access_token, pair.refresh_token);
    const user = await api.get<UserRead>("/api/v1/auth/me");
    set({ user, status: "authenticated" });
  },

  async register(email, password, displayName) {
    set({ status: "loading" });
    await api.post(
      "/api/v1/auth/register",
      { email, password, display_name: displayName },
      false,
    );
    const pair = await api.post<TokenPair>("/api/v1/auth/login", { email, password }, false);
    setTokens(pair.access_token, pair.refresh_token);
    const user = await api.get<UserRead>("/api/v1/auth/me");
    set({ user, status: "authenticated" });
  },

  async loginAsGuest() {
    set({ status: "loading" });
    const pair = await api.post<TokenPair>("/api/v1/auth/guest", undefined, false);
    setTokens(pair.access_token, pair.refresh_token);
    const user = await api.get<UserRead>("/api/v1/auth/me");
    set({ user, status: "authenticated" });
  },

  async upgradeGuest(email, password, displayName) {
    const user = await api.post<UserRead>("/api/v1/auth/guest/upgrade", {
      email,
      password,
      display_name: displayName,
    });
    set({ user });
  },

  async adoptSession(accessToken, refreshToken) {
    set({ status: "loading" });
    setTokens(accessToken, refreshToken);
    const user = await api.get<UserRead>("/api/v1/auth/me");
    set({ user, status: "authenticated" });
  },

  async logoutAllDevices() {
    await api.post("/api/v1/auth/logout-all");
    clearTokens();
    set({ user: null, status: "unauthenticated" });
  },

  async deleteAccount(password) {
    await api.delete("/api/v1/auth/me", password ? { password } : {});
    clearTokens();
    set({ user: null, status: "unauthenticated" });
  },

  async logout() {
    const refreshToken = getRefreshToken();
    clearTokens();
    set({ user: null, status: "unauthenticated" });
    if (refreshToken) {
      // Best-effort: revoke server-side so the refresh token can't mint new
      // access tokens if it leaked. Local sign-out already happened above
      // regardless of whether this call succeeds.
      try {
        await api.post("/api/v1/auth/logout", { refresh_token: refreshToken }, false);
      } catch {
        // Network error or already-invalid token — nothing more to do.
      }
    }
  },

  async hydrate() {
    if (!getAccessToken()) {
      set({ status: "unauthenticated" });
      return;
    }
    set({ status: "loading" });
    try {
      const user = await api.get<UserRead>("/api/v1/auth/me");
      set({ user, status: "authenticated" });
    } catch {
      clearTokens();
      set({ user: null, status: "unauthenticated" });
    }
  },
}));
