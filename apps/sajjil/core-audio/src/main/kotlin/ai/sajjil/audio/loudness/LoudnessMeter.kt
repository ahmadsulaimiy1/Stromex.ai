package ai.sajjil.audio.loudness

import ai.sajjil.audio.AudioBuffer
import ai.sajjil.audio.dbToLinear
import ai.sajjil.audio.dsp.BiquadCoefficients
import ai.sajjil.audio.dsp.BiquadChain
import kotlin.math.PI
import kotlin.math.abs
import kotlin.math.log10
import kotlin.math.max
import kotlin.math.pow
import kotlin.math.sin
import kotlin.math.tan

/**
 * ITU-R BS.1770-4 K-weighting.
 *
 * Two cascaded biquads: a high-frequency shelf approximating the acoustic effect of the head,
 * then an RLB high-pass. The coefficients are derived from the standard's analog prototype at the
 * actual sample rate rather than hard-coded for 48 kHz, so metering is correct at 44.1 and 16 kHz
 * too — hard-coded 48 kHz coefficients silently misreport at every other rate, which is a common
 * bug in loudness implementations.
 */
object KWeighting {

    // Prototype constants from BS.1770-4.
    private const val SHELF_FREQUENCY = 1681.974450955533
    private const val SHELF_GAIN_DB = 3.999843853973347
    private const val SHELF_Q = 0.7071752369554196
    private const val HIGHPASS_FREQUENCY = 38.13547087602444
    private const val HIGHPASS_Q = 0.5003270373238773

    fun shelf(sampleRate: Int): BiquadCoefficients {
        val k = tan(PI * SHELF_FREQUENCY / sampleRate)
        val vh = 10.0.pow(SHELF_GAIN_DB / 20.0)
        val vb = vh.pow(0.4996667741545416)
        val a0 = 1.0 + k / SHELF_Q + k * k
        return BiquadCoefficients(
            b0 = (vh + vb * k / SHELF_Q + k * k) / a0,
            b1 = 2.0 * (k * k - vh) / a0,
            b2 = (vh - vb * k / SHELF_Q + k * k) / a0,
            a1 = 2.0 * (k * k - 1.0) / a0,
            a2 = (1.0 - k / SHELF_Q + k * k) / a0,
        )
    }

    fun highPass(sampleRate: Int): BiquadCoefficients {
        val k = tan(PI * HIGHPASS_FREQUENCY / sampleRate)
        val a0 = 1.0 + k / HIGHPASS_Q + k * k
        return BiquadCoefficients(
            b0 = 1.0,
            b1 = -2.0,
            b2 = 1.0,
            a1 = 2.0 * (k * k - 1.0) / a0,
            a2 = (1.0 - k / HIGHPASS_Q + k * k) / a0,
        )
    }

    fun chain(sampleRate: Int): BiquadChain =
        BiquadChain(listOf(shelf(sampleRate), highPass(sampleRate)))
}

/**
 * Loudness measurements for one buffer.
 *
 * @property integratedLufs gated integrated loudness, or null when the material never rises above
 *   the absolute gate (i.e. it is effectively silent) — null rather than a misleading number.
 * @property loudnessRange LRA in LU, the spread between the 10th and 95th percentile of
 *   short-term loudness. High values mean the recording swings between quiet and loud.
 * @property truePeakDb inter-sample peak in dBTP, measured on a 4x oversampled signal.
 */
data class LoudnessMeasurement(
    val integratedLufs: Double?,
    val shortTermMaxLufs: Double?,
    val momentaryMaxLufs: Double?,
    val loudnessRange: Double,
    val truePeakDb: Double,
    val samplePeakDb: Double,
)

/**
 * BS.1770-4 loudness meter with EBU R128 gating.
 *
 * Loudness is computed over overlapping 400 ms blocks, then gated twice: an absolute gate at
 * -70 LUFS drops silence, and a relative gate 10 LU below the ungated mean drops the quiet
 * passages that would otherwise drag a spoken-word recording's measured loudness far below what
 * a listener perceives.
 */
class LoudnessMeter(private val sampleRate: Int) {

    /** Per-channel weights G. L/R/C are 1.0; surround channels would be 1.41. */
    private fun weightFor(channelIndex: Int, channelCount: Int): Double =
        if (channelCount > 3 && channelIndex >= 3) 1.41 else 1.0

    fun measure(buffer: AudioBuffer): LoudnessMeasurement {
        val weighted = kWeight(buffer)
        val momentary = blockLoudness(weighted, buffer.channelCount, windowSeconds = 0.4, hopSeconds = 0.1)
        val shortTerm = blockLoudness(weighted, buffer.channelCount, windowSeconds = 3.0, hopSeconds = 1.0)

        return LoudnessMeasurement(
            integratedLufs = gatedIntegrated(momentary),
            shortTermMaxLufs = shortTerm.maxOfOrNull { it.loudness },
            momentaryMaxLufs = momentary.maxOfOrNull { it.loudness },
            loudnessRange = loudnessRange(shortTerm),
            truePeakDb = TruePeak.measureDb(buffer),
            samplePeakDb = 20.0 * log10(max(1e-12, buffer.peak().toDouble())),
        )
    }

