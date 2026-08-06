#!/usr/bin/env python3
"""
One concise block naming which device test failed, emitted at the tail of the job.

Why this exists
---------------
Run 31116068441 failed with `> There were failing tests. See the report at: file:///home/runner/...`
and an `android.system.ErrnoException: read failed: EBADF` stack. That is enough to know something
broke and not enough to know *what* — the test's name was in an HTML report on a runner that no
longer exists, and in an artifact whose blob host is blocked from the development sandbox.

So the same rule the screenshot subsystem is held to now applies here: a first-time engineer should
be able to diagnose the failure from the last screen of the log without reading anything above it.
Gradle prints a `file://` URL to a machine that has been destroyed. This prints the test.

Reads the JUnit XML that AGP writes beside the HTML report, which is the same data the report is
rendered from — so this adds no new source of truth, it only moves the existing one somewhere
reachable.
"""

import glob
import os
import sys
import xml.etree.ElementTree as ET

BANNER = "=" * 26

# The path AGP writes connected-test XML to. Several are tried because the layout has moved between
# AGP versions and a summary that silently finds nothing is worse than no summary.
CANDIDATES = [
    "apps/sautiy/app/build/outputs/androidTest-results/connected",
    "apps/sautiy/app/build/outputs/androidTest-results",
    "apps/sautiy/app/build/reports/androidTests/connected",
]


def first_app_frame(text):
    """The first line of a stack trace that is our own code rather than the framework's."""
    for line in (text or "").split("\n"):
        stripped = line.strip()
        if "ai.sautiy" in stripped and stripped.startswith("at "):
            return stripped
    return ""


def headline(text):
    """The exception line, without the stack under it."""
    for line in (text or "").split("\n"):
        stripped = line.strip()
        if stripped:
            return stripped
    return "(no message)"


def collect(roots):
    files = []
    for root in roots:
        if os.path.isdir(root):
            files.extend(sorted(glob.glob(os.path.join(root, "**", "*.xml"), recursive=True)))
    return files


def main():
    roots = sys.argv[1:] or CANDIDATES
    files = collect(roots)

    total = 0
    skipped = 0
    failures = []
    unreadable = []

    for path in files:
        try:
            root = ET.parse(path).getroot()
        except Exception as error:  # a truncated XML is itself a finding, not a crash
            unreadable.append(f"{os.path.basename(path)}: {error}")
            continue
        suites = [root] if root.tag == "testsuite" else root.iter("testsuite")
        for suite in suites:
            for case in suite.iter("testcase"):
                total += 1
                if case.find("skipped") is not None:
                    skipped += 1
                for bad in list(case.iter("failure")) + list(case.iter("error")):
                    failures.append(
                        {
                            "name": f"{case.get('classname', '?')}.{case.get('name', '?')}",
                            "message": headline(bad.get("message") or bad.text),
                            "frame": first_app_frame(bad.text),
                        }
                    )

    print(BANNER)
    print("SAUTIY DEVICE TEST SUMMARY")
    print(BANNER)

    if not files:
        print("Result: NO RESULTS")
        print("Failure reason:")
        print("  No JUnit XML was written. The instrumented tests never ran — this says nothing")
        print("  about whether they would pass.")
        print("Searched:")
        for root in roots:
            print(f"  - {root}")
        print("Next action:")
        print("  Look for INSTALL_FAILED or 'Finished 0 tests' above; the run died before testing.")
        print(BANNER)
        return

    print(f"Result: {'FAILED' if failures else 'PASSED'}")
    print(f"Tests: {total}   Failures: {len(failures)}   Skipped: {skipped}")

    if failures:
        print("Failing tests:")
        for failure in failures:
            print(f"  ✗ {failure['name']}")
            print(f"      {failure['message']}")
            if failure["frame"]:
                print(f"      {failure['frame']}")
    if unreadable:
        print("Unreadable result files:")
        for entry in unreadable:
            print(f"  ! {entry}")

    print("Failure reason:")
    if failures:
        print(f"  {failures[0]['message']}")
    else:
        print("  None.")
    print("Next action:")
    if failures:
        print("  The test name and the first line of our own stack are above. Nothing needs to be")
        print("  downloaded and nothing above this block needs to be read.")
    else:
        print("  None. The device tests passed.")
    print(BANNER)


if __name__ == "__main__":
    main()
