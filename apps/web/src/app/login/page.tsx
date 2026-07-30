"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import type { FormEvent } from "react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Mark } from "@/components/ui/Mark";
import { useAuth } from "@/hooks/useAuth";
import { ApiError, NetworkError } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const login = useAuth((state) => state.login);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isUnreachable, setIsUnreachable] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setIsUnreachable(false);
    setIsSubmitting(true);
    try {
      await login(email, password);
      router.push("/chat");
    } catch (err) {
      if (err instanceof NetworkError) {
        setIsUnreachable(true);
        setError(err.message);
      } else {
        setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center gap-3">
          <Mark className="h-10 w-10 text-brass" />
          <h1 className="font-display text-2xl font-semibold">Sign in to StromeX</h1>
        </div>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <Input
            id="email"
            type="email"
            label="Email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <Input
            id="password"
            type="password"
            label="Password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {error && <p className="text-sm text-rubrication">{error}</p>}
          {isUnreachable && (
            <p className="text-sm text-[color:var(--fg-muted)]">
              You can still{" "}
              <Link href="/welcome" className="font-medium text-brass hover:underline">
                continue as a guest
              </Link>{" "}
              while you&apos;re offline.
            </p>
          )}
          <Button type="submit" isLoading={isSubmitting} className="mt-2 w-full">
            Sign in
          </Button>
        </form>
        <p className="mt-4 text-center text-sm">
          <Link href="/reset-password" className="text-brass hover:underline">
            Forgot your password?
          </Link>
        </p>
        <p className="mt-2 text-center text-sm text-[color:var(--fg-muted)]">
          No account yet?{" "}
          <Link href="/register" className="font-medium text-brass hover:underline">
            Create one
          </Link>
        </p>
        <p className="mt-6 text-center text-xs text-[color:var(--fg-muted)]">
          <Link href="/welcome" className="hover:underline">
            ← Other ways to sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