    /** Integrated loudness only — cheaper when the caller just needs a normalisation target. */
    fun measureIntegrated(buffer: AudioBuffer): Double? {
        val weighted = kWeight(buffer)
        return gatedIntegrated(blockLoudness(weighted, buffer.channelCount, 0.4, 0.1))
    }

    private fun kWeight(buffer: AudioBuffer): Array<FloatArray> =
        Array(buffer.channelCount) { c ->
            val copy = buffer.channels[c].copyOf()
            KWeighting.chain(sampleRate).process(copy)
            copy
        }

    /** One gating block: its power sum across channels, and the loudness that implies. */
    private data class Block(val powerSum: Double, val loudness: Double)

    private fun blockLoudness(
        weighted: Array<FloatArray>,
        channelCount: Int,
        windowSeconds: Double,
        hopSeconds: Double,
    ): List<Block> {
        val windowSamples = (windowSeconds * sampleRate).toInt()
        val hopSamples = max(1, (hopSeconds * sampleRate).toInt())
        val length = weighted.firstOrNull()?.size ?: return emptyList()
        if (length < windowSamples) return emptyList()

        val blocks = ArrayList<Block>((length - windowSamples) / hopSamples + 1)
        var offset = 0
        while (offset + windowSamples <= length) {
            var powerSum = 0.0
            for (c in 0 until channelCount) {
                val channel = weighted[c]
                var sum = 0.0
                for (i in offset until offset + windowSamples) {
                    val v = channel[i].toDouble()
                    sum += v * v
                }
                powerSum += weightFor(c, channelCount) * (sum / windowSamples)
            }
            blocks += Block(powerSum, loudnessOf(powerSum))
            offset += hopSamples
        }
        return blocks
    }

    private fun loudnessOf(powerSum: Double): Double =
        if (powerSum <= 0.0) Double.NEGATIVE_INFINITY else -0.691 + 10.0 * log10(powerSum)

    private fun gatedIntegrated(blocks: List<Block>): Double? {
        if (blocks.isEmpty()) return null

        // Absolute gate at -70 LUFS removes silence.
        val aboveAbsolute = blocks.filter { it.loudness > ABSOLUTE_GATE_LUFS }
        if (aboveAbsolute.isEmpty()) return null

        // Relative gate sits 10 LU below the mean of what survived the absolute gate.
        val meanPower = aboveAbsolute.sumOf { it.powerSum } / aboveAbsolute.size
        val relativeGate = loudnessOf(meanPower) - RELATIVE_GATE_LU

        val aboveRelative = aboveAbsolute.filter { it.loudness > relativeGate }
        if (aboveRelative.isEmpty()) return null

        val gatedPower = aboveRelative.sumOf { it.powerSum } / aboveRelative.size
        return loudnessOf(gatedPower)
    }

    /** EBU R128 loudness range: the 10th-to-95th percentile spread of gated short-term loudness. */
    private fun loudnessRange(shortTerm: List<Block>): Double {
        val above = shortTerm.filter { it.loudness > ABSOLUTE_GATE_LUFS }
        if (above.size < 2) return 0.0
        val meanPower = above.sumOf { it.powerSum } / above.size
        val gate = loudnessOf(meanPower) - LRA_GATE_LU
        val values = above.map { it.loudness }.filter { it > gate }.sorted()
        if (values.size < 2) return 0.0
        val low = values[(values.size * 0.10).toInt().coerceIn(0, values.size - 1)]
        val high = values[(values.size * 0.95).toInt().coerceIn(0, values.size - 1)]
        return high - low
    }

    private companion object {
        const val ABSOLUTE_GATE_LUFS = -70.0
        const val RELATIVE_GATE_LU = 10.0
        const val LRA_GATE_LU = 20.0
    }
}

/**
 * Inter-sample (true) peak measurement per BS.1770-4 Annex 2.
 *
 * A signal can sit at -0.2 dBFS on every sample and still reconstruct to +0.5 dB between them,
 * which then clips in the listener's DAC or in a lossy encoder. Measuring the 4x oversampled
 * signal catches that; measuring raw sample peaks does not.
 */
object TruePeak {

    private const val OVERSAMPLE = 4
    private const val TAPS_PER_PHASE = 12

    // Windowed-sinc polyphase interpolator, built once.
    private val phases: Array<DoubleArray> = buildPhases()

