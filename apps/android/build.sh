#!/usr/bin/env bash
# Builds apps/android (StromeX's native WebView shell) into a signed release
# APK and a signed release AAB, using raw SDK command-line tools directly
# (javac, d8, aapt2, zipalign, apksigner, bundletool, jarsigner) instead of
# Gradle/AGP. See docs/ANDROID-BUILD.md for why: this project's original
# build environment could not reach Google's Maven repository (dl.google.com),
# which AGP itself must be downloaded from, so no Gradle-based Android build
# is possible there. This script has no such requirement — every tool it
# calls is either bundled with the Android SDK's build-tools or is a
# standalone jar (r8lib.jar, bundletool.jar) — so it also works unchanged in
# a normal, unrestricted environment with a standard SDK install.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

: "${ANDROID_HOME:?Set ANDROID_HOME to an Android SDK root (platforms/, build-tools/)}"
BUILD_TOOLS_VERSION="${BUILD_TOOLS_VERSION:-34.0.0}"
PLATFORM_VERSION="${PLATFORM_VERSION:-34}"
BUILD_TOOLS="$ANDROID_HOME/build-tools/$BUILD_TOOLS_VERSION"
ANDROID_JAR="$ANDROID_HOME/platforms/android-$PLATFORM_VERSION/android.jar"
AAPT2="$BUILD_TOOLS/aapt2"
ZIPALIGN="$BUILD_TOOLS/zipalign"

# Standalone dexer/bundler jars. r8lib.jar ships D8 (and R8); bundletool.jar
# builds/signs/inspects .aab files. Neither is fetched from Google Maven —
# both are plain downloadable jars (see docs/ANDROID-BUILD.md for sources).
R8_JAR="${R8_JAR:-/opt/android-tools/r8lib.jar}"
BUNDLETOOL_JAR="${BUNDLETOOL_JAR:-/opt/android-tools/bundletool.jar}"

APP_ID="ai.stromex.app"
VERSION_CODE="${VERSION_CODE:-1}"
VERSION_NAME="${VERSION_NAME:-1.0.0}"
MIN_SDK="${MIN_SDK:-29}"
TARGET_SDK="${TARGET_SDK:-34}"

KEYSTORE="${KEYSTORE:-$HERE/keystore/stromex-release.keystore}"
KEY_ALIAS="${KEY_ALIAS:-stromex}"
KEYSTORE_PASS="${KEYSTORE_PASS:-StromeXRelease2026!}"

BUILD="$HERE/build"
rm -rf "$BUILD"
mkdir -p "$BUILD"/{classes,dex,res-compiled,apk-out,aab,gen}

if [ ! -d "$HERE/assets" ] || [ -z "$(ls -A "$HERE/assets" 2>/dev/null)" ]; then
  echo "error: $HERE/assets is empty. Run:" >&2
  echo "  (cd ../web && CAPACITOR_BUILD=1 npm run build) && cp -r ../web/out/* android/assets/" >&2
  exit 1
fi

if [ ! -f "$KEYSTORE" ]; then
  echo "== Generating release keystore (first run only) =="
  mkdir -p "$(dirname "$KEYSTORE")"
  keytool -genkeypair -v \
    -keystore "$KEYSTORE" \
    -alias "$KEY_ALIAS" \
    -keyalg RSA -keysize 2048 -validity 10950 \
    -storepass "$KEYSTORE_PASS" -keypass "$KEYSTORE_PASS" \
    -dname "CN=StromeX, OU=Engineering, O=StromeX, L=Unknown, ST=Unknown, C=US"
fi

echo "== Compiling Java sources =="
javac -d "$BUILD/classes" \
  -cp "$ANDROID_JAR" -bootclasspath "$ANDROID_JAR" \
  -source 8 -target 8 \
  $(find src -name "*.java")

echo "== Dexing (D8) =="
java -cp "$R8_JAR" com.android.tools.r8.D8 \
  --release --min-api "$MIN_SDK" --lib "$ANDROID_JAR" \
  --output "$BUILD/dex" \
  $(find "$BUILD/classes" -name "*.class")

echo "== Compiling resources (aapt2 compile) =="
"$AAPT2" compile --dir res -o "$BUILD/res-compiled/res.zip"

