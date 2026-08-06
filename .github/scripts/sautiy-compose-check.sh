#!/usr/bin/env bash
#
# The cheap checks for the mistakes I actually keep making in the Compose layer.
#
# The Android module cannot be compiled in the development sandbox — Google's Maven is blocked —
# so the first thing that ever type-checks `:app` is CI, several minutes after a push. That has now
# cost three cycles, each on a mistake a grep would have caught in a second. This is that grep.
#
# It is not a type checker and does not pretend to be. It looks for two specific shapes:
#
#   1. `return@Column` / `return@Row` / `return@Box` — a non-local return out of a composable
#      content lambda. Those lambdas are not inline, so this does not compile. The fix is an
#      if/else, or extracting the tail into its own composable.
#
#   2. Dereferencing a nullable property of a `sautiy-core` type after an `x.y != null` check.
#      Kotlin cannot smart-cast a public property from another module, because nothing stops that
#      module from making it a computed property later. The fix is to read it into a local val.
#
# Both are real compiler errors, both are invisible to the eye in a 1500-line file, and both are
# mine rather than the platform's.

set -euo pipefail

ROOT="${1:-apps/sautiy/app/src/main/java}"
STATUS=0

if [ ! -d "$ROOT" ]; then
  echo "no Compose sources at $ROOT" >&2
  exit 1
fi

# --- 1. Non-local return out of a composable content lambda ---------------------------------------

while IFS= read -r hit; do
  echo "error: non-local return from a composable content lambda — these lambdas are not inline."
  echo "       $hit"
  echo "       Use an if/else, or extract the remainder into its own @Composable."
  STATUS=1
done < <(grep -rnE 'return@(Column|Row|Box|LazyColumn|LazyRow|Scaffold|Surface|Card)\b' "$ROOT" || true)

# --- 2. Cross-module smart cast ------------------------------------------------------------------
#
# Finds `<receiver>.<property> != null` where the receiver is not `this`/a local-looking name, then
# checks whether the same `<receiver>.<property>` is used as a value in the following 20 lines.
# Deliberately reported as a warning to look at rather than a hard failure: the pattern is legal
# whenever the property belongs to a type in this module, and this script cannot tell which.

python3 - "$ROOT" <<'PYTHON' || STATUS=1
import os, re, sys

root = sys.argv[1]
pattern = re.compile(r'\b(\w+)\.(\w+)\s*!=\s*null\b')
findings = []

for directory, _, files in os.walk(root):
    for name in files:
        if not name.endswith('.kt'):
            continue
        path = os.path.join(directory, name)
        lines = open(path, encoding='utf-8').read().split('\n')
        for index, line in enumerate(lines):
            for receiver, prop in pattern.findall(line):
                if receiver in ('it', 'this'):
                    continue
                # Used as a value — passed as an argument or assigned — rather than re-checked.
                use = re.compile(r'[=(,]\s*' + re.escape(f'{receiver}.{prop}') + r'\b')
                for offset, following in enumerate(lines[index + 1:index + 21], start=1):
                    if use.search(following) and '!= null' not in following:
                        findings.append(
                            f'{path}:{index + 1} checks {receiver}.{prop} != null, '
                            f'then line {index + 1 + offset} uses it as a value'
                        )
                        break

if findings:
    print('warning: possible cross-module smart cast — a public property from another module')
    print('         cannot be smart-cast. Read it into a local val before the check.')
    for finding in findings:
        print(f'         {finding}')
    # A warning, not a failure: the pattern is fine for same-module types.
sys.exit(0)
PYTHON

# --- 3. Invented sizes ----------------------------------------------------------------------------
#
# Phase Ω, directive 6: consistency is quality. The app once drew icons at 20, 22, 24 and 26 dp in
# four files, dots at 8 and 10, strokes at 1.5 and 2. None of it was a decision. A user cannot name
# that, but they can see it — it is exactly what makes an interface feel assembled rather than
# designed.
#
# So every size lives in `Sizes` in the tested module and is exposed as `SautiySize`. This finds any
# raw dp literal that has crept back into a composable. The theme file itself is exempt: that is
# where the tokens are turned into dp, and it is the one place a number belongs.

RAW=$(grep -rnE '\b[0-9]+(\.[0-9]+)?\.dp\b' "$ROOT" --include='*.kt' \
      | grep -v '/ui/theme/Theme.kt' || true)

if [ -n "$RAW" ]; then
  echo "error: raw dp literals in the Compose layer. Every size belongs in Sizes/SautiySize —"
  echo "       four icon sizes in four files is what makes an interface look assembled."
  echo "$RAW" | sed 's/^/       /'
  STATUS=1
fi

if [ "$STATUS" -eq 0 ]; then
  echo "Compose shape checks passed."
fi
exit "$STATUS"
