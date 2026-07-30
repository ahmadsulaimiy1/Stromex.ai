package com.sajjil.core.dsp

import kotlin.math.PI
import kotlin.math.abs
import kotlin.math.log10
import kotlin.math.sin
import kotlin.math.sqrt
import kotlin.test.Test
import kotlin.test.assertTrue

class CompressorTest {
    private val sampleRate = 48000

    private fun rmsDbOfTone(compressor: Compressor, amplitude: Double, seconds: Double = 1.0): Double {
        val n = (sampleRate * seconds).toInt()
        val freq = 440.0
        var sumSquares = 0.0
        val settle = sampleRate / 4
        for (i in 0 until n) {
            val x = (amplitude * sin(2.0 * PI * freq * i / sampleRate)).toFloat()
            val y = compressor.process(x)
            if (i >= settle) sumSquares += y.toDouble() * y
        }
        val measured = n - settle
        return 20.0 * log10(sqrt(sumSquares / measured))
    }

    @Test
    fun `signal above threshold is compressed toward the expected ratio`() {
        val compressor = Compressor(
            sampleRate, thresholdDb = -18.0, ratio = 4.0,
            attackMs = 2.0, releaseMs = 50.0, kneeDb = 0.0, makeupGainDb = 0.0,
        )
        // 0 dBFS sine has RMS at -3.01 dBFS; amplitude 1.0 -> input RMS ~ -3 dB.
        val outputDb = rmsDbOfTone(compressor, amplitude = 1.0)
        val inputDb = -3.01
        val expectedDb = -18.0 + (inputDb - -18.0) / 4.0
        assertTrue(abs(outputDb - expectedDb) < 2.0, "expected ~$expectedDb dB, got $outputDb dB")
    }

    @Test
    fun `signal below threshold passes through with unity gain`() {
        val compressor = Compressor(
            sampleRate, thresholdDb = -6.0, ratio = 4.0,
            attackMs = 2.0, releaseMs = 50.0, kneeDb = 0.0, makeupGainDb = 0.0,
        )
        val outputDb = rmsDbOfTone(compressor, amplitude = 0.05)
        val inputDb = 20.0 * log10(0.05 / sqrt(2.0))
        assertTrue(abs(outputDb - inputDb) < 1.0, "expected ~unity gain ($inputDb dB), got $outputDb dB")
    }

    @Test
    fun `auto makeup gain compensates threshold and ratio`() {
        val compressor = Compressor(sampleRate, thresholdDb = -20.0, ratio = 4.0)
        val makeup = compressor.autoMakeupGain()
        assertTrue(makeup > 0, "expected positive makeup gain, got $makeup")
    }
}
