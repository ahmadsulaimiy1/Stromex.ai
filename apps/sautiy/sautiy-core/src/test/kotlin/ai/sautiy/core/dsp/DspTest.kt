package ai.sautiy.core.dsp

import ai.sautiy.core.TestSignals
import ai.sautiy.core.audio.AudioBuffer
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class FftTest {

    @Test
    fun `a forward transform followed by an inverse returns the original`() {
        val fft = Fft(1024)
        val original = DoubleArray(1024) { kotlin.math.sin(it * 0.05) + 0.3 * kotlin.math.cos(it * 0.31) }
        val real = original.copyOf()
        val imaginary = DoubleArray(1024)

        fft.forward(real, imaginary)
        fft.inverse(real, imaginary)

        for (i in original.indices) {
            assertEquals("Round trip diverged at $i", original[i], real[i], 1e-9)
        }
    }

    @Test
    fun `a tone appears at its own bin with its own amplitude`() {
        val fft = Fft(4096)
        val rate = 48_000
        val tone = TestSignals.sine(1_500.0, 4096.0 / rate, rate, amplitude = 0.6)

        val spectrum = fft.magnitudeSpectrum(tone.channels[0])
        val bin = (1_500.0 * 4096 / rate).toInt()

        assertEquals("Amplitude must survive the window's gain correction", 0.6, spectrum[bin], 0.02)
        assertTrue("The peak must be at the tone's own bin", spectrum.indexOfFirst { it == spectrum.max() } == bin)
    }

    @Test
    fun `a hann window keeps a loud tone from masquerading as distant content`() {
        val fft = Fft(4096)
        val rate = 48_000
        val tone = TestSignals.sine(1_000.0, 4096.0 / rate, rate, amplitude = 1.0)

        val hann = fft.magnitudeSpectrum(tone.channels[0], Window.HANN)
        val rectangular = fft.magnitudeSpectrum(tone.channels[0], Window.RECTANGULAR)

        val farBin = (8_000.0 * 4096 / rate).toInt()
        assertTrue(
            "Hann leakage ${hann[farBin]} should be far below rectangular ${rectangular[farBin]}",
            hann[farBin] < rectangular[farBin] / 50.0,
        )
    }

    @Test
    fun `a non power of two size is rejected rather than silently truncated`() {
        assertTrue(runCatching { Fft(1000) }.isFailure)
    }
}

class BiquadTest {

    private val rate = 48_000

    @Test
    fun `a high pass removes rumble and keeps the voice`() {
        val rumble = TestSignals.sine(40.0, 0.5, rate, amplitude = 0.5)
        val voice = TestSignals.sine(1_000.0, 0.5, rate, amplitude = 0.5)

        val mixed = AudioBuffer.mono(
            FloatArray(rumble.frameCount) { rumble.channels[0][it] + voice.channels[0][it] },
            rate,
        )
        val single = mixed.copy()
        Biquad.highPass(100.0, rate).process(single.channels[0])
        val trimmed = TestSignals.trimEdges(single, 4_800)

        // One biquad is 12 dB per octave. 40 Hz is 1.32 octaves below a 100 Hz corner, so the
        // theoretical Butterworth attenuation is 16.0 dB and no more — asserting a larger
        // number would be asserting a filter that does not exist.
        val rumbleDb = TestSignals.magnitudeDbAt(trimmed, 40.0)
        assertEquals("A second-order Butterworth gives 16 dB here", -6.0 - 16.0, rumbleDb, 1.0)
        assertEquals("The voice must be untouched", 0.5, TestSignals.magnitudeAt(trimmed, 1_000.0), 0.03)
    }

