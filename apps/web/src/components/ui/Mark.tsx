export function Mark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 100 100" className={className} aria-hidden="true">
      <circle cx="50" cy="50" r="36" fill="none" stroke="currentColor" strokeWidth="4.2" />
      <line
        x1="10.59"
        y1="25.01"
        x2="96.25"
        y2="56.19"
        stroke="currentColor"
        strokeWidth="4.2"
        strokeLinecap="round"
      />
      <circle cx="20.92" cy="28.77" r="3.1" fill="currentColor" />
      <circle cx="85.92" cy="52.43" r="3.1" fill="currentColor" />
      <circle cx="50" cy="50" r="2.1" fill="currentColor" />
    </svg>
  );
}
