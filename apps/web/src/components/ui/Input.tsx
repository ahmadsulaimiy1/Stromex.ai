import clsx from "clsx";
import type { InputHTMLAttributes, LabelHTMLAttributes } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export function Input({ label, error, id, className, ...rest }: InputProps) {
  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor={id} className="text-xs font-semibold uppercase tracking-wide text-[color:var(--fg-muted)]">
          {label}
        </label>
      )}
      <input
        id={id}
        className={clsx(
          "rounded-md border border-[color:var(--hairline)] bg-transparent px-3 py-2 text-sm",
          "focus:outline-none focus:ring-2 focus:ring-brass/40",
          error && "border-rubrication",
          className,
        )}
        {...rest}
      />
      {error && <p className="text-xs text-rubrication">{error}</p>}
    </div>
  );
}

export function FieldLabel(props: LabelHTMLAttributes<HTMLLabelElement>) {
  return (
    <label
      className="text-xs font-semibold uppercase tracking-wide text-[color:var(--fg-muted)]"
      {...props}
    />
  );
}
