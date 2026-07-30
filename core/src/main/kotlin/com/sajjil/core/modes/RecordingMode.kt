package com.sajjil.core.modes

import com.sajjil.core.dsp.NoiseReductionStrength
import com.sajjil.core.dsp.ProcessingChainConfig

/**
 * Flagship recording modes. Each carries a [ProcessingChainConfig] tuned for
 * its content type — Qur'an Studio favors Tajweed-safe gating (long hold,
 * gentle ratio) over aggressive gain reduction, Nasheed leans into harmonic
 * presence and denser compression, Podcast targets consistent broadcast tone.
 */
enum class RecordingMode(val displayName: String, val config: ProcessingChainConfig) {
    QURAN_STUDIO(
        "Qur'an Studio",
        ProcessingChainConfig(
            label = "Qur'an Studio",
            description = "Tajweed-safe enhancement: preserves Makharij articulation and natural breath, " +
                "gentle noise gating with long hold so soft letters are never clipped.",
            eqBassDb = 1.5, eqMidDb = 0.5, eqPresenceDb = 1.0, eqTrebleDb = 0.5,
            gateThresholdDb = -50.0, gateRangeDb = -12.0, gateHoldMs = 220.0, gateReleaseMs = 400.0,
            deEsserEnabled = true, deEsserThresholdDb = -22.0, deEsserRatio = 3.0,
            compressorThresholdDb = -20.0, compressorRatio = 2.0, compressorAttackMs = 15.0, compressorReleaseMs = 180.0,
            limiterCeilingDb = -1.0, limiterDriveDb = 3.0,
            noiseReductionStrength = NoiseReductionStrength.LIGHT,
        ),
    ),
    IMAM_AL_HARAM(
        "Imam Al-Haram",
        ProcessingChainConfig(
            label = "Imam Al-Haram",
            description = "Premium broadcast-quality preset inspired by Haramain sound: warm vocal body, " +
                "controlled bass, smooth dynamics, natural spaciousness.",
            eqBassDb = 2.5, eqMidDb = 1.0, eqPresenceDb = 1.5, eqTrebleDb = 1.0,
            gateThresholdDb = -48.0, gateRangeDb = -14.0, gateHoldMs = 200.0, gateReleaseMs = 350.0,
            deEsserEnabled = true, deEsserThresholdDb = -22.0, deEsserRatio = 3.5,
            compressorThresholdDb = -18.0, compressorRatio = 2.5, compressorAttackMs = 12.0, compressorReleaseMs = 160.0,
            limiterCeilingDb = -0.6, limiterDriveDb = 4.5,
            noiseReductionStrength = NoiseReductionStrength.MODERATE,
        ),
    ),
    LECTURE(
        "Lecture",
        ProcessingChainConfig(
            label = "Lecture",
            description = "Speech clarity and voice projection for scholars and teachers, tuned for long " +
                "sessions with stronger noise suppression.",
            eqBassDb = -1.0, eqMidDb = 1.5, eqPresenceDb = 2.5, eqTrebleDb = 1.0,
            gateThresholdDb = -42.0, gateRangeDb = -22.0, gateHoldMs = 120.0, gateReleaseMs = 220.0,
            deEsserEnabled = true, deEsserThresholdDb = -20.0, deEsserRatio = 4.0,
            compressorThresholdDb = -20.0, compressorRatio = 3.0, compressorAttackMs = 8.0, compressorReleaseMs = 120.0,
            limiterCeilingDb = -0.5, limiterDriveDb = 5.0,
            noiseReductionStrength = NoiseReductionStrength.STRONG,
        ),
    ),
    NASHEED(
        "Nasheed",
        ProcessingChainConfig(
            label = "Nasheed",
            description = "Vocal richness and harmonic enhancement with studio-style mastering compression " +
                "balance for a fuller, more produced sound.",
            eqBassDb = 2.0, eqMidDb = 0.5, eqPresenceDb = 2.5, eqTrebleDb = 2.0,
            gateThresholdDb = -45.0, gateRangeDb = -16.0, gateHoldMs = 100.0, gateReleaseMs = 180.0,
            deEsserEnabled = true, deEsserThresholdDb = -20.0, deEsserRatio = 4.5,
            compressorThresholdDb = -16.0, compressorRatio = 3.5, compressorAttackMs = 6.0, compressorReleaseMs = 100.0,
            limiterCeilingDb = -0.3, limiterDriveDb = 6.5,
            noiseReductionStrength = NoiseReductionStrength.MODERATE,
        ),
    ),
    PODCAST(
        "Podcast",
        ProcessingChainConfig(
            label = "Podcast",
            description = "Radio-grade tone with consistent volume and broadcast mastering character.",
            eqBassDb = 1.0, eqMidDb = 0.5, eqPresenceDb = 2.0, eqTrebleDb = 0.5,
            gateThresholdDb = -40.0, gateRangeDb = -24.0, gateHoldMs = 100.0, gateReleaseMs = 200.0,
            deEsserEnabled = true, deEsserThresholdDb = -20.0, deEsserRatio = 4.0,
            compressorThresholdDb = -18.0, compressorRatio = 3.0, compressorAttackMs = 8.0, compressorReleaseMs = 130.0,
            limiterCeilingDb = -0.3, limiterDriveDb = 6.0,
            noiseReductionStrength = NoiseReductionStrength.STRONG,
        ),
    ),
}
