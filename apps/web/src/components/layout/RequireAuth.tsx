"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import type { ReactNode } from "react";

import { useAuth } from "@/hooks/useAuth";

import { AppShell } from "./AppShell";

export function RequireAuth({ children }: { children: ReactNode }) {
  const { status, hydrate } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (status === "idle") {
      void hydrate();
    }
  }, [status, hydrate]);

  useEffect(() => {
    if (status === "unauthenticated") {
      // /welcome, not /login directly — a visitor with no session at all
      // should always see all three entry paths (Google/Email/Guest), not
      // just be dropped straight into the email form.
      router.replace("/welcome");
    }
  }, [status, router]);

  if (status !== "authenticated") {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-[color:var(--fg-muted)]">
        Loading StromeX…
      </div>
    );
  }

  return <AppShell>{children}</AppShell>;
}