    private fun buildPhases(): Array<DoubleArray> {
        val total = OVERSAMPLE * TAPS_PER_PHASE
        val kernel = DoubleArray(total)
        val centre = (total - 1) / 2.0
        for (i in 0 until total) {
            val x = (i - centre) / OVERSAMPLE
            val sinc = if (abs(x) < 1e-9) 1.0 else sin(PI * x) / (PI * x)
            // Blackman window keeps the stopband low enough that the interpolation does not
            // invent peaks of its own.
            val w = 2.0 * PI * i / (total - 1)
            val window = 0.42 - 0.5 * kotlin.math.cos(w) + 0.08 * kotlin.math.cos(2 * w)
            kernel[i] = sinc * window
        }
        // Each phase is normalised to unit sum. Without this the bank has the oversampling
        // factor's worth of gain built in and every true-peak reading is ~12 dB too high — which
        // looks plausible enough on a relative comparison to pass unnoticed.
        return Array(OVERSAMPLE) { phase ->
            val taps = DoubleArray(TAPS_PER_PHASE) { tap -> kernel[tap * OVERSAMPLE + phase] }
            val sum = taps.sum()
            if (abs(sum) > 1e-12) {
                for (i in taps.indices) taps[i] /= sum
            }
            taps
        }
    }

    fun measureDb(buffer: AudioBuffer): Double {
        var peak = 0.0
        for (channel in buffer.channels) {
            val channelPeak = channelTruePeak(channel)
            if (channelPeak > peak) peak = channelPeak
        }
        return 20.0 * log10(max(1e-12, peak))
    }

    private fun channelTruePeak(samples: FloatArray): Double {
        // Interpolating every sample costs 48 multiply-accumulates each, which is minutes of work
        // on a long recording. An inter-sample peak can only occur next to samples that are
        // already near the sample peak, so the filter only runs in those neighbourhoods. The
        // -6 dB gate is well below the ~3 dB of overshoot real audio can produce, so nothing that
        // matters is missed.
        var samplePeak = 0.0
        for (sample in samples) {
            val a = abs(sample.toDouble())
            if (a > samplePeak) samplePeak = a
        }
        if (samplePeak <= 0.0) return 0.0
        val gate = samplePeak * 0.5

        var peak = samplePeak
        var i = 0
        while (i < samples.size) {
            if (abs(samples[i]) < gate) {
                i++
                continue
            }
            // Evaluate a window covering the filter's span on both sides of the loud sample.
            val from = max(0, i - TAPS_PER_PHASE)
            val until = kotlin.math.min(samples.size, i + TAPS_PER_PHASE)
            for (j in from until until) {
                for (phase in phases) {
                    var acc = 0.0
                    for (tap in phase.indices) {
                        val index = j - tap
                        if (index >= 0) acc += samples[index] * phase[tap]
                    }
                    val a = abs(acc)
                    if (a > peak) peak = a
                }
            }
            i = until
        }
        return peak
    }
}

/**
 * Normalises a recording to a target integrated loudness while guaranteeing a true-peak ceiling.
 *
 * Gain is applied first, then a limiter catches anything the gain pushed over the ceiling. Doing
 * it the other way round would let the limiter's own gain reduction change the measured loudness
 * out from under the target.
 */
class LoudnessNormalizer(private val sampleRate: Int) {

    data class Result(
        val appliedGainDb: Double,
        val measuredBeforeLufs: Double?,
        val measuredAfterLufs: Double?,
        val limiterEngaged: Boolean,
        /**
         * True when the target was out of reach because it would have needed more than
         * [normalize]'s gain limit.
         *
         * This is surfaced rather than silently swallowed: a recording that arrived far too quiet
         * cannot be brought to a delivery target without also raising its noise floor to
         * something unusable, and the honest thing is to say so instead of pretending the target
         * was met.
         */
        val gainLimited: Boolean = false,
    )

    fun normalize(
        buffer: AudioBuffer,
        targetLufs: Double = -16.0,
        truePeakCeilingDb: Double = -1.0,
        maximumGainDb: Double = 30.0,
    ): Result {
        val meter = LoudnessMeter(sampleRate)
        val before = meter.measureIntegrated(buffer)
            ?: return Result(0.0, null, null, false)

        val requestedGainDb = targetLufs - before
        val desiredGainDb = requestedGainDb.coerceIn(-maximumGainDb, maximumGainDb)
        val gainLimited = abs(requestedGainDb - desiredGainDb) > 0.01
        buffer.applyGain(dbToLinear(desiredGainDb).toFloat())

        // Only engage the limiter if the gain actually pushed the signal over the ceiling.
        val peakAfterGain = TruePeak.measureDb(buffer)
        val limiterEngaged = peakAfterGain > truePeakCeilingDb
        if (limiterEngaged) {
            ai.sajjil.audio.dsp.Limiter(
                sampleRate,
                ai.sajjil.audio.dsp.LimiterSettings(ceilingDb = truePeakCeilingDb),
            ).process(buffer)
        }

        return Result(
            appliedGainDb = desiredGainDb,
            measuredBeforeLufs = before,
            measuredAfterLufs = meter.measureIntegrated(buffer),
            limiterEngaged = limiterEngaged,
            gainLimited = gainLimited,
        )
    }

    companion object {
        /** Common delivery targets, exposed in the export sheet. */
        const val TARGET_PODCAST = -16.0
        const val TARGET_BROADCAST_EBU = -23.0
        const val TARGET_STREAMING = -14.0
        const val TARGET_SPOKEN_WORD = -18.0
    }
}
