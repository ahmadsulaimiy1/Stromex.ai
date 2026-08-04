package ai.sajjil.audio.dsp

import ai.sajjil.audio.AudioBuffer
import ai.sajjil.audio.TestSignals
import ai.sajjil.audio.dbToLinear
import ai.sajjil.audio.linearToDb
import kotlin.math.abs
import kotlin.test.Test
import kotlin.test.assertTrue

class CompressorTest {

    private val sampleRate = 48000

    @Test
    fun `signal below the threshold is untouched`() {
        val signal = TestSignals.sineAtDbfs(1000.0, -40.0, 1.0, sampleRate)
        val original = signal.copy()
        Compressor(sampleRate, CompressorSettings(thresholdDb = -20.0, ratio = 4.0, kneeDb = 0.0))
            .process(signal)
        assertTrue(
            TestSignals.maxAbsoluteDifference(original, signal) < 1e-6,
            "a -40 dB signal must pass a -20 dB threshold untouched",
        )
    }

    @Test
    fun `above the threshold gain reduction follows the ratio`() {
        // 12 dB over a -30 dB threshold at 4:1 should come out 9 dB lower, i.e. 3 dB over.
        val signal = TestSignals.sineAtDbfs(1000.0, -18.0, 3.0, sampleRate)
        Compressor(
            sampleRate,
            CompressorSettings(
                thresholdDb = -30.0, ratio = 4.0, kneeDb = 0.0,
                attackMs = 1.0, releaseMs = 50.0,
            ),
        ).process(signal)

        // Measure once the envelope has settled.
        val settled = signal.slice(sampleRate, signal.frameCount)
        val outputDb = linearToDb(settled.peak().toDouble())
        assertTrue(
            abs(outputDb - (-27.0)) < 1.0,
            "expected about -27 dBFS out, got $outputDb dBFS",
        )
    }

    @Test
    fun `a soft knee compresses gradually instead of switching on`() {
        val hard = CompressorSettings(thresholdDb = -20.0, ratio = 4.0, kneeDb = 0.0)
        val soft = CompressorSettings(thresholdDb = -20.0, ratio = 4.0, kneeDb = 12.0)

        // Just below the threshold, a soft knee is already working and a hard knee is not.
        val level = -23.0
        val hardOut = compressPeakDb(level, hard)
        val softOut = compressPeakDb(level, soft)

        assertTrue(abs(hardOut - level) < 0.3, "a hard knee should not act below the threshold")
        assertTrue(softOut < level - 0.2, "a soft knee should already be reducing gain here")
    }

    @Test
    fun `makeup gain is applied`() {
        val signal = TestSignals.sineAtDbfs(1000.0, -40.0, 1.0, sampleRate)
        Compressor(
            sampleRate,
            CompressorSettings(thresholdDb = -10.0, ratio = 2.0, makeupGainDb = 6.0),
        ).process(signal)
        val outputDb = linearToDb(signal.slice(sampleRate / 2, signal.frameCount).peak().toDouble())
        assertTrue(abs(outputDb - (-34.0)) < 0.5, "expected -34 dBFS after 6 dB makeup, got $outputDb")
    }

    private fun compressPeakDb(inputDb: Double, settings: CompressorSettings): Double {
        val signal = TestSignals.sineAtDbfs(1000.0, inputDb, 3.0, sampleRate)
        Compressor(sampleRate, settings.copy(attackMs = 1.0, releaseMs = 50.0)).process(signal)
        return linearToDb(signal.slice(sampleRate, signal.frameCount).peak().toDouble())
    }
}

class LimiterTest {

    private val sampleRate = 48000

    @Test
    fun `nothing gets past the ceiling`() {
        for (ceiling in listOf(-0.5, -1.0, -3.0, -6.0)) {
            val signal = TestSignals.sine(500.0, 2.0, sampleRate, amplitude = 0.99)
            Limiter(sampleRate, LimiterSettings(ceilingDb = ceiling)).process(signal)
            val peakDb = linearToDb(signal.peak().toDouble())
            assertTrue(
                peakDb <= ceiling + 0.01,
                "with a $ceiling dB ceiling the output peaked at $peakDb dB",
            )
        }
    }

    @Test
    fun `quiet material passes through unchanged apart from the lookahead delay`() {
        val signal = TestSignals.sineAtDbfs(1000.0, -20.0, 1.0, sampleRate)
        val original = signal.copy()
        val limiter = Limiter(sampleRate, LimiterSettings(ceilingDb = -1.0, lookaheadMs = 5.0))
        limiter.process(signal)

        val delay = limiter.latencySamples
        // Compare the delayed output against the original, skipping the priming region.
        var worst = 0.0
        for (i in delay + 100 until signal.frameCount) {
            worst = maxOf(worst, abs(signal[0][i] - original[0][i - delay]).toDouble())
        }
        assertTrue(worst < 1e-6, "quiet audio should survive the limiter intact, worst diff $worst")
    }

    @Test
    fun `a transient is caught rather than clipped`() {
        // Quiet throughout with one loud spike: the look-ahead should have the gain down before
        // the spike arrives, so nothing is squared off.
        val frames = sampleRate
        val data = FloatArray(frames) { 0.05f }
        for (i in frames / 2 until frames / 2 + 50) data[i] = 0.98f
        val signal = AudioBuffer(sampleRate, arrayOf(data))

        Limiter(sampleRate, LimiterSettings(ceilingDb = -6.0, lookaheadMs = 5.0)).process(signal)
        val ceiling = dbToLinear(-6.0).toFloat()
        assertTrue(signal.peak() <= ceiling + 1e-4, "the transient was not contained")
    }
}

