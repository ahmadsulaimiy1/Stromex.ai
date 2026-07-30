"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import type { FormEvent } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { RequireAuth } from "@/components/layout/RequireAuth";
import { useAuth } from "@/hooks/useAuth";
import { api, ApiError } from "@/lib/api";

function GuestUpgradeCard() {
  const upgradeGuest = useAuth((state) => state.upgradeGuest);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await upgradeGuest(email, password, displayName);
      setDone(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (done) {
    return (
      <Card>
        <h2 className="mb-2 font-display text-lg font-semibold">Account created</h2>
        <p className="text-sm text-[color:var(--fg-muted)]">
          Check your email for a verification link. Your existing chats and data carried
          over automatically — nothing was lost.
        </p>
      </Card>
    );
  }

  return (
    <Card>
      <h2 className="mb-1 font-display text-lg font-semibold">Create a full account</h2>
      <p className="mb-4 text-sm text-[color:var(--fg-muted)]">
        You&apos;re using a guest account. Add an email and password to keep access to this
        account from other devices — your chats and data stay exactly as they are.
      </p>
      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <Input
          id="displayName"
          label="Name"
          required
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
        />
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
          minLength={8}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        {error && <p className="text-sm text-rubrication">{error}</p>}
        <Button type="submit" isLoading={isSubmitting} className="mt-1">
          Create account
        </Button>
      </form>
    </Card>
  );
}

function VerifyEmailCard() {
  const [sent, setSent] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleResend() {
    setIsSubmitting(true);
    try {
      await api.post("/api/v1/auth/email/verify/request");
      setSent(true);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Card>
      <h2 className="mb-1 font-display text-lg font-semibold">Verify your email</h2>
      <p className="mb-4 text-sm text-[color:var(--fg-muted)]">
        {sent
          ? "A new verification link is on its way."
          : "Your email address hasn't been verified yet."}
      </p>
      <Button variant="secondary" isLoading={isSubmitting} onClick={handleResend} disabled={sent}>
        Resend verification email
      </Button>
    </Card>
  );
}

function SecurityCard() {
  const router = useRouter();
  const logoutAllDevices = useAuth((state) => state.logoutAllDevices);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSignOutEverywhere() {
    setIsSubmitting(true);
    try {
      await logoutAllDevices();
      router.push("/login");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Card>
      <h2 className="mb-1 font-display text-lg font-semibold">Security</h2>
      <p className="mb-4 text-sm text-[color:var(--fg-muted)]">
        Sign out of every device where you&apos;re currently signed in, including this one.
      </p>
      <Button variant="secondary" isLoading={isSubmitting} onClick={handleSignOutEverywhere}>
        Sign out of all devices
      </Button>
    </Card>
  );
}

function DeleteAccountCard() {
  const router = useRouter();
  const user = useAuth((state) => state.user);
  const deleteAccount = useAuth((state) => state.deleteAccount);
  const [confirming, setConfirming] = useState(false);
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleDelete() {
    setError(null);
    setIsSubmitting(true);
    try {
      await deleteAccount(user?.is_guest ? undefined : password);
      router.push("/welcome");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Card>
      <h2 className="mb-1 font-display text-lg font-semibold">Delete account</h2>
      <p className="mb-4 text-sm text-[color:var(--fg-muted)]">
        Permanently deletes this account and everything in it — conversations, memory,
        Qur&apos;an plans, and books. This cannot be undone.
      </p>
      {confirming ? (
        <div className="flex flex-col gap-3">
          {!user?.is_guest && (
            <Input
              id="confirmPassword"
              type="password"
              label="Confirm your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          )}
          {error && <p className="text-sm text-rubrication">{error}</p>}
          <div className="flex gap-2">
            <Button variant="danger" isLoading={isSubmitting} onClick={handleDelete}>
              Permanently delete
            </Button>
            <Button variant="ghost" onClick={() => setConfirming(false)}>
              Cancel
            </Button>
          </div>
        </div>
      ) : (
        <Button variant="danger" onClick={() => setConfirming(true)}>
          Delete my account
        </Button>
      )}
    </Card>
  );
}

function SettingsContent() {
  const user = useAuth((state) => state.user);

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-6">
      <h1 className="font-display text-2xl font-semibold">Settings</h1>
      <Card>
        <h2 className="mb-3 font-display text-lg font-semibold">Account</h2>
        <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-sm">
          <dt className="text-[color:var(--fg-muted)]">Name</dt>
          <dd>{user?.display_name}</dd>
          <dt className="text-[color:var(--fg-muted)]">Email</dt>
          <dd>{user?.is_guest ? "— (guest account)" : user?.email}</dd>
          <dt className="text-[color:var(--fg-muted)]">Type</dt>
          <dd>{user?.is_guest ? "Guest" : "Full account"}</dd>
        </dl>
      </Card>
      {user?.is_guest && <GuestUpgradeCard />}
      {!user?.is_guest && !user?.is_verified && <VerifyEmailCard />}
      <SecurityCard />
      <DeleteAccountCard />
    </div>
  );
}

export default function SettingsPage() {
  return (
    <RequireAuth>
      <SettingsContent />
    </RequireAuth>
  );
}