    @Test
    fun `cascading two sections doubles the slope, which is what rumble needs`() {
        val rumble = TestSignals.sine(40.0, 0.5, rate, amplitude = 0.5)
        val voice = TestSignals.sine(1_000.0, 0.5, rate, amplitude = 0.5)
        val mixed = AudioBuffer.mono(
            FloatArray(rumble.frameCount) { rumble.channels[0][it] + voice.channels[0][it] },
            rate,
        )
        Biquad.highPass(100.0, rate).process(mixed.channels[0])
        Biquad.highPass(100.0, rate).process(mixed.channels[0])
        val trimmed = TestSignals.trimEdges(mixed, 4_800)

        assertTrue(
            "Two sections should reach roughly 32 dB, got ${TestSignals.magnitudeDbAt(trimmed, 40.0) + 6.0} dB",
            TestSignals.magnitudeDbAt(trimmed, 40.0) < -34.0,
        )
        assertEquals("The voice must still be untouched", 0.5, TestSignals.magnitudeAt(trimmed, 1_000.0), 0.03)
    }

    @Test
    fun `a peaking filter delivers exactly the gain it advertises`() {
        val filter = Biquad.peaking(1_000.0, rate, gainDb = 6.0, q = 1.0)
        assertEquals("At its centre, a +6 dB bell is +6 dB", 6.0, filter.magnitudeDbAt(1_000.0, rate), 0.01)
        assertEquals("Far below, it does nothing", 0.0, filter.magnitudeDbAt(50.0, rate), 0.5)
        assertEquals("Far above, it does nothing", 0.0, filter.magnitudeDbAt(15_000.0, rate), 0.5)
    }

    @Test
    fun `the drawn curve is the filter that is heard`() {
        // The response is computed from the coefficients, so the curve and the audio cannot
        // drift apart. This checks the computed curve against the filter's measured effect.
        val filter = Biquad.peaking(2_000.0, rate, gainDb = 8.0, q = 1.0)
        val predictedDb = filter.magnitudeDbAt(2_000.0, rate)

        val tone = TestSignals.sine(2_000.0, 0.5, rate, amplitude = 0.3)
        val before = TestSignals.magnitudeDbAt(TestSignals.trimEdges(tone, 4_800), 2_000.0)
        filter.process(tone.channels[0])
        val after = TestSignals.magnitudeDbAt(TestSignals.trimEdges(tone, 4_800), 2_000.0)

        assertEquals("Drawn curve and measured effect must agree", predictedDb, after - before, 0.2)
    }

    @Test
    fun `shelves affect one side of their corner and not the other`() {
        val low = Biquad.lowShelf(200.0, rate, gainDb = 6.0)
        assertEquals(6.0, low.magnitudeDbAt(30.0, rate), 0.5)
        assertEquals(0.0, low.magnitudeDbAt(6_000.0, rate), 0.5)

        val high = Biquad.highShelf(6_000.0, rate, gainDb = -6.0)
        assertEquals(-6.0, high.magnitudeDbAt(18_000.0, rate), 0.6)
        assertEquals(0.0, high.magnitudeDbAt(200.0, rate), 0.5)
    }

    @Test
    fun `a multi band equaliser sums its bands`() {
        val eq = Equaliser(
            listOf(
                EqBand(EqBand.Type.PEAKING, 500.0, 4.0, 1.0),
                EqBand(EqBand.Type.PEAKING, 4_000.0, -3.0, 1.0),
            ),
            rate,
        )
        assertEquals(4.0, eq.magnitudeDbAt(500.0), 0.2)
        assertEquals(-3.0, eq.magnitudeDbAt(4_000.0), 0.2)
        assertEquals(0.0, eq.magnitudeDbAt(50.0), 0.5)

        val curve = eq.curve(128)
        assertEquals(128, curve.size)
        assertTrue("The curve must show the boost", curve.max() > 3.0)
        assertTrue("The curve must show the cut", curve.min() < -2.0)
    }

    @Test
    fun `a disabled band is not applied`() {
        val eq = Equaliser(listOf(EqBand(EqBand.Type.PEAKING, 1_000.0, 12.0, 1.0, enabled = false)), rate)
        assertEquals(0.0, eq.magnitudeDbAt(1_000.0), 1e-9)
    }

