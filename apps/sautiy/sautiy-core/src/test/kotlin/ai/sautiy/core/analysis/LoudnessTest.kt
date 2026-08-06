package ai.sautiy.core.analysis

import ai.sautiy.core.TestSignals
import ai.sautiy.core.audio.AudioBuffer
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * ITU-R BS.1770-4 conformance.
 *
 * The reference points here come from the standard itself: a −20 dBFS 1 kHz sine, applied to
 * one channel, must read **−23.0 LUFS**. That single number exercises the K-weighting, the
 * block gating and the loudness equation together, and an implementation that gets it right is
 * an implementation a broadcaster can be held to.
 */
class LoudnessTest {

    private val rate = 48_000

    @Test
    fun `a minus twenty dBFS thousand hertz tone reads minus twenty three LUFS`() {
        val tone = TestSignals.sine(1_000.0, 10.0, rate, amplitude = 0.1)
        assertEquals(
            "BS.1770-4 reference: the anchor of the entire measurement",
            -23.0,
            Loudness.integrated(tone),
            0.15,
        )
    }

    @Test
    fun `the reference holds at other sample rates`() {
        // BS.1770 tabulates coefficients at 48 kHz only. Reusing those numbers at 44.1 kHz —
        // which a lot of code does — silently mis-weights the measurement.
        for (sampleRate in listOf(44_100, 32_000, 96_000)) {
            val tone = TestSignals.sine(1_000.0, 10.0, sampleRate, amplitude = 0.1)
            assertEquals(
                "At $sampleRate Hz the K-weighting must be re-derived, not reused",
                -23.0,
                Loudness.integrated(tone),
                0.3,
            )
        }
    }

    @Test
    fun `doubling the amplitude raises loudness by six decibels`() {
        val quiet = TestSignals.sine(1_000.0, 8.0, rate, amplitude = 0.1)
        val loud = TestSignals.sine(1_000.0, 8.0, rate, amplitude = 0.2)
        assertEquals(6.02, Loudness.integrated(loud) - Loudness.integrated(quiet), 0.05)
    }

    @Test
    fun `stereo reads three decibels louder than the same signal in mono`() {
        // Two coherent channels sum to twice the power, which is +3 dB.
        val mono = TestSignals.sine(1_000.0, 8.0, rate, amplitude = 0.1, channels = 1)
        val stereo = TestSignals.sine(1_000.0, 8.0, rate, amplitude = 0.1, channels = 2)
        assertEquals(3.01, Loudness.integrated(stereo) - Loudness.integrated(mono), 0.1)
    }

    @Test
    fun `gating stops silence between sentences from dragging the average down`() {
        // This is the clause naive implementations omit, and the reason their numbers are wrong.
        val speech = TestSignals.sine(1_000.0, 6.0, rate, amplitude = 0.1)
        val silence = TestSignals.silence(20.0, rate)
        val withGaps = AudioBuffer.concat(listOf(speech, silence, speech, silence))

        val speechOnly = Loudness.integrated(speech)
        val withSilence = Loudness.integrated(withGaps)

        assertEquals(
            "Twenty-second gaps must not change the programme loudness",
            speechOnly,
            withSilence,
            0.4,
        )
    }

    @Test
    fun `a passage more than ten LU below the rest is gated out`() {
        val loud = TestSignals.sine(1_000.0, 8.0, rate, amplitude = 0.2)
        val veryQuiet = TestSignals.sine(1_000.0, 8.0, rate, amplitude = 0.01)
        val mixed = AudioBuffer.concat(listOf(loud, veryQuiet))

        assertEquals(
            "The quiet passage sits below the relative gate and must not count",
            Loudness.integrated(loud),
            Loudness.integrated(mixed),
            0.4,
        )
    }

    @Test
    fun `digital silence reads as negative infinity rather than a number`() {
        assertFalse(Loudness.integrated(TestSignals.silence(5.0, rate)).isFinite())
    }

    @Test
    fun `material shorter than one block is reported as unmeasurable, not guessed`() {
        val tiny = TestSignals.sine(1_000.0, 0.1, rate)
        assertFalse(Loudness.integrated(tiny).isFinite())
    }

    @Test
    fun `true peak sees between the samples where a sample meter cannot`() {
        // A tone at a frequency that never lands on a sample maximum reads low on a sample
        // meter and can still clip a consumer converter. This is why delivery specifications
        // are written in dBTP.
        val awkward = TestSignals.sine(11_999.0, 1.0, rate, amplitude = 0.98, phase = 0.7)
        val samplePeakDb = ai.sautiy.core.audio.Decibels.fromLinear(awkward.peak().toDouble())
        val truePeakDb = Loudness.truePeakDb(awkward)

        assertTrue(
            "True peak $truePeakDb must be at least the sample peak $samplePeakDb",
            truePeakDb >= samplePeakDb - 0.01,
        )
        assertTrue("True peak should exceed the sample peak on inter-sample material", truePeakDb > samplePeakDb)
    }

