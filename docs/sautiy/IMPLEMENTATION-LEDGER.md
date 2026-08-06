# SAUTIY™ — Implementation Ledger

**This document does not round up.**

The record distinguishes what is *built*, what is *tested*, what is *verified by an executed
test run*, and what is *source-complete but unproven*. Overstating would be worse than saying
nothing, because the next person builds on it.

Branch `claude/sautiy-editorial-bible-app-nhdku6`.

---

## The Build Environment

The development sandbox blocks `dl.google.com` and `maven.google.com`, so `:app` cannot be
compiled there. **The build runs on GitHub Actions**, whose runners ship the Android SDK and
reach Google's Maven without restriction. `.github/workflows/sautiy-apk.yml` runs the engine
tests, builds the debug APK, lints it, uploads the artifact, and then **installs it on an
emulator and launches it**. That workflow is the source of truth for anything claimed about the
Android layer.

---

## Verified — tests written and executed, passing

**411 tests, 0 failures.** Reproduce with `cd apps/sautiy && gradle :sautiy-core:test`.

| Area | Tests | What was actually measured |
|---|---|---|
| **Ch.1 no-placeholder clause** | 6 | Source scan fails the build on placeholder tokens; proven not to false-positive on `toDouble` and proven to catch real ones |
| **Ch.2 colour** | 7 | WCAG contrast for every text and status role against every legal surface, both themes |
| **Ch.2/5/6 design system** | 10 | 4 dp grid, tabular figures, line heights, Qur'anic leading, motion tiers, no overshoot, meter ballistics |
| **Ch.3/4 workspace law** | 26 | Asserted over **224 enumerated states**: one destination, immovable dock, ≤6 context tools, exactly one primary action, no destructive control while recording, no panel over the dock, 3-word labels, errors with remedies, exactly four interruptions |
| **Ch.7 PCM/format** | 15 | All six encodings round-trip within a quantisation step; +1.0 never wraps negative; capture hot path matches the byte path |
| **Ch.7 WAV** | 14 | Chunk-tolerant reading; **after every flush the file is a complete playable WAV**; a process kill recovers every flushed frame |
| **WAV stream reader** | 12 | Every block matches the reference reader sample for sample; reads independent of order; stale scratch bytes never leak into a short read; both edges padded; streamed peaks equal in-memory peaks exactly |
| **Ch.7/8 transport** | 23 | Both state machines; illegal transitions refused; flush cadence inside the loss ceiling; storage critical at exactly two minutes |
| **Resampling** | 12 | 20 kHz → 32 kHz alias below −60 dBFS; per-tier rejection floors; no edge fade; channel independence |
| **Ch.15 waveform** | 13 | Decimation preserves extremes exactly; the loudest sample survives full zoom-out; incremental build matches one-shot |
| **Ch.9 edit engine** | 35 | Invariants unconstructable when violated; ripple law; 5 ms seam fades; equal-power crossfades hold power where linear provably dips; exact undo/redo/time-travel |
| **Ch.9.7 silence** | 10 | Threshold follows the room; sub-350 ms pauses preserved as rhythm |
| **Ch.10 DSP** | 26 | 4:1 means 4:1; continuous knee; limiter holds its ceiling and stays time-aligned; noise profile in real signal RMS |
| **Ambience engine** | 20 | **Measured T30 matches the stated RT60 within 25% at 0.5, 1, 2 and 3 seconds**; pre-delay is a real gap and never delays the dry voice; width 0 gives one room in both ears and width 1 two; warmth cuts the 8 kHz tail by more than half while leaving 200 Hz alone; a larger room answers later; **137-frame blocks are bit-identical to one pass**; every space finite and within ±18/+6 dB of dry |
| **Voice Studio** | 29 | **Preview output is sample-identical to the render**, and identical at 97-frame blocks as at 4 096; the stages a preview cannot run are named rather than faked; each of the eight controls moves its own range >2 dB in both directions and a centred control is bit-transparent; tone provably cannot reach the compressor's detector; the de-esser cuts 7 kHz >3 dB while moving a 300 Hz vowel <1 dB; hum removal takes the fundamental *and* two harmonics >20 dB; all twelve spaces render finite and unclipped; every stated delivery standard is reached within 2 LU and every ceiling respected |
| **Ch.10.4 loudness** | 17 | **−20 dBFS 1 kHz reads −23.0 LUFS at 44.1, 48, 32 and 96 kHz**; 20 s silences do not shift programme loudness; true peak exceeds sample peak on inter-sample material |
| **Ch.14 FLAC** | 12 | **Bit-exact round trips** through SAUTIY's own decoder; 2 s silence under 2 KB; speech under 75% of WAV |
| **Ch.14 export registry** | 5 | Unregistered formats fail loudly; platform encoders register without core knowledge |
| **Ch.13 library store** | 19 | Save survives restart; delete goes to trash with a stated date; atomic write leaves no temp file; a corrupt index does not take the recordings with it |
| **Ch.4.6 search** | 12 | Full ranking order title > tag > marker > transcript > date; trashed entries never appear; an unrecognised phrase matches nothing rather than guessing |
| **Ch.14 export pipeline** | 13 | What is exported is what was heard; progress is monotonic 0→1; a format that cannot carry the project rate is resampled to the nearest legal rate at or above it |
| **Voice tuning** | 28 | Each of the seven listener words moves the voice in the direction it names, and too-bright/too-dark undo each other; a panel applies only the majority's notes and applies them once; every `VoiceAdvisor` rule fires on material that warrants it and stays silent on material that does not; Voice Match closes half the measured gap and never claims to close it |
| **Voice Space layers** | 7 | Choosing an acoustic environment changes the room and provably nothing else; all eight are distinct, finite and unclipped, and their decays order the way the names imply; the seven recitation profiles are distinct rooms and each preserves a recited phrase's loudest-to-quietest ratio at 2.5 or better; the disclosure denies both reproduction and affiliation; Auto Studio returns a defensible outcome and a reason for it |
| **Signature sound** | 9 | **Every acoustic, outcome, acoustic space and recitation profile is inside the house style — at all five intensity stops.** The pre-delay floor scales with decay and is monotonic in it, so a booth may answer in 6 ms and a hall may not; every decibel of room provably buys a matching amount of ducking, and that relationship is monotonic; Voice Space at 100% can no longer reach a room level that drowns the voice; a hand-edited voice with every slider at its end is brought inside the rules and *still has a big room*; `applyTo` is idempotent on all ten outcomes; every rule states an audible consequence |
| **Voice DNA** | 10 | A saved sound restores the complete instrument including hand edits, not a preset reference; saving puts it inside the house style; a file written by an older version still loads; a corrupt file loses the sounds and not the app; saving over an existing sound replaces rather than duplicates; the list orders by what the user reaches for; two lecture series can both be saved; the summary cannot disagree with the settings it describes; a blank name is refused at construction |
| **Adaptive restraint** | 5 | **A clean recording comes out within 1 dB of how it went in, in every band** — measured, not inferred from which stages were enabled — with no compressor, no de-esser, no noise reduction and no tone shaping; a noisy, quiet, uneven, sibilant recording gets all four; four small imperfections produce less than 35% of the treatment; strength never leaves 0–1 and the summary is never blank |
| **Recording guidance** | 8 | **A good signal produces silence.** Clipping outranks everything and only one thing is ever said; distance advice is a physical action with no decibels or gain in it; a noisy room is a suggestion and not a warning; a closed microphone produces nothing rather than advice about silence; a noisy room is never told to add a large space; the level gauge puts the ideal level in the middle and is monotonic across the whole range |
| **Listening database** | 8 | One listener never moves a preset; a majority calling it too bright makes it less bright; a panel of 40 moves a preset exactly as far as a panel of 3; every critical note in majority at once still leaves the result inside the house style with its room intact; a well-liked preset can prove it; unheard and disliked are never the same value; the tally survives a round trip and fails an empty database on a corrupt file |

