// The Kotlin Android plugin and the Android Gradle Plugin must be loaded by the *same*
// classloader. Resolving them at different levels — KGP at the root, AGP in `:app` — puts them
// in separate loaders, and applying `kotlin.android` then dies with
// `NoClassDefFoundError: com/android/build/gradle/api/BaseVariant` because it cannot see AGP's
// types at all.
//
// So both go on one buildscript classpath here, and the modules apply them by id with no
// version.
//
// AGP is added **only when an Android SDK is actually present**. The root build file is
// evaluated on every invocation, including `:sautiy-core:test` on a bare JDK with no access to
// Google's Maven — and unconditionally requesting AGP there would make the engine tests
// impossible to run without an Android toolchain they do not need.
buildscript {
    val androidSdk: String? = System.getenv("ANDROID_HOME")
        ?: System.getenv("ANDROID_SDK_ROOT")
        ?: rootDir.resolve("local.properties")
            .takeIf { it.isFile }
            ?.let { file ->
                java.util.Properties().apply { file.inputStream().use(::load) }.getProperty("sdk.dir")
            }
    val androidPresent = androidSdk != null && java.io.File(androidSdk).isDirectory

    repositories {
        mavenCentral()
        gradlePluginPortal()
        if (androidPresent) google()
    }

    dependencies {
        classpath("org.jetbrains.kotlin:kotlin-gradle-plugin:2.0.21")
        classpath("org.jetbrains.kotlin:kotlin-serialization:2.0.21")
        if (androidPresent) {
            classpath("com.android.tools.build:gradle:8.7.2")
            classpath("org.jetbrains.kotlin:compose-compiler-gradle-plugin:2.0.21")
        }
    }
}
