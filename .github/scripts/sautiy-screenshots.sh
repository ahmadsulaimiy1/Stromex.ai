#!/usr/bin/env bash
#
# Real screenshots of SAUTIY, taken on the emulator.
#
# This exists because the development sandbox has no emulator — no KVM, and Google's Maven is
# blocked — so nobody working on this can see the app they are building. CI is the only place it
# runs, so CI is where the pictures have to come from.
#
# Every image here is `adb exec-out screencap` of the actual running application. Nothing is drawn,
# mocked or reconstructed: a picture of what the app is supposed to look like would be worse than no
# picture at all, because it would be believed.
#
# Navigation is by content description rather than by coordinate. Tapping a hardcoded x,y works on
# one emulator resolution and silently taps the wrong thing on every other, and a screenshot of the
# wrong screen is indistinguishable from a screenshot of the right one.
#
# --- Why this script ends the way it does -------------------------------------------------------
#
# Diagnostics should travel to the engineer. The engineer should not have to travel through the log.
#
# The first two versions of this script produced everything needed to fix themselves and produced it
# in the wrong place: ~1,300 lines from the end of a ~1,500-line job log, behind the native-build
# warnings, and the log retrieval available to whoever is reading it returns a tail. Twice the
# diagnostic was written and twice it was never read. Evidence that cannot be reached has not been
# produced.
#
# So the last thing this script does — on success, on failure, and on an unexpected exit, because the
# summary is emitted from an EXIT trap — is print one fixed-shape block containing the result, what
# was captured, what is missing, which selector each missing screen needed, which selectors were
# actually on screen when the lookup failed, the reason, and the next action. Nothing else in the
# block, and nothing after it.

set -euo pipefail

PACKAGE="ai.sautiy.debug"
SHOTS="${1:-screenshots}"
mkdir -p "$SHOTS"

# --- The eight screens, and the one control each needs -------------------------------------------
#
# One table, read by both the manifest and the summary, so the two can never disagree about what a
# complete set is. `file|name in the summary|the selector that screen is reached by`.
#
# 05 and 06 name "Studio" because they are gated behind that same tap: when the Studio lookup fails
# it costs three screens, not one, and a summary that blamed a swipe would send the fix to the wrong
# place.
SCREENS="01-workspace-empty|Home|-
02-recording-live-studio|Recording|Record
03-after-recording|Playback|Stop
04-studio-panel|Studio|Studio
05-studio-scrolled|Studio, scrolled|Studio
06-studio-layer-two|Studio, second layer|Studio
07-export-panel|Export|Export
08-analysis-gauges|Analysis|Analysis"

# Every lookup this run attempted, `needle|found` or `needle|missing`.
LOOKUPS="$SHOTS/lookups.txt"
# Every content description and text node visible at the moment a lookup failed.
VISIBLE="$SHOTS/visible.txt"
# Images that were written but are suspiciously small.
SUSPECT="$SHOTS/suspect.txt"
SUMMARY="$SHOTS/summary.txt"
: > "$LOOKUPS"
: > "$VISIBLE"
: > "$SUSPECT"
rm -f "$SUMMARY" "$SHOTS/missing.txt" "$SHOTS/diagnostic.txt"

shot() {
  local name="$1"
  # A settle before the shutter: Compose animations are up to 320 ms and a screenshot taken
  # mid-transition shows a half-faded panel, which reads as a rendering bug.
  sleep 2
  adb exec-out screencap -p > "$SHOTS/$name.png"
  local bytes
  bytes=$(stat -c%s "$SHOTS/$name.png" 2>/dev/null || echo 0)
  if [ "$bytes" -lt 5000 ]; then
    # Still counted as captured — a dark screen genuinely compresses small, and turning a warning
    # into a failure here would fail the release on a guess. Recorded so the summary can say so.
    echo "::warning::$name.png is only $bytes bytes — the screen may not have rendered"
    echo "$name.png is only $bytes bytes" >> "$SUSPECT"
  else
    echo "captured $name.png ($bytes bytes)"
  fi
}

