"use client";

import type { UserRead } from "./types";

const ACCESS_KEY = "stromex.access_token";
const REFRESH_KEY = "stromex.refresh_token";
const USER_CACHE_KEY = "stromex.cached_user";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(REFRESH_KEY);
}

export function setTokens(access: string, refresh: string): void {
  window.localStorage.setItem(ACCESS_KEY, access);
  window.localStorage.setItem(REFRESH_KEY, refresh);
}

export function clearTokens(): void {
  window.localStorage.removeItem(ACCESS_KEY);
  window.localStorage.removeItem(REFRESH_KEY);
  window.localStorage.removeItem(USER_CACHE_KEY);
}

/** Last-known account details, cached alongside the tokens purely so a
 * restart with no network yet (or a network blip) can still render "signed
 * in as X" immediately instead of forcing a sign-in screen just because the
 * one confirming API call hasn't succeeded yet — see hydrate() in
 * useAuth.ts, which only trusts this for a genuine network failure, never
 * in place of a real 401. */
export function getCachedUser(): UserRead | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(USER_CACHE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as UserRead;
  } catch {
    return null;
  }
}

export function setCachedUser(user: UserRead): void {
  window.localStorage.setItem(USER_CACHE_KEY, JSON.stringify(user));
}
