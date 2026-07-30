package com.sajjil.core.audio

import java.io.File
import kotlin.math.abs
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class WavStreamWriterTest {
    @Test
    fun `streamed writes round trip and produce a correct header`() {
        val file = File.createTempFile("sajjil-stream-test", ".wav")
        file.deleteOnExit()

        val writer = WavStreamWriter(file, sampleRate = 48000, channels = 1, bitDepth = BitDepth.PCM_16)
        val chunk1 = FloatArray(1000) { i -> (kotlin.math.sin(i * 0.1) * 0.5).toFloat() }
        val chunk2 = FloatArray(500) { i -> (kotlin.math.sin(i * 0.2) * 0.3).toFloat() }
        writer.write(chunk1)
        writer.write(chunk2, count = 500)
        assertEquals(1500L * 1000 / 48000, writer.durationMs)
        writer.close()

        val decoded = WavIO.read(file.readBytes())
        assertEquals(48000, decoded.sampleRate)
        assertEquals(1500, decoded.samples.size)
        for (i in chunk1.indices) assertTrue(abs(decoded.samples[i] - chunk1[i]) < 0.001f)
        for (i in chunk2.indices) assertTrue(abs(decoded.samples[chunk1.size + i] - chunk2[i]) < 0.001f)

        file.delete()
    }
}
