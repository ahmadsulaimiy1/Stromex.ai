package com.sajjil.core.modes

import com.sajjil.core.dsp.ParametricEqualizer
import kotlin.test.Test
import kotlin.test.assertTrue

class MicrophoneProfileTest {

    @Test
    fun `every profile's correction bands build a stable EQ at common sample rates`() {
        for (profile in MicrophoneProfile.entries) {
            for (sampleRate in listOf(44100, 48000, 96000)) {
                val eq = ParametricEqualizer.parametric(sampleRate, profile.correctionBands)
                var y = 0f
                for (i in 0 until 2000) y = eq.process(if (i % 7 == 0) 0.4f else -0.2f)
                assertTrue(!y.isNaN() && y.isFinite(), "${profile.name} unstable at ${sampleRate}Hz")
            }
        }
    }

    @Test
    fun `flat reference applies no correction bands`() {
        assertTrue(MicrophoneProfile.FLAT_REFERENCE.correctionBands.isEmpty())
    }
}
