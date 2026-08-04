plugins {
    // Versions come from the root project (see its comment).
    id("org.jetbrains.kotlin.jvm")
    id("org.jetbrains.kotlin.plugin.serialization")
}

// sautiy-core is consumed by the Android app, so it targets JVM 17 bytecode — the level
// Android's toolchain accepts — while compiling on whatever modern JDK the machine has.
// Targeting rather than pinning a toolchain keeps the module buildable on a bare JDK image
// with no toolchain download repository configured.
kotlin {
    compilerOptions {
        jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17)
        freeCompilerArgs.add("-Xjvm-default=all")
    }
}

java {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
}

tasks.withType<JavaCompile>().configureEach {
    options.release.set(17)
}

dependencies {
    implementation(libs.kotlinx.coroutines.core)
    implementation(libs.kotlinx.serialization.json)

    testImplementation(libs.junit)
    testImplementation(libs.kotlinx.coroutines.test)
    // Third-party MP3 decoder, test scope only. Used to decode the output of
    // SAUTIY's own encoder and measure round-trip signal accuracy — an
    // independent check that the bitstream we emit is really MPEG-1 Layer III.
    testImplementation(libs.jlayer)
}

tasks.test {
    useJUnit()
    testLogging {
        events("passed", "skipped", "failed")
        showStandardStreams = false
    }
    maxHeapSize = "2g"
}
