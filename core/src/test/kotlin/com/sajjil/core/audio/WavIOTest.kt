package com.sajjil.core.audio

import kotlin.math.abs
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class WavIOTest {
    private fun testSignal(n: Int) = FloatArray(n) { i -> (kotlin.math.sin(i * 0.05) * 0.7).toFloat() }

    @Test
    fun `round trips PCM16 within quantization error`() {
        val original = testSignal(4800)
        val bytes = WavIO.write(original, sampleRate = 48000, channels = 1, bitDepth = BitDepth.PCM_16)
        val decoded = WavIO.read(bytes)

        assertEquals(48000, decoded.sampleRate)
        assertEquals(1, decoded.channels)
        assertEquals(original.size, decoded.samples.size)
        for (i in original.indices) {
            assertTrue(abs(original[i] - decoded.samples[i]) < 0.001f, "sample $i drifted too much")
        }
    }

    @Test
    fun `round trips PCM24 with tighter precision than PCM16`() {
        val original = testSignal(4800)
        val bytes = WavIO.write(original, sampleRate = 48000, bitDepth = BitDepth.PCM_24)
        val decoded = WavIO.read(bytes)
        for (i in original.indices) {
            assertTrue(abs(original[i] - decoded.samples[i]) < 0.0001f, "sample $i drifted too much")
        }
    }

    @Test
    fun `round trips float32 exactly modulo clamping`() {
        val original = testSignal(4800)
        val bytes = WavIO.write(original, sampleRate = 96000, bitDepth = BitDepth.FLOAT_32)
        val decoded = WavIO.read(bytes)
        assertEquals(96000, decoded.sampleRate)
        for (i in original.indices) {
            assertTrue(abs(original[i] - decoded.samples[i]) < 1e-6f, "sample $i mismatch")
        }
    }

    @Test
    fun `header declares correct RIFF and data sizes`() {
        val bytes = WavIO.write(FloatArray(1000), sampleRate = 44100, bitDepth = BitDepth.PCM_16)
        assertEquals("RIFF", String(bytes, 0, 4))
        assertEquals("WAVE", String(bytes, 8, 4))
        assertEquals(44 + 2000, bytes.size)

        val buf = java.nio.ByteBuffer.wrap(bytes).order(java.nio.ByteOrder.LITTLE_ENDIAN)
        val riffChunkSize = buf.getInt(4)
        val dataChunkSize = buf.getInt(40)
        assertEquals(36 + 2000, riffChunkSize)
        assertEquals(2000, dataChunkSize)
    }
}
