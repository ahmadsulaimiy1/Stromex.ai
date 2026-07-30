package com.sajjil.core.dsp

import kotlin.math.PI
import kotlin.math.abs
import kotlin.math.log10
import kotlin.math.sin
import kotlin.math.sqrt
import kotlin.test.Test
import kotlin.test.assertTrue

class BiquadFilterTest {
    private val sampleRate = 48000.0

    private fun sineToneDbAfterFilter(filter: BiquadFilter, freqHz: Double, cycles: Int = 200): Double {
        filter.reset()
        val samplesPerCycle = (sampleRate / freqHz).toInt()
        val n = samplesPerCycle * cycles
        var sumSquares = 0.0
        var settleSamples = samplesPerCycle * 10
        for (i in 0 until n) {
            val x = sin(2.0 * PI * freqHz * i / sampleRate).toFloat()
            val y = filter.process(x)
            if (i >= settleSamples) sumSquares += y.toDouble() * y
        }
        val measured = n - settleSamples
        val rms = sqrt(sumSquares / measured)
        return 20.0 * log10(rms / (1.0 / sqrt(2.0)))
    }

    @Test
    fun `peaking filter boosts the target frequency and leaves DC-ish low freq alone`() {
        val filter = BiquadFilter.peaking(1000.0, sampleRate, q = 1.0, gainDb = 12.0)
        val gainAtTarget = sineToneDbAfterFilter(filter, 1000.0)
        assertTrue(abs(gainAtTarget - 12.0) < 1.0, "expected ~12dB boost at 1kHz, got $gainAtTarget")

        val gainFarAway = sineToneDbAfterFilter(BiquadFilter.peaking(1000.0, sampleRate, q = 1.0, gainDb = 12.0), 50.0)
        assertTrue(abs(gainFarAway) < 1.0, "expected ~0dB far from center, got $gainFarAway")
    }

    @Test
    fun `peaking filter cuts when gain is negative`() {
        val filter = BiquadFilter.peaking(2000.0, sampleRate, q = 1.0, gainDb = -9.0)
        val gain = sineToneDbAfterFilter(filter, 2000.0)
        assertTrue(abs(gain - (-9.0)) < 1.0, "expected ~-9dB at 2kHz, got $gain")
    }

    @Test
    fun `low shelf boosts bass and leaves treble unaffected`() {
        val bassGain = sineToneDbAfterFilter(BiquadFilter.lowShelf(200.0, sampleRate, gainDb = 6.0), 60.0)
        assertTrue(abs(bassGain - 6.0) < 1.5, "expected ~6dB boost at 60Hz, got $bassGain")

        val trebleGain = sineToneDbAfterFilter(BiquadFilter.lowShelf(200.0, sampleRate, gainDb = 6.0), 8000.0)
        assertTrue(abs(trebleGain) < 1.0, "expected ~0dB at 8kHz, got $trebleGain")
    }

    @Test
    fun `high shelf boosts treble and leaves bass unaffected`() {
        val trebleGain = sineToneDbAfterFilter(BiquadFilter.highShelf(4000.0, sampleRate, gainDb = 6.0), 12000.0)
        assertTrue(abs(trebleGain - 6.0) < 1.5, "expected ~6dB boost at 12kHz, got $trebleGain")

        val bassGain = sineToneDbAfterFilter(BiquadFilter.highShelf(4000.0, sampleRate, gainDb = 6.0), 100.0)
        assertTrue(abs(bassGain) < 1.0, "expected ~0dB at 100Hz, got $bassGain")
    }

    @Test
    fun `low pass attenuates high frequencies`() {
        val gain = sineToneDbAfterFilter(BiquadFilter.lowPass(500.0, sampleRate), 8000.0)
        assertTrue(gain < -20.0, "expected strong attenuation at 8kHz, got $gain")
    }

    @Test
    fun `high pass attenuates low frequencies`() {
        val gain = sineToneDbAfterFilter(BiquadFilter.highPass(2000.0, sampleRate), 60.0)
        assertTrue(gain < -20.0, "expected strong attenuation at 60Hz, got $gain")
    }
}
