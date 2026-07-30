package com.sajjil.core.dsp

import kotlin.math.PI
import kotlin.math.sin
import kotlin.test.Test
import kotlin.test.assertTrue

class ParametricEqualizerTest {

    @Test
    fun `basic 4-band EQ stays stable at a low capture sample rate`() {
        // 16kHz puts the fixed 9kHz treble shelf's design frequency close to
        // Nyquist (8kHz) — this is the exact configuration that used to blow
        // up to NaN within a few hundred samples before the frequencies were
        // clamped against Nyquist.
        val sampleRate = 16000
        val eq = ParametricEqualizer.basic(sampleRate, bassDb = 1.0, midDb = 0.5, trebleDb = 1.0, presenceDb = 1.5)
        val samples = FloatArray(sampleRate) { i -> (0.3 * sin(2.0 * PI * 300 * i / sampleRate)).toFloat() }

        for (s in samples) {
            val y = eq.process(s)
            assertTrue(!y.isNaN() && y.isFinite(), "EQ output went unstable: $y")
        }
    }

    @Test
    fun `basic EQ at a very low sample rate still produces bounded output`() {
        val sampleRate = 8000
        val eq = ParametricEqualizer.basic(sampleRate, bassDb = 2.0, midDb = 2.0, trebleDb = 3.0, presenceDb = 3.0)
        val samples = FloatArray(sampleRate) { i -> (0.5 * sin(2.0 * PI * 200 * i / sampleRate)).toFloat() }

        for (s in samples) {
            val y = eq.process(s)
            assertTrue(!y.isNaN() && y.isFinite() && kotlin.math.abs(y) < 100f, "EQ output unbounded: $y")
        }
    }

    @Test
    fun `parametric bands above Nyquist are clamped rather than left unstable`() {
        val sampleRate = 8000
        val eq = ParametricEqualizer.parametric(sampleRate, listOf(Triple(7500.0, 1.0, 6.0)))
        val samples = FloatArray(sampleRate) { i -> (0.4 * sin(2.0 * PI * 500 * i / sampleRate)).toFloat() }
        for (s in samples) {
            val y = eq.process(s)
            assertTrue(!y.isNaN() && y.isFinite(), "clamped parametric band still went unstable: $y")
        }
    }
}
