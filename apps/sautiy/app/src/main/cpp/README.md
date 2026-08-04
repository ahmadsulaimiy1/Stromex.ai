# MP3 export — enabling the native encoder

**Android has no MP3 encoder.** `MediaCodec` decodes `audio/mpeg` and will not encode it, on any
API level, with any configuration. This is a platform fact, not a gap in SAUTIY.

SAUTIY therefore ships MP3 as an **optional native component** built on LAME. Without it, the
app is complete and MP3 simply does not appear in the export panel — see chapter 14.2: a format
is never listed unless an encoder for it is actually registered.

## Enabling it

LAME is **not vendored** in this repository, because it is LGPL-2.1 and vendoring it into an
application's tree makes the licence obligations of the whole tree ambiguous. Fetch it:

```bash
cd apps/sautiy/app/src/main/cpp
curl -L -o lame.tar.gz https://downloads.sourceforge.net/project/lame/lame/3.100/lame-3.100.tar.gz
tar xzf lame.tar.gz && mv lame-3.100 lame && rm lame.tar.gz
```

Then build with the NDK flag:

```bash
cd apps/sautiy
gradle :app:assembleRelease -PsautiyMp3=true
```

`app/build.gradle.kts` reads `sautiyMp3` and only then adds the `externalNativeBuild` block, so
a build without it needs no NDK at all.

## Licence obligations

LAME is **LGPL-2.1**. Linking it as a *separate shared library* (`libsautiymp3.so`) rather than
statically into the app is what keeps SAUTIY's own code outside the LGPL's reach: a user can
replace `libsautiymp3.so` with their own build of LAME, which is precisely the freedom the
licence requires. Do not link it statically, and do not merge it into another `.so`.

A release that includes it must:

1. State in About that the app contains LAME, with a link to <https://lame.sourceforge.io>.
2. Offer the LAME source, or a written offer for it.
3. Keep `libsautiymp3.so` a standalone shared object.

## Verifying it

The encoder is exercised by `Mp3EncoderTest` (instrumented — it needs the native library, so it
cannot run on the JVM). It encodes a 1 kHz tone, decodes the result, and asserts the tone is
present at the right frequency and level. Do not mark MP3 export as working until that test has
run on a device.

## Why not a Kotlin Layer III encoder

It was considered and rejected. A conformant encoder must reproduce roughly 1,500 entries of
Huffman table data exactly; a single wrong code yields files that some decoders open and others
reject, which is the worst class of bug — one the user discovers later, on somebody else's
machine. LAME is the reference implementation, and using it is the professional answer.
