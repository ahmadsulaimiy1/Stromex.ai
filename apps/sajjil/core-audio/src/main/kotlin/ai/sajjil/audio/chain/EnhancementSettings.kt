package ai.sajjil.audio.chain

import ai.sajjil.audio.dsp.CompressorSettings
import ai.sajjil.audio.dsp.DeEsserSettings
import ai.sajjil.audio.dsp.GateSettings
import ai.sajjil.audio.dsp.LimiterSettings
import ai.sajjil.audio.dsp.NoiseReductionSettings
import ai.sajjil.audio.dsp.ReverbSettings

/** One band of the parametric equaliser. */
data class EqBand(
    val frequencyHz: Double,
    val gainDb: Double,
    val q: Double = 1.0,
    val type: EqBandType = EqBandType.PEAKING,
)

enum class EqBandType { PEAKING, LOW_SHELF, HIGH_SHELF, HIGH_PASS, LOW_PASS }

/**
 * The complete enhancement state for one recording.
 *
 * Every studio preset and every voice style is just a value of this type, which is what makes
 * "simple mode" and "advanced mode" genuinely the same engine: tapping a preset card sets this
 * whole object, and opening the advanced panel edits the very same fields. There is no second
 * code path that could drift out of sync with the first.
 */
data class EnhancementSettings(
    val repairClicks: Boolean = false,
    val repairClipping: Boolean = false,
    val removeHum: Boolean = false,
    /** Null asks the engine to detect 50 vs 60 Hz from the audio itself. */
    val humFundamentalHz: Double? = null,
    val windReduction: Double = 0.0,
    val noiseReduction: NoiseReductionSettings? = null,
    val gate: GateSettings? = null,
    val highPassHz: Double? = null,
    val equaliser: List<EqBand> = emptyList(),
    val deEsser: DeEsserSettings? = null,
    val compressor: CompressorSettings? = null,
    val reverb: ReverbSettings? = null,
    val stereoWidth: Double = 1.0,
    /** Target integrated loudness in LUFS, or null to leave levels alone. */
    val targetLoudnessLufs: Double? = null,
    val limiter: LimiterSettings? = LimiterSettings(),
) {
    companion object {
        val NONE = EnhancementSettings(limiter = null)
    }
}

/**
 * A named starting point.
 *
 * @property summary the one line shown under the card's title. Written for someone who does not
 *   know what a compressor is — it says what the preset is *for*, not what it does technically.
 */
data class StudioPreset(
    val id: String,
    val name: String,
    val summary: String,
    val settings: EnhancementSettings,
)

/**
 * The five preset cards on the Studio screen.
 *
 * Deliberately five. Every one of them is a different job someone actually has, and none of them
 * overlaps enough that a user would have to compare specifications to choose.
 */
object StudioPresets {

    val CLEAN_VOICE = StudioPreset(
        id = "clean_voice",
        name = "Clean Voice",
        summary = "Removes background noise and evens out the level. The safe default.",
        settings = EnhancementSettings(
            removeHum = true,
            noiseReduction = NoiseReductionSettings(strength = 0.45),
            highPassHz = 80.0,
            equaliser = listOf(
                EqBand(200.0, -1.5, q = 0.9),
                EqBand(3200.0, 2.0, q = 0.8),
            ),
            deEsser = DeEsserSettings(thresholdDb = -26.0, rangeDb = 5.0),
            compressor = CompressorSettings(thresholdDb = -20.0, ratio = 2.5, kneeDb = 8.0),
            targetLoudnessLufs = -18.0,
        ),
    )

    val STUDIO_VOICE = StudioPreset(
        id = "studio_voice",
        name = "Studio Voice",
        summary = "A close, controlled sound, as though recorded in a treated room.",
        settings = EnhancementSettings(
            repairClicks = true,
            removeHum = true,
            noiseReduction = NoiseReductionSettings(strength = 0.6),
            gate = GateSettings(thresholdDb = -48.0, rangeDb = -12.0),
            highPassHz = 90.0,
            equaliser = listOf(
                EqBand(120.0, 1.5, type = EqBandType.LOW_SHELF),
                EqBand(400.0, -2.5, q = 1.1),
                EqBand(5000.0, 3.0, q = 0.7),
                EqBand(11000.0, 1.5, type = EqBandType.HIGH_SHELF),
            ),
            deEsser = DeEsserSettings(thresholdDb = -30.0, rangeDb = 7.0),
            compressor = CompressorSettings(thresholdDb = -22.0, ratio = 3.5, attackMs = 8.0, kneeDb = 6.0),
            reverb = ReverbSettings(amount = 0.06, size = 0.25, decaySeconds = 0.5, warmth = 0.5, preDelayMs = 8.0),
            targetLoudnessLufs = -17.0,
        ),
    )