---

## Verified on a running Android — 24 instrumented tests, all passing

`AudioRecord`, `AudioTrack` and `MediaCodec` have no meaningful stand-in on the JVM, so every
claim about them is earned here: the CI emulator job installs the APK, launches it, and then
runs the instrumented suite. **All 24 pass**; the task fails on a single failing test, so a
green job is every test passing.

| Phase | What the device confirmed |
|---|---|
| **A — recording** | The microphone opens and reports no failure; frames arrive and reach the waveform callback; the file on disk is a real WAV whose header agrees with what capture reported; **the file is complete and readable while recording is still running** — the crash-recovery guarantee observed rather than argued; pause stops promptly and stays stopped, and resume continues the same take; a second take opens after the first is stopped, which is the only way a leaked `AudioEffect` ever shows itself |
| **B — playback** | Playback starts and the head advances; a take recorded on the device plays back on it; playback through a Voice Space does not stall and changing the space mid-playback does not stop it; **starting and immediately stopping six times over does not take the process with it** |
| **MP3** | **The encoder is in the APK and loads** — asserted, not skipped when absent. Android's own `MediaExtractor`/`MediaCodec` — the code every other application uses to open an audio file — reports `audio/mpeg`, the right rate and channel count; the duration survives within 150 ms declared *and* decoded; the file decodes to real audio rather than silence; the ID3v2 synchsafe size lands exactly on an MPEG frame sync; 44.1 and 48 kHz in mono and stereo all round-trip; the file survives being handed to another application as a `content://` URI; two minutes encodes with monotonic progress in under 30 seconds |
| **Latency** | **Measured, not asserted.** The clock starts on the call a tap makes and stops when the playhead moves — which only happens once a block has been accepted by `AudioTrack`, so it times audio genuinely leaving the application. The median of five runs on a five-minute recording is inside the constitution's 100 ms tap-to-audible budget; starting deep inside a long recording costs no more than starting at the top; the largest Voice Space does not cost the instant start; and opening a five-minute recording and hearing it is under a second, with the peaks built afterwards rather than on the way |
| **E — export** | Every format the panel offers writes bytes and reports the length it wrote; an exported WAV re-probes as the same project; progress runs 0→1 without going backwards; M4A comes back from MediaCodec; a format with no encoder refuses loudly rather than writing a broken file |

