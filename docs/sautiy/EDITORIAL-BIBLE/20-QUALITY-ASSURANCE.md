# Chapter 20 — Quality Assurance

> A standard nobody checks is a preference.

---

## 20.1 The Design Review Gate

No screen enters the product until every answer is *yes* (chapter 1.9):

1. Can a child understand what they are looking at?
2. Can a professional trust the numbers it shows?
3. Can the primary task be completed in one or two taps?
4. Does it look premium?
5. Does it feel effortless?
6. Does it reduce cognitive load compared to the alternative?
7. Does it answer *What am I looking at? What is the primary action? What happens next?*

Any "no" sends the screen back to design. There is no override.

## 20.2 What The Build Enforces

These are not review items. They fail the build.

| Rule | Test |
|---|---|
| No placeholder tokens anywhere in the source | `NoPlaceholderTest` |
| Contrast floors, every role, every surface, both themes | `ContrastTest` |
| Spacing on the 4 dp grid | `DesignSystemTest` |
| Tabular figures on every in-place number | `DesignSystemTest` |
| Motion within tiers, no overshoot | `DesignSystemTest` |
| One destination plus settings and about | `WorkspaceLawTest` |
| The transport dock never changes | `WorkspaceLawTest` |
| No destructive control while recording | `WorkspaceLawTest` |
| Context bar within budget, in every state | `WorkspaceLawTest` |
| One primary action per state | `WorkspaceLawTest` |
| Labels within three words, never capitals | `WorkspaceLawTest` |
| No panel covers the dock | `WorkspaceLawTest` |
| Errors cannot exist without a remedy | `WorkspaceLawTest` |
| Exactly four permitted interruptions | `WorkspaceLawTest` |
| Flush cadence inside the sample-loss ceiling | `DesignSystemTest`, `RecordingMachineTest` |

## 20.3 The Audio Checklist

Run against real recordings, not test tones, before release:

- [ ] A 90-minute capture, screen off, in a bag, verified complete afterwards
- [ ] A forced process kill mid-recording, and the take recovered on next launch
- [ ] A phone call arriving mid-recording — pauses, does not stop, does not record the call
- [ ] Bluetooth headset connected and disconnected mid-recording
- [ ] Storage filled during a recording — stops cleanly, everything captured is saved
- [ ] Every preset applied to speech, listened to end to end
- [ ] Every export format opened in a third-party player
- [ ] FLAC output opened by a third-party decoder
- [ ] Loudness of an exported file confirmed against an independent meter

## 20.4 The Accessibility Checklist

- [ ] Whole product operated with a screen reader, end to end, without sight
- [ ] Font scale at 200%, every screen, no truncation or overlap
- [ ] Every state distinguishable with colour vision simulated for deuteranopia
- [ ] Reduce-motion on — no capability lost
- [ ] Right-to-left layout, with the waveform's time direction unchanged
- [ ] Every interactive element measured at 48 dp or more
- [ ] Every gesture performed by its non-gesture equivalent

## 20.5 The Performance Checklist

Measured on a **mid-range** device, never a flagship:

- [ ] Cold start to armed workspace ≤ 700 ms
- [ ] Tap to first sample ≤ 300 ms
- [ ] Tap to audible ≤ 100 ms
- [ ] 60 fps sustained during live recording, zero dropped frames
- [ ] Panel open to interactive ≤ 220 ms
- [ ] A two-hour project opens as fast as a two-minute one
- [ ] Battery drain over a one-hour recording, screen off, measured

## 20.6 Device Coverage

| Class | Why |
|---|---|
| Mid-range Android, 4 GB RAM, minSdk | The device most users have |
| Current flagship | Where regressions hide behind headroom |
| A tablet | Layout at width |
| A device with a notch and gesture navigation | Insets against the transport dock |
| A device with no AAC encoder, if one can be found | Chapter 18.6's degraded path |

## 20.7 Release Criteria

The build is releasable only when **all** hold:

1. Every test passes. Not most.
2. Every checklist above is completed and signed.
3. No entry in the implementation ledger claims more than was verified.
4. Every chapter of this Bible has an implementation, or an explicit, written statement of what
   is not built and why.
5. The design review gate has been applied to every screen since the last release.
6. The APK contains no analytics dependency and no internet permission.

## 20.8 Honesty In Reporting

The implementation ledger records what is **built**, what is **tested**, what is **verified by
an executed test run**, and what is **source-complete but not executable in the current build
environment**. It does not round up. A report that overstates is worse than no report, because
the next person builds on it.

---

### Implementation

`apps/sautiy/sautiy-core/src/test/` — the enforcing tests.
`docs/sautiy/IMPLEMENTATION-LEDGER.md` — the honest record.