    val PODCAST = StudioPreset(
        id = "podcast",
        name = "Podcast",
        summary = "Consistent and forward, at the loudness podcast platforms expect.",
        settings = EnhancementSettings(
            repairClicks = true,
            removeHum = true,
            noiseReduction = NoiseReductionSettings(strength = 0.5),
            gate = GateSettings(thresholdDb = -46.0, rangeDb = -14.0),
            highPassHz = 85.0,
            equaliser = listOf(
                EqBand(150.0, 1.0, type = EqBandType.LOW_SHELF),
                EqBand(350.0, -2.0, q = 1.0),
                EqBand(4000.0, 2.5, q = 0.8),
            ),
            deEsser = DeEsserSettings(thresholdDb = -28.0, rangeDb = 6.0),
            compressor = CompressorSettings(thresholdDb = -24.0, ratio = 4.0, attackMs = 6.0, releaseMs = 90.0),
            targetLoudnessLufs = -16.0,
        ),
    )

    val LECTURE = StudioPreset(
        id = "lecture",
        name = "Lecture",
        summary = "For a room and a distant microphone. Prioritises clarity over warmth.",
        settings = EnhancementSettings(
            repairClicks = true,
            removeHum = true,
            windReduction = 0.3,
            noiseReduction = NoiseReductionSettings(strength = 0.65),
            gate = GateSettings(thresholdDb = -44.0, rangeDb = -10.0, holdMs = 120.0),
            highPassHz = 110.0,
            equaliser = listOf(
                EqBand(300.0, -3.0, q = 1.2),
                EqBand(2000.0, 3.5, q = 0.9),
                EqBand(6000.0, 2.0, q = 0.8),
            ),
            deEsser = DeEsserSettings(thresholdDb = -26.0, rangeDb = 5.0),
            compressor = CompressorSettings(thresholdDb = -26.0, ratio = 4.5, attackMs = 12.0, releaseMs = 150.0),
            targetLoudnessLufs = -18.0,
        ),
    )

    val PRESTIGE_RECITATION = StudioPreset(
        id = "prestige_recitation",
        name = "Prestige Recitation",
        summary = "Full and unhurried, with a natural sense of space. For recitation.",
        settings = EnhancementSettings(
            repairClicks = true,
            removeHum = true,
            noiseReduction = NoiseReductionSettings(strength = 0.55),
            highPassHz = 70.0,
            equaliser = listOf(
                EqBand(110.0, 2.0, type = EqBandType.LOW_SHELF),
                EqBand(450.0, -1.5, q = 1.0),
                EqBand(2800.0, 1.5, q = 0.7),
                EqBand(9000.0, 2.0, type = EqBandType.HIGH_SHELF),
            ),
            deEsser = DeEsserSettings(thresholdDb = -30.0, rangeDb = 5.0),
            // Gentle and slow: heavy compression flattens the dynamics that carry the recitation.
            compressor = CompressorSettings(thresholdDb = -20.0, ratio = 2.0, attackMs = 20.0, releaseMs = 250.0, kneeDb = 10.0),
            reverb = ReverbSettings(amount = 0.16, size = 0.6, decaySeconds = 1.8, warmth = 0.45, preDelayMs = 28.0),
            targetLoudnessLufs = -17.0,
        ),
    )

    val ALL = listOf(CLEAN_VOICE, STUDIO_VOICE, PODCAST, LECTURE, PRESTIGE_RECITATION)

    fun byId(id: String): StudioPreset? = ALL.firstOrNull { it.id == id }
}

/**
 * Voice character adjustments, applied on top of whichever studio preset is active.
 *
 * These are EQ and dynamics only. Nothing here resynthesises or pitch-shifts the voice, because
 * every technique that does introduces artefacts on speech that people hear as "processed", and a
 * recitation or a lecture cannot afford that.
 */
data class VoiceStyle(
    val id: String,
    val name: String,
    val summary: String,
    val bands: List<EqBand>,
    val compressorAdjust: (CompressorSettings) -> CompressorSettings = { it },
)

object VoiceStyles {

    val NATURAL = VoiceStyle(
        id = "natural",
        name = "Natural",
        summary = "No colouring. The voice as recorded.",
        bands = emptyList(),
    )

    val WARM = VoiceStyle(
        id = "warm",
        name = "Warm",
        summary = "Rounder and softer in the upper mids.",
        bands = listOf(
            EqBand(180.0, 2.0, type = EqBandType.LOW_SHELF),
            EqBand(3000.0, -1.5, q = 0.8),
        ),
    )

    val DEEP = VoiceStyle(
        id = "deep",
        name = "Deep",
        summary = "More weight underneath, without losing words.",
        bands = listOf(
            EqBand(100.0, 3.5, type = EqBandType.LOW_SHELF),
            EqBand(250.0, 1.5, q = 0.9),
            EqBand(2500.0, -1.0, q = 0.9),
        ),
    )

    val SOFT = VoiceStyle(
        id = "soft",
        name = "Soft",
        summary = "Gentler and less forward. Good for quiet listening.",
        bands = listOf(
            EqBand(400.0, -1.5, q = 1.0),
            EqBand(7000.0, -2.5, type = EqBandType.HIGH_SHELF),
        ),
        compressorAdjust = { it.copy(ratio = it.ratio * 0.8, attackMs = it.attackMs * 1.5) },
    )