**What the device tests found, which is the point of them.**

`lame_encode_buffer_interleaved` is documented for stereo, and its `num_samples` parameter means
samples *per channel* — it reads `num_samples × 2` shorts whatever the encoder is configured for.
Handing it mono audio makes it read twice the data that exists: a native overrun that killed the
process with no Java exception, no stack and nothing to act on. Mono now goes through
`lame_encode_buffer`. The bridge also refuses an out-of-range read rather than performing it, so
a wrong frame count is a returned error code with a sentence attached instead of a dead
application.

Two earlier failures in the same sequence were harness faults, not product faults, and are
recorded as such: the device-test job rebuilt the app without the LAME sources, so it tested a
build that was not the one shipped; and `Mp3Encoder` discarded the reason `System.loadLibrary`
failed, making "library missing" and "library failed to link" indistinguishable.

And earlier still:

`AudioTrack.write` with `WRITE_BLOCKING` does not respond to coroutine cancellation — it
returns when the track is paused, flushed or drained, and not before. `stop()` cancelled the
render loop and released the track while a write was still in flight, the native pointer went
away underneath it, and the uncaught `IllegalStateException` **killed the process**. Stopping
playback at that moment is the ordinary case, not an edge, and no amount of reading the code
was going to surface it. The ordering is now pause → flush → cancel, with the loop owning the
release on its way out.

A second defect fell out of the same reading: a cancelled loop invoked `onFinished`, so
stopping playback reported reaching the end and moved the transport to STOPPED behind the back
of whatever had just stopped it.

## Compiles, lints and launches — verified on CI

The APK builds, lints clean, installs on an emulator and **the app opens**. The smoke job boots
an x86_64 emulator (API 30), installs the APK, starts the activity and checks it 20 seconds
later; it fails the build on anything in the crash buffer or if the activity is not the resumed
one. This is a permanent gate on every push, not a one-off.

**The launch crash that reached the first APK:** `splash_background.xml` wrapped a
VectorDrawable in `<bitmap>`. That drawable was the window background, so the framework
inflated it while creating the window — before `onCreate`. It crashed on every device, every
launch, and both the compiler and lint were silent, because it is a runtime resource-inflation
failure.

---

## Fixed under the executive reset

Each of these was a control that looked complete and carried out no work. All were found by
reading the code against the reported symptoms.

