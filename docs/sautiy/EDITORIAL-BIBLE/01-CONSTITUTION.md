# Chapter 1 — Constitution

> The supreme clause. Every other chapter is subordinate to this one.

---

## 1.1 Vision

A person should be able to lift a phone out of a pocket, capture a thought, a lesson, a
recitation or a performance at professional quality, and publish it — without ever once
thinking about software.

SAUTIY exists to make the distance between *the sound in the room* and *the finished
recording in the world* as close to zero as physics and craft allow.

## 1.2 Mission

Build the most elegant, dependable and enjoyable mobile audio recording platform in
existence: one that a first-time user can operate in three seconds, and a professional
cannot outgrow.

## 1.3 Product Philosophy

### 1.3.1 The interface must disappear

The user is not operating an application. They are handling their recording. Every pixel
that draws attention to itself, rather than to the audio, is a defect. Chrome is a tax on
attention; SAUTIY pays as little of it as possible.

### 1.3.2 One workspace

SAUTIY is not a collection of screens. It is **one intelligent recording workspace** with
the rare specialised room attached. Record, listen, edit, enhance and export all happen in
the same place, on the same waveform, without navigation. Secondary destinations exist only
for the library, settings, projects and About.

**Constitutional limit:** if a task in the Record → Review → Edit → Enhance → Export chain
requires leaving the workspace, that is a design failure to be fixed, not a navigation
decision to be documented.

### 1.3.3 Invisible complexity

Depth is not removed; it is *deferred*. The surface carries only what the current moment
needs. Advanced control is always exactly one deliberate gesture away, never zero (which is
clutter) and never three (which is burial).

### 1.3.4 Listening outranks everything

Analysis, waveform rendering, loudness measurement, transcription and enhancement are all
subordinate to playback. **Playback must never wait for analysis.** Audio starts; the
picture fills in behind it.

### 1.3.5 Nothing is ever lost

Every destructive-looking action is reversible. Every recording is durable from its first
sample, not from the moment the user remembers to press save. A crash, a battery death or a
killed process costs the user *at most* the last few seconds of audio — and SAUTIY offers
that audio back on next launch without being asked.

### 1.3.6 Offline is the normal case

A recording app that needs a network is not a recording app. Every core capability —
capture, playback, editing, the full DSP chain, MP3/WAV/FLAC export — runs entirely on the
device with no account, no connection and no server. Networked features, if ever added, are
strictly additive and strictly optional.

### 1.3.7 The user's audio is the user's

SAUTIY collects nothing. No analytics, no telemetry, no uploads, no advertising identifiers.
Audio never leaves the device unless the user explicitly exports or shares it.

## 1.4 Design Principles

The seven principles, in priority order. When two conflict, the lower number wins.

| # | Principle | Test |
|---|-----------|------|
| 1 | **Immediate** | Record begins within 300 ms of tap. Playback begins within 100 ms. Nothing blocks. |
| 2 | **Obvious** | A first-time user starts recording in ≤ 3 seconds with no instruction. |
| 3 | **Reversible** | Every edit undoes. Every deletion recovers. |
| 4 | **Calm** | No badge, no nag, no interruption, no celebration the user did not earn. |
| 5 | **Honest** | The meter shows the truth. Clipping is shown as clipping. Nothing is faked. |
| 6 | **Deep** | A professional finds real compression, real EQ, real limiting, real loudness targets. |
| 7 | **Beautiful** | Spacing, type, alignment and motion are of a standard that reads as luxury. |

## 1.5 Core Values

- **Craftsmanship over feature count.** A feature that is not excellent is not shipped.
- **Precision over approximation.** DSP is implemented to specification (BS.1770-4, ISO 11172-3), not to "sounds about right".
- **Restraint over decoration.** Motion exists to explain; colour exists to signal.
- **Dignity of use.** The app is quiet, respectful, and never manipulative.
- **Accessibility is quality.** An interface a blind reciter cannot use is a broken interface.

## 1.6 Success Criteria

SAUTIY is succeeding when all of the following are true and measured:

| Criterion | Standard |
|-----------|----------|
| Cold start to armed record UI | ≤ 700 ms on a mid-range device |
| Tap-to-first-sample | ≤ 300 ms |
| Tap-to-audible playback | ≤ 100 ms |
| Frame budget during live recording | 60 fps sustained; zero dropped frames on the waveform |
| Sample loss on process death | ≤ 2 seconds, recoverable on next launch |
| Taps to export a finished recording | ≤ 3 |
| Taps to start a recording from cold launch | 1 |
| Screens needed for the full Record→Export chain | 1 |
| Core capability requiring network | none |
| Interactive elements below 48 dp | none |
| Text/background contrast | ≥ 4.5:1 body, ≥ 3:1 large & non-text |
| Unlabelled controls for a screen reader | none |

## 1.7 What SAUTIY Is

- A professional field and studio recorder that happens to fit in a pocket.
- A waveform editor with a real, sample-accurate, non-destructive timeline.
- A mastering chain: noise reduction, EQ, compression, de-essing, limiting, loudness normalisation.
- A publishing tool: MP3, WAV, FLAC, M4A, straight to storage or the share sheet.
- A disciplined practice instrument for reciters, with takes, comparison and progress.

## 1.8 What SAUTIY Is Not

Recorded explicitly so that future work does not drift into them:

- **Not a DAW.** No MIDI, no virtual instruments, no unlimited track counts, no plugin hosting.
- **Not a social network.** No feed, no followers, no comments, no profiles.
- **Not a subscription trap.** No paywalled meters, no watermarks, no export limits on core formats.
- **Not a telemetry vehicle.** No analytics SDKs. Ever.
- **Not a cloud service.** No mandatory account. No server dependency for anything that matters.
- **Not a toy.** No gimmick filters, no cartoon voice effects, no gamification.

## 1.9 The Design Review Gate

No screen enters the product until every answer is *yes*:

1. Can a child understand what they are looking at?
2. Can a professional trust the numbers it shows?
3. Can the primary task be completed in one or two taps?
4. Does it look premium?
5. Does it feel effortless?
6. Does it reduce cognitive load compared to the alternative?
7. Does it answer *What am I looking at? What is the primary action? What happens next?* instantly?

Any "no" sends the screen back to design. There is no override.

## 1.10 The No-Placeholder Clause

The strings `TODO`, `Placeholder`, `Coming Soon`, `Future Work`, `Planned`, and
`Not Implemented` are forbidden in shipped code and shipped UI. Where a capability depends
on something genuinely unavailable, SAUTIY implements the best real solution achievable on
the device today and exposes a clean extension point — a named interface with a working
default implementation — rather than an empty promise.

## 1.11 Amendment

This Bible is amended by editing it, in the same commit as the code that motivated the
change, with the reason stated. Silent divergence between code and constitution is the one
unrecoverable defect.

---

### Implementation

| Clause | Code |
|--------|------|
| 1.4 Principles, 1.6 criteria | `sautiy-core/.../SautiyConstitution.kt` — machine-readable budgets asserted by tests |
| 1.6 Performance budgets | `sautiy-core/.../PerformanceBudget.kt` |
| 1.10 No-placeholder clause | `sautiy-core/src/test/.../NoPlaceholderTest.kt` — scans the source tree and fails the build on any banned token |
