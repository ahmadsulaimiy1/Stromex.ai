package ai.sajjil.audio.analysis

import ai.sajjil.audio.AudioBuffer
import ai.sajjil.audio.dbToLinear
import ai.sajjil.audio.linearToDb
import ai.sajjil.audio.loudness.LoudnessMeter
import kotlin.math.abs
import kotlin.math.roundToInt
import kotlin.math.sqrt

/**
 * A recording's measured quality, as one headline number plus the findings behind it.
 *
 * The number exists so the Library can sort and label recordings at a glance. The findings exist
 * because a bare score is not actionable — "68" tells someone nothing, "the room is noisy and the
 * level is low" tells them what to change next time.
 */
data class QualityReport(
    /** 0-100. Above 80 is good, 60-80 usable, below 60 has a problem worth fixing. */
    val score: Int,
    val noiseFloorDb: Double,
    val signalToNoiseDb: Double,
    val integratedLufs: Double?,
    val truePeakDb: Double,
    val clippedSampleCount: Int,
    val findings: List<QualityFinding>,
) {
    val grade: String
        get() = when {
            score >= 85 -> "Excellent"
            score >= 70 -> "Good"
            score >= 55 -> "Usable"
            else -> "Needs work"
        }
}

/**
 * One thing worth telling the user about.
 *
 * @property message plain language, no jargon, and it says what to do rather than only what is
 *   wrong. This text is shown verbatim in the UI.
 */
data class QualityFinding(
    val severity: Severity,
    val message: String,
    /** Set when a preset or action in the app would address this. */
    val suggestedPresetId: String? = null,
) {
    enum class Severity { INFO, WARNING, PROBLEM }
}

/**
 * Measures a recording without modifying it.
 *
 * The noise floor is estimated as a low percentile of short-window RMS, which lands on the
 * quietest genuine part of the recording. Using the absolute minimum instead would land on a
 * single digital-silence frame and report a floor of -inf for almost every file.
 */
class QualityAnalyzer(private val sampleRate: Int) {

    fun analyse(buffer: AudioBuffer): QualityReport {
        if (buffer.frameCount == 0) {
            return QualityReport(
                score = 0,
                noiseFloorDb = -120.0,
                signalToNoiseDb = 0.0,
                integratedLufs = null,
                truePeakDb = -120.0,
                clippedSampleCount = 0,
                findings = listOf(
                    QualityFinding(QualityFinding.Severity.PROBLEM, "This recording is empty.")
                ),
            )
        }

        val windows = rmsWindows(buffer)
        val noiseFloorDb = linearToDb(percentile(windows, 0.10))
        val speechLevelDb = linearToDb(percentile(windows, 0.90))
        val signalToNoiseDb = speechLevelDb - noiseFloorDb

        val measurement = LoudnessMeter(sampleRate).measure(buffer)
        val clipped = countClipped(buffer)

        val findings = ArrayList<QualityFinding>()
        var score = 100.0

        // A noise floor only means something if the recording contains quiet moments to measure
        // it in. Continuous material — a sustained tone, unbroken music, a recitation with no
        // pause — has a "floor" equal to its own level, and reading that as 0 dB of headroom
        // would condemn a perfectly clean recording as the noisiest possible one.
        val floorIsMeasurable = noiseFloorDb < MEASURABLE_NOISE_FLOOR_DB

        // Noise: the single biggest determinant of whether a recording sounds amateur.
        when {
            !floorIsMeasurable -> findings += QualityFinding(
                QualityFinding.Severity.INFO,
                "This recording has no pauses, so its background noise cannot be measured.",
            )
            signalToNoiseDb < 15 -> {
                score -= 32
                findings += QualityFinding(
                    QualityFinding.Severity.PROBLEM,
                    "There is a lot of background noise. Studio Voice will clean this up.",
                    StudioPresetIds.STUDIO_VOICE,
                )
            }
            signalToNoiseDb < 25 -> {
                score -= 16
                findings += QualityFinding(
                    QualityFinding.Severity.WARNING,
                    "Some background noise is audible. Clean Voice will reduce it.",
                    StudioPresetIds.CLEAN_VOICE,
                )
            }
            signalToNoiseDb < 40 -> score -= 5
        }

        // Clipping is unrecoverable damage, so it is weighted heavily.
        if (clipped > 0) {
            val proportion = clipped.toDouble() / (buffer.frameCount * buffer.channelCount)
            score -= (proportion * 4000).coerceAtMost(30.0)
            findings += QualityFinding(
                if (proportion > 0.001) QualityFinding.Severity.PROBLEM else QualityFinding.Severity.WARNING,
                "The recording is distorted in places because the input was too loud. " +
                    "SAJJIL can repair most of it, and lowering the input level will prevent it.",
            )
        }

        // Level. Too quiet is fixable and only mildly penalised; too loud risks clipping.
        val lufs = measurement.integratedLufs
        if (lufs != null) {
            when {
                lufs < -32 -> {
                    score -= 14
                    findings += QualityFinding(
                        QualityFinding.Severity.WARNING,
                        "This recording is very quiet. Any studio preset will bring it up to a normal level.",
                        StudioPresetIds.CLEAN_VOICE,
                    )
                }
                lufs < -24 -> score -= 5
                lufs > -9 -> {
                    score -= 8
                    findings += QualityFinding(
                        QualityFinding.Severity.WARNING,
                        "This recording is unusually loud, which leaves no room for mastering.",
                    )
                }
            }
        } else {
            score -= 40
            findings += QualityFinding(
                QualityFinding.Severity.PROBLEM,
                "SAJJIL could not find any audio in this recording. Check that the microphone was working.",
            )
        }

        if (measurement.truePeakDb > -0.1) {
            score -= 6
            findings += QualityFinding(
                QualityFinding.Severity.INFO,
                "Peaks are right at the ceiling. Exporting with a limiter will keep them safe.",
            )
        }

        // A very wide loudness range on speech usually means the speaker moved relative to the mic.
        if (measurement.loudnessRange > 20) {
            score -= 8
            findings += QualityFinding(
                QualityFinding.Severity.WARNING,
                "The level moves around a lot. Podcast evens this out.",
                StudioPresetIds.PODCAST,
            )
        }

        if (findings.none { it.severity != QualityFinding.Severity.INFO }) {
            findings += QualityFinding(
                QualityFinding.Severity.INFO,
                "This is a clean recording. No repair needed.",
            )
        }

        return QualityReport(
            score = score.coerceIn(0.0, 100.0).roundToInt(),
            noiseFloorDb = noiseFloorDb,
            signalToNoiseDb = signalToNoiseDb,
            integratedLufs = lufs,
            truePeakDb = measurement.truePeakDb,
            clippedSampleCount = clipped,
            findings = findings,
        )
    }

