"use client";

import { useEffect } from "react";

import { Button } from "@/components/ui/Button";
import { Mark } from "@/components/ui/Mark";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // eslint-disable-next-line no-console
    console.error("Unhandled StromeX UI error:", error);
  }, [error]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 px-4 text-center">
      <Mark className="h-10 w-10 text-brass" />
      <h1 className="font-display text-xl font-semibold">Something went wrong</h1>
      <p className="max-w-sm text-sm text-[color:var(--fg-muted)]">
        StromeX hit an unexpected error. You can try again, or head back and pick up where you left
        off.
      </p>
      <Button onClick={() => reset()}>Try again</Button>
    </div>
  );
}
