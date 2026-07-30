import clsx from "clsx";
import type { HTMLAttributes } from "react";

export function Card({ className, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={clsx(
        "rounded-lg border border-[color:var(--hairline)] bg-[color:var(--bg-raised)] p-5",
        className,
      )}
      {...rest}
    />
  );
}