| Reported symptom | Actual cause | State |
|---|---|---|
| Enhancement is ineffective | `applyPreset()` was `_state.update { it.copy(appliedPreset = preset) }` — the card highlighted and no sample was ever processed | Applies to playback and export |
| Reverb and echo do not work | Same cause; the Space panel was a read-only list of the preset's numbers | Nine live ambience controls |
| No graphs or waveform | `openRecording()` never rebuilt the peaks, so a saved recording opened against whatever the last recording left in the builder | Streamed from the file off the main thread |
| Playback is slow | `FileSourceProvider` called `WavCodec.readRange` per block — twenty-five file opens and header walks per second of audio, on the thread feeding the speaker | One open reader per take |
| Delete and file management broken | The library panel had no rename and no delete at all | Both on the row; delete confirmed in place |
| — | `onExport` was `{}` | Runs `ExportJob`, reports progress, deletes part-written files and states failures |
| — | `onShare` was `{}` | Exports first if needed, then a `content://` URI through the FileProvider |
| — | A/B compare flipped a boolean and never told the player | Reaches the audio |
| — | Playback and export assumed mono regardless of the material | Carries the project's channel count |

**Removed rather than left in place**, per the directive: the previous `Reverb` (allocated its
comb bank per call, so it restarted the tail at every block boundary — usable offline,
impossible to preview live), `Echo`, and `StudioChain` with its nine presets. Two space engines
would be exactly the disconnected-sliders problem the reset rejects.

---

## What remains unproven, precisely

The emulator has no microphone in front of it and no speaker behind it. So the device tests
establish that the platform objects open, that frames flow, that files are written and reopen
correctly, and that nothing crashes — but **not** that the captured audio sounds like the room,
that playback is audible, that any space sounds like its name, that the waveform draws
under a finger, or that a gesture selects what the user meant. Those need a human with a phone.

The Voice Studio's *arithmetic* is proven on the JVM to a measured standard; its *sound* is a
judgement only a listener can make.

A CI emulator is also slower and jerkier than a phone, so the latency figures are a floor rather
than a measurement of real hardware. A failure there would be real anywhere; a pass means the
budget is met on something slower than the target device.

| Item | Why | Where recorded |
|---|---|---|
| **On-device transcription** | Depends on a platform recogniser; where none is present the capability is absent rather than degraded. | Ch. 11.4 |
| **Qur'an Studio project store** | Model complete; persistence and panel not written. | Ch. 12 |
| **Spectrogram rendering** | The FFT is implemented and tested; the drawing is not written. | Ch. 15.2 |
| **Media session / lock screen** | Not implemented. | Ch. 8.7 |
| **Settings and About screens** | Not built. | Ch. 4.1.2, 22.3 |
| **Instrumented UI tests** | Require a device. | Ch. 19.7 |
| **Voice Match reference picker** | The analysis, the half-gap match and the honest explanation are written and tested; there is no file picker to point them at a reference recording, so the feature is unreachable from the app. | Ch. 10 |
| **Listening panel persistence** | `ListeningPanel` computes consensus correctly; notes are not stored between sessions, so a multi-listener panel cannot yet be run over days. | Ch. 10 |
| **Waveform editing** | Deliberately not started. Blocked behind the four listening questions. | Ch. 9 |
| **Rename before export** | Exports take the project name; there is no field to change it at the moment of export. | Ch. 14 |
| **That the signature sound is recognisable** | The rules hold everywhere and that is tested. Whether they add up to a sound a person could identify blind is a listening judgement, and it is not claimed. | Ch. 10 |
| **Playback "like Spotify"** | Start latency is measured inside the 100 ms budget on an emulator, and reads are streamed rather than reopening the file per block. Whether it *feels* instant and fluid on a real phone under a real finger has not been seen. | Ch. 8 |
| **That the Studio feels like a mastering suite** | Deliberately not claimed. Gauges, restraint reporting and a calm recording view are the parts that can be built; how it feels is the user's to judge. | Ch. 6 |

---

## Voice Space 2.0 — what was fixed, and what is still unknown

**Four causes of an artificial-sounding room, each removed and each measured:**

