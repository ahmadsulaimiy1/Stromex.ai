# Chapter 2 — Brand Identity

> Everything in this chapter exists as code. Nothing here is decoration; every token has a
> job, and every token is referenced by name — never by literal value — in the UI layer.

---

## 2.1 The Name

**SAUTIY™** — from *ṣawtī* (صَوْتِي), "my voice".

Set in capitals, no spacing tricks, no stylised glyph substitutions. The ™ is set at
superscript, 55% of cap height, and is present in the app icon wordmark, the About screen
and the splash, and nowhere else in the running UI.

## 2.2 The Mark

The SAUTIY mark is the **Aperture**: a vertical, centre-anchored symmetric waveform of five
strokes whose heights follow the ratio `0.34 : 0.68 : 1.00 : 0.68 : 0.34`, with fully
rounded caps, drawn on a 48-unit grid.

| Property | Value |
|---|---|
| Grid | 48 × 48 |
| Stroke width | 5 units |
| Stroke gap | 4 units |
| Cap | round |
| Tallest stroke | 40 units (centred) |
| Optical centre | exact geometric centre |

Reasons it is the mark: it reads at 24 dp, it is the same shape as the live meter the user
watches while recording, it is culturally neutral, and it is trivially animatable — the
same five strokes become the recording indicator by driving their heights from the input
level.

**Forbidden:** gradients on the mark, drop shadows on the mark, rotation, skew, outline
versions, recolouring outside the palette, and placing the mark on a photograph.

## 2.3 Colour System

SAUTIY is **dark-first**. Recording happens in dark rooms, at night, in mosques, in
studios; a bright screen is a physical intrusion. A light theme is provided and is a
first-class citizen, not an afterthought.

### 2.3.1 Semantic roles

Colour is never chosen for looks at the call site. It is requested by role.

| Role | Meaning |
|---|---|
| `canvas` | The page itself. The deepest surface. |
| `surface` | A resting plane holding content |
| `surfaceRaised` | A plane above `surface` — cards, layer strips |
| `surfaceOverlay` | Sheets, menus, dialogs |
| `border` | Structural hairlines |
| `textPrimary` / `textSecondary` / `textTertiary` / `textDisabled` | Type hierarchy |
| `signal` | The waveform, analysis, selection — SAUTIY's voice |
| `signalMuted` | Non-focused waveform material |
| `ember` | Record. This colour means recording and nothing else. |
| `commit` | The forward/primary action of the current screen |
| `safe` | Success, healthy level, completion |
| `caution` | Approaching a limit — hot input, low storage |
| `critical` | Clipping, error, destruction |

### 2.3.2 Dark palette (default)

| Token | Hex | Role |
|---|---|---|
| `ink900` | `#05070A` | canvas |
| `ink850` | `#0A0D13` | surface |
| `ink800` | `#11151D` | surfaceRaised |
| `ink750` | `#161B25` | surfaceOverlay |
| `ink700` | `#1E2532` | border strong |
| `ink600` | `#2A3341` | border |
| `paper050` | `#F2F5F9` | textPrimary |
| `slate300` | `#A9B3C1` | textSecondary |
| `slate500` | `#6D7887` | textTertiary |
| `slate600` | `#4C5462` | textDisabled |
| `signal500` | `#2F80FF` | signal |
| `signal300` | `#7FB2FF` | signal light |
| `signal900` | `#0D1B33` | selected-region fill behind the waveform |
| `ember500` | `#E63329` | ember |
| `ember300` | `#FF6A5E` | ember light |
| `rose500` | `#E0246B` | commit |
| `rose300` | `#FF6FA3` | commit light |
| `verdant500` | `#2FBF71` | safe |
| `amber500` | `#F5A524` | caution |
| `crimson500` | `#F0483E` | critical |

### 2.3.3 Light palette

| Token | Hex | Role |
|---|---|---|
| `paper000` | `#FFFFFF` | surface |
| `paper050` | `#F7F9FC` | canvas |
| `paper100` | `#EDF1F6` | surfaceRaised |
| `paper200` | `#E2E8F0` | surfaceOverlay border |
| `paper300` | `#CBD3DE` | border |
| `ink900` | `#080B11` | textPrimary |
| `ink600` | `#48525F` | textSecondary |
| `ink400` | `#6E7887` | textTertiary |
| `signal600` | `#1A63D8` | signal (darkened for contrast on white) |
| `ember600` | `#C42A21` | ember |
| `rose600` | `#BE1B59` | commit |
| `verdant600` | `#1E9B58` | safe |
| `amber600` | `#B87610` | caution |
| `crimson600` | `#C93227` | critical |

