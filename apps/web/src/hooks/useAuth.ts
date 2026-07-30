"use client";

import { create } from "zustand";

import { NetworkError, api } from "@/lib/api";
import {
  clearTokens,
  getAccessToken,
  getCachedUser,
  getRefreshToken,
  setCachedUser,
  setTokens,
} from "@/lib/auth-storage";
import type { TokenPair, UserRead } from "@/lib/types";

const LOCAL_GUEST_USER: UserRead = {
  id: "local-guest",
  email: "",
  display_name: "Guest (offline)",
  role: "user",
  preferred_language: "en",
  is_active: true,
  is_guest: true,
  is_verified: true,
};

interface AuthState {
  user: UserRead | null;
  status: "idle" | "loading" | "authenticated" | "unauthenticated";
  // True once a real session exists but the last attempt to confirm/use it
  // hit a NetworkError rather than a rejection from the server — the
  // account itself may be perfectly valid, StromeX just couldn't reach the
  // backend to prove it. Never true alongside a genuine auth failure.
  isOffline: boolean;
  // True only for the local-only guest fallback created when "Continue as
  // Guest" itself can't reach the backend — this session has no real
  // tokens and nothing typed here reaches a server until the app is
  // reopened with connectivity, at which point a real guest account takes
  // its place.
  isLocalGuest: boolean;
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
  isOffline: false,
  isLocalGuest: false,

  async login(email, password) {
    set({ status: "loading" });
    const pair = await api.post<TokenPair>("/api/v1/auth/login", { email, password }, false);
    setTokens(pair.access_token, pair.refresh_token);
    const user = await api.get<UserRead>("/api/v1/auth/me");
    setCachedUser(user);
    set({ user, status: "authenticated", isOffline: false, isLocalGuest: false });
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
    setCachedUser(user);
    set({ user, status: "authenticated", isOffline: false, isLocalGuest: false });
  },

  async loginAsGuest() {
    set({ status: "loading" });
    try {
      const pair = await api.post<TokenPair>("/api/v1/auth/guest", undefined, false);
      setTokens(pair.access_token, pair.refresh_token);
      const user = await api.get<UserRead>("/api/v1/auth/me");
      setCachedUser(user);
      set({ user, status: "authenticated", isOffline: false, isLocalGuest: false });
    } catch (err) {
      if (!(err instanceof NetworkError)) throw err; // a real server rejection — let the caller show it
      // The whole point of Guest mode is instant entry with zero setup —
      // that has to hold even when the backend itself is unreachable, so
      // fall back to a local-only identity rather than blocking entry.
      // Nothing typed in this state is sent anywhere; it starts a real
      // guest account automatically the next time the app opens with
      // connectivity.
      set({ user: LOCAL_GUEST_USER, status: "authenticated", isOffline: true, isLocalGuest: true });
    }
  },

  async upgradeGuest(email, password, displayName) {
    const user = await api.post<UserRead>("/api/v1/auth/guest/upgrade", {
      email,
      password,
      display_name: displayName,
    });
    setCachedUser(user);
    set({ user });
  },

  async adoptSession(accessToken, refreshToken) {
    set({ status: "loading" });
    setTokens(accessToken, refreshToken);
    const user = await api.get<UserRead>("/api/v1/auth/me");
    setCachedUser(user);
    set({ user, status: "authenticated", isOffline: false, isLocalGuest: false });
  },

  async logoutAllDevices() {
    await api.post("/api/v1/auth/logout-all");
    clearTokens();
    set({ user: null, status: "unauthenticated", isOffline: false, isLocalGuest: false });
  },

  async deleteAccount(password) {
    await api.delete("/api/v1/auth/me", password ? { password } : {});
    clearTokens();
    set({ user: null, status: "unauthenticated", isOffline: false, isLocalGuest: false });
  },

  async logout() {
    const refreshToken = getRefreshToken();
    clearTokens();
    set({ user: null, status: "unauthenticated", isOffline: false, isLocalGuest: false });
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
      setCachedUser(user);
      set({ user, status: "authenticated", isOffline: false, isLocalGuest: false });
    } catch (err) {
      if (err instanceof NetworkError) {
        // A real session exists (there's a token) — the network, not the
        // account, is the problem. Trust the last confirmed identity rather
        // than forcing the user back through a sign-in screen for
        // something a login prompt can't fix anyway.
        const cached = getCachedUser();
        set({ user: cached, status: "authenticated", isOffline: true, isLocalGuest: false });
        return;
      }
      // A real rejection from the server (expired/revoked/invalid token) —
      // this is a genuine "you're signed out," not a connectivity blip.
      clearTokens();
      set({ user: null, status: "unauthenticated", isOffline: false, isLocalGuest: false });
    }
  },
}));