| Cause | What was done | How it is checked |
|---|---|---|
| Static comb delays ring at fixed frequencies — the metallic sound that makes a recording seem to *have reverb on it* | Every comb's read position wanders ~½ ms on a slow, mutually detuned LFO, fractionally interpolated | Spectral crest inside narrow sub-bands is lower with the tail moving than still |
| Thin echo density is heard as separate ticks | Diffusion drives both the number of all-pass sections and their coefficient | Tail density rises measurably with the control |
| Low frequencies turn a large room to mud | The reverb send is high-passed at 190 Hz; the dry voice keeps its weight | 70 Hz reaches the room at under half the level of 1 kHz |
| The room masks consonants | Speech priority ducks the wet by the dry envelope, so the room recedes while a word is spoken and blooms in the gaps | The room is measurably quieter during speech and still present in the gaps |

**Two real gain bugs, both of which would have made tuning by ear impossible:**

The all-pass sections were Freeverb's simplified form, which is **not** all-pass — its gain rises
with the feedback coefficient, so raising diffusion raised the volume and no two presets could be
compared. Replaced with the textbook unity-gain Schroeder structure. Removing that accidental
gain then exposed a second: the comb-bank normalisation used the textbook formula, which ignores
that the damping filter sits *inside* the loop and cuts effective feedback everywhere except DC.
On a damped hall it understated the loop gain by around 17 dB.

**Four of the measurements were themselves wrong** and had to be fixed before they measured
anything — recorded because they are the kind of error that produces confident nonsense: crest
over one wide band confuses ringing with tone (a darker tail reads as more metallic); RMS across
windows of different lengths measures how long the tail is, not how loud it is; and ducking
measured on the mixture confuses "the room got quieter" with "everything got quieter".

**Fifteen spaces, three modes.** Natural, Studio and Immersive are one control over *how much*
room, separate from *which* room. Immersive raises the mix and also raises the floor under speech
priority, so turning the room up cannot quietly cost intelligibility.

**Not tuned by ear, and not claimed to be.** The numbers are derived from the acoustics of the
places the presets are named for — a plastered room absorbs less treble than a carpeted one, a
larger space answers later and needs more diffusion to stop sounding grainy, a longer tail needs
more speech priority to stay intelligible. That reasoning gets a preset close. Only listening
gets it right, and no one has listened to these yet. **Hear every space** exists for exactly that:
it loops one five-second passage, starts on the original, and changes the room underneath the
same phrase every five seconds, so the whole roster is one tap and seventy-five seconds instead
of fifteen separate manual comparisons.

## The signature sound, as rules the build enforces

A signature sound is not a preset. It is what is true of **every** SAUTIY recording, whichever
preset made it — the reason someone could recognise the app across ten voices in ten rooms. Reverb
engines have no signature; record labels and mastering houses do, and the difference is that a house
has rules. `SignatureSound` is the house, and it is written as rules rather than as a preset:

* **The voice is in front of the room.** Pre-delay is not a fixed minimum — the rule is a
  *relationship*: 5 ms floor plus 3.5 ms per second of the room's own tail. A vocal booth genuinely
  answers in 6 ms, and forcing it to 12 would make it a different room; a 3.6-second hall answering
  in 6 ms is a voice smeared with a hall. Stated as a house rule chosen to hold of real rooms, not
  as anything derived from Sabine.
* **Every decibel of room buys a matching amount of standing back.** `requiredProtection(mix)` ties
  the two together, so a preset cannot add room without adding the ducking that keeps words above
  it. This is the central law and the thing most likely to be audibly different from other mobile
  recorders, where turning the reverb up buries the speech.
* **Never harsh, never thin, one ceiling.** Presence capped, air capped, warmth floored once a room
  is present, room brightness capped, −1 dBTP on everything that leaves.

`verify()` returns the rules a setting breaks **and what each one sounds like** — a rule whose
consequence cannot be described to a listener was invented for the code. A test runs every acoustic,
every outcome, every acoustic space and every recitation profile through it, at all five intensity
stops. **A preset that breaks the house style fails the build rather than shipping.**

**What this does not claim.** That the rules produce a sound anyone recognises is a listening
judgement and is not asserted. What is asserted is that the rules hold everywhere — which is the
part a listener could not check for themselves, and the part that has to be true first.

### What writing the rules down immediately caught

