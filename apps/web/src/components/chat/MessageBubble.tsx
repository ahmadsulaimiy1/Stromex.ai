import clsx from "clsx";

import { isArabicText } from "@/lib/textDirection";
import type { MessageRead } from "@/lib/types";

export function MessageBubble({ message }: { message: MessageRead }) {
  const isUser = message.role === "user";
  const isArabic = isArabicText(message.content);
  return (
    <div className={clsx("flex flex-col gap-1", isUser ? "items-end" : "items-start")}>
      <div
        dir={isArabic ? "rtl" : "ltr"}
        className={clsx(
          "max-w-2xl whitespace-pre-wrap rounded-lg px-4 py-2.5 text-sm leading-relaxed",
          isArabic ? "font-sans-ar text-base" : "font-sans",
          isUser
            ? "bg-brass text-white"
            : "border border-[color:var(--hairline)] bg-[color:var(--bg-raised)] text-[color:var(--fg)]",
        )}
      >
        {message.content}
      </div>
      {!isUser && message.provider && (
        <span className="px-1 text-[11px] uppercase tracking-wide text-[color:var(--fg-muted)]">
          {message.provider} · {message.model}
        </span>
      )}
    </div>
  );
}
