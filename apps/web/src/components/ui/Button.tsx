import clsx from "clsx";
import type { ButtonHTMLAttributes } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  isLoading?: boolean;
}

export function Button({
  variant = "primary",
  isLoading = false,
  className,
  children,
  disabled,
  ...rest
}: ButtonProps) {
  return (
    <button
      className={clsx(
        "inline-flex items-center justify-center gap-2 rounded-md px-4 py-2 text-sm font-semibold transition-colors",
        "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brass",
        "disabled:cursor-not-allowed disabled:opacity-50",
        variant === "primary" && "bg-brass text-white hover:opacity-90",
        variant === "secondary" &&
          "border border-[color:var(--hairline)] bg-transparent text-[color:var(--fg)] hover:bg-[color:var(--bg-raised)]",
        variant === "ghost" && "bg-transparent text-[color:var(--fg-muted)] hover:text-[color:var(--fg)]",
        variant === "danger" && "bg-rubrication text-white hover:opacity-90",
        className,
      )}
      disabled={disabled || isLoading}
      {...rest}
    >
      {isLoading ? "…" : children}
    </button>
  );
}
