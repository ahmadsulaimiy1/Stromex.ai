"use client";

import { clearTokens, getAccessToken, getRefreshToken, setTokens } from "./auth-storage";
import type { TokenPair } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const REQUEST_TIMEOUT_MS = 8000;

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/** The backend never responded at all — unreachable host, DNS failure, no
 * network, or it simply took too long. Distinct from ApiError (a real HTTP
 * error response) so callers like guest-mode entry can tell "the server
 * said no" apart from "there's no server to ask" and behave differently. */
export class NetworkError extends Error {
  constructor(message = "Could not reach the StromeX server.") {
    super(message);
    this.name = "NetworkError";
  }
}

async function fetchWithTimeout(input: string, init: RequestInit): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    return await fetch(input, { ...init, signal: controller.signal });
  } catch (err) {
    throw new NetworkError(
      err instanceof DOMException && err.name === "AbortError"
        ? "The StromeX server took too long to respond."
        : "Could not reach the StromeX server. Check your connection.",
    );
  } finally {
    clearTimeout(timeoutId);
  }
}

async function parseErrorDetail(response: Response): Promise<string> {
  try {
    const body = await response.json();
    if (typeof body?.detail === "string") return body.detail;
    return JSON.stringify(body);
  } catch {
    return response.statusText || "Request failed";
  }
}

async function refreshAccessToken(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;

  // A network failure here must NOT clear tokens — that would sign out a
  // real, valid session just because the network blipped. Only an actual
  // rejection from the server (bad/expired/revoked refresh token) should.
  let response: Response;
  try {
    response = await fetchWithTimeout(`${API_BASE}/api/v1/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  } catch {
    return false;
  }
  if (!response.ok) {
    clearTokens();
    return false;
  }
  const pair: TokenPair = await response.json();
  setTokens(pair.access_token, pair.refresh_token);
  return true;
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  auth?: boolean;
}

async function request<T>(path: string, options: RequestOptions = {}, retried = false): Promise<T> {
  const { method = "GET", body, auth = true } = options;

  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (auth) {
    const token = getAccessToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetchWithTimeout(`${API_BASE}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (response.status === 401 && auth && !retried) {
    const refreshed = await refreshAccessToken();
    if (refreshed) return request<T>(path, options, true);
  }

  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorDetail(response));
  }

  if (response.status === 204) return undefined as T;

  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    return (await response.json()) as T;
  }
  return (await response.blob()) as unknown as T;
}

export const api = {
  get: <T>(path: string, auth = true) => request<T>(path, { method: "GET", auth }),
  post: <T>(path: string, body?: unknown, auth = true) =>
    request<T>(path, { method: "POST", body, auth }),
  patch: <T>(path: string, body?: unknown, auth = true) =>
    request<T>(path, { method: "PATCH", body, auth }),
  delete: <T>(path: string, body?: unknown, auth = true) =>
    request<T>(path, { method: "DELETE", body, auth }),
  base: API_BASE,
};
