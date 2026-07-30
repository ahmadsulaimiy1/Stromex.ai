#!/usr/bin/env bash
# Builds StromeX for a specific environment: rebuilds the web bundle with
# that environment's backend URL baked in (Next.js's NEXT_PUBLIC_API_URL is
# a build-time constant, not something a shipped app can switch at runtime —
# the same reason RN/Capacitor apps use separate build "flavors" per
# environment rather than in-app environment switching), copies it into
# apps/android/assets/, then runs build.sh.
#
# Usage: ./build-for-env.sh [development|staging|production]
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENVIRONMENT="${1:-development}"
ENV_FILE="$HERE/environments/$ENVIRONMENT.env"

if [ ! -f "$ENV_FILE" ]; then
  echo "error: no environments/$ENVIRONMENT.env (have: $(ls "$HERE/environments" | sed 's/\.env$//' | tr '\n' ' '))" >&2
  exit 1
fi

echo "== Loading $ENVIRONMENT environment ($ENV_FILE) =="
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a
echo "NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL"

echo "== Building the web bundle for $ENVIRONMENT =="
(cd "$HERE/../web" && CAPACITOR_BUILD=1 NEXT_PUBLIC_API_URL="$NEXT_PUBLIC_API_URL" npm run build)

echo "== Copying the web bundle into apps/android/assets =="
rm -rf "$HERE/assets"
mkdir -p "$HERE/assets"
cp -r "$HERE/../web/out/"* "$HERE/assets/"

echo "== Building the Android app =="
export VERSION_NAME="${VERSION_NAME:-1.0.0}${VERSION_NAME_SUFFIX:-}"
"$HERE/build.sh"
