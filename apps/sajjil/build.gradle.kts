// Intentionally empty of plugin declarations.
//
// Declaring the Android Gradle Plugin here (even with `apply false`) would force Gradle to
// resolve it against dl.google.com before configuring ANY project, which makes `:core-audio`
// unbuildable without Android tooling. Each subproject declares the plugins it needs; versions
// come from `pluginManagement.plugins` in settings.gradle.kts.

tasks.register<Delete>("clean") {
    delete(rootProject.layout.buildDirectory)
}