class NoiseGateTest {

    private val sampleRate = 48000

    @Test
    fun `loud material passes and quiet material is pulled down`() {
        val signal = TestSignals.burstsAndSilence(
            burstSeconds = 0.5, silenceSeconds = 0.5, repeats = 3, sampleRate = sampleRate,
        )
        // A little noise in the gaps, which is what a gate is actually for.
        val noise = TestSignals.noise(signal.durationSeconds, sampleRate, amplitude = 0.004)
        for (i in 0 until signal.frameCount) signal[0][i] += noise[0][i]

        NoiseGate(
            sampleRate,
            GateSettings(thresholdDb = -40.0, rangeDb = -24.0, releaseMs = 60.0),
        ).process(signal)

        // Mid-burst should be essentially intact.
        val burstPeak = signal.slice((0.2 * sampleRate).toInt(), (0.4 * sampleRate).toInt()).peak()
        assertTrue(burstPeak > 0.4, "the gate closed on real signal, peak was $burstPeak")

        // Deep inside a gap the noise should be well down.
        val gapRms = signal.slice((0.85 * sampleRate).toInt(), (0.95 * sampleRate).toInt()).rms()
        assertTrue(gapRms < 0.0015, "noise in the gap was not reduced, RMS $gapRms")
    }

    @Test
    fun `hysteresis stops the gate chattering at the threshold`() {
        // A signal parked exactly at the threshold would flap a gate without hysteresis.
        val signal = TestSignals.sineAtDbfs(300.0, -40.0, 2.0, sampleRate)
        NoiseGate(sampleRate, GateSettings(thresholdDb = -40.0, hysteresisDb = 6.0)).process(signal)

        // Count how often the envelope crosses the halfway mark; chatter shows up as many crossings.
        val settled = signal.slice(sampleRate / 2, signal.frameCount)
        var transitions = 0
        var wasLoud = false
        val window = 480
        var i = 0
        while (i + window < settled.frameCount) {
            val rms = settled.slice(i, i + window).rms()
            val loud = rms > dbToLinear(-46.0)
            if (loud != wasLoud) transitions++
            wasLoud = loud
            i += window
        }
        assertTrue(transitions <= 2, "the gate chattered $transitions times")
    }
}

class DeEsserTest {

    @Test
    fun `sibilance is reduced while the fundamental is left alone`() {
        val sampleRate = 48000
        // A low tone plus a strong 7 kHz "ess".
        val low = TestSignals.sine(200.0, 2.0, sampleRate, amplitude = 0.3)
        val sibilant = TestSignals.sine(7000.0, 2.0, sampleRate, amplitude = 0.3)
        for (i in 0 until low.frameCount) low[0][i] += sibilant[0][i]

        val before = bandEnergy(low, sampleRate, 7000.0)
        val lowBefore = bandEnergy(low, sampleRate, 200.0)

        DeEsser(sampleRate, DeEsserSettings(frequencyHz = 7000.0, thresholdDb = -30.0, rangeDb = 10.0))
            .process(low)

        val after = bandEnergy(low, sampleRate, 7000.0)
        val lowAfter = bandEnergy(low, sampleRate, 200.0)

        assertTrue(after < before * 0.6, "sibilance was not reduced ($before -> $after)")
        assertTrue(
            lowAfter > lowBefore * 0.8,
            "the de-esser ducked the whole signal instead of the sibilant band",
        )
    }

    private fun bandEnergy(buffer: AudioBuffer, sampleRate: Int, frequency: Double): Double {
        val filtered = buffer.copy()
        Biquad(BiquadDesign.bandPass(frequency, sampleRate, q = 4.0)).process(filtered[0])
        return filtered.slice(sampleRate / 2, filtered.frameCount).rms()
    }
}

class StereoWidenerTest {

    @Test
    fun `width of one changes nothing`() {
        val signal = TestSignals.sine(440.0, 0.2, 48000, channels = 2)
        val original = signal.copy()
        StereoWidener.process(signal, 1.0)
        assertTrue(TestSignals.maxAbsoluteDifference(original, signal) < 1e-9)
    }

    @Test
    fun `width of zero collapses to mono`() {
        val sampleRate = 48000
        val left = TestSignals.sine(440.0, 0.2, sampleRate)[0]
        val right = TestSignals.sine(660.0, 0.2, sampleRate)[0]
        val signal = AudioBuffer(sampleRate, arrayOf(left, right))

        StereoWidener.process(signal, 0.0)

        for (i in 0 until signal.frameCount) {
            assertTrue(abs(signal[0][i] - signal[1][i]) < 1e-6, "channels should be identical at width 0")
        }
    }

    @Test
    fun `widening increases the difference between channels`() {
        val sampleRate = 48000
        val signal = AudioBuffer(
            sampleRate,
            arrayOf(TestSignals.sine(440.0, 0.2, sampleRate)[0], TestSignals.sine(660.0, 0.2, sampleRate)[0]),
        )
        val sideBefore = sideEnergy(signal)
        StereoWidener.process(signal, 1.8)
        assertTrue(sideEnergy(signal) > sideBefore * 1.5, "widening did not increase the side signal")
    }

    private fun sideEnergy(buffer: AudioBuffer): Double {
        var sum = 0.0
        for (i in 0 until buffer.frameCount) {
            val side = (buffer[0][i] - buffer[1][i]) / 2.0
            sum += side * side
        }
        return sum
    }
}