    @Test
    fun `stereo channels are filtered independently so the image does not collapse`() {
        val left = TestSignals.sine(1_000.0, 0.3, rate, amplitude = 0.5).channels[0]
        val right = FloatArray(left.size)
        val stereo = AudioBuffer(arrayOf(left, right), rate)

        Equaliser(listOf(EqBand(EqBand.Type.PEAKING, 1_000.0, 6.0, 1.0)), rate).process(stereo)

        assertTrue("The left channel must be boosted", stereo.channels[0].maxOf { kotlin.math.abs(it) } > 0.9f)
        assertEquals("A silent channel must stay silent", 0f, stereo.channels[1].maxOf { kotlin.math.abs(it) }, 1e-7f)
    }
}

class DynamicsTest {

    private val rate = 48_000

    @Test
    fun `the compressor curve is exactly the ratio printed on the panel`() {
        val compressor = Compressor(thresholdDb = -20.0, ratio = 4.0, kneeDb = 0.0)

        assertEquals("Below the threshold, nothing happens", -30.0, compressor.outputLevelDb(-30.0), 1e-9)
        assertEquals("At the threshold, nothing happens", -20.0, compressor.outputLevelDb(-20.0), 1e-9)
        // 4:1 means 4 dB in above threshold gives 1 dB out above threshold.
        assertEquals("4 dB over becomes 1 dB over", -19.0, compressor.outputLevelDb(-16.0), 1e-9)
        assertEquals("20 dB over becomes 5 dB over", -15.0, compressor.outputLevelDb(0.0), 1e-9)
    }

    @Test
    fun `the knee is continuous, so a transient cannot click through it`() {
        val compressor = Compressor(thresholdDb = -20.0, ratio = 4.0, kneeDb = 8.0)
        val samples = (-40..0).map { compressor.outputLevelDb(it.toDouble()) }

        assertTrue("Output must rise monotonically", samples.zipWithNext().all { it.first < it.second })
        val steps = samples.zipWithNext().map { it.second - it.first }
        assertTrue(
            "The curve must have no corner: steps ranged ${steps.min()}..${steps.max()}",
            steps.zipWithNext().all { kotlin.math.abs(it.second - it.first) < 0.15 },
        )
    }

    @Test
    fun `compression reduces the dynamic range of real material`() {
        val loud = TestSignals.sine(440.0, 0.5, rate, amplitude = 0.9)
        val quiet = TestSignals.sine(440.0, 0.5, rate, amplitude = 0.05)
        val material = AudioBuffer.concat(listOf(quiet, loud, quiet))

        val processed = material.copy()
        val reduction = Compressor(thresholdDb = -20.0, ratio = 4.0, makeupDb = 0.0).process(processed)

        assertTrue("The compressor must actually have worked", reduction < -6.0)

        fun rangeDb(b: AudioBuffer): Double {
            val loudPart = b.slice(rate / 2 + 4_800, rate - 4_800).rms()
            val quietPart = b.slice(4_800, rate / 2 - 4_800).rms()
            return 20.0 * kotlin.math.log10(loudPart / quietPart)
        }
        assertTrue(
            "Range went from ${rangeDb(material)} dB to ${rangeDb(processed)} dB",
            rangeDb(processed) < rangeDb(material) - 6.0,
        )
    }

    @Test
    fun `a compressor with a ratio below one to one is refused`() {
        assertTrue(runCatching { Compressor(ratio = 0.5) }.isFailure)
    }

    @Test
    fun `the limiter holds the ceiling absolutely`() {
        val hot = TestSignals.sine(300.0, 0.5, rate, amplitude = 0.95)
        val limited = hot.copy()
        Limiter(ceilingDb = -6.0).process(limited)

        val ceiling = Math.pow(10.0, -6.0 / 20.0).toFloat()
        assertTrue(
            "Peak ${limited.peak()} exceeded the ceiling $ceiling",
            limited.peak() <= ceiling * 1.02f,
        )
    }

