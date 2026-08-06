# Chapter 19 — Engineering Standards

> The architecture exists to make the Editorial Bible testable. That is its whole purpose.

---

## 19.1 The Two-Tier Split

```
sautiy-core     Pure JVM Kotlin. Zero Android dependencies.
                Audio engine, DSP, codecs, timeline, workspace law, domain model.
                Compiles and its full suite runs on any JDK.

app             Android. Compose UI, AudioRecord, AudioTrack, MediaCodec,
                foreground service, file access, permissions.
                Included by Gradle automatically when an SDK is resolvable.
```

**The rule:** if a line of code makes a *product decision* — which tools appear, whether a
transition is legal, how long a fade is, when to flush, what a preset does — it belongs in
`sautiy-core`, where it can be tested. The Android layer owns only what genuinely needs a
device.

This is why the one-canvas law, the cognitive budget, the contrast floors, the DSP chain and
the entire edit engine are verified by 248 tests that need no emulator, no device and no
Android SDK.

## 19.2 State

- **Unidirectional.** State flows down as one immutable value; events flow up as callbacks.
- **One source of truth per concern.** The timeline lives in `EditHistory`; the workspace
  configuration lives in `WorkspaceState`; the UI holds neither, it renders them.
- **Immutable throughout.** Every core type is a `data class` or a `class` with no public
  mutation. `AudioBuffer` is the sole exception, and deliberately so: audio processing that
  allocated a new buffer per stage would allocate gigabytes per export.
- **No product logic in the ViewModel.** It translates device events into core calls and core
  state into UI state. If a policy question is ever answered there, that is the bug.

## 19.3 Threading

| Work | Where |
|---|---|
| Capture read loop | A dedicated IO coroutine. Never the main thread. Never allocating. |
| Playback render/write loop | A dedicated IO coroutine |
| DSP, encoding, analysis | IO dispatcher |
| Waveform column resolution | Off the draw phase, before it |
| Everything the user touches | Main thread, and nothing else on it |

**Invariant:** the main thread never performs file I/O, never encodes, never renders audio and
never resolves a pyramid. It has 16.67 ms and it spends them drawing.

## 19.4 Errors

- A failure that the user must know about becomes a `SautiyError` — a type that cannot be
  constructed without fact, consequence and remedy.
- A failure the user cannot act on is not shown. It is handled.
- `runCatching` is used only where a specific, recoverable, expected failure exists, and is
  never used to swallow a category of exceptions silently.
- Invariants are enforced with `require`/`check` at construction, so illegal states cannot be
  built rather than being detected later.

## 19.5 Privacy And Security

| Rule | Mechanism |
|---|---|
| Audio never leaves the device | **No `INTERNET` permission in the manifest.** The process cannot open a socket. |
| No telemetry, ever | No analytics dependency exists in the build |
| No advertising identifiers | Not read, not declared |
| Recordings are private | App-private internal storage; nothing in a public directory |
| Sharing is per-file and explicit | `FileProvider`, granted URI, only from the export staging directory |
| Backups exclude audio | Capture and export directories excluded from cloud backup |
| No broad storage permission | Export writes through the document picker, where the user chose |

The absence of the internet permission is the strongest privacy claim in the product, because
it is enforced by the operating system rather than by our good intentions — and any future
networked capability is a conscious amendment to the manifest, visible in a diff.

## 19.6 Dependencies

The runtime dependency list is deliberately short: Kotlin stdlib, coroutines, serialization,
AndroidX and Compose. **The entire audio engine is original work in this repository** — capture,
DSP, timeline, WAV, FLAC. There is no audio library.

JLayer appears at **test scope only**, as an independent decoder used to check SAUTIY's own
output. It is not on any runtime classpath.

A new dependency requires a stated reason and an assessment of what it costs in size, in
permissions and in trust.

## 19.7 Testing

| Kind | Where | Runs on |
|---|---|---|
| Law tests | `WorkspaceLawTest`, `ContrastTest`, `DesignSystemTest`, `NoPlaceholderTest` | Any JDK |
| Engine tests | PCM, WAV, FLAC, resampler, peaks, edit engine, DSP, loudness | Any JDK |
| Transport tests | Recording and playback state machines | Any JDK |
| UI tests | Compose semantics and accessibility | A device |

**Signal assertions, not shape assertions.** "The 20 kHz tone's alias is below −60 dBFS" is a
claim about whether the resampler works. "The array has 32,000 entries" is not.

**Laws are asserted over the whole state space.** `WorkspaceLawTest` enumerates every reachable
workspace state and checks the chapter 3 and 4 rules against all of them, rather than against
the handful a reviewer happened to open.

## 19.8 Code Style

- British English in all identifiers and prose: `normalise`, `colour`, `centre`, `favourite`.
- Explicit API mode in `sautiy-core`: every public symbol has an explicit visibility and type.
- Comments explain **why**, never what. A comment restating the code is noise; a comment
  recording why a scale factor is 32768 and not 32767 is the difference between maintainable
  and mysterious.
- Names are the domain's: `frames`, not `count`; `dBFS`, not `level`; `take`, not `item`.
- No abbreviations that are not domain terms.

## 19.9 Backup And Restore

Projects and settings are backed up; raw capture audio is not — it is large, and the user did
not ask for it to leave the device. Device-to-device transfer includes takes, because that is a
move rather than a copy to somebody else's server.

---

### Implementation

`apps/sautiy/settings.gradle.kts` (the two-tier split and conditional `:app` inclusion),
`apps/sautiy/app/src/main/AndroidManifest.xml` (the absent internet permission),
`apps/sautiy/sautiy-core/src/test/` (248 tests).
