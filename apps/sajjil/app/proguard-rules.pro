# SAJJIL release rules.
#
# R8 is on in release builds because startup time and memory headroom on mid-range devices are
# product requirements. Everything kept below is kept for a stated reason.

# Room generates implementations reflectively named after the DAO interfaces.
-keep class * extends androidx.room.RoomDatabase { <init>(); }
-dontwarn androidx.room.paging.**

# Media3 resolves the playback service by its component name from the manifest, so the class
# name has to survive.
-keep class ai.sajjil.app.audio.PlaybackService { *; }
-keep class ai.sajjil.app.audio.RecordingService { *; }

# Compose keeps its own rules via consumer files; nothing extra is needed here.

# Kotlin coroutines' debug agent probes for these and logs noisily if they are absent.
-dontwarn kotlinx.coroutines.debug.**

# The audio engine is plain Kotlin with no reflection, so it can be shrunk and renamed freely.
# Its entry points are all reached from app code that R8 can trace.