# Taps the centre of the first node whose content description or text matches, read from the live
# view hierarchy. Returns non-zero when there is no such node, so a renamed control shows up as a
# missing screenshot rather than as a tap into empty space.
tap_by_description() {
  local needle="$1"
  adb shell uiautomator dump /sdcard/ui.xml > /dev/null 2>&1 || return 1
  local bounds
  # The `|| true` is not decoration and its absence cost a whole run's evidence.
  #
  # Under `set -euo pipefail`, a command substitution whose pipeline ends in a `grep` that matches
  # nothing exits non-zero, and `set -e` then kills the entire script — so the *first* control this
  # could not find silently destroyed every screenshot after it. The intent was always to fall
  # through to the emptiness check below, which is unreachable if the shell has already exited.
  bounds=$( { adb shell cat /sdcard/ui.xml | tr '>' '\n' \
    | grep -iF "$needle" | head -1 \
    | grep -oE 'bounds="\[[0-9]+,[0-9]+\]\[[0-9]+,[0-9]+\]"' | head -1 \
    | grep -oE '[0-9]+' | tr '\n' ' '; } || true )
  if [ -z "$bounds" ]; then
    echo "::warning::no control matching '$needle' in the view hierarchy"
    printf '%s|missing\n' "$needle" >> "$LOOKUPS"
    # What *is* on screen, collected for the summary rather than only printed here. Inferring these
    # control names from outside the emulator has not worked, so the run says what it can see.
    { adb shell cat /sdcard/ui.xml | grep -oE '(content-desc|text)="[^"]+"' \
      | sed -E 's/^(content-desc|text)="//; s/"$//' \
      | grep -vE '^\s*$' | sort -u >> "$VISIBLE"; } || true
    return 1
  fi
  # shellcheck disable=SC2086
  set -- $bounds
  local x=$(( ($1 + $3) / 2 ))
  local y=$(( ($2 + $4) / 2 ))
  echo "tapping '$needle' at $x,$y"
  if ! adb shell input tap "$x" "$y"; then
    printf '%s|tap-failed\n' "$needle" >> "$LOOKUPS"
    return 1
  fi
  printf '%s|found\n' "$needle" >> "$LOOKUPS"
  return 0
}

# --- The Release Summary --------------------------------------------------------------------------
#
# Emitted from an EXIT trap, so it survives the manifest's `exit 1`, an `adb` failure under `set -e`,
# and a cancelled step alike. One shape, always the last thing in the log: Result / Captured /
# Missing / Expected selectors / Visible selectors at failure / Failure reason / Next action.

emit_summary() {
  local code=$?
  if [ -n "${SUMMARY_EMITTED:-}" ]; then return 0; fi
  SUMMARY_EMITTED=1

  local captured="" missing="" expected="" missing_names=""
  local file friendly selector
  while IFS='|' read -r file friendly selector; do
    [ -z "$file" ] && continue
    if [ -s "$SHOTS/$file.png" ]; then
      captured="${captured}  ✓ ${friendly}"$'\n'
    else
      missing="${missing}  ✗ ${friendly}"$'\n'
      missing_names="${missing_names} ${file}"
      if [ "$selector" = "-" ]; then
        expected="${expected}  - (none — ${friendly} needs no tap; it is where the app opens)"$'\n'
      else
        expected="${expected}  - ${selector}   (${friendly})"$'\n'
      fi
    fi
  done <<EOF
$SCREENS
EOF

  local not_found
  not_found=$( { grep '|missing$' "$LOOKUPS" 2>/dev/null | cut -d'|' -f1 | sort -u \
    | tr '\n' ' ' | sed 's/ *$//'; } || true )
  local tap_failed
  tap_failed=$( { grep '|tap-failed$' "$LOOKUPS" 2>/dev/null | cut -d'|' -f1 | sort -u \
    | tr '\n' ' ' | sed 's/ *$//'; } || true )

  local result reason action
  if [ -z "$missing_names" ] && [ "$code" -eq 0 ]; then
    result="PASSED"
    reason="None."
    action="Review the eight images in the screenshots artifact. Nothing to fix in the tooling."
  else
    result="FAILED"
    if [ -n "$not_found" ]; then
      reason="Selector not found: ${not_found}"
      action="Pick a replacement for each selector above from the visible list, and change only the"$'\n'
      action="${action}tap_by_description call in .github/scripts/sautiy-screenshots.sh. Release tooling"$'\n'
      action="${action}only — do not rename the control in the app to suit this script."
    elif [ -n "$tap_failed" ]; then
      reason="Control found but the tap did not reach it: ${tap_failed}"
      action="Check adb connectivity in the step above; the view hierarchy was readable, so the"$'\n'
      action="${action}emulator was alive and the failure is in the input injection, not the selector."
    elif [ ! -s "$LOOKUPS" ] && [ -n "$missing_names" ]; then
      # Nothing was ever looked for, so nothing about the app can be concluded. Said explicitly,
      # because the next branch down would otherwise blame the app for a dead emulator.
      reason="The script exited with code ${code} before any control lookup happened — adb was"$'\n'
      reason="${reason}unavailable, or the emulator was not reachable. This says nothing about the app."
      action="Read the lines above '=== 1. the workspace as it opens ==='; the emulator, not the"$'\n'
      action="${action}interface, is what failed."
    elif [ -n "$missing_names" ]; then
      reason="Control found and tapped, but no image was written — the screen did not render, or"$'\n'
      reason="${reason}screencap failed."
      action="Re-read the 'captured …' lines above for the last screen that did write, and check"$'\n'
      action="${action}whether the panel it opened is the one the next shot expected."
    else
      reason="The script exited with code ${code} before the manifest was reached — no screen is"$'\n'
      reason="${reason}missing, so the failure is in this script rather than in the app."
      action="Read the last command echoed above this block."
    fi
  fi

  local seen
  seen=$( { sort -u "$VISIBLE" 2>/dev/null | head -30 | sed 's/^/  - /'; } || true )
  if [ -z "$seen" ]; then
    seen="  (no lookup failed, so nothing was recorded)"
  fi

  {
    echo "=========================="
    echo "SAUTIY SCREENSHOT SUMMARY"
    echo "=========================="
    echo "Result: $result"
    echo "Captured:"
    if [ -n "$captured" ]; then printf '%s' "$captured"; else echo "  (none)"; fi
    echo "Missing:"
    if [ -n "$missing" ]; then printf '%s' "$missing"; else echo "  (none)"; fi
    if [ -n "$missing" ]; then
      echo "Expected selectors:"
      printf '%s' "$expected"
      echo "Visible selectors at failure:"
      printf '%s\n' "$seen"
    fi
    if [ -s "$SUSPECT" ]; then
      echo "Captured but suspiciously small:"
      sed 's/^/  ! /' "$SUSPECT"
    fi
    echo "Failure reason:"
    printf '%s\n' "$reason" | sed 's/^/  /'
    echo "Next action:"
    printf '%s\n' "$action" | sed 's/^/  /'
    echo "=========================="
  } > "$SUMMARY"

  cat "$SUMMARY"
}

