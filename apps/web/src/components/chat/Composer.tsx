"use client";

import { useState } from "react";
import type { FormEvent } from "react";

import { Button } from "@/components/ui/Button";
import type { ConversationMode } from "@/lib/types";

const MODES: { value: ConversationMode; label: string }[] = [
  { value: "general", label: "General" },
  { value: "research", label: "Research" },
  { value: "quran", label: "Qur'an" },
  { value: "arabic_learning", label: "Arabic ⇄ English" },
  { value: "book_writing", label: "Book writing" },
];

interface ComposerProps {
  mode: ConversationMode;
  onModeChange: (mode: ConversationMode) => void;
  onSend: (message: string) => Promise<void>;
  disabled?: boolean;
}

export function Composer({ mode, onModeChange, onSend, disabled }: ComposerProps) {
  const [value, setValue] = useState("");
  const [sending, setSending] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!value.trim() || sending) return;
    setSending(true);
    const toSend = value;
    setValue("");
    try {
      await onSend(toSend);
    } finally {
      setSending(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-2 border-t border-[color:var(--hairline)] p-4">
      <div className="flex gap-1.5 overflow-x-auto pb-1">
        {MODES.map((item) => (
          <button
            type="button"
            key={item.value}
            onClick={() => onModeChange(item.value)}
            className={`whitespace-nowrap rounded-full px-3 py-1 text-xs font-medium transition-colors ${
              mode === item.value
                ? "bg-brass text-white"
                : "bg-[color:var(--bg-raised)] text-[color:var(--fg-muted)] hover:text-[color:var(--fg)]"
            }`}
          >
            {item.label}
          </button>
        ))}
      </div>
      <div className="flex items-end gap-2">
        <textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
          rows={2}
          placeholder="Ask StromeX anything…"
          disabled={disabled}
          className="flex-1 resize-none rounded-md border border-[color:var(--hairline)] bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brass/40"
        />
        <Button type="submit" isLoading={sending} disabled={disabled}>
          Send
        </Button>
      </div>
    </form>
  );
}
