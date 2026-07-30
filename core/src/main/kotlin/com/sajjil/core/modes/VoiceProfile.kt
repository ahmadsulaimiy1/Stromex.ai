package com.sajjil.core.modes

import com.sajjil.core.dsp.NoiseReductionStrength
import com.sajjil.core.dsp.ProcessingChainConfig

/**
 * Mastering-stage voice character profiles (SAJJIL Master). Unlike
 * [RecordingMode], which shapes the live capture chain, a [VoiceProfile]
 * is applied when mastering an already-recorded file toward a specific
 * target character.
 */
enum class VoiceProfile(val displayName: String, val config: ProcessingChainConfig) {
    HARAMAIN(
        "Haramain",
        ProcessingChainConfig(
            label = "Haramain", description = "Premium mosque broadcast quality: warm, spacious, controlled.",
            eqBassDb = 2.5, eqMidDb = 1.0, eqPresenceDb = 1.5, eqTrebleDb = 1.0,
            compressorThresholdDb = -18.0, compressorRatio = 2.5, limiterCeilingDb = -0.6, limiterDriveDb = 4.5,
            noiseReductionStrength = NoiseReductionStrength.MODERATE,
        ),
    ),
    MADINAH(
        "Madinah",
        ProcessingChainConfig(
            label = "Madinah", description = "Warm and natural, gentle on dynamics.",
            eqBassDb = 2.0, eqMidDb = 0.5, eqPresenceDb = 1.0, eqTrebleDb = 0.5,
            compressorThresholdDb = -20.0, compressorRatio = 2.0, limiterCeilingDb = -1.0, limiterDriveDb = 3.0,
            noiseReductionStrength = NoiseReductionStrength.LIGHT,
        ),
    ),
    MAKKAH(
        "Makkah",
        ProcessingChainConfig(
            label = "Makkah", description = "Powerful and majestic, more presence and drive.",
            eqBassDb = 2.5, eqMidDb = 1.5, eqPresenceDb = 2.5, eqTrebleDb = 1.5,
            compressorThresholdDb = -16.0, compressorRatio = 3.0, limiterCeilingDb = -0.5, limiterDriveDb = 6.0,
            noiseReductionStrength = NoiseReductionStrength.MODERATE,
        ),
    ),
    STUDIO_QARI(
        "Studio Qari",
        ProcessingChainConfig(
            label = "Studio Qari", description = "Balanced and intimate, close-mic character.",
            eqBassDb = 1.0, eqMidDb = 0.5, eqPresenceDb = 1.5, eqTrebleDb = 1.0,
            compressorThresholdDb = -19.0, compressorRatio = 2.2, limiterCeilingDb = -0.8, limiterDriveDb = 3.5,
            noiseReductionStrength = NoiseReductionStrength.LIGHT,
        ),
    ),
    LECTURE_HALL(
        "Lecture Hall",
        ProcessingChainConfig(
            label = "Lecture Hall", description = "Clear and authoritative for spoken word.",
            eqBassDb = -1.0, eqMidDb = 1.5, eqPresenceDb = 2.5, eqTrebleDb = 1.0,
            compressorThresholdDb = -20.0, compressorRatio = 3.0, limiterCeilingDb = -0.5, limiterDriveDb = 5.0,
            noiseReductionStrength = NoiseReductionStrength.STRONG,
        ),
    ),
    BROADCAST(
        "Broadcast",
        ProcessingChainConfig(
            label = "Broadcast", description = "Television-quality density and loudness.",
            eqBassDb = 1.0, eqMidDb = 1.0, eqPresenceDb = 2.0, eqTrebleDb = 1.0,
            compressorThresholdDb = -16.0, compressorRatio = 4.0, limiterCeilingDb = -0.2, limiterDriveDb = 7.0,
            noiseReductionStrength = NoiseReductionStrength.STRONG,
        ),
    ),
    PODCAST(
        "Podcast",
        ProcessingChainConfig(
            label = "Podcast", description = "Radio-quality consistency for spoken-word shows.",
            eqBassDb = 1.0, eqMidDb = 0.5, eqPresenceDb = 2.0, eqTrebleDb = 0.5,
            compressorThresholdDb = -18.0, compressorRatio = 3.0, limiterCeilingDb = -0.3, limiterDriveDb = 6.0,
            noiseReductionStrength = NoiseReductionStrength.STRONG,
        ),
    ),
}