    @Test
    fun `look ahead means the very first transient is already controlled`() {
        // Without look-ahead, the first peak passes through unattenuated for the length of the
        // attack. This is the test that distinguishes a limiter from a fast compressor.
        val samples = FloatArray(rate / 10)
        for (i in 2_000 until 2_100) samples[i] = 0.99f
        val buffer = AudioBuffer.mono(samples, rate)

        Limiter(ceilingDb = -6.0, lookAheadMs = 5.0).process(buffer)
        val ceiling = Math.pow(10.0, -6.0 / 20.0).toFloat()

        assertTrue(
            "The first transient escaped at ${buffer.channels[0].maxOf { kotlin.math.abs(it) }}",
            buffer.channels[0].maxOf { kotlin.math.abs(it) } <= ceiling * 1.02f,
        )
    }

    @Test
    fun `the limiter leaves material under the ceiling completely alone`() {
        val quiet = TestSignals.sine(440.0, 0.3, rate, amplitude = 0.2)
        val processed = quiet.copy()
        val reduction = Limiter(ceilingDb = -1.0).process(processed)

        assertEquals("Nothing under the ceiling may be touched", 0.0, reduction, 1e-9)
        assertEquals(TestSignals.peak(quiet), TestSignals.peak(processed), 1e-4)
    }

    @Test
    fun `the limiter output stays time aligned with its input`() {
        // A limiter that shifts its output by the look-ahead would put a processed layer out of
        // sync with an unprocessed one.
        val samples = FloatArray(rate / 4)
        samples[5_000] = 0.99f
        val buffer = AudioBuffer.mono(samples, rate)
        Limiter(ceilingDb = -3.0, lookAheadMs = 5.0).process(buffer)

        val loudest = buffer.channels[0].indices.maxByOrNull { kotlin.math.abs(buffer.channels[0][it]) }!!
        assertEquals("The transient moved in time", 5_000, loudest)
    }

    @Test
    fun `the gate closes on noise, opens on speech, and holds through syllables`() {
        val noise = TestSignals.noise(0.5, rate, amplitude = 0.005)
        val speech = TestSignals.noise(0.5, rate, amplitude = 0.4, seed = 7)
        val material = AudioBuffer.concat(listOf(noise, speech, noise))

        val gated = material.copy()
        NoiseGate(thresholdDb = -35.0, rangeDb = -24.0).process(gated)

        val noiseBefore = material.slice(0, rate / 4).rms()
        val noiseAfter = gated.slice(0, rate / 4).rms()
        val speechAfter = gated.slice(rate / 2 + 4_800, rate - 4_800).rms()
        val speechBefore = material.slice(rate / 2 + 4_800, rate - 4_800).rms()

        assertTrue("The gate did not close on noise", noiseAfter < noiseBefore * 0.2)
        assertTrue("The gate damaged the speech", speechAfter > speechBefore * 0.9)
    }

    @Test
    fun `the de-esser reduces sibilance without ducking the vowel underneath it`() {
        // A full-band compressor triggered by an "s" ducks the whole voice; this checks that
        // the low band survives while the sibilant band comes down.
        val vowel = TestSignals.sine(300.0, 0.4, rate, amplitude = 0.35)
        val sibilance = TestSignals.sine(7_000.0, 0.4, rate, amplitude = 0.35)
        val together = AudioBuffer.mono(
            FloatArray(vowel.frameCount) { vowel.channels[0][it] + sibilance.channels[0][it] },
            rate,
        )

        val processed = together.copy()
        val reduction = DeEsser(frequencyHz = 5_000.0, thresholdDb = -24.0, ratio = 5.0).process(processed)
        assertTrue("The de-esser did nothing", reduction < -3.0)

        val trimmedBefore = TestSignals.trimEdges(together, 4_800)
        val trimmedAfter = TestSignals.trimEdges(processed, 4_800)

        val vowelChange = TestSignals.magnitudeDbAt(trimmedAfter, 300.0) - TestSignals.magnitudeDbAt(trimmedBefore, 300.0)
        val sibilanceChange =
            TestSignals.magnitudeDbAt(trimmedAfter, 7_000.0) - TestSignals.magnitudeDbAt(trimmedBefore, 7_000.0)

        assertTrue("Sibilance was not reduced ($sibilanceChange dB)", sibilanceChange < -3.0)
        assertTrue("The vowel was ducked by $vowelChange dB", vowelChange > -1.0)
    }
}

