# SAUTIY™

**The world's finest mobile audio recording platform.** One intelligent studio, not an
application with screens.

Developed by **Imam Ahmad Sulaimiy** — Senior Software Engineer, Product Architect & Founder.

---

## What this is

SAUTIY™ is engineered to deliver an elegant, dependable and professional mobile audio production
experience with intuitive workflows, premium design, and high-quality recording, editing and
publishing capabilities for creators, educators, reciters, lecturers, broadcasters and
podcasters.

Its constitution is [**The SAUTIY Editorial Bible**](../../docs/sautiy/EDITORIAL-BIBLE/00-INDEX.md) —
twenty-two chapters that are *executable*, not aspirational. Where the code and the Bible
disagree, the code is wrong.

Its honest state is [**the Implementation Ledger**](../../docs/sautiy/IMPLEMENTATION-LEDGER.md),
which records what is built, what is tested, what was actually verified by an executed test run,
and what is not built at all. It does not round up.

## The idea, in one paragraph

Everything happens on **one canvas**. There is no Record page, Enhance page, Library page or
Mixer page — those are twelve panels that arrive over a single workspace which never goes away
underneath them. The transport dock is five slots and never changes for the life of the product.
The context bar adapts to whatever is selected, and *is* the entire navigation model. Recording
begins in one tap from a cold launch, with no name, no format and no destination to choose
first.

## Architecture

```
sautiy-core   Pure JVM Kotlin. Zero Android dependencies.
              Audio engine, DSP, codecs, timeline, product law, domain model.
              Compiles and tests on any JDK — no Android SDK, no emulator, no device.

app           Android. Compose UI, AudioRecord, AudioTrack, MediaCodec,
              foreground service. Included by Gradle when an SDK is resolvable.
```

The split is the point. **If a line of code makes a product decision, it belongs in the core,
where it can be tested.** That is why the one-canvas law, the cognitive budget, the contrast
floors, the entire DSP chain and both transport state machines are held by 248 tests that need
no device.

## Build

Core only — any JDK 17 or later, no Android SDK:

```bash
cd apps/sautiy
gradle :sautiy-core:test     # 248 tests
```

The Android app — needs an Android SDK:

```bash
export ANDROID_HOME=/path/to/android-sdk
cd apps/sautiy
gradle :app:assembleDebug
```

`:app` is included automatically once an SDK is detected. Force it with `-PsautiyAndroid=true`.

## What is genuinely engineered here

The audio engine is original work in this repository. There is no audio library.

- **WAV** written incrementally, so that after every flush the file on disk is already a
  complete, playable recording — a process kill costs at most one second, and it is offered back
  on next launch.
- **FLAC**, encoder *and* decoder, in pure Kotlin. The decoder exists so that "lossless" is a
  proven property rather than a claim.
- **Band-limited resampling** with the anti-alias cutoff pulled below the new Nyquist, so the
  transition band does not fold back into the audible range.
- **A non-destructive, sample-accurate edit engine** whose invariants cannot be violated because
  an illegal timeline cannot be constructed, with history stored as states rather than inverses
  so undo is exact and any step can be travelled to.
- **A DSP chain measured to ITU-R BS.1770-4 and EBU R128** — a −20 dBFS 1 kHz tone reads −23.0
  LUFS at every sample rate, because the K-weighting is re-derived rather than reused.
- **Nine preset cards** named for situations rather than processes, each expanding to its real
  parameters.

## Privacy

**There is no `INTERNET` permission in the manifest.** That is not an oversight and not a
default: without it the process cannot open a socket, so the promise that audio never leaves the
device is enforced by the operating system rather than by good intentions. No analytics, no
telemetry, no advertising identifiers, no account. Any future networked capability is a
conscious amendment to that file, visible in a diff.

## Status

Read [the Implementation Ledger](../../docs/sautiy/IMPLEMENTATION-LEDGER.md). The short version:
the engine is complete and proven by 248 executed tests; the Android layer is source-complete
but has never been compiled, because this repository's build environment cannot reach
`dl.google.com`; MP3 export, transcription and persistence are not built, and are named as such.
