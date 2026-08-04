plugins {
    id("org.jetbrains.kotlin.jvm")
    `java-library`
}

// core-audio is deliberately platform-free: no Android imports, no java.nio.file, nothing that
// ties it to a device. Everything here runs on a plain JVM, which is what makes the DSP
// verifiable by unit tests on any machine.
java {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
}

kotlin {
    compilerOptions {
        jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17)
        freeCompilerArgs.add("-Xjvm-default=all")
    }
}

dependencies {
    testImplementation(kotlin("test"))
}

tasks.test {
    useJUnitPlatform()
    testLogging {
        events("passed", "failed", "skipped")
    }
}