Turning Voice Space to 100% on an already-wet preset reached **73% room against 65% ducking**. That
is the washy sound the control exists to avoid, and it was reachable in two taps by anybody. Someone
asking for a bigger space did not ask to be buried in one. `VoiceCharacter` now clamps the mix to
the house ceiling and raises protection to match, so **the control is safe at its maximum** — which
is not true of the equivalent control in any mobile recorder I know of.

A second, quieter defect came out of the same test: `applyTo` computed the pre-delay floor from the
*stored* decay, but the character control lengthens the tail — so every saved sound sat one notch of
intensity away from breaking its own rule. Both floors are now computed from the room the listener
actually gets.

## Voice DNA — your own sound, saved whole

The problem is not storage. A reciter who spent twenty minutes getting their Qur'an voice right, and
who records twice a week, currently has to get it right again every time — and will not. They will
settle for the nearest preset, and twenty minutes of judgement about *their own voice* is discarded
every session.

So a Voice DNA is the **complete** instrument: cleanup, dynamics, tone, room, intensity, loudness,
output gain. Not a preset reference with adjustments on top — a preset re-tuned in a later version
would silently change a sound the user had already decided was finished. **A saved sound is a promise
that it will not move.**

* Names are occasions, not settings. "My Qur'an Voice", offered as a chip, because naming is the
  step at which people abandon a save.
* Two lecture series can both be saved: a duplicate name gets a number rather than a refusal.
* Written atomically — temp file, `fsync`, rename. The flush is the part people leave out, and
  without it a power loss leaves a correctly-named empty file, which is worse than a corrupt one
  because nothing detects it.
* Tolerant decode: a file written by an older version still loads after a field is added. A test
  asserts it, because losing somebody's saved Qur'an voice to an app update is unforgivable and
  entirely preventable.
* Saving runs the sound through `SignatureSound.applyTo`, which is idempotent — a test asserts that,
  because `applyTo` runs on every save and a function that drifted would slowly change finished work.

## Restraint — the best enhancement is often none

The failure mode of every "enhance" button is that it does the same amount of work to everything.
Hand it a clean, close, well-levelled recording and it compresses, brightens and de-esses anyway,
and the output is worse than the input — leaving the user in the worst position an app can create:
the feature made it worse and they cannot tell which part.

`Restraint` measures four deficits — noise, level, balance, movement — each scaled against the point
at which it stops being a problem rather than against perfection. The **mean**, not the sum: four
small imperfections are not one large problem, and a test asserts that a recording slightly short of
ideal in four ways gets less than 35% of the treatment.

Below 18% total deficit, `enhance` returns **no compressor, no de-esser, no noise reduction, no tone
shaping** — a 70 Hz high-pass and a delivery level, nothing else. The test for this does not count
enabled stages; it measures band energy before and after and requires every band to move **less than
1 dB**. That is as close as a machine can get to "it sounds like itself".

The other half is asserted too: a noisy, quiet, uneven, sibilant recording gets the compressor, the
noise reduction, the de-esser and the presence lift. Restraint must not become inertia.

## Intelligent recording — guidance that stays quiet

Almost every bad recording is bad for one of four reasons, all fixable in the two seconds before the
take: too far, too close, too loud, or too noisy a room. **None is fixable afterwards.** Noise
reduction is repair; moving 15 cm is prevention, and prevention sounds better than any processing.

`RecordingAdvisor` reads the live input and says **one** thing, only when something is wrong, in
words that need no equipment — "move closer, about a hand's width from the microphone", never
"increase input gain by 6 dB". It never blocks, never confirms, never asks. A test asserts that a
good signal produces **silence**: advice that always appears is wallpaper, and wallpaper is not read
when it matters.

It also decides how much Voice Space the room can carry afterwards, because ambience is a delay line
fed by whatever the microphone heard — a large space on a noisy recording gives the noise a tail. A
test asserts a noisy room is never told to add a large space.

**A defect this exposed:** the noise floor was the constant `-62.0` in the ViewModel. Every quality
score and every claim about background noise was about a number nobody had measured — somebody
recording in a car with the engine running was told their floor was clean. It is now a decaying
minimum of the running level, because the gaps between words *are* the room.

## Live Studio — recording should feel calm

While the microphone is open, the layer strip and the context tools disappear. Both are things to
decide about, and a person mid-sentence cannot decide about anything. What is left is the waveform,
the level meter, and three conditions as words-with-dots: headroom, quiet room, quality. **Calm is
mostly subtraction.**