    @Test
    fun `loudness range separates even material from dynamic material`() {
        val even = TestSignals.sine(1_000.0, 20.0, rate, amplitude = 0.1)
        val dynamic = AudioBuffer.concat(
            listOf(
                TestSignals.sine(1_000.0, 5.0, rate, amplitude = 0.3),
                TestSignals.sine(1_000.0, 5.0, rate, amplitude = 0.05),
                TestSignals.sine(1_000.0, 5.0, rate, amplitude = 0.3),
                TestSignals.sine(1_000.0, 5.0, rate, amplitude = 0.05),
            ),
        )
        assertTrue("Constant material has no range", Loudness.loudnessRange(even) < 1.0)
        assertTrue(
            "Dynamic material must show a range: got ${Loudness.loudnessRange(dynamic)} LU",
            Loudness.loudnessRange(dynamic) > 8.0,
        )
    }

    @Test
    fun `a normalisation plan reaches the target when there is headroom`() {
        val quiet = TestSignals.sine(1_000.0, 10.0, rate, amplitude = 0.02)
        val plan = Loudness.planNormalisation(quiet, Loudness.Target.PODCAST)

        assertTrue("A quiet recording must be turned up", plan.gainDb > 5.0)
        assertFalse(plan.limitedByTruePeak)
        assertEquals(Loudness.Target.PODCAST.lufs, plan.achievedLufs, 0.2)
    }

    @Test
    fun `a normalisation plan stops at the ceiling and says so`() {
        // Returning a gain that would clip and leaving the caller to notice is how loudness
        // normalisation ends up distorting the material it was meant to fix.
        val hot = TestSignals.sine(1_000.0, 10.0, rate, amplitude = 0.95)
        val plan = Loudness.planNormalisation(hot, Loudness.Target.STREAMING)

        assertTrue("This material is already too loud for its target", plan.gainDb < 0.0)
        val verify = hot.copy().applyGain(Math.pow(10.0, plan.gainDb / 20.0).toFloat())
        assertTrue(
            "The plan must keep the true peak under the ceiling",
            Loudness.truePeakDb(verify) <= Loudness.Target.STREAMING.truePeakCeilingDb + 0.1,
        )
    }

    @Test
    fun `the shortfall is reported so a limiter can be offered instead of a wrong number`() {
        val peaky = AudioBuffer.mono(
            FloatArray(rate * 8).also { samples ->
                for (i in samples.indices) {
                    samples[i] = (0.02 * kotlin.math.sin(2 * Math.PI * 1_000 * i / rate)).toFloat()
                }
                // One very short, very loud transient: quiet programme, no headroom.
                for (i in 1_000 until 1_050) samples[i] = 0.99f
            },
            rate,
        )
        val plan = Loudness.planNormalisation(peaky, Loudness.Target.PODCAST)
        assertTrue("This is exactly the case where the two constraints conflict", plan.limitedByTruePeak)
        assertTrue("The shortfall must be stated, not hidden", plan.shortfallDb > 0.0)
    }

    @Test
    fun `peak normalisation hits its target exactly`() {
        val quiet = TestSignals.sine(440.0, 1.0, rate, amplitude = 0.1)
        val gain = Loudness.peakNormalisationGain(quiet, targetDb = -1.0)
        quiet.applyGain(Math.pow(10.0, gain / 20.0).toFloat())
        assertEquals(-1.0, ai.sautiy.core.audio.Decibels.fromLinear(quiet.peak().toDouble()), 0.05)
    }

    @Test
    fun `crest factor distinguishes a sine from a transient`() {
        val sine = TestSignals.sine(1_000.0, 1.0, rate, amplitude = 0.5)
        assertEquals("A sine's crest factor is 3.01 dB", 3.01, Loudness.crestFactorDb(sine), 0.1)

        val spiky = AudioBuffer.mono(FloatArray(rate).also { it[100] = 1.0f }, rate)
        assertTrue("A lone transient is very peaky", Loudness.crestFactorDb(spiky) > 40.0)
    }

    @Test
    fun `a full measurement reports every number the analysis panel shows`() {
        val material = TestSignals.sine(1_000.0, 10.0, rate, amplitude = 0.15)
        val measurement = Loudness.measure(material)

        assertTrue(measurement.integratedLufs.isFinite())
        assertTrue(measurement.truePeakDb.isFinite())
        assertTrue(measurement.momentaryMaxLufs.isFinite())
        assertTrue(measurement.shortTermMaxLufs.isFinite())
        assertTrue(measurement.loudnessRangeLu >= 0.0)

        val gain = measurement.gainToReach(Loudness.Target.PODCAST)
        assertEquals(Loudness.Target.PODCAST.lufs, measurement.integratedLufs + gain, 1e-9)
    }

    @Test
    fun `every delivery target is plausible and has real headroom`() {
        for (target in Loudness.Target.entries) {
            assertTrue("${target.displayName} loudness", target.lufs in -30.0..-10.0)
            assertTrue("${target.displayName} ceiling", target.truePeakCeilingDb in -3.0..0.0)
            assertTrue(target.displayName.isNotBlank())
        }
    }
}
