package com.sajjil.core.modes

import com.sajjil.core.dsp.NoiseReductionStrength
import com.sajjil.core.dsp.ProcessingChainConfig

/**
 * SAJJIL's flagship Haramain-inspired production chains (SAJJIL Master).
 * Unlike [RecordingMode], which shapes the *live capture* chain, a
 * [VoiceProfile] is applied when mastering an already-recorded file toward
 * a specific target character. Each profile carries its own custom EQ
 * curve (not just gain offsets on four shared points) plus distinct
 * compressor/limiter/de-esser behavior, so switching profiles genuinely
 * changes the sound rather than nudging a single shared shape.
 */
enum class VoiceProfile(val displayName: String, val config: ProcessingChainConfig) {
    HARAMAIN_BROADCAST(
        "Haramain Broadcast",
        ProcessingChainConfig(
            label = "Haramain Broadcast",
            description = "Premium mosque broadcast quality: warm body, decluttered low-mids, gentle air.",
            customEqBands = listOf(
                Triple(100.0, 0.9, 2.0),
                Triple(400.0, 1.2, -1.0),
                Triple(3000.0, 1.0, 1.5),
                Triple(12000.0, 0.8, 1.0),
            ),
            deEsserThresholdDb = -22.0, deEsserRatio = 3.5,
            compressorThresholdDb = -18.0, compressorRatio = 2.5, compressorKneeDb = 6.0,
            compressorAttackMs = 12.0, compressorReleaseMs = 160.0,
            limiterCeilingDb = -0.6, limiterDriveDb = 4.5,
            noiseReductionStrength = NoiseReductionStrength.MODERATE,
        ),
    ),
    MAKKAH_STUDIO(
        "Makkah Studio",
        ProcessingChainConfig(
            label = "Makkah Studio",
            description = "Powerful and majestic: weighted low end, driven presence, tight and fast.",
            customEqBands = listOf(
                Triple(90.0, 0.9, 3.0),
                Triple(2500.0, 1.1, 2.5),
                Triple(5000.0, 1.0, 1.5),
            ),
            deEsserThresholdDb = -21.0, deEsserRatio = 4.0,
            compressorThresholdDb = -16.0, compressorRatio = 3.2, compressorKneeDb = 3.0,
            compressorAttackMs = 6.0, compressorReleaseMs = 110.0,
            limiterCeilingDb = -0.4, limiterDriveDb = 6.5,
            noiseReductionStrength = NoiseReductionStrength.MODERATE,
        ),
    ),
    MADINAH_STUDIO(
        "Madinah Studio",
        ProcessingChainConfig(
            label = "Madinah Studio",
            description = "Warm and natural, gentle on dynamics — the least processed-sounding profile.",
            customEqBands = listOf(
                Triple(150.0, 0.9, 2.0),
                Triple(8000.0, 0.9, 0.5),
            ),
            deEsserThresholdDb = -23.0, deEsserRatio = 2.5,
            compressorThresholdDb = -20.0, compressorRatio = 2.0, compressorKneeDb = 9.0,
            compressorAttackMs = 18.0, compressorReleaseMs = 200.0,
            limiterCeilingDb = -1.0, limiterDriveDb = 3.0,
            noiseReductionStrength = NoiseReductionStrength.LIGHT,
        ),
    ),
    QARI_PRESTIGE(
        "Qari Prestige",
        ProcessingChainConfig(
            label = "Qari Prestige",
            description = "Balanced and intimate close-mic character: proximity-boom controlled, silky top.",
            customEqBands = listOf(
                Triple(80.0, 1.0, -1.0),
                Triple(1800.0, 1.1, 1.5),
                Triple(10000.0, 0.9, 1.0),
            ),
            deEsserThresholdDb = -22.0, deEsserRatio = 3.0,
            compressorThresholdDb = -19.0, compressorRatio = 2.2, compressorKneeDb = 8.0,
            compressorAttackMs = 14.0, compressorReleaseMs = 170.0,
            limiterCeilingDb = -0.8, limiterDriveDb = 3.5,
            noiseReductionStrength = NoiseReductionStrength.LIGHT,
        ),
    ),
    LECTURE_AUTHORITY(
        "Lecture Authority",
        ProcessingChainConfig(
            label = "Lecture Authority",
            description = "Clear and authoritative for spoken word: mud cut, strong intelligibility presence.",
            customEqBands = listOf(
                Triple(250.0, 1.1, -2.0),
                Triple(3500.0, 1.0, 3.0),
                Triple(7500.0, 0.9, 0.5),
            ),
            deEsserThresholdDb = -20.0, deEsserRatio = 4.0,
            compressorThresholdDb = -20.0, compressorRatio = 3.5, compressorKneeDb = 4.0,
            compressorAttackMs = 7.0, compressorReleaseMs = 110.0,
            limiterCeilingDb = -0.5, limiterDriveDb = 5.5,
            noiseReductionStrength = NoiseReductionStrength.STRONG,
        ),
    ),
    ROYAL_PODCAST(
        "Royal Podcast",
        ProcessingChainConfig(
            label = "Royal Podcast",
            description = "Radio-quality consistency for spoken-word shows: mid-forward, dense and tight.",
            customEqBands = listOf(
                Triple(1000.0, 0.9, 1.0),
                Triple(4000.0, 1.0, 2.0),
            ),
            deEsserThresholdDb = -20.0, deEsserRatio = 4.0,
            compressorThresholdDb = -18.0, compressorRatio = 3.5, compressorKneeDb = 3.0,
            compressorAttackMs = 8.0, compressorReleaseMs = 130.0,
            limiterCeilingDb = -0.3, limiterDriveDb = 6.0,
            noiseReductionStrength = NoiseReductionStrength.STRONG,
        ),
    ),
    EXECUTIVE_VOICE(
        "Executive Voice",
        ProcessingChainConfig(
            label = "Executive Voice",
            description = "Television-quality density and loudness: controlled low end, driven presence.",
            customEqBands = listOf(
                Triple(100.0, 1.0, 1.0),
                Triple(2000.0, 1.0, 2.0),
                Triple(5000.0, 1.0, 1.5),
            ),
            deEsserThresholdDb = -19.0, deEsserRatio = 4.5,
            compressorThresholdDb = -16.0, compressorRatio = 4.0, compressorKneeDb = 2.0,
            compressorAttackMs = 5.0, compressorReleaseMs = 100.0,
            limiterCeilingDb = -0.2, limiterDriveDb = 7.0,
            noiseReductionStrength = NoiseReductionStrength.STRONG,
        ),
    ),
}
