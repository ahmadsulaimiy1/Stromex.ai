package com.sajjil.core.analysis

import kotlin.math.PI
import kotlin.math.sin
import kotlin.test.Test
import kotlin.test.assertTrue

class SpectrogramAnalyzerTest {
    private val sampleRate = 48000

    @Test
    fun `a full-scale tone peaks near its own frequency bin and near 0 dBFS`() {
        val freq = 2000.0
        val samples = FloatArray(sampleRate) { i -> sin(2.0 * PI * freq * i / sampleRate).toFloat() }
        val spectrogram = SpectrogramAnalyzer.compute(samples, sampleRate, fftSize = 1024)

        assertTrue(spectrogram.frames.isNotEmpty())
        val frame = spectrogram.frames[spectrogram.frames.size / 2]
        val peakBin = frame.indices.maxByOrNull { frame[it] }!!
        val peakFreq = spectrogram.binFrequencyHz[peakBin]

        assertTrue(kotlin.math.abs(peakFreq - freq) < 100.0, "expected peak near ${freq}Hz, got ${peakFreq}Hz")
        assertTrue(frame[peakBin] > -6.0, "expected near-0dBFS peak, got ${frame[peakBin]}")
    }

    @Test
    fun `silence sits near the noise floor across all bins`() {
        val samples = FloatArray(sampleRate)
        val spectrogram = SpectrogramAnalyzer.compute(samples, sampleRate)
        val frame = spectrogram.frames.first()
        assertTrue(frame.all { it <= -90.0 })
    }

    @Test
    fun `loudness history tracks a step from quiet to loud`() {
        val quiet = FloatArray(sampleRate / 2) { 0.01f }
        val loud = FloatArray(sampleRate / 2) { 0.5f }
        val history = SpectrogramAnalyzer.loudnessHistory(quiet + loud, sampleRate, windowSeconds = 0.1, hopSeconds = 0.1)

        val early = history.first { it.timeSeconds < 0.3 }.rmsDb
        val late = history.last { it.timeSeconds > 0.7 }.rmsDb
        assertTrue(late > early + 10.0, "expected loud segment much higher than quiet segment: $early vs $late")
    }
}