echo "== Linking binary APK (aapt2 link) =="
"$AAPT2" link -o "$BUILD/apk-out/base.apk" \
  --manifest AndroidManifest.xml \
  -I "$ANDROID_JAR" \
  -A assets \
  --min-sdk-version "$MIN_SDK" --target-sdk-version "$TARGET_SDK" \
  --version-code "$VERSION_CODE" --version-name "$VERSION_NAME" \
  --java "$BUILD/gen" \
  "$BUILD/res-compiled/res.zip"

echo "== Merging classes.dex, zipaligning, signing (APK) =="
cp "$BUILD/apk-out/base.apk" "$BUILD/apk-out/unsigned.apk"
(cd "$BUILD/apk-out" && zip -q -j unsigned.apk ../dex/classes.dex)
"$ZIPALIGN" -f -p 4 "$BUILD/apk-out/unsigned.apk" "$BUILD/apk-out/aligned.apk"
apksigner sign \
  --ks "$KEYSTORE" --ks-key-alias "$KEY_ALIAS" \
  --ks-pass "pass:$KEYSTORE_PASS" --key-pass "pass:$KEYSTORE_PASS" \
  --out "$BUILD/apk-out/stromex-release.apk" \
  "$BUILD/apk-out/aligned.apk"
apksigner verify "$BUILD/apk-out/stromex-release.apk" >/dev/null
echo "APK -> $BUILD/apk-out/stromex-release.apk"

echo "== Building proto-format resources for the App Bundle =="
"$AAPT2" link -o "$BUILD/aab/base-proto.apk" \
  --manifest AndroidManifest.xml \
  -I "$ANDROID_JAR" \
  -A assets \
  --proto-format \
  --min-sdk-version "$MIN_SDK" --target-sdk-version "$TARGET_SDK" \
  --version-code "$VERSION_CODE" --version-name "$VERSION_NAME" \
  "$BUILD/res-compiled/res.zip"

echo "== Assembling the base module =="
mkdir -p "$BUILD/aab/extracted" "$BUILD/aab/module/manifest" "$BUILD/aab/module/dex"
(cd "$BUILD/aab/extracted" && unzip -q ../base-proto.apk)
mv "$BUILD/aab/extracted/AndroidManifest.xml" "$BUILD/aab/module/manifest/AndroidManifest.xml"
mv "$BUILD/aab/extracted/resources.pb" "$BUILD/aab/module/resources.pb"
mv "$BUILD/aab/extracted/res" "$BUILD/aab/module/res"
mv "$BUILD/aab/extracted/assets" "$BUILD/aab/module/assets"
cp "$BUILD/dex/classes.dex" "$BUILD/aab/module/dex/classes.dex"
(cd "$BUILD/aab/module" && zip -qr ../base.zip .)

echo "== Building and signing the App Bundle (bundletool) =="
java -jar "$BUNDLETOOL_JAR" build-bundle \
  --modules="$BUILD/aab/base.zip" \
  --output="$BUILD/aab/stromex-release.aab" \
  --overwrite
jarsigner -sigalg SHA256withRSA -digestalg SHA-256 \
  -keystore "$KEYSTORE" -storepass "$KEYSTORE_PASS" \
  "$BUILD/aab/stromex-release.aab" "$KEY_ALIAS"
jarsigner -verify "$BUILD/aab/stromex-release.aab" >/dev/null
java -jar "$BUNDLETOOL_JAR" validate --bundle="$BUILD/aab/stromex-release.aab" >/dev/null
echo "AAB -> $BUILD/aab/stromex-release.aab"

echo "== Deriving a universal APK from the AAB as an end-to-end sanity check =="
java -jar "$BUNDLETOOL_JAR" build-apks \
  --bundle="$BUILD/aab/stromex-release.aab" \
  --output="$BUILD/aab/stromex.apks" \
  --ks="$KEYSTORE" --ks-key-alias="$KEY_ALIAS" \
  --ks-pass="pass:$KEYSTORE_PASS" --key-pass="pass:$KEYSTORE_PASS" \
  --mode=universal --overwrite

echo "== Copying deliverables to release/ =="
mkdir -p "$HERE/release"
cp "$BUILD/apk-out/stromex-release.apk" "$HERE/release/stromex-v${VERSION_NAME}.apk"
cp "$BUILD/aab/stromex-release.aab" "$HERE/release/stromex-v${VERSION_NAME}.aab"
echo "APK -> $HERE/release/stromex-v${VERSION_NAME}.apk"
echo "AAB -> $HERE/release/stromex-v${VERSION_NAME}.aab"
echo "Done."
