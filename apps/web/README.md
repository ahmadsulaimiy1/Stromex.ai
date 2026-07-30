# StromeX Web

Next.js 15 (App Router) + TypeScript + Tailwind frontend for the StromeX MVP.

## Local development

```bash
npm install
cp .env.local.example .env.local   # set NEXT_PUBLIC_API_URL if your API isn't on :8000
npm run dev
```

Requires the API (`../api`) running — see its README.

## Build

```bash
npm run typecheck   # tsc --noEmit
npm run build        # next build — also runs ESLint
```

## Brand system

Fonts (Fraunces, Archivo, Amiri, Cairo) are self-hosted from `public/fonts`
and declared in `src/app/globals.css`, matching the palette and typography
defined in the StromeX Brand & Editorial System. `tailwind.config.ts` exposes
the same tokens (`brass`, `verdigris`, `rubrication`, `ink`, `paper`) as
Tailwind color/font utilities so product UI and brand publications share one
source of truth.

## Structure

- `src/app` — routes: `/login`, `/register`, `/chat`, `/quran`, `/books`,
  `/books/[bookId]`, `/admin`.
- `src/components` — `ui/` (Button, Input, Card, Mark), `layout/` (AppShell,
  RequireAuth), `chat/` (Composer, MessageBubble).
- `src/lib` — `api.ts` (fetch wrapper with auth + refresh-on-401), `types.ts`
  (mirrors the API's Pydantic schemas).
- `src/hooks/useAuth.ts` — zustand store for session state.
