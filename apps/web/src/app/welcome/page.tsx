"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import Link from "next/link";

import { Button } from "@/components/ui/Button";
import { Mark } from "@/components/ui/Mark";
import { useAuth } from "@/hooks/useAuth";
import { api, ApiError } from "@/lib/api";

export default function WelcomePage() {
  const router = useRouter();
  const loginAsGuest = useAuth((state) => state.loginAsGuest);
  const [isContinuingAsGuest, setIsContinuingAsGuest] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function continueWithGoogle() {
    // A full page navigation, not a fetch: Google's own terms disallow
    // signing in inside an embedded WebView, so this has to hand off to
    // whatever browser is actually hosting this page (the system browser
    // on Android, since the app's WebView passes external navigation
    // straight to it — see MainActivity.shouldOverrideUrlLoading).
    window.location.href = `${api.base}/api/v1/auth/google/authorize?platform=web`;
  }

  async function continueAsGuest() {
    setError(null);
    setIsContinuingAsGuest(true);
    try {
      await loginAsGuest();
      router.push("/chat");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setIsContinuingAsGuest(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="mb-10 flex flex-col items-center gap-3">
          <Mark className="h-12 w-12 text-brass" />
          <h1 className="font-display text-2xl font-semibold">Welcome to StromeX</h1>
          <p className="text-center text-sm text-[color:var(--fg-muted)]">
            Intelligence Without Limits — pick how you&apos;d like to start.
          </p>
        </div>

        <div className="flex flex-col gap-3">
          <Button variant="secondary" className="w-full" onClick={continueWithGoogle}>
            Continue with Google
          </Button>
          <Link href="/login" className="w-full">
            <Button variant="secondary" className="w-full">
              Continue with Email
            </Button>
          </Link>
          <Button
            variant="ghost"
            className="w-full"
            isLoading={isContinuingAsGuest}
            onClick={continueAsGuest}
          >
            Continue as Guest
          </Button>
        </div>

        {error && <p className="mt-4 text-center text-sm text-rubrication">{error}</p>}

        <p className="mt-8 text-center text-xs text-[color:var(--fg-muted)]">
          Guest accounts have no email or password attached — you can upgrade
          to a full account any time from Settings without losing your chats.
        </p>
      </div>
    </div>
  );
}
