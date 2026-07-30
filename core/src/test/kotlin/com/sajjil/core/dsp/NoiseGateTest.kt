package com.sajjil.core.dsp

import kotlin.math.abs
import kotlin.test.Test
import kotlin.test.assertTrue

class NoiseGateTest {
    private val sampleRate = 48000

    @Test
    fun `low level noise is attenuated after release settles`() {
        val gate = NoiseGate(sampleRate, thresholdDb = -30.0, rangeDb = -40.0, holdMs = 10.0, releaseMs = 20.0)
        var lastOut = 0f
        // Feed 0.5s of quiet noise (-50 dBFS-ish), well below threshold.
        repeat((sampleRate * 0.5).toInt()) {
            lastOut = gate.process(0.003f)
        }
        assertTrue(abs(lastOut) < 0.003f, "expected gated (attenuated) output, got $lastOut")
    }

    @Test
    fun `signal above threshold passes through open`() {
        val gate = NoiseGate(sampleRate, thresholdDb = -30.0, rangeDb = -40.0, attackMs = 1.0)
        var lastOut = 0f
        repeat((sampleRate * 0.1).toInt()) {
            lastOut = gate.process(0.5f)
        }
        assertTrue(abs(lastOut - 0.5f) < 0.05f, "expected near-unity when open, got $lastOut")
    }
}
