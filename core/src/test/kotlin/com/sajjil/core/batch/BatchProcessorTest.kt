package com.sajjil.core.batch

import com.sajjil.core.audio.BitDepth
import com.sajjil.core.audio.WavIO
import com.sajjil.core.modes.VoiceProfile
import java.io.File
import kotlin.math.PI
import kotlin.math.sin
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class BatchProcessorTest {
    private val sampleRate = 16000

    private fun writeTestWav(name: String): File {
        val file = File.createTempFile(name, ".wav")
        file.deleteOnExit()
        val samples = FloatArray(sampleRate) { i -> (0.3 * sin(2.0 * PI * 300 * i / sampleRate)).toFloat() }
        file.outputStream().use { WavIO.write(it, samples, sampleRate, 1, BitDepth.PCM_16) }
        return file
    }

    @Test
    fun `processes a batch of files and writes mastered output for each`() {
        val outDir = File.createTempFile("sajjil-batch-out", "").apply { delete(); mkdirs(); deleteOnExit() }
        val items = (1..3).map { n ->
            val input = writeTestWav("ayah$n")
            BatchJobItem("Ayah $n", input, File(outDir, "ayah$n.wav"))
        }

        val result = BatchProcessor.run(items, VoiceProfile.STUDIO_QARI.config)

        assertEquals(3, result.successCount)
        assertEquals(0, result.failureCount)
        for (item in items) {
            assertTrue(item.outputFile.exists(), "expected mastered output for ${item.label}")
            assertTrue(item.outputFile.length() > 44, "expected non-empty audio payload for ${item.label}")
        }
        assertTrue(result.results.all { it.report != null })
    }

    @Test
    fun `a missing input file fails that item without aborting the batch`() {
        val outDir = File.createTempFile("sajjil-batch-out2", "").apply { delete(); mkdirs(); deleteOnExit() }
        val goodInput = writeTestWav("good")
        val items = listOf(
            BatchJobItem("Missing", File("/nonexistent/does-not-exist.wav"), File(outDir, "missing.wav")),
            BatchJobItem("Good", goodInput, File(outDir, "good.wav")),
        )

        val result = BatchProcessor.run(items, VoiceProfile.STUDIO_QARI.config)

        assertEquals(1, result.successCount)
        assertEquals(1, result.failureCount)
        assertTrue(result.results.first { it.item.label == "Missing" }.error != null)
        assertTrue(result.results.first { it.item.label == "Good" }.success)
    }
}
