pluginManagement {
    repositories {
        google {
            content {
                includeGroupByRegex("com\\.android.*")
                includeGroupByRegex("com\\.google.*")
                includeGroupByRegex("androidx.*")
            }
        }
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.PREFER_SETTINGS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "sautiy"

// ---------------------------------------------------------------------------
// SAUTIY builds in two tiers.
//
//   :sautiy-core  Pure JVM Kotlin. The complete audio engine, DSP chain,
//                 codecs, timeline/edit engine and domain model. Zero Android
//                 dependencies, so it compiles and its full test suite runs on
//                 any machine with a JDK — no Android SDK required.
//
//   :app          The Android application (Jetpack Compose). Included only
//                 when an Android SDK is actually resolvable, so that
//                 `gradle :sautiy-core:test` works everywhere — CI containers,
//                 review sandboxes, a bare JDK image — instead of failing at
//                 configuration time on a missing SDK.
//
// Force either decision with -PsautiyAndroid=true|false.
// ---------------------------------------------------------------------------
include(":sautiy-core")

val androidOverride: String? = providers.gradleProperty("sautiyAndroid").orNull

val androidSdkPresent: Boolean = when (androidOverride) {
    "true" -> true
    "false" -> false
    else -> {
        val fromEnv = System.getenv("ANDROID_HOME") ?: System.getenv("ANDROID_SDK_ROOT")
        val fromLocalProperties = rootDir.resolve("local.properties")
            .takeIf { it.isFile }
            ?.let { file ->
                java.util.Properties().apply { file.inputStream().use(::load) }.getProperty("sdk.dir")
            }
        sequenceOf(fromEnv, fromLocalProperties)
            .filterNotNull()
            .filter { it.isNotBlank() }
            .any { java.io.File(it).isDirectory }
    }
}

if (androidSdkPresent) {
    include(":app")
} else {
    logger.lifecycle(
        "SAUTIY: no Android SDK detected — configuring :sautiy-core only. " +
            "Set ANDROID_HOME (or sdk.dir in local.properties) to build the Android app, " +
            "or pass -PsautiyAndroid=true to force it."
    )
}