### 2.3.4 Colour law

1. **`ember` is reserved.** It appears on the record control and the recording indicator.
   Nowhere else, ever. When the user sees that red, the device is capturing.
2. **Never signal by colour alone.** Every colour-carried state also carries a shape, an
   icon, a number or a label. (Chapter 17.)
3. **Contrast floors are absolute:** 4.5:1 for body text, 3:1 for large text, icons,
   meters and focus rings, against the surface they actually sit on.
4. **No gradients on surfaces.** The only gradient in SAUTIY is the level-meter ramp
   (`verdant → amber → crimson`) and the spectrogram colour map, both of which encode data.
5. **Opacity is not a colour.** Disabled states use `textDisabled`, not alpha on
   `textPrimary`, so contrast stays predictable.

## 2.4 Typography

Three families, each with one job. All bundled in the APK — SAUTIY never fetches a font at
runtime, because SAUTIY never requires a network.

| Family | Job | Weights |
|---|---|---|
| **Fraunces** | Display & brand moments — splash, About, empty-state headline, project titles | Light 300, SemiBold 600 |
| **Archivo** | The entire working UI — labels, body, controls, numerals | Regular 400, Bold 700 |
| **Amiri** | Qur'anic Arabic text in Qur'an Studio | Regular 400, Bold 700 |
| **Cairo** | Arabic UI text (non-Qur'anic) | Regular 400, Bold 700 |

All are SIL Open Font Licence 1.1. See `apps/sautiy/THIRD-PARTY-NOTICES.md`.

### 2.4.1 Type scale

Sizes are in **sp** and scale with the user's font-size preference (Chapter 17). Line
heights are absolute so vertical rhythm survives scaling.

| Style | Family / Weight | Size | Line | Tracking | Use |
|---|---|---|---|---|---|
| `displayLarge` | Fraunces 300 | 40 | 46 | −0.6 | Splash, About |
| `displaySmall` | Fraunces 600 | 28 | 34 | −0.3 | Screen title, empty-state headline |
| `titleLarge` | Archivo 700 | 22 | 28 | −0.2 | Sheet titles |
| `titleMedium` | Archivo 700 | 17 | 24 | 0 | Section headers, layer names |
| `bodyLarge` | Archivo 400 | 16 | 24 | 0 | Reading text |
| `bodyMedium` | Archivo 400 | 14 | 20 | 0.1 | Secondary text |
| `labelLarge` | Archivo 700 | 14 | 18 | 0.4 | Buttons |
| `labelMedium` | Archivo 700 | 12 | 16 | 0.6 | Chips, tab labels |
| `labelSmall` | Archivo 700 | 11 | 14 | 0.8 | Meter captions, axis ticks |
| `timerHero` | Archivo 400, **tabular** | 44 | 48 | −1.2 | The recording timer |
| `timerInline` | Archivo 400, **tabular** | 15 | 20 | 0 | Positions, durations |
| `numeric` | Archivo 700, **tabular** | 13 | 16 | 0 | dB values, ratios, Hz |
| `quranAyah` | Amiri 400 | 26 | 48 | 0 | Qur'anic text |

### 2.4.2 Typographic law

1. **Every number that changes in place is tabular.** Timers, dB readouts, positions and
   counters must not shift width as digits change. A jittering timer is a defect.
2. **Two type sizes per screen region, maximum.** Hierarchy comes from weight, colour and
   space before it comes from size.
3. **Sentence case everywhere.** No ALL CAPS in the working UI — it is slower to read and
   reads as shouting. The sole exception is the wordmark.
4. **No italics.** SAUTIY has no italic faces; emphasis is carried by weight and colour.
5. **Arabic is never squeezed.** Qur'anic lines get 48 sp of line height regardless of the
   surrounding density, and are never truncated with an ellipsis — they wrap or they scroll.

## 2.5 Iconography

Icons are the primary language of the workspace. Text labels appear only where an icon
cannot be unambiguous.

| Property | Value |
|---|---|
| Grid | 24 × 24 dp |
| Live area | 20 × 20 dp |
| Stroke | 1.75 dp, `round` cap, `round` join |
| Corner radius | 2 dp minimum on any corner |
| Optical alignment | centred on optical mass, not bounding box |
| Fill | outline by default; solid **only** to indicate an active/engaged state |
| Minimum touch target | 48 × 48 dp regardless of icon size |

**Icon law**

1. Every icon in the workspace has a `contentDescription`. No exceptions. (Chapter 17.)
2. Every icon that is not universally understood carries a persistent 11 sp label beneath
   it. "Universally understood" means: record, play, pause, stop, skip, undo, redo, share,
   delete, search, settings, add, close, back. Everything else — trim, split, normalise,
   de-ess — is labelled.
3. An icon never changes meaning between screens.
4. Toggle state is shown by fill *and* by a 2 dp underline in `signal`, never by colour alone.

## 2.6 Motion — brand level

Full specification in Chapter 6. At brand level, only this: **SAUTIY moves like a
well-damped mechanism, not like a bouncing toy.** No overshoot above 3%, no rotation for
effect, no confetti, no elastic easing.

## 2.7 App Icon

- Background: solid `ink900` `#05070A` — never a gradient, never transparent.
- Foreground: the Aperture in `signal500` `#2F80FF`, at 62% of the safe-zone diameter.
- Adaptive icon: foreground and background layers supplied separately; the mark sits
  entirely within the 66 dp safe circle so no mask can clip it.
- Monochrome layer supplied for Android 13+ themed icons.
- No text in the icon. The launcher already prints the name.

## 2.8 Splash

The splash exists for exactly as long as the process takes to become interactive, and not
one frame longer. It is not a brand moment; it is a seam-cover.

- `ink900` field, Aperture centred, no animation on first frame.
- If — and only if — cold start exceeds 400 ms, the Aperture's five strokes begin a
  1.4 s breathing loop at 30% amplitude, so a slow device looks calm rather than frozen.
- Implemented with the platform splash-screen API so it is the *actual* first frame, with
  no separate splash Activity and no artificial delay.

## 2.9 Tone of Voice

SAUTIY speaks like a skilled engineer who respects your time.

| Do | Don't |
|---|---|
| "Recording saved." | "Great job! Your awesome recording is saved! 🎉" |
| "Storage is low — about 12 minutes left." | "Uh oh! You're running out of space!" |
| "Microphone unavailable. Another app is using it." | "Something went wrong." |
| "Trimmed 4.2 s from the start." | "Trim applied successfully." |
| "Undo" | "Oops, undo that!" |

**Voice law**

1. **State the fact, then the consequence, then the action.** In that order.
2. **Never apologise.** "Sorry" wastes a line and helps nobody.
3. **Never blame the user.** Errors describe the situation, not their mistake.
4. **No exclamation marks. No emoji.** Anywhere in the product UI.
5. **Numbers are specific.** "about 12 minutes left", not "low storage".
6. **Second person, present tense, active voice.**
7. **British English** throughout: *normalise, colour, centre, favourite, analyse.*

---

### Implementation

| Clause | Code |
|--------|------|
| 2.3 Colour tokens | `sautiy-core/.../design/SautiyPalette.kt` (platform-neutral ARGB), `app/.../ui/theme/Colour.kt` |
| 2.3.4 Contrast law | `sautiy-core/src/test/.../ContrastTest.kt` — computes WCAG contrast for every role pair and fails below floor |
| 2.4 Typography | `app/src/main/res/font/*`, `app/.../ui/theme/Type.kt` |
| 2.5 Iconography | `app/.../ui/icons/SautiyIcons.kt` — every icon drawn as a vector path on the 24 dp grid |
| 2.2 The Aperture | `app/.../ui/brand/Aperture.kt`, `res/drawable/ic_launcher_foreground.xml` |
| 2.7 App icon | `res/mipmap-anydpi-v26/ic_launcher.xml` + monochrome layer |
| 2.8 Splash | `res/values/themes.xml` (`Theme.Sautiy.Splash`), `SplashController.kt` |
| 2.9 Tone | `app/src/main/res/values/strings.xml` — every user-facing string, checked by `ToneOfVoiceTest` |
