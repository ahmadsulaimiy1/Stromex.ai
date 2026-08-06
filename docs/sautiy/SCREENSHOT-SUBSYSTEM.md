# The screenshot subsystem

**Version 2.** Version 1 captured eight screens and reported failures in the middle of the log.
Version 2 captures the same eight and reports them where they can be read.

This is release tooling, not part of SAUTIY. It is documented to the same standard as the app
because it is the only reason anybody can see the app at all, and because a verification tool that
is wrong is worse than no verification tool: it produces confidence rather than evidence.

---

## What it is for

Nobody working on SAUTIY can run it. The development sandbox has no emulator — no KVM, and Google's
Maven is blocked, so the Android module does not even compile there. CI is the only place the
application has ever executed. These screenshots are therefore not a nicety; they are the entire
visual review channel, and Blocker #4 of the release order — *manual review of every captured
screen* — cannot begin until all eight exist.

Every image is `adb exec-out screencap` of the running application. Nothing is drawn, mocked or
reconstructed. A picture of what a screen is *supposed* to look like would be worse than no picture,
because it would be believed.

## The two files

| File | Responsibility |
| --- | --- |
| `.github/scripts/sautiy-screenshots.sh` | Navigates the app, captures the eight screens, checks the manifest, emits the Release Summary. |
| `.github/scripts/sautiy-smoke.sh` | Installs, launches, verifies the process is alive, calls the above, runs the device tests, then gates. |

## The eight screens

One table in the script, `file|name|selector`, read by both the manifest and the summary so the two
cannot disagree about what a complete set is.

| File | Name in the summary | Reached by |
| --- | --- | --- |
| `01-workspace-empty` | Home | nothing — the app opens here |
| `02-recording-live-studio` | Recording | `Record` |
| `03-after-recording` | Playback | `Stop` |
| `04-studio-panel` | Studio | `Studio` |
| `05-studio-scrolled` | Studio, scrolled | `Studio`, then a swipe |
| `06-studio-layer-two` | Studio, second layer | `Studio`, then two swipes |
| `07-export-panel` | Export | `Export` |
| `08-analysis-gauges` | Analysis | `Analysis` |

Rows 5 and 6 name `Studio` deliberately. They are gated behind that one tap, so when it fails it
costs three screens rather than one, and a summary that blamed a swipe would send the fix to the
wrong place.

## Rules this subsystem is held to

1. **Navigate by name, never by coordinate.** A hardcoded `x,y` works on one emulator resolution and
   silently taps the wrong thing on every other, and a screenshot of the wrong screen is
   indistinguishable from a screenshot of the right one. Selectors come from the live view hierarchy
   via `uiautomator dump`.
2. **Never change production code to satisfy this script.** If a selector stops matching, the
   selector is what is wrong. Renaming a control in the app so a screenshot passes is falsifying the
   evidence, and the control's name belongs to the user, not to CI.
3. **A missing screen fails the release.** If it cannot be captured it cannot be reviewed, and an
   unreviewed screen is an unreleased one.
4. **The gate comes after the device tests, never before.** For two runs the missing-screenshot check
   aborted the script before `connectedDebugAndroidTest` started, so a missing picture of the
   Analysis panel cost the evidence about whether recording, playback and export still worked. A
   missing picture is a smaller loss than a missing test result; the ordering encodes that.
5. **Every release tool ends with a concise summary.** Result, failure reason, missing items, next
   action. See below.

## The Release Summary

> **Diagnostics should travel to the engineer. The engineer should not have to travel through the
> log.**

Version 1 produced everything needed to fix itself, roughly 1,300 lines from the end of a
~1,500-line job log, behind the LAME compiler warnings. It was written twice and read zero times.
The information was never the problem. Its location was.

The last thing either script prints is one block of a fixed shape:

```
==========================
SAUTIY SCREENSHOT SUMMARY
==========================
Result: FAILED
Captured:
  ✓ Home
  ✓ Recording
  ✓ Playback
  ✓ Studio
Missing:
  ✗ Export
  ✗ Analysis
Expected selectors:
  - Export   (Export)
  - Analysis   (Analysis)
Visible selectors at failure:
  - Enhanced
  - Original
  - Record
  - Studio
Failure reason:
  Selector not found: Analysis Export
Next action:
  Pick a replacement for each selector above from the visible list, and change only the
  tap_by_description call in .github/scripts/sautiy-screenshots.sh.
==========================
```

Properties that matter, each of which is a defect in version 1:

* **It is emitted from an `EXIT` trap.** So it survives the manifest's `exit 1`, an `adb` failure
  under `set -e`, and a killed step alike. There is no path out of the script that skips it.
* **It is re-printed by the smoke script after the device tests**, because two minutes of Gradle
  output otherwise pushes the screenshot script's own copy out of reach of a tail.
* **It is printed on success too.** `Result: PASSED` at the tail is the evidence that the run got
  that far, and a tool that only speaks when it fails leaves silence ambiguous.
* **The failure reason is derived, not guessed.** Four distinguishable causes: a selector that was
  not in the hierarchy, a control found but not tappable, a control tapped but no image written, and
  an exit before any lookup was attempted at all. The last one exists because the branch above it
  would otherwise blame the interface for a dead emulator.
* **It depends on nothing else.** No earlier log section, no artifact download, no scrolling.

If the smoke script finds no summary was written, it prints one saying so — absence means the
screenshot script never ran, which is itself the finding.

**Success criterion.** The next screenshot failure is diagnosable from the last screen of the CI log
alone. If identifying the problem needs a search through 1,500 lines, this subsystem is not finished.

## Known weakness, deliberately not yet fixed

Selectors are plain strings matched case-insensitively against content descriptions and text nodes.
That is fragile: a wording change in the app silently breaks navigation, and `grep -iF "Record"`
matches "Recording" as happily as "Record". The robust answer is stable test tags that are part of
the interface's contract rather than its copy.

It is recorded here rather than fixed because Release Candidate Lockdown permits work on the current
blocker only, and adding test tags is production code. It belongs in the Version 1.1 backlog.

## How to run it locally

There is no emulator here, so the only thing testable locally is the reporting. Put a stub `adb`
early on `PATH` that answers `shell uiautomator dump`, `shell cat /sdcard/ui.xml` with a fake
hierarchy, `shell input …`, and `exec-out screencap -p` with any bytes. Version 2 was exercised in
three shapes before being pushed: a set missing Export and Analysis, a complete set, and no `adb` at
all. Each is diagnosable from the last thirty lines.

This proves the reporting. It proves nothing about the app, and must never be described as though it
did.
