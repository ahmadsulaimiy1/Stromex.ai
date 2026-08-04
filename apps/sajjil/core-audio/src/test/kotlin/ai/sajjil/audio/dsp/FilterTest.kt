package ai.sajjil.audio.dsp

import ai.sajjil.audio.TestSignals
import ai.sajjil.audio.linearToDb
import kotlin.math.abs
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class FftTest {

    @Test
    fun `inverse transform recovers the original signal`() {
        val n = 1024
        val fft = Fft(n)
        val original = DoubleArray(n) { kotlin.math.sin(2 * Math.PI * 7 * it / n) + 0.3 * it / n }
        val re = original.copyOf()
        val im = DoubleArray(n)

        fft.forward(re, im)
        fft.inverse(re, im)

        for (i in 0 until n) {
            assertTrue(
                abs(re[i] - original[i]) < 1e-9,
                "sample $i drifted: ${re[i]} vs ${original[i]}",
            )
        }
    }

    @Test
    fun `a pure tone lands in a single bin`() {
        val n = 1024
        val bin = 64
        val fft = Fft(n)
        val re = DoubleArray(n) { kotlin.math.cos(2 * Math.PI * bin * it / n) }
        val im = DoubleArray(n)
        fft.forward(re, im)
        val magnitudes = fft.magnitudes(re, im)

        val peak = magnitudes.indices.maxByOrNull { magnitudes[it] }
        assertEquals(bin, peak, "energy should be concentrated at bin $bin")
        // Every other bin should be negligible.
        val leakage = magnitudes.filterIndexed { i, _ -> i != bin }.max()
        assertTrue(leakage < magnitudes[bin] * 1e-9, "unexpected spectral leakage: $leakage")
    }

    @Test
    fun `rejects sizes that are not powers of two`() {
        val error = runCatching { Fft(1000) }.exceptionOrNull()
        assertTrue(error is IllegalArgumentException)
    }
}

class BiquadDesignTest {

    private val sampleRate = 48000

    @Test
    fun `low pass passes below cutoff and rejects above`() {
        val filter = BiquadDesign.lowPass(1000.0, sampleRate)
        assertTrue(linearToDb(filter.magnitudeAt(100.0, sampleRate)) > -1.0, "100 Hz should pass")
        assertTrue(linearToDb(filter.magnitudeAt(10000.0, sampleRate)) < -30.0, "10 kHz should be rejected")
    }

    @Test
    fun `high pass rejects below cutoff and passes above`() {
        val filter = BiquadDesign.highPass(1000.0, sampleRate)
        assertTrue(linearToDb(filter.magnitudeAt(50.0, sampleRate)) < -40.0, "50 Hz should be rejected")
        assertTrue(linearToDb(filter.magnitudeAt(8000.0, sampleRate)) > -1.0, "8 kHz should pass")
    }

    @Test
    fun `cutoff frequency sits at minus three decibels`() {
        for (cutoff in listOf(100.0, 1000.0, 5000.0)) {
            val filter = BiquadDesign.lowPass(cutoff, sampleRate)
            val db = linearToDb(filter.magnitudeAt(cutoff, sampleRate))
            assertTrue(
                abs(db - (-3.01)) < 0.15,
                "low pass at $cutoff Hz should be -3 dB at its cutoff, was $db dB",
            )
        }
    }

    @Test
    fun `peaking filter delivers the gain it was asked for`() {
        for (gain in listOf(-12.0, -6.0, 3.0, 9.0)) {
            val filter = BiquadDesign.peaking(2000.0, sampleRate, gain, q = 1.0)
            val actual = linearToDb(filter.magnitudeAt(2000.0, sampleRate))
            assertTrue(
                abs(actual - gain) < 0.05,
                "peaking filter asked for $gain dB, delivered $actual dB",
            )
            // Far from the centre it should be out of the way.
            assertTrue(abs(linearToDb(filter.magnitudeAt(50.0, sampleRate))) < 0.5)
        }
    }