    /** RMS of successive 50 ms windows, which is long enough to average out a single syllable. */
    private fun rmsWindows(buffer: AudioBuffer): DoubleArray {
        val windowSamples = (sampleRate * 0.05).toInt().coerceAtLeast(1)
        val count = (buffer.frameCount + windowSamples - 1) / windowSamples
        val out = DoubleArray(count)
        for (w in 0 until count) {
            val from = w * windowSamples
            val until = minOf(from + windowSamples, buffer.frameCount)
            var sum = 0.0
            var n = 0
            for (channel in buffer.channels) {
                for (i in from until until) {
                    val v = channel[i].toDouble()
                    sum += v * v
                    n++
                }
            }
            out[w] = if (n == 0) 0.0 else sqrt(sum / n)
        }
        return out
    }

    private fun percentile(values: DoubleArray, fraction: Double): Double {
        if (values.isEmpty()) return 0.0
        val sorted = values.clone()
        sorted.sort()
        val index = ((sorted.size - 1) * fraction).roundToInt().coerceIn(0, sorted.size - 1)
        return sorted[index]
    }

    private fun countClipped(buffer: AudioBuffer): Int {
        val threshold = dbToLinear(-0.05).toFloat()
        var count = 0
        for (channel in buffer.channels) {
            var run = 0
            for (sample in channel) {
                if (abs(sample) >= threshold) {
                    run++
                } else {
                    // Only runs of consecutive pinned samples count; one loud sample is a peak,
                    // not clipping, and counting it would flag every well-recorded file.
                    if (run >= 3) count += run
                    run = 0
                }
            }
            if (run >= 3) count += run
        }
        return count
    }
}

/**
 * Above this level, the tenth-percentile window is not a noise floor — it is simply more signal.
 * Real recorded noise floors sit well below it even in poor conditions.
 */
private const val MEASURABLE_NOISE_FLOOR_DB = -30.0

/** Preset identifiers referenced by analysis findings, kept in one place. */
object StudioPresetIds {
    const val CLEAN_VOICE = "clean_voice"
    const val STUDIO_VOICE = "studio_voice"
    const val PODCAST = "podcast"
    const val LECTURE = "lecture"
    const val PRESTIGE_RECITATION = "prestige_recitation"
}
