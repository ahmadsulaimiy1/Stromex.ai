"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import { Mark } from "@/components/ui/Mark";
import { api } from "@/lib/api";

function VerifyEmailContent() {
  const token = useSearchParams().get("token");
  const [status, setStatus] = useState<"checking" | "verified" | "failed" | "missing">(
    token ? "checking" : "missing",
  );

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    api
      .post("/api/v1/auth/email/verify/confirm", { token }, false)
      .then(() => {
        if (!cancelled) setStatus("verified");
      })
      .catch(() => {
        if (!cancelled) setStatus("failed");
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  const message = {
    checking: "Verifying your email…",
    verified: "Your email is verified. You're all set.",
    failed: "This verification link is invalid or has expired.",
    missing: "No verification token was provided.",
  }[status];

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-sm text-center">
        <div className="mb-8 flex flex-col items-center gap-3">
          <Mark className="h-10 w-10 text-brass" />
          <h1 className="font-display text-2xl font-semibold">Verify email</h1>
        </div>
        <p className="text-sm text-[color:var(--fg-muted)]">{message}</p>
        <p className="mt-6 text-sm">
          <Link href="/chat" className="text-brass hover:underline">
            Go to StromeX
          </Link>
        </p>
      </div>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={null}>
      <VerifyEmailContent />
    </Suspense>
  );
}