## The listening database — presets shaped by real listeners

Not machine learning, not a cloud service, nothing leaves the phone. A tally: every "too bright"
tapped while auditioning Rich Narration lands against Rich Narration, and once enough people agree,
the preset moves.

No amount of acoustic reasoning can tell you whether Grand Space is slightly too bright on the
average person's headphones. Only the average person can, and they will say so for free if tapping a
word costs one second.

Five limits, each tested:
* **Three independent notes minimum.** One note is a person's taste, their headphones, and possibly
  a mistap.
* **Each agreed note applied once**, however many said it. A test asserts a panel of 40 moves a
  preset exactly as far as a panel of 3.
* **Two steps maximum** per preset, so it can be improved and cannot be walked off a cliff. A test
  puts every critical note in majority at once and asserts the result is still inside the house style
  and still has a room.
* **Approval is counted too**, so a preset most people like can prove it rather than only complaints
  being recorded.
* **Unheard and disliked are never shown as the same thing** — `null` versus `0.0`, because a gauge
  that conflates them is lying.

## Premium visual feedback

`ValueArc`, `ConditionDot` and `RangeBar` replace prose where prose made the user read during the one
activity where they should be listening. Three rules hold across all of them: **a number is always
available** (professionals must be able to write a setting down and quote it), **colour is never the
only signal** (roughly one man in twelve cannot rely on it), and **nothing animates faster than the
eye integrates**.

## Two layers, one path through them

**Layer one is outcomes.** Ten, in four groups: Speech (Clear Speech, Warm Voice, Rich Narration),
Professional (Studio, Broadcast, Podcast, Lecture), Recitation (Prestige Recitation), Space (Grand
Space, Immersive). Group headings rather than a second level of choice. Lecture is in the list
because a lecture is a thing people record, not an acoustic to be inferred; Majestic Recitation
left it because a list of ten is only useful while it stays ten.

**Layer two is acoustic space, and it is optional.** Eight environments — Vocal Booth, Broadcast
Booth, Small Hall, Large Hall, Auditorium, Small Mosque, Large Mosque, Grand Mosque — below
everything else, as rows rather than cards. Two sets of equally-weighted cards read as two
competing answers to one question, so the visual weight carries the hierarchy. **Choosing an
environment changes the room and nothing else**: `chooseSpace` copies the ambience profile over the
current voice and leaves cleanup, dynamics and tone exactly where they were. Someone who moves to a
larger hall did not ask for a different voice, and an environment that quietly re-tuned the tone
would make the two layers indistinguishable, which is the confusion having two layers exists to
avoid. A test asserts this directly.

**The Recitation Studio** is seven complete recitation voices — Natural, Makkah Inspired, Madinah
Inspired, Grand Mosque, Prestige, Majestic, Immersive — each built on Prestige Recitation's
treatment (light compression that leaves the delivery's dynamics alone, a gentle de-esser, no
presence lift) in a space of its own character. Grand Mosque and Majestic were literally the same
room until a test caught them sharing a decay; they are now different rooms, and the test that
caught it stayed. A second test holds the loudest-to-quietest ratio of a recited phrase at or above
2.5 through every profile: flattening the delivery is the one thing a reciter will never forgive.

**The disclosure is always on screen**, under the list, not behind a tap:

> Creative ambience profiles inspired by the character of large stone spaces. They do not reproduce
> any specific building, and SAUTIY is not affiliated with any mosque or institution.

A test asserts the text denies both reproduction and affiliation. The people who care most about
these recordings are exactly the people a name like "Makkah Inspired" could mislead.

**Auto Studio proposes, and waits.** One tap renders at most twenty seconds, measures it with
`VoiceAnalysis`, and returns an outcome, an intensity and a reason in one sentence — "The recording
sounds distant, so this brings the voice forward before anything else." Nothing is applied until
the user accepts. A recommendation that simply happens to your recording is a decision taken on
your behalf; one you can read and disagree with is a starting point. The rules are ordered by how
confidently each can be read from audio: noise and distance first, because they are unmistakable,
and the safe middle answer where nothing stands out.

