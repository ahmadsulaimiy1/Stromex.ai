# SAUTIY™ — Third-Party Notices

SAUTIY ships no third-party runtime code beyond the Kotlin standard library, JetBrains
coroutines/serialization, and AndroidX/Jetpack Compose. The audio engine — capture, DSP,
timeline, and every encoder including MP3 — is original work in this repository.

## Bundled fonts

All bundled typefaces are licensed under the **SIL Open Font License, Version 1.1**
(<https://openfontlicense.org>), which permits bundling and redistribution inside an
application.

| Family | Files | Copyright |
|---|---|---|
| Archivo | `archivo_regular.ttf`, `archivo_bold.ttf` | Copyright (c) Omnibus-Type |
| Fraunces | `fraunces_light.ttf`, `fraunces_semibold.ttf` | Copyright (c) The Fraunces Project Authors |
| Amiri | `amiri_regular.ttf`, `amiri_bold.ttf` | Copyright (c) Khaled Hosny |
| Cairo | `cairo_regular.ttf`, `cairo_bold.ttf` | Copyright (c) The Cairo Project Authors |

The `.ttf` files in `app/src/main/res/font/` were produced from the `.woff2` originals
already present in this repository by lossless container conversion (fontTools); no glyph,
metric or hinting data was altered.

## Test-only dependencies

| Library | Licence | Why |
|---|---|---|
| JUnit 4 | EPL 1.0 | Test framework |
| JLayer 1.0.1 | LGPL 2.1 | An **independent** MP3 decoder used only inside `sautiy-core` unit tests, to decode the output of SAUTIY's own encoder and measure round-trip accuracy. It is not on any runtime classpath and is not shipped in the APK. |