class NoiseReductionTest {

    private val rate = 48_000

    @Test
    fun `noise is reduced and the tone underneath survives`() {
        val tone = TestSignals.sine(800.0, 2.0, rate, amplitude = 0.4)
        val hiss = TestSignals.noise(2.0, rate, amplitude = 0.03, seed = 99)
        // A quiet head, so the reducer has somewhere to learn the profile from.
        val head = TestSignals.noise(0.7, rate, amplitude = 0.03, seed = 99)

        val noisy = AudioBuffer.concat(
            listOf(
                head,
                AudioBuffer.mono(FloatArray(tone.frameCount) { tone.channels[0][it] + hiss.channels[0][it] }, rate),
            ),
        )

        val cleaned = NoiseReduction(strength = 1.8).reduce(noisy)

        val headBefore = noisy.slice(4_800, rate / 2).rms()
        val headAfter = cleaned.slice(4_800, rate / 2).rms()
        assertTrue(
            "Noise floor went from $headBefore to $headAfter — not reduced enough",
            headAfter < headBefore * 0.45,
        )

        val toneRegion = cleaned.slice(rate, cleaned.frameCount - rate / 4)
        assertTrue(
            "The tone was destroyed: ${TestSignals.magnitudeDbAt(toneRegion, 800.0)} dBFS",
            TestSignals.magnitudeAt(toneRegion, 800.0) > 0.25,
        )
    }

    @Test
    fun `the residual is held at a floor rather than gouged to silence`() {
        // Subtracting to zero leaves isolated surviving bins that are heard as flickering
        // tones. Holding a floor is what keeps a quiet, steady bed instead.
        val hiss = TestSignals.noise(1.5, rate, amplitude = 0.02, seed = 5)
        val cleaned = NoiseReduction(strength = 3.0, floorDb = -18.0).reduce(hiss)

        val remaining = cleaned.slice(rate / 2, rate).rms()
        assertTrue("Everything was removed, which sounds like a dropout", remaining > 1e-5)
        assertTrue("Nothing was removed", remaining < hiss.rms() * 0.6)
    }

    @Test
    fun `the profile is a median, so a stray sound does not poison it`() {
        // A mean profile would absorb the chair creak and then subtract its spectrum from the
        // entire recording.
        val reducer = NoiseReduction()
        val quiet = TestSignals.noise(1.0, rate, amplitude = 0.01, seed = 3)
        val withStray = quiet.copy()
        val strayTone = TestSignals.sine(2_000.0, 0.05, rate, amplitude = 0.8)
        for (i in 0 until strayTone.frameCount) withStray.channels[0][i + 4_800] += strayTone.channels[0][i]

        val clean = reducer.learn(quiet)
        val poisoned = reducer.learn(withStray)

        val fft = Fft(1024)
        val bin = (2_000.0 * 1024 / rate).toInt()
        assertTrue(
            "A stray tone moved the profile from ${clean.magnitudes[bin]} to ${poisoned.magnitudes[bin]}",
            poisoned.magnitudes[bin] < clean.magnitudes[bin] * 3.0,
        )
        assertTrue(fft.binFrequency(bin, rate) > 1_800.0)
    }

    @Test
    fun `the quietest passage is found automatically`() {
        val loud = TestSignals.noise(1.0, rate, amplitude = 0.4, seed = 1)
        val quiet = TestSignals.noise(1.0, rate, amplitude = 0.005, seed = 2)
        val material = AudioBuffer.concat(listOf(loud, quiet, loud))

        val profile = NoiseReduction().learnFromQuietest(material, windowSeconds = 0.5)
        assertTrue("The profile must come from the quiet passage", profile.levelDb < -40.0)
        assertTrue(profile.framesAnalysed > 0)
    }
}
