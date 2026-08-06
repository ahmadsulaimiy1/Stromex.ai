# Build SAUTIY, then listen to it

Everything needed to get the app onto a phone and judge it. Written for the machine that has an
Android SDK, because the one this was developed on does not.

---

## Why this file exists

SAUTIY has been built in a sandbox with no Android SDK and no access to Google's Maven, so the
Android half of it has never been compiled locally — only on CI. And CI runs on an emulator, which
has **no microphone**. Every recording ever made of this app is near-silence.

That is the important sentence. The engine has 428 tests and they pass. The reverb topology, the
loudness measurement, the limiter, the signature-sound rules — all verified as arithmetic. But
**nobody has heard SAUTIY**. Not one word of speech has gone through it. Every claim about how it
*sounds* is architectural, not auditory.

A real machine and a real phone close that gap in an afternoon. That is not a workaround for a
broken pipeline; it is the only environment in which the thing this app is *for* can be evaluated.

---

## 1. Build it

```bash
git clone https://github.com/ahmadsulaimiy1/Stromex.ai
cd Stromex.ai
git checkout claude/sautiy-editorial-bible-app-nhdku6
cd apps/sautiy
./gradlew :app:assembleDebug
```

The APK lands at `app/build/outputs/apk/debug/app-debug.apk`.

`settings.gradle.kts` detects the SDK from `ANDROID_HOME`, `ANDROID_SDK_ROOT`, or `sdk.dir` in
`local.properties`, and only then includes `:app`. If the build reports *"no Android SDK detected —
configuring :sautiy-core only"*, that detection failed and nothing else will work until it is fixed.

Opening `apps/sautiy` in Android Studio does the same thing with a Run button.

### If it does not compile

Six commits on this branch have never been through a compiler — `faf78f8`, `6c16355`, `f5abf51`,
`25df211`, `93b2e68` and the tooling one between them. Every changed line has been read by hand and a
static shape-check passes, but read-by-hand is not type-checked.

A compile error here is cheap: Android Studio names the file and line in seconds. Paste it back and it
gets fixed. It is only expensive in the sandbox, where it costs a six-minute CI cycle to discover.

### Install

```bash
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

Grant the microphone when asked. Notifications too, or the foreground recording service cannot show
its notification and Android will stop it.

---

## 2. Listen to it

Do these in order, on a real phone, out loud. Fifteen minutes. The point is not to confirm the app
works — it is to find out whether it is **good**, which is a different question and the only one that
matters now.

**The first thirty seconds.** Open it and press record without reading anything. Speak a sentence.
Stop. Press play. That path is meant to be one tap, one tap, one tap, with no dialogue, no naming, no
quality prompt. If anything interrupted you, that is the most important bug in the app.

**Original versus Enhanced.** After a take, both appear with Enhanced selected. Switch between them
while listening.
- Can you hear a difference at all? If not, either the enhancement is too timid or the recording was
  already clean — and if it was already clean it should say *"Already clean"* rather than *"Enhanced"*.
- Is Enhanced actually **better**, or just louder and brighter? Louder reads as better for about five
  seconds. Listen to a whole sentence twice.
- Does Original sound untouched? It is meant to be the raw file, unmodified.

**Voice Space.** Studio → the intensity slider. Sweep it slowly from 0 to 100 while a recitation
plays.
- At 100%, is the speech still intelligible? There is a rule in the engine tying room level to
  ducking specifically so that it stays clear. This is the test of whether that rule works in the ear
  rather than on paper.
- Does any position sound like a cheap plugin — metallic, ringing, obviously artificial?
- Is there a position you would actually publish? If not, the presets need redesigning, not tuning.

**The rooms.** Try Recitation Studio and the acoustic spaces on the same take. Any two you cannot
tell apart should be merged — that is a standing rule for this project, and the automated distinctness
test only measures a proxy for it.

**Auto Studio.** Press it on a deliberately bad recording — too far from the phone, in a noisy room.
Then on a good one. On the good one it should do almost nothing, and say so. Restraint is the design;
confirm it is not just weakness.

**Export.** MP3, then WAV. Play both in another app — a music player, not SAUTIY.
- Is the MP3 the right length and not sped up or slowed? It is encoded by LAME through JNI.
- Does the export sound like what you heard in the app? Voice Space and enhancement are supposed to be
  in the file, not just the preview.
- Does Share hand a real file to WhatsApp or Drive?

**Save to the phone.** Export to Downloads, then find the file in the Files app. If it is not there
under the name you gave it, the whole export chain is worthless regardless of how it sounds.

**A long one.** Record ten minutes. Lock the screen halfway. Take a phone call if you can.
- Is the recording complete afterwards? Nothing may be lost — that is the app's first promise.
- Does the timer stay accurate?
- Does the phone get hot?

**The Founder's four questions.** They are in `docs/sautiy/FOUNDER-REVIEW.md` and all four are
currently answered "Not yet" or "Unknown", because they cannot be answered from inside a sandbox.
Would you record the whole Qur'an with this? Use it for a public lecture? Recommend it over what you
use now? Demonstrate it on stage?

---

## 3. What to send back

Sound complaints in plain language, not diagnoses. *"The reverb makes the s sounds hiss"* is more
useful than a guess at which filter. *"Enhanced sounds thin"* is enough to work from.

Screenshots of anything that looks wrong. Nobody has seen this interface on a real screen at real
density; spacing and type that read correctly in code can be wrong in the hand.

Compile errors verbatim.

---

## 4. Keep CI, but not as the loop

Once Actions minutes are restored, CI is worth keeping as a regression net: 428 engine tests, the
Compose shape checks, the APK build, lint, and eight screenshots per push. It catches what a person
forgets to re-check.

It is the wrong place to *develop*. Six minutes per compile error, an emulator with no microphone, and
no ears. The loop belongs on a desk with a phone plugged into it.
