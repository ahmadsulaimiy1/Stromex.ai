plugins {
    // Versions come from the root buildscript classpath, so AGP and the Kotlin plugins share
    // one classloader. See the root build file.
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
    id("org.jetbrains.kotlin.plugin.serialization")
}

android {
    namespace = "ai.sautiy"
    compileSdk = 35

    defaultConfig {
        applicationId = "ai.sautiy"
        // 26 rather than 21: below Oreo there is no foreground-service model that survives a
        // ninety-minute lecture with the screen off, and shipping a recorder that silently dies
        // at minute forty would violate chapter 1.3.5 on the devices that most need it.
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "1.0"
        resourceConfigurations += listOf("en", "ar")

        // Instrumented tests are how the device layer stops being "source complete".
        // AudioRecord, AudioTrack and MediaCodec have no meaningful JVM stand-in, so anything
        // claimed about them has to be claimed from a running Android.
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
        debug {
            applicationIdSuffix = ".debug"
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    buildFeatures {
        compose = true
    }

    // MP3 export is an optional native component (LAME via the NDK). Android has no MP3
    // encoder, so this is the only honest way to offer the format.
    //
    // The block is added only when -PsautiyMp3=true, which means an ordinary build needs no NDK,
    // no CMake and no LAME checkout — and simply ships without MP3 rather than failing to build.
    // See app/src/main/cpp/README.md.
    if (providers.gradleProperty("sautiyMp3").orNull == "true") {
        externalNativeBuild {
            cmake {
                path = file("src/main/cpp/CMakeLists.txt")
                version = "3.22.1"
            }
        }
        defaultConfig {
            ndk {
                abiFilters += listOf("arm64-v8a", "armeabi-v7a", "x86_64")
            }
        }
    }

    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}

dependencies {
    implementation(project(":sautiy-core"))

    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.androidx.lifecycle.service)
    implementation(libs.androidx.documentfile)
    implementation(libs.androidx.datastore.preferences)
    implementation(libs.androidx.media3.session)
    implementation(libs.androidx.media3.common)
    implementation(libs.kotlinx.coroutines.android)
    implementation(libs.kotlinx.serialization.json)

    implementation(platform(libs.compose.bom))
    implementation(libs.compose.ui)
    implementation(libs.compose.ui.graphics)
    implementation(libs.compose.foundation)
    implementation(libs.compose.material3)
    implementation(libs.compose.animation)
    implementation(libs.compose.ui.tooling.preview)
    debugImplementation(libs.compose.ui.tooling)

    testImplementation(libs.junit)

    androidTestImplementation(libs.junit)
    androidTestImplementation(libs.androidx.test.runner)
    androidTestImplementation(libs.androidx.test.rules)
    androidTestImplementation(libs.androidx.test.ext.junit)
}
