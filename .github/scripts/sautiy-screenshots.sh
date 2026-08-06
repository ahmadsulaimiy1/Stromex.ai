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

set -euo pipefail

PACKAGE="ai.sautiy.debug"
SHOTS="${1:-screenshots}"
mkdir -p "$SHOTS"

shot() {
  local name="$1"
  # A settle before the shutter: Compose animations are up to 320 ms and a screenshot taken
  # mid-transition shows a half-faded panel, which reads as a rendering bug.
  sleep 2
  adb exec-out screencap -p > "$SHOTS/$name.png"
  local bytes
  bytes=$(stat -c%s "$SHOTS/$name.png" 2>/dev/null || echo 0)
  if [ "$bytes" -lt 5000 ]; then
    echo "::warning::$name.png is only $bytes bytes — the screen may not have rendered"
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
  bounds=$(adb shell cat /sdcard/ui.xml | tr '>' '\n' \
    | grep -iF "$needle" | head -1 \
    | grep -oE 'bounds="\[[0-9]+,[0-9]+\]\[[0-9]+,[0-9]+\]"' | head -1 \
    | grep -oE '[0-9]+' | tr '\n' ' ')
  if [ -z "$bounds" ]; then
    echo "::warning::no control matching '$needle' in the view hierarchy"
    return 1
  fi
  # shellcheck disable=SC2086
  set -- $bounds
  local x=$(( ($1 + $3) / 2 ))
  local y=$(( ($2 + $4) / 2 ))
  echo "tapping '$needle' at $x,$y"
  adb shell input tap "$x" "$y"
  return 0
}

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
  adb shell input swipe 540 1500 540 600 400
  shot "05-studio-scrolled"
  adb shell input swipe 540 1500 540 600 400
  shot "06-studio-layer-two"
fi

echo "=== 7. the Export panel ==="
adb shell input keyevent KEYCODE_BACK
sleep 1
if tap_by_description "Export"; then
  shot "07-export-panel"
fi

echo "=== 8. the Analysis panel — the gauges ==="
adb shell input keyevent KEYCODE_BACK
sleep 1
if tap_by_description "Analysis"; then
  shot "08-analysis-gauges"
fi

echo "=== captured ==="
ls -la "$SHOTS"
