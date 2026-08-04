package ai.sajjil.audio.loudness

import ai.sajjil.audio.AudioBuffer
import ai.sajjil.audio.TestSignals
import ai.sajjil.audio.linearToDb
import kotlin.math.abs
import kotlin.test.Test
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertTrue

/**
 * The numeric expectations here come from EBU Tech 3341's compliance test cases, which state the
 * reading a conforming BS.1770 meter must produce for a given signal. They are the reason this
 * meter can be trusted to hit an export loudness target rather than merely being self-consistent.
 */
class LoudnessMeterTest {

    private val sampleRate = 48000

    @Test
    fun `K-weighting matches the tabulated 48 kHz coefficients`() {
        // BS.1770-4 tabulates these for 48 kHz. Deriving them from the analog prototype must
        // reproduce them exactly, which is what proves the derivation is right at other rates too.
        val shelf = KWeighting.shelf(48000)
        assertClose(1.53512485958697, shelf.b0, 1e-12, "shelf b0")
        assertClose(-2.69169618940638, shelf.b1, 1e-12, "shelf b1")
        assertClose(1.19839281085285, shelf.b2, 1e-12, "shelf b2")
        assertClose(-1.69065929318241, shelf.a1, 1e-12, "shelf a1")
        assertClose(0.73248077421585, shelf.a2, 1e-12, "shelf a2")

        val highPass = KWeighting.highPass(48000)
        assertClose(1.0, highPass.b0, 1e-12, "high-pass b0")
        assertClose(-2.0, highPass.b1, 1e-12, "high-pass b1")
        assertClose(1.0, highPass.b2, 1e-12, "high-pass b2")
        assertClose(-1.99004745483398, highPass.a1, 1e-9, "high-pass a1")
        assertClose(0.99007225036621, highPass.a2, 1e-9, "high-pass a2")
    }

    @Test
    fun `EBU 3341 case 1 - a stereo 1 kHz sine at -23 dBFS reads -23 LUFS`() {
        val signal = TestSignals.sineAtDbfs(1000.0, -23.0, seconds = 20.0, sampleRate = sampleRate, channels = 2)
        val measured = LoudnessMeter(sampleRate).measureIntegrated(signal)
        assertNotNull(measured)
        assertClose(-23.0, measured, 0.1, "integrated loudness")
    }

    @Test
    fun `EBU 3341 case 2 - the same signal at -33 dBFS reads -33 LUFS`() {
        val signal = TestSignals.sineAtDbfs(1000.0, -33.0, seconds = 20.0, sampleRate = sampleRate, channels = 2)
        val measured = LoudnessMeter(sampleRate).measureIntegrated(signal)
        assertNotNull(measured)
        assertClose(-33.0, measured, 0.1, "integrated loudness")
    }

    @Test
    fun `loudness tracks amplitude decibel for decibel`() {
        val quiet = TestSignals.sineAtDbfs(1000.0, -30.0, 12.0, sampleRate, channels = 2)
        val loud = TestSignals.sineAtDbfs(1000.0, -18.0, 12.0, sampleRate, channels = 2)
        val quietLufs = LoudnessMeter(sampleRate).measureIntegrated(quiet)!!
        val loudLufs = LoudnessMeter(sampleRate).measureIntegrated(loud)!!
        assertClose(12.0, loudLufs - quietLufs, 0.05, "a 12 dB amplitude change")
    }

    @Test
    fun `measurement is correct at 44_1 kHz as well as 48`() {
        // The whole point of deriving K-weighting per sample rate: the reading must not shift.
        val at48 = LoudnessMeter(48000)
            .measureIntegrated(TestSignals.sineAtDbfs(1000.0, -23.0, 12.0, 48000, channels = 2))!!
        val at441 = LoudnessMeter(44100)
            .measureIntegrated(TestSignals.sineAtDbfs(1000.0, -23.0, 12.0, 44100, channels = 2))!!
        assertClose(at48, at441, 0.1, "loudness across sample rates")
    }

    @Test
    fun `the relative gate ignores silence between speech`() {
        // Real speech is mostly pauses. Without the relative gate, a recording that is half
        // silence would measure roughly 3 LU quieter than it sounds.
        val speech = TestSignals.sineAtDbfs(1000.0, -20.0, 4.0, sampleRate, channels = 2)
        val silence = AudioBuffer.silence(sampleRate, 2, sampleRate * 4)
        val mixed = AudioBuffer.concat(listOf(speech, silence, speech, silence, speech))

        val continuous = LoudnessMeter(sampleRate).measureIntegrated(speech)!!
        val gapped = LoudnessMeter(sampleRate).measureIntegrated(mixed)!!
        assertClose(continuous, gapped, 0.5, "gating should make these read alike")
    }

    @Test
    fun `digital silence has no integrated loudness rather than a fake number`() {
        val silence = AudioBuffer.silence(sampleRate, 1, sampleRate * 5)
        assertNull(LoudnessMeter(sampleRate).measureIntegrated(silence))
    }

