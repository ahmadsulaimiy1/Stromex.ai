"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useRef } from "react";

import { useAuth } from "@/hooks/useAuth";

function GoogleCallbackContent() {
  const router = useRouter();
  const params = useSearchParams();
  const adoptSession = useAuth((state) => state.adoptSession);
  const attempted = useRef(false);

  useEffect(() => {
    if (attempted.current) return;
    attempted.current = true;

    const accessToken = params.get("access_token");
    const refreshToken = params.get("refresh_token");
    if (!accessToken || !refreshToken) {
      router.replace("/welcome");
      return;
    }
    adoptSession(accessToken, refreshToken)
      .then(() => router.replace("/chat"))
      .catch(() => router.replace("/welcome"));
  }, [params, adoptSession, router]);

  return (
    <div className="flex min-h-screen items-center justify-center text-sm text-[color:var(--fg-muted)]">
      Signing you in…
    </div>
  );
}

export default function GoogleCallbackPage() {
  return (
    <Suspense fallback={null}>
      <GoogleCallbackContent />
    </Suspense>
  );
}
