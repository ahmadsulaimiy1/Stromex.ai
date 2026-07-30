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
      router.replace("/login");
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
