"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import type { FormEvent } from "react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Mark } from "@/components/ui/Mark";
import { api, ApiError } from "@/lib/api";

function RequestResetForm() {
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await api.post("/api/v1/auth/password-reset/request", { email }, false);
      // Always shown, whether or not the address is registered — the API
      // itself never reveals that, so the UI can't either.
      setDone(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (done) {
    return (
      <p className="text-center text-sm text-[color:var(--fg-muted)]">
        If an account exists for <strong>{email}</strong>, a reset link is on its way.
      </p>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <Input
        id="email"
        type="email"
        label="Email"
        required
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />
      {error && <p className="text-sm text-rubrication">{error}</p>}
      <Button type="submit" isLoading={isSubmitting} className="mt-2 w-full">
        Send reset link
      </Button>
    </form>
  );
}

function ConfirmResetForm({ token }: { token: string }) {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await api.post(
        "/api/v1/auth/password-reset/confirm",
        { token, new_password: password },
        false,
      );
      router.push("/login");
    } catch (err) {
      setError(
        err instanceof ApiError
          ? "This reset link is invalid or has expired. Request a new one."
          : "Something went wrong. Please try again.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <Input
        id="password"
        type="password"
        label="New password"
        required
        minLength={8}
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      {error && <p className="text-sm text-rubrication">{error}</p>}
      <Button type="submit" isLoading={isSubmitting} className="mt-2 w-full">
        Set new password
      </Button>
    </form>
  );
}

function ResetPasswordContent() {
  const token = useSearchParams().get("token");

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center gap-3">
          <Mark className="h-10 w-10 text-brass" />
          <h1 className="font-display text-2xl font-semibold">
            {token ? "Set a new password" : "Reset your password"}
          </h1>
        </div>
        {token ? <ConfirmResetForm token={token} /> : <RequestResetForm />}
        <p className="mt-6 text-center text-sm text-[color:var(--fg-muted)]">
          <Link href="/login" className="text-brass hover:underline">
            Back to sign in
          </Link>
        </p>
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={null}>
      <ResetPasswordContent />
    </Suspense>
  );
}