    val RICH = VoiceStyle(
        id = "rich",
        name = "Rich",
        summary = "Fuller across the whole range. Adds body and presence together.",
        bands = listOf(
            EqBand(130.0, 2.5, type = EqBandType.LOW_SHELF),
            EqBand(700.0, -1.5, q = 1.1),
            EqBand(3500.0, 2.0, q = 0.8),
            EqBand(10000.0, 1.5, type = EqBandType.HIGH_SHELF),
        ),
    )

    val BROADCAST = VoiceStyle(
        id = "broadcast",
        name = "Broadcast",
        summary = "Tight, even and close. The radio sound.",
        bands = listOf(
            EqBand(120.0, 2.0, type = EqBandType.LOW_SHELF),
            EqBand(500.0, -2.5, q = 1.2),
            EqBand(4500.0, 3.0, q = 0.8),
        ),
        compressorAdjust = { it.copy(ratio = it.ratio * 1.4, attackMs = 5.0, releaseMs = 80.0) },
    )

    val PRESTIGE = VoiceStyle(
        id = "prestige",
        name = "Prestige",
        summary = "Weight and clarity together, with the dynamics left intact.",
        bands = listOf(
            EqBand(110.0, 2.5, type = EqBandType.LOW_SHELF),
            EqBand(350.0, -1.0, q = 1.0),
            EqBand(2600.0, 1.5, q = 0.7),
            EqBand(8500.0, 2.0, type = EqBandType.HIGH_SHELF),
        ),
        compressorAdjust = { it.copy(ratio = it.ratio * 0.85, kneeDb = 10.0) },
    )

    val ALL = listOf(NATURAL, WARM, DEEP, SOFT, RICH, BROADCAST, PRESTIGE)

    fun byId(id: String): VoiceStyle? = ALL.firstOrNull { it.id == id }

    /** Layers a style onto a preset's settings. */
    fun apply(settings: EnhancementSettings, style: VoiceStyle): EnhancementSettings =
        settings.copy(
            equaliser = settings.equaliser + style.bands,
            compressor = settings.compressor?.let(style.compressorAdjust),
        )
}

/** A named ambience, expressed entirely as reverb settings. */
data class AmbienceProfile(
    val id: String,
    val name: String,
    val summary: String,
    val reverb: ReverbSettings,
)

object AmbienceProfiles {

    val DRY_STUDIO = AmbienceProfile(
        "dry_studio", "Dry Studio",
        "No space at all. What the microphone heard.",
        ReverbSettings(amount = 0.0),
    )

    val VOCAL_BOOTH = AmbienceProfile(
        "vocal_booth", "Vocal Booth",
        "A small treated room. Barely there, but not lifeless.",
        ReverbSettings(amount = 0.07, size = 0.18, decaySeconds = 0.35, warmth = 0.55, preDelayMs = 6.0,
            width = 0.3, earlyReflections = 0.7),
    )

    val BROADCAST_ROOM = AmbienceProfile(
        "broadcast", "Broadcast",
        "A controlled studio. Close, with just enough air.",
        ReverbSettings(amount = 0.1, size = 0.3, decaySeconds = 0.6, warmth = 0.5, preDelayMs = 12.0,
            width = 0.45, earlyReflections = 0.6),
    )

    val LECTURE_HALL = AmbienceProfile(
        "lecture_hall", "Lecture Hall",
        "A room with hard surfaces and an audience in it.",
        ReverbSettings(amount = 0.18, size = 0.55, decaySeconds = 1.3, warmth = 0.4, preDelayMs = 22.0,
            width = 0.7, earlyReflections = 0.5),
    )

    val LARGE_HALL = AmbienceProfile(
        "large_hall", "Large Hall",
        "A big, resonant space with a long tail.",
        ReverbSettings(amount = 0.26, size = 0.8, decaySeconds = 2.6, warmth = 0.35, preDelayMs = 35.0,
            width = 0.9, earlyReflections = 0.3),
    )

    val GRAND_MASJID = AmbienceProfile(
        "grand_masjid", "Grand Masjid",
        "A large stone interior — wide, slow and warm.",
        ReverbSettings(amount = 0.3, size = 0.92, decaySeconds = 3.4, warmth = 0.5, preDelayMs = 45.0,
            width = 1.0, earlyReflections = 0.25),
    )

    val PRESTIGE_RECITATION = AmbienceProfile(
        "prestige_recitation", "Prestige Recitation",
        "Generous space that stays clear enough to follow every word.",
        ReverbSettings(amount = 0.2, size = 0.7, decaySeconds = 2.2, warmth = 0.48, preDelayMs = 30.0,
            width = 0.8, earlyReflections = 0.4),
    )

    val ALL = listOf(
        DRY_STUDIO, VOCAL_BOOTH, BROADCAST_ROOM, LECTURE_HALL,
        LARGE_HALL, GRAND_MASJID, PRESTIGE_RECITATION,
    )

    fun byId(id: String): AmbienceProfile? = ALL.firstOrNull { it.id == id }
}