    @Test
    fun `loudness range is near zero for a steady tone and wide for a varying one`() {
        val steady = TestSignals.sineAtDbfs(1000.0, -20.0, 20.0, sampleRate, channels = 2)
        assertTrue(
            LoudnessMeter(sampleRate).measure(steady).loudnessRange < 1.0,
            "a constant tone should have almost no loudness range",
        )

        val varying = AudioBuffer.concat(
            listOf(
                TestSignals.sineAtDbfs(1000.0, -12.0, 10.0, sampleRate, channels = 2),
                TestSignals.sineAtDbfs(1000.0, -34.0, 10.0, sampleRate, channels = 2),
            )
        )
        assertTrue(
            LoudnessMeter(sampleRate).measure(varying).loudnessRange > 10.0,
            "a signal swinging 22 dB should report a wide loudness range",
        )
    }
}

class TruePeakTest {

    @Test
    fun `true peak of a full scale sine is close to zero dBFS`() {
        val signal = TestSignals.sine(1000.0, 1.0, 48000, amplitude = 1.0)
        val peak = TruePeak.measureDb(signal)
        assertTrue(abs(peak) < 0.5, "expected about 0 dBTP for a full-scale sine, got $peak")
    }

    @Test
    fun `true peak finds overshoot that sample peak misses`() {
        // A 12 kHz tone at 48 kHz samples only four times per cycle. Phase-shifted so no sample
        // lands on a crest, the sample peak reads low while the reconstructed waveform does not.
        val sampleRate = 48000
        val frames = sampleRate
        val data = FloatArray(frames) {
            (0.95 * kotlin.math.sin(2 * Math.PI * 12000 * it / sampleRate + Math.PI / 4)).toFloat()
        }
        val signal = AudioBuffer(sampleRate, arrayOf(data))

        val samplePeakDb = linearToDb(signal.peak().toDouble())
        val truePeakDb = TruePeak.measureDb(signal)

        assertTrue(
            truePeakDb > samplePeakDb + 1.5,
            "true peak ($truePeakDb dB) should exceed sample peak ($samplePeakDb dB) here",
        )
    }

    @Test
    fun `silence reports no peak instead of failing`() {
        val silence = AudioBuffer.silence(48000, 1, 1000)
        assertTrue(TruePeak.measureDb(silence) < -100.0)
    }
}

class LoudnessNormalizerTest {

    private val sampleRate = 48000

    @Test
    fun `normalising hits the requested target`() {
        for (target in listOf(-23.0, -18.0, -16.0, -14.0)) {
            val signal = TestSignals.sineAtDbfs(1000.0, -35.0, 12.0, sampleRate, channels = 2)
            val result = LoudnessNormalizer(sampleRate).normalize(signal, targetLufs = target)
            val after = result.measuredAfterLufs
            assertNotNull(after, "normalisation should report a measurement")
            assertClose(target, after, 0.3, "loudness after normalising to $target")
        }
    }

    @Test
    fun `the true peak ceiling wins when the loudness target demands more headroom`() {
        // A sine's loudness and its peak level track each other, so normalising to -10 LUFS puts
        // peaks near -10 dBFS. Asking for that under a -16 dB ceiling forces the conflict the
        // limiter exists to resolve, and the ceiling must be what survives it.
        val signal = TestSignals.sineAtDbfs(1000.0, -30.0, 12.0, sampleRate, channels = 2)
        val result = LoudnessNormalizer(sampleRate)
            .normalize(signal, targetLufs = -10.0, truePeakCeilingDb = -16.0)

        assertTrue(result.appliedGainDb > 15.0, "the target should have called for real gain")
        assertTrue(result.limiterEngaged, "the limiter should have engaged")
        val peak = linearToDb(signal.peak().toDouble())
        assertTrue(peak <= -16.0 + 0.05, "sample peak $peak dB exceeded the -16 dB ceiling")
    }

    @Test
    fun `a comfortable ceiling leaves the limiter out of the path entirely`() {
        val signal = TestSignals.sineAtDbfs(1000.0, -30.0, 12.0, sampleRate, channels = 2)
        val result = LoudnessNormalizer(sampleRate)
            .normalize(signal, targetLufs = -20.0, truePeakCeilingDb = -1.0)

        assertTrue(!result.limiterEngaged, "nothing approached the ceiling, so nothing should limit")
        assertClose(-20.0, result.measuredAfterLufs!!, 0.3, "loudness after normalising")
    }

    @Test
    fun `gain is bounded so silence is not amplified into noise`() {
        val nearlySilent = TestSignals.sineAtDbfs(1000.0, -80.0, 12.0, sampleRate, channels = 2)
        val result = LoudnessNormalizer(sampleRate)
            .normalize(nearlySilent, targetLufs = -16.0, maximumGainDb = 24.0)
        assertTrue(
            result.appliedGainDb <= 24.0 + 1e-9,
            "applied ${result.appliedGainDb} dB, more than the 24 dB limit",
        )
    }

    @Test
    fun `silence is left alone rather than crashing`() {
        val silence = AudioBuffer.silence(sampleRate, 1, sampleRate)
        val result = LoudnessNormalizer(sampleRate).normalize(silence)
        assertTrue(result.appliedGainDb == 0.0)
        assertTrue(silence.peak() == 0f)
    }
}

internal fun assertClose(expected: Double, actual: Double, tolerance: Double, what: String) {
    assertTrue(
        abs(expected - actual) <= tolerance,
        "$what: expected $expected but was $actual (tolerance $tolerance)",
    )
}
