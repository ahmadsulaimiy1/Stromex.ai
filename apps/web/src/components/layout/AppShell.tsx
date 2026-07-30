"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import type { ReactNode } from "react";

import { Mark } from "@/components/ui/Mark";
import { useAuth } from "@/hooks/useAuth";

const NAV_ITEMS = [
  { href: "/chat", label: "Chat" },
  { href: "/quran", label: "Qur'an" },
  { href: "/books", label: "Books" },
  { href: "/settings", label: "Settings" },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout, isOffline, isLocalGuest } = useAuth();

  const items = user?.role === "admin" ? [...NAV_ITEMS, { href: "/admin", label: "Admin" }] : NAV_ITEMS;

  return (
    <div className="flex min-h-screen flex-col">
      {isOffline && (
        <div className="border-b border-[color:var(--hairline)] bg-rubrication/10 px-4 py-2 text-center text-xs text-rubrication">
          {isLocalGuest
            ? "Can't reach the StromeX server — you're browsing as a temporary offline guest. Chat and other features need a connection."
            : "Can't reach the StromeX server right now — showing your last known session. Some features won't work until you're back online."}
        </div>
      )}
      <div className="flex flex-1">
        <aside className="flex w-56 shrink-0 flex-col border-r border-[color:var(--hairline)] px-4 py-6">
          <div className="mb-8 flex items-center gap-2 px-2">
            <Mark className="h-6 w-6 text-brass" />
            <span className="font-display text-lg font-semibold">StromeX</span>
          </div>
          <nav className="flex flex-col gap-1">
            {items.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                  pathname?.startsWith(item.href)
                    ? "bg-[color:var(--bg-raised)] text-[color:var(--fg)]"
                    : "text-[color:var(--fg-muted)] hover:bg-[color:var(--bg-raised)]"
                }`}
              >
                {item.label}
              </Link>
            ))}
          </nav>
          <div className="mt-auto flex flex-col gap-2 px-2 pt-6 text-xs text-[color:var(--fg-muted)]">
            <span>{user?.display_name ?? "Guest"}</span>
            <button
              className="text-left text-rubrication hover:underline"
              onClick={() => {
                void logout();
                router.push("/welcome");
              }}
            >
              Sign out
            </button>
          </div>
        </aside>
        <main className="flex-1 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}