    @Test
    fun `shelving filters reach their gain in the band they act on`() {
        val low = BiquadDesign.lowShelf(200.0, sampleRate, 6.0)
        assertTrue(abs(linearToDb(low.magnitudeAt(20.0, sampleRate)) - 6.0) < 0.3)
        assertTrue(abs(linearToDb(low.magnitudeAt(8000.0, sampleRate))) < 0.3)

        val high = BiquadDesign.highShelf(4000.0, sampleRate, -6.0)
        assertTrue(abs(linearToDb(high.magnitudeAt(20000.0, sampleRate)) - (-6.0)) < 0.3)
        assertTrue(abs(linearToDb(high.magnitudeAt(100.0, sampleRate))) < 0.3)
    }

    @Test
    fun `notch removes its centre frequency and leaves neighbours alone`() {
        val filter = BiquadDesign.notch(50.0, sampleRate, bandwidthHz = 4.0)
        assertTrue(
            linearToDb(filter.magnitudeAt(50.0, sampleRate)) < -40.0,
            "the notch centre should be deeply attenuated",
        )
        assertTrue(
            abs(linearToDb(filter.magnitudeAt(200.0, sampleRate))) < 0.5,
            "200 Hz is far outside a 4 Hz notch and must be untouched",
        )
    }

    @Test
    fun `designs stay stable when asked for a frequency above Nyquist`() {
        // The UI clamps sliders, but a preset built for 48 kHz can be loaded at 16 kHz.
        val filter = BiquadDesign.lowPass(30000.0, 16000)
        assertTrue(filter.b0.isFinite() && filter.a1.isFinite() && filter.a2.isFinite())
        assertTrue(abs(filter.a2) < 1.0, "poles must stay inside the unit circle")
    }

    @Test
    fun `zero gain filters are exact passthroughs`() {
        assertEquals(BiquadCoefficients.PASSTHROUGH, BiquadDesign.peaking(1000.0, sampleRate, 0.0))
        assertEquals(BiquadCoefficients.PASSTHROUGH, BiquadDesign.lowShelf(1000.0, sampleRate, 0.0))
    }
}

class BiquadProcessingTest {

    @Test
    fun `running a filter matches its designed magnitude response`() {
        val sampleRate = 48000
        val coefficients = BiquadDesign.lowPass(1000.0, sampleRate)

        for (frequency in listOf(200.0, 1000.0, 4000.0)) {
            val signal = TestSignals.sine(frequency, 0.5, sampleRate, amplitude = 0.5)
            val filter = Biquad(coefficients)
            filter.process(signal[0])

            // Skip the first 10 ms so the filter's transient does not skew the measurement.
            val settled = signal.slice(sampleRate / 100, signal.frameCount)
            val measuredGain = settled.peak() / 0.5
            val expectedGain = coefficients.magnitudeAt(frequency, sampleRate)

            assertTrue(
                abs(linearToDb(measuredGain.toDouble()) - linearToDb(expectedGain)) < 0.3,
                "at $frequency Hz measured ${linearToDb(measuredGain.toDouble())} dB " +
                    "but design predicts ${linearToDb(expectedGain)} dB",
            )
        }
    }

    @Test
    fun `a chain applies every stage`() {
        val sampleRate = 48000
        val chain = BiquadChain(
            listOf(
                BiquadDesign.peaking(1000.0, sampleRate, 6.0, q = 2.0),
                BiquadDesign.peaking(1000.0, sampleRate, 6.0, q = 2.0),
            )
        )
        val signal = TestSignals.sine(1000.0, 0.5, sampleRate, amplitude = 0.2)
        chain.process(signal[0])
        val settled = signal.slice(sampleRate / 50, signal.frameCount)
        val gainDb = linearToDb(settled.peak().toDouble() / 0.2)
        assertTrue(abs(gainDb - 12.0) < 0.5, "two 6 dB stages should give 12 dB, gave $gainDb")
    }

    @Test
    fun `reset clears filter memory`() {
        val filter = Biquad(BiquadDesign.lowPass(500.0, 48000))
        repeat(100) { filter.processSample(1.0) }
        filter.reset()
        assertEquals(0.0, filter.processSample(0.0), 1e-12)
    }
}
