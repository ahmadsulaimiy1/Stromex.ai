// Plugin versions are declared once, here, with `apply false`.
//
// A subproject cannot request a plugin *with a version* once that plugin is already on the build
// classpath from a sibling — Gradle refuses because it cannot check compatibility. So the root
// resolves each one, and the modules apply them by id without a version.
//
// The Android Gradle Plugin is deliberately NOT declared here: it lives only in `:app`, which is
// itself only included when an Android SDK is present. Declaring it at the root would make every
// build — including `:sautiy-core:test` on a bare JDK — depend on reaching Google's Maven.
plugins {
    alias(libs.plugins.kotlin.jvm) apply false
    alias(libs.plugins.kotlin.android) apply false
    alias(libs.plugins.kotlin.compose) apply false
    alias(libs.plugins.kotlin.serialization) apply false
}
