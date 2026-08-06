package ai.sautiy.core.dsp

import ai.sautiy.core.TestSignals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class ResamplerTest {

    @Test
    fun `converting 48k to 44_1k preserves a tone's frequency and amplitude`() {
        val source = TestSignals.sine(1_000.0, 0.5, 48_000, amplitude = 0.5)
        val converted = Resampler.resample(source, 44_100, Resampler.Quality.TRANSPARENT)

        assertEquals(44_100, converted.sampleRate)
        assertEquals("Duration must be preserved", 0.5, converted.durationSeconds, 0.001)

        val trimmed = TestSignals.trimEdges(converted, 2_000)
        assertEquals(
            "Amplitude drifted during conversion",
            0.5,
            TestSignals.magnitudeAt(trimmed, 1_000.0),
            0.01,
        )
    }

    @Test
    fun `downsampling rejects content above the new nyquist instead of aliasing it`() {
        // This is the test that separates a real resampler from a decimator. A 20 kHz tone
        // dropped from 48 kHz to 32 kHz has nowhere legitimate to go — a naive implementation
        // folds it to 12 kHz, straight into the most audible part of the spectrum.
        val source = TestSignals.sine(20_000.0, 0.5, 48_000, amplitude = 0.7)
        val converted = Resampler.resample(source, 32_000, Resampler.Quality.TRANSPARENT)
        val trimmed = TestSignals.trimEdges(converted, 3_000)

        val aliasDb = TestSignals.magnitudeDbAt(trimmed, 12_000.0)
        assertTrue(
            "20 kHz folded back to 12 kHz at $aliasDb dBFS — the anti-alias filter is not working",
            aliasDb < -60.0,
        )
    }

    @Test
    fun `content below the new nyquist passes through untouched`() {
        val source = TestSignals.sine(2_000.0, 0.5, 48_000, amplitude = 0.6)
        val converted = Resampler.resample(source, 24_000, Resampler.Quality.TRANSPARENT)
        val trimmed = TestSignals.trimEdges(converted, 2_000)

        assertEquals(0.6, TestSignals.magnitudeAt(trimmed, 2_000.0), 0.02)
    }

    @Test
    fun `upsampling introduces no image above the original nyquist`() {
        val source = TestSignals.sine(5_000.0, 0.5, 16_000, amplitude = 0.6)
        val converted = Resampler.resample(source, 48_000, Resampler.Quality.TRANSPARENT)
        val trimmed = TestSignals.trimEdges(converted, 3_000)

        assertEquals("Original tone must survive", 0.6, TestSignals.magnitudeAt(trimmed, 5_000.0), 0.02)
        val imageDb = TestSignals.magnitudeDbAt(trimmed, 11_000.0)
        assertTrue("Upsampling produced an image at 11 kHz at $imageDb dBFS", imageDb < -60.0)
    }

    @Test
    fun `a round trip through another rate stays clean in the voice band`() {
        val source = TestSignals.sine(800.0, 0.4, 48_000, amplitude = 0.5)
        val there = Resampler.resample(source, 44_100, Resampler.Quality.TRANSPARENT)
        val back = Resampler.resample(there, 48_000, Resampler.Quality.TRANSPARENT)

        val trimmed = TestSignals.trimEdges(back, 4_000)
        assertEquals(0.5, TestSignals.magnitudeAt(trimmed, 800.0), 0.01)

        // Anything that is not the original tone is distortion the user would hear.
        val distortionDb = maxOf(
            TestSignals.magnitudeDbAt(trimmed, 1_600.0),
            TestSignals.magnitudeDbAt(trimmed, 2_400.0),
        )
        assertTrue("Round trip generated harmonics at $distortionDb dBFS", distortionDb < -70.0)
    }

    @Test
    fun `converting to the same rate is a no-op that allocates nothing`() {
        val source = TestSignals.sine(440.0, 0.1, 48_000)
        assertTrue("Same-rate conversion must return the same instance", Resampler.resample(source, 48_000) === source)
    }

    @Test
    fun `stereo channels stay independent through conversion`() {
        val left = TestSignals.sine(1_000.0, 0.3, 48_000, amplitude = 0.5).channels[0]
        val right = TestSignals.sine(3_000.0, 0.3, 48_000, amplitude = 0.5).channels[0]
        val stereo = ai.sautiy.core.audio.AudioBuffer(arrayOf(left, right), 48_000)

        val converted = Resampler.resample(stereo, 24_000, Resampler.Quality.TRANSPARENT)
        val trimmed = TestSignals.trimEdges(converted, 1_500)

        assertEquals(0.5, TestSignals.magnitudeAt(trimmed, 1_000.0, channel = 0), 0.02)
        assertTrue(
            "The 1 kHz tone leaked into the right channel",
            TestSignals.magnitudeDbAt(trimmed, 1_000.0, channel = 1) < -60.0,
        )
        assertEquals(0.5, TestSignals.magnitudeAt(trimmed, 3_000.0, channel = 1), 0.02)
    }

    @Test
    fun `speed change shortens the material and raises the pitch, like tape`() {
        val source = TestSignals.sine(1_000.0, 1.0, 48_000, amplitude = 0.5)
        val faster = Resampler.changeSpeed(source, 2.0, Resampler.Quality.TRANSPARENT)

        assertEquals("Sample rate is unchanged by speed", 48_000, faster.sampleRate)
        assertEquals("Double speed halves the duration", 0.5, faster.durationSeconds, 0.001)

        val trimmed = TestSignals.trimEdges(faster, 2_000)
        assertEquals("Double speed doubles the pitch", 0.5, TestSignals.magnitudeAt(trimmed, 2_000.0), 0.02)
    }

    @Test
    fun `slowing down does not alias`() {
        val source = TestSignals.sine(2_000.0, 0.5, 48_000, amplitude = 0.5)
        val slower = Resampler.changeSpeed(source, 0.5, Resampler.Quality.TRANSPARENT)

        assertEquals(1.0, slower.durationSeconds, 0.001)
        val trimmed = TestSignals.trimEdges(slower, 3_000)
        assertEquals(0.5, TestSignals.magnitudeAt(trimmed, 1_000.0), 0.02)
    }

    @Test
    fun `the edges of a file are not faded by kernel truncation`() {
        // Normalising by the realised weight sum is what prevents a resampled file from
        // starting and ending with a quiet ramp that was never in the audio.
        val flat = ai.sautiy.core.audio.AudioBuffer.mono(FloatArray(4_800) { 0.5f }, 48_000)
        val converted = Resampler.resample(flat, 44_100, Resampler.Quality.TRANSPARENT)

        assertEquals("First sample was faded", 0.5, converted.channels[0][0].toDouble(), 0.02)
        assertEquals(
            "Last sample was faded",
            0.5,
            converted.channels[0][converted.frameCount - 1].toDouble(),
            0.02,
        )
    }

    @Test
    fun `every quality tier rejects aliasing to the standard it claims`() {
        // The tiers are a real trade-off, not three names for the same filter: each is held to
        // the rejection its own kernel width can deliver, and FAST is only ever used for a
        // preview the user hears for a fraction of a second.
        val floors = mapOf(
            Resampler.Quality.FAST to -55.0,
            Resampler.Quality.GOOD to -70.0,
            Resampler.Quality.TRANSPARENT to -80.0,
        )
        val source = TestSignals.sine(19_000.0, 0.3, 48_000, amplitude = 0.7)

        val results = Resampler.Quality.entries.associateWith { quality ->
            val converted = Resampler.resample(source, 32_000, quality)
            TestSignals.magnitudeDbAt(TestSignals.trimEdges(converted, 2_000), 13_000.0)
        }
        for ((quality, aliasDb) in results) {
            assertTrue(
                "$quality aliased at $aliasDb dBFS, above its ${floors.getValue(quality)} dB floor",
                aliasDb < floors.getValue(quality),
            )
        }
        assertTrue(
            "TRANSPARENT must reject aliasing at least as well as FAST",
            results.getValue(Resampler.Quality.TRANSPARENT) <= results.getValue(Resampler.Quality.FAST),
        )
    }

    @Test
    fun `the anti-alias cutoff is pulled below the new nyquist, not placed on it`() {
        for (quality in Resampler.Quality.entries) {
            assertTrue(
                "$quality places its cutoff at or above Nyquist, so its whole transition band aliases",
                quality.cutoffSafety < 1.0,
            )
        }
        assertTrue(
            "A narrower kernel needs more margin, not less",
            Resampler.Quality.FAST.cutoffSafety < Resampler.Quality.TRANSPARENT.cutoffSafety,
        )
    }
}
