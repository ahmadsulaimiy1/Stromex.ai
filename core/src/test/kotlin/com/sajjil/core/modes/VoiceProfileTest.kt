package com.sajjil.core.modes

import com.sajjil.core.dsp.AudioProcessingChain
import kotlin.math.PI
import kotlin.math.sin
import kotlin.math.sqrt
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class VoiceProfileTest {
    private val sampleRate = 44100

    private fun render(profile: VoiceProfile, samples: FloatArray): FloatArray {
        val chain = AudioProcessingChain(sampleRate, profile.config)
        return FloatArray(samples.size) { i -> chain.process(samples[i]) }
    }

    private fun testSignal() = FloatArray(sampleRate) { i ->
        (0.3 * sin(2.0 * PI * 220 * i / sampleRate) + 0.15 * sin(2.0 * PI * 3000 * i / sampleRate)).toFloat()
    }

    @Test
    fun `there are exactly seven flagship production chains`() {
        assertEquals(7, VoiceProfile.entries.size)
    }

    @Test
    fun `every profile stays stable at common sample rates`() {
        for (profile in VoiceProfile.entries) {
            for (rate in listOf(44100, 48000, 96000)) {
                val chain = AudioProcessingChain(rate, profile.config)
                val samples = FloatArray(rate) { i -> (0.3 * sin(2.0 * PI * 300 * i / rate)).toFloat() }
                for (s in samples) {
                    val y = chain.process(s)
                    assertTrue(!y.isNaN() && y.isFinite(), "${profile.name} unstable at ${rate}Hz")
                }
            }
        }
    }

    @Test
    fun `profiles are sonically distinct, not just relabeled duplicates`() {
        val source = testSignal()
        val outputs = VoiceProfile.entries.associateWith { render(it, source) }

        val profiles = VoiceProfile.entries.toList()
        for (i in profiles.indices) {
            for (j in i + 1 until profiles.size) {
                val a = outputs.getValue(profiles[i])
                val b = outputs.getValue(profiles[j])
                var sumSquareDiff = 0.0
                for (k in a.indices) {
                    val diff = (a[k] - b[k]).toDouble()
                    sumSquareDiff += diff * diff
                }
                val rmsDiff = sqrt(sumSquareDiff / a.size)
                assertTrue(
                    rmsDiff > 0.001,
                    "${profiles[i].name} and ${profiles[j].name} sound identical (rmsDiff=$rmsDiff)",
                )
            }
        }
    }

    @Test
    fun `each profile carries its own custom EQ shape`() {
        for (profile in VoiceProfile.entries) {
            assertTrue(!profile.config.customEqBands.isNullOrEmpty(), "${profile.name} has no custom EQ bands")
        }
    }
}