**Voice Space is one control** — the old Character slider, renamed for what it is and read as a
percentage with its name ("50% · Rich"). It is the only room control the Space panel shows by
default. Fifteen sliders is the correct set of controls and the wrong first screen; Advanced Studio
reveals all fifteen, and reveals all of them, because the reason a professional opened it is the
one control that would have been left out of a curated subset.

**What sits under an outcome is a room**, and the fifteen `VoiceSpacePreset` acoustics remain the
implementation of every outcome. Inside layer one they appear only as an Advanced disclosure —
"Based on: Grand Hall" — inside an applied card, never as a thing to choose. **Layer two is the one
place a room is chosen by its own name, and it is a deliberate detour rather than the main path.** A
person offered "Prestige Recitation" and "Large Mosque" as equals has to work out which to pick, and
the honest answer is not something they should have to learn; offered the outcome first and the room
below it, they only reach the room if they came for a room.

**Voice Space has five stops** — Natural, Refined, Rich, Grand, Immersive — and a
listener may stop anywhere between them. Four things move together, because more space is not
one parameter: the room grows, lasts longer and gets louder, and the speech protection rises with
all three. A raised mix on an unchanged room sounds like the volume of an effect rather than a
larger place. Above Rich it also adds richness, air and depth to the voice, so the word means what
it says. Moving Voice Space keeps the preset name; moving a detailed control clears it.

**The tuning loop.** Seven words — too bright, too dark, too harsh, too muddy, too much room, too
little room, excellent — each mapping to a defined adjustment, tested for direction and for the
two brightness notes undoing each other. A listener taps a word, the voice moves, they listen
again. `ListeningPanel` applies only what a majority of listeners agreed, once, so a preset moves
by the amount the panel agreed rather than by how many people were in the room.

**Enhance Voice decides.** `VoiceAnalysis` measures level, true peak, loudness range, noise floor
and three tonal tilts; every rule in `VoiceAdvisor` has a stated threshold and reason. Noise
reduction only where there is noise. Presence only on a dull recording. A de-esser only on
sibilant material. No room, because a room nobody asked for is the change most likely to be wrong.

**Voice Match** closes half the gap to a reference in level, tonal balance and dynamics, and says
outright that it cannot reproduce someone else's sound — the reference was a different voice in a
different room with a different microphone, and none of those is recoverable from a mix. Level is
the one characteristic that can be matched exactly, so it is.

**Not verified by listening.** None of the above has been heard by anyone. The four acceptance
questions — more natural, spacious without artifice, less fatiguing, audibly better blind — cannot
be answered from code and are not claimed.

## The Voice Studio

The signal chain is fixed: `Input → Cleanup → Dynamics → Tone → Ambience → Loudness → Output`.

**Fifteen acoustics** (`VoiceSpacePreset`), each a complete voice rather than a reverb setting:
Pure Studio, Natural Presence, Vocal Booth, Warm Studio, Broadcast, Podcast, Lecture Hall, Small
Mosque, Large Mosque, Grand Hall, Auditorium, Prestige Recitation, Majestic Recitation, Royal
Presence, Cinematic Voice. These are the engine's vocabulary; ten of them reach layer one under
outcome names, eight environments reach layer two under their own.

**Fifteen ambience controls**: amount, wet/dry mix, room size, decay time (RT60 in seconds),
pre-delay, early reflections, late reflections, diffusion, damping, presence, tail smoothness,
speech priority, width, warmth, brightness. All fifteen behind Advanced Studio; one Voice Space
control in front of it.

**Eight refinement controls**, each −1 to +1 with 0 exactly transparent: clarity, warmth,
richness, presence, body, air, brightness, depth. Warmth and brightness appear in both groups
because they are not the same control — one shapes the voice, the other the room it is in.
Depth drives the room rather than the equaliser, because depth is distance and distance is a
room; with no space selected the panel says so instead of pretending.

**Two one-taps**: ✨ Enhance Voice (clean, even, clear; adds no room) and 🎙 Studio Voice (the
finished production, room and all).

**Live preview is the same processing as the export.** `render()` drives the same streaming
chain `live()` returns, so preview output is sample-identical for every setting except noise
reduction and loudness normalisation — which cannot exist under a playback callback and are
therefore named in `deferredStages` and displayed, rather than silently differing.
