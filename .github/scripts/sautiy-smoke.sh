#!/usr/bin/env bash
#
# SAUTIY launch smoke test.
#
# Runs inside the emulator-runner. It must be ONE script file rather than a list of lines in
# the workflow: the action executes each line of an inline `script:` in its own `sh -c`, so a
# variable set on one line is gone by the next — which is exactly how the first attempt failed.
set -euo pipefail

PACKAGE="ai.sautiy.debug"
ACTIVITY="ai.sautiy.SautiyActivity"

APK=$(find apk -name '*.apk' | head -1)
if [ -z "$APK" ]; then
  echo "::error::No APK was downloaded"
  find apk -type f || true
  exit 1
fi
echo "Installing $APK"

adb install -r "$APK"

# Granted up front: a permission dialog is not a crash, and this test is about whether the
# workspace survives being started at all.
adb shell pm grant "$PACKAGE" android.permission.RECORD_AUDIO || true
adb shell pm grant "$PACKAGE" android.permission.POST_NOTIFICATIONS || true

adb logcat -c
adb shell am start -W -n "$PACKAGE/$ACTIVITY"

# Long enough for Compose to lay out the first frame, the ViewModel to run its init, and any
# background work to reach a steady state.
sleep 20

echo "=== crash buffer ==="
adb logcat -d -b crash > crash.txt 2>/dev/null || true
cat crash.txt || true

echo "=== relevant log ==="
adb logcat -d | grep -iE "sautiy|AndroidRuntime|FATAL|Compose|Resources\\\$NotFound" | tail -100 || true

if [ -s crash.txt ]; then
  echo "::error::SAUTIY crashed on launch"
  exit 1
fi

if ! adb shell pidof "$PACKAGE" > /dev/null 2>&1; then
  echo "::error::SAUTIY is not running 20 seconds after launch"
  echo "=== full tail ==="
  adb logcat -d | tail -200
  exit 1
fi

# A process that is alive but showing nothing is still a failure. Confirm our activity is the
# one actually resumed, rather than the launcher having come back after a silent death.
echo "=== resumed activity ==="
adb shell dumpsys activity activities | grep -E "ResumedActivity|topResumedActivity" || true

if ! adb shell dumpsys activity activities | grep -q "$PACKAGE"; then
  echo "::error::SAUTIY is running but its activity is not on screen"
  exit 1
fi

echo "SAUTIY launched, is alive, and its activity is resumed."

# Launching is not working. AudioRecord, AudioTrack and MediaCodec have no meaningful stand-in
# on the JVM, so the only place a claim about them can be earned is on a running Android — which
# is what this is. The emulator has no microphone in front of it, so what is captured is
# near-silence; that still proves the device opens, that frames arrive, that the file on disk is
# a real WAV of the right length, that playback runs and that an export writes a file.
# The artifact APK was signed with the *build* job's debug keystore; this runner generates its
# own, and Gradle is about to build and install its own copy of the same package. Android
# refuses that as INSTALL_FAILED_UPDATE_INCOMPATIBLE, and the run reports "Finished 0 tests" —
# a green-looking failure to run anything at all. Remove the launched copy first.
# Screenshots first, while the launched copy is still installed and on screen. Nobody working on
# this app can see it — there is no emulator in the development sandbox — so these are the only
# pictures of it that exist, and they are pictures of the real thing rather than of an intention.
echo "=== screenshots ==="
# Captured here, while the launched copy is still on screen — but the *gate* on them is deferred to
# the end of this script.
#
# For two runs the missing-screenshot check aborted before the device tests ever started, so a
# missing picture of the Analysis panel cost the evidence about whether recording, playback and
# export still work. Screenshots remain part of the release and still fail the build; they no longer
# mask the verification that matters more.
SCREENSHOTS_OK=0
bash "$GITHUB_WORKSPACE/.github/scripts/sautiy-screenshots.sh" "$GITHUB_WORKSPACE/screenshots" \
  || SCREENSHOTS_OK=1

echo "=== device audio tests ==="
adb uninstall "$PACKAGE" || true

cd apps/sautiy
# Not allowed to abort the script. Under `set -e` a Gradle failure killed this run before either
# summary was printed, so run 31116068441 reported "There were failing tests" and a `file://` URL to
# a machine that no longer exists — and named no test. The gate is deferred to the end, exactly as
# the screenshot gate is, for exactly the same reason.
TESTS_OK=0
./gradlew --no-daemon :app:connectedDebugAndroidTest || TESTS_OK=1
cd "$GITHUB_WORKSPACE"

# The gate, after the evidence. A red build either way, but never a red build with nothing to read.
#
# The Release Summary is re-printed *here*, last, because the screenshot script's own copy is now
# behind two minutes of Gradle output and the log retrieval available to whoever is reading this
# returns a tail. It is printed whether the set is complete or not: every release tool ends with a
# summary, and "PASSED" at the tail is the evidence that the run got that far.
if [ ! -s "$GITHUB_WORKSPACE/screenshots/summary.txt" ]; then
  # The summary is emitted from an EXIT trap, so its absence means the script never ran at all.
  echo "=========================="
  echo "SAUTIY SCREENSHOT SUMMARY"
  echo "=========================="
  echo "Result: FAILED"
  echo "Failure reason:"
  echo "  No summary was written. The screenshot script did not start, or the runner killed it"
  echo "  before its exit trap could run."
  echo "Next action:"
  echo "  Search this log for '=== screenshots ===' — the failure is above that line, not below it."
  echo "=========================="
else
  cat "$GITHUB_WORKSPACE/screenshots/summary.txt"
fi

# The device-test summary is printed *after* the screenshot one, so the higher blocker sits closest
# to the exit. Blocker order is 1. device tests, 2. screenshots, and the log tail should read in the
# same order of importance rather than the order the steps happened to run in.
python3 "$GITHUB_WORKSPACE/.github/scripts/sautiy-test-summary.py" \
  "$GITHUB_WORKSPACE/apps/sautiy/app/build/outputs/androidTest-results/connected" \
  "$GITHUB_WORKSPACE/apps/sautiy/app/build/outputs/androidTest-results" || true

if [ "$TESTS_OK" -ne 0 ]; then
  echo "::error::device tests failed. The failing test is named in the summary above."
  exit 1
fi

if [ "$SCREENSHOTS_OK" -ne 0 ]; then
  echo "::error::device tests passed; the screenshot set is incomplete. See the summary above."
  exit 1
fi
