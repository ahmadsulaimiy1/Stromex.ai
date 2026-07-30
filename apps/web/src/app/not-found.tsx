import Link from "next/link";

import { Mark } from "@/components/ui/Mark";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 px-4 text-center">
      <Mark className="h-10 w-10 text-brass" />
      <h1 className="font-display text-xl font-semibold">Page not found</h1>
      <p className="max-w-sm text-sm text-[color:var(--fg-muted)]">
        That page doesn&apos;t exist, or you don&apos;t have access to it.
      </p>
      <Link href="/chat" className="text-sm font-medium text-brass hover:underline">
        Back to StromeX
      </Link>
    </div>
  );
}