trap emit_summary EXIT

echo "=== 1. the workspace as it opens ==="
shot "01-workspace-empty"

echo "=== 2. recording — Live Studio, with everything else gone ==="
if tap_by_description "Record"; then
  sleep 4
  shot "02-recording-live-studio"
  # Stop, so the rest of the screenshots have real audio behind them.
  tap_by_description "Stop" || tap_by_description "Record" || true
  sleep 3
fi
shot "03-after-recording"

echo "=== 4. the Studio panel — outcomes, Voice Space, Auto Studio ==="
if tap_by_description "Studio"; then
  shot "04-studio-panel"
  # Scrolled, because the two layers and the Recitation Studio are below the fold by design and
  # a screenshot of only the top would misrepresent the panel.
  adb shell input swipe 540 1500 540 600 400 || true
  shot "05-studio-scrolled"
  adb shell input swipe 540 1500 540 600 400 || true
  shot "06-studio-layer-two"
fi

echo "=== 7. the Export panel ==="
adb shell input keyevent KEYCODE_BACK || true
sleep 1
if tap_by_description "Export"; then
  shot "07-export-panel"
fi

echo "=== 8. the Analysis panel — the gauges ==="
adb shell input keyevent KEYCODE_BACK || true
sleep 1
if tap_by_description "Analysis"; then
  shot "08-analysis-gauges"
fi

# --- The manifest -------------------------------------------------------------------------------
#
# "If screenshots fail, the release is incomplete." So a missing screen is an error rather than a
# line in a log nobody reads. The per-file byte table stays here, verbose, for anyone reading the
# whole log; the summary the EXIT trap prints is what a tail can reach.

echo "=== manifest ==="
MISSING=""
while IFS='|' read -r file friendly selector; do
  [ -z "$file" ] && continue
  if [ -s "$SHOTS/$file.png" ]; then
    printf "  ok      %-28s %s bytes\n" "$file" "$(stat -c%s "$SHOTS/$file.png")"
  else
    printf "  MISSING %-28s (needs selector: %s)\n" "$file" "$selector"
    MISSING="$MISSING $file"
  fi
done <<EOF
$SCREENS
EOF

if [ -n "$MISSING" ]; then
  echo "::error::screenshots missing:$MISSING — a screen that cannot be captured is a screen"
  echo "::error::nobody can review, and the control names this script taps by may have changed."
  exit 1
fi

echo "all 8 screens captured."
