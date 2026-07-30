"use client";

import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import { RequireAuth } from "@/components/layout/RequireAuth";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { api } from "@/lib/api";
import type { QuranAnalytics, QuranPlanRead, QuranRevisionItemRead } from "@/lib/types";

function CreatePlanForm({ onCreated }: { onCreated: () => void }) {
  const [title, setTitle] = useState("");
  const [surah, setSurah] = useState(114);
  const [ayahStart, setAyahStart] = useState(1);
  const [ayahEnd, setAyahEnd] = useState(6);
  const [dailyTarget, setDailyTarget] = useState(3);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await api.post("/api/v1/quran/plans", {
        title,
        plan_type: "memorization",
        surah_start: surah,
        ayah_start: ayahStart,
        surah_end: surah,
        ayah_end: ayahEnd,
        daily_target_ayahs: dailyTarget,
      });
      setTitle("");
      onCreated();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create plan.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Card>
      <h2 className="mb-4 font-display text-lg font-semibold">New memorization plan</h2>
      <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-3">
        <div className="col-span-2">
          <Input
            id="title"
            label="Plan title"
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        </div>
        <Input
          id="surah"
          label="Surah"
          type="number"
          min={1}
          max={114}
          required
          value={surah}
          onChange={(e) => setSurah(Number(e.target.value))}
        />
        <Input
          id="dailyTarget"
          label="Daily target (ayahs)"
          type="number"
          min={1}
          required
          value={dailyTarget}
          onChange={(e) => setDailyTarget(Number(e.target.value))}
        />
        <Input
          id="ayahStart"
          label="Ayah start"
          type="number"
          min={1}
          required
          value={ayahStart}
          onChange={(e) => setAyahStart(Number(e.target.value))}
        />
        <Input
          id="ayahEnd"
          label="Ayah end"
          type="number"
          min={1}
          required
          value={ayahEnd}
          onChange={(e) => setAyahEnd(Number(e.target.value))}
        />
        {error && <p className="col-span-2 text-sm text-rubrication">{error}</p>}
        <Button type="submit" isLoading={submitting} className="col-span-2">
          Create plan
        </Button>
      </form>
    </Card>
  );
}

function PlanPanel({ plan }: { plan: QuranPlanRead }) {
  const [due, setDue] = useState<QuranRevisionItemRead[]>([]);
  const [analytics, setAnalytics] = useState<QuranAnalytics | null>(null);

  async function refresh() {
    const [dueItems, stats] = await Promise.all([
      api.get<QuranRevisionItemRead[]>(`/api/v1/quran/plans/${plan.id}/due`),
      api.get<QuranAnalytics>(`/api/v1/quran/plans/${plan.id}/analytics`),
    ]);
    setDue(dueItems);
    setAnalytics(stats);
  }

  useEffect(() => {
    void refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [plan.id]);

  async function submitGrade(itemId: string, grade: number) {
    await api.post("/api/v1/quran/review", { item_id: itemId, grade });
    void refresh();
  }

  return (
    <Card>
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-display text-base font-semibold">{plan.title}</h3>
        <span className="text-xs text-[color:var(--fg-muted)]">
          Surah {plan.surah_start}:{plan.ayah_start}–{plan.ayah_end}
        </span>
      </div>

      {analytics && (
        <div className="mb-4 grid grid-cols-4 gap-2 text-center text-xs">
          <div>
            <div className="font-display text-lg">{analytics.due_today}</div>
            <div className="text-[color:var(--fg-muted)]">Due today</div>
          </div>
          <div>
            <div className="font-display text-lg">{analytics.average_ease_factor}</div>
            <div className="text-[color:var(--fg-muted)]">Avg. ease</div>
          </div>
          <div>
            <div className="font-display text-lg">{analytics.reviews_last_7_days}</div>
            <div className="text-[color:var(--fg-muted)]">Reviews / 7d</div>
          </div>
          <div>
            <div className="font-display text-lg">
              {analytics.retention_rate_30_days !== null
                ? `${Math.round(analytics.retention_rate_30_days * 100)}%`
                : "—"}
            </div>
            <div className="text-[color:var(--fg-muted)]">Retention / 30d</div>
          </div>
        </div>
      )}

      <div className="flex flex-col gap-2">
        {due.length === 0 && (
          <p className="text-sm text-[color:var(--fg-muted)]">Nothing due right now. Well done.</p>
        )}
        {due.map((item) => (
          <div
            key={item.id}
            className="flex items-center justify-between rounded-md border border-[color:var(--hairline)] px-3 py-2"
          >
            <span className="text-sm">
              Surah {item.surah}: {item.ayah_start}–{item.ayah_end}
            </span>
            <div className="flex gap-1">
              {[0, 1, 2, 3, 4, 5].map((grade) => (
                <button
                  key={grade}
                  onClick={() => submitGrade(item.id, grade)}
                  className="h-7 w-7 rounded-md border border-[color:var(--hairline)] text-xs font-semibold hover:bg-brass hover:text-white"
                  title={`Recall quality ${grade}`}
                >
                  {grade}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

function QuranPage() {
  const [plans, setPlans] = useState<QuranPlanRead[]>([]);

  async function loadPlans() {
    setPlans(await api.get<QuranPlanRead[]>("/api/v1/quran/plans"));
  }

  useEffect(() => {
    void loadPlans();
  }, []);

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-6">
      <h1 className="font-display text-2xl font-semibold">Qur&apos;an Tutor</h1>
      <CreatePlanForm onCreated={loadPlans} />
      {plans.map((plan) => (
        <PlanPanel key={plan.id} plan={plan} />
      ))}
    </div>
  );
}

export default function Page() {
  return (
    <RequireAuth>
      <QuranPage />
    </RequireAuth>
  );
}
