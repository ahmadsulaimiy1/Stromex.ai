package ai.sajjil.audio.codec

import ai.sajjil.audio.AudioBuffer
import ai.sajjil.audio.TestSignals
import java.io.File
import kotlin.test.Test
import kotlin.test.assertTrue

/**
 * Writes FLAC files and their exact source PCM to `build/flac-fixtures/`.
 *
 * These are not assertions in themselves — they are the input to `tools/verify-flac.py`, which
 * decodes them with libsndfile (an independent implementation) and checks the samples match.
 * A codec can only really be trusted against a decoder that shares none of its assumptions; a
 * self-round-trip would pass just as happily if the bitstream were wrong in a self-consistent way.
 */
class FlacFixtureTest {

    private val sampleRate = 48000

    @Test
    fun `write fixtures for independent decoding`() {
        val directory = File("build/flac-fixtures")
        directory.mkdirs()

        // Each case exercises a different subframe or coding path.
        val cases = mapOf(
            // Fixed predictors, well-behaved residuals.
            "tone" to TestSignals.sine(440.0, 2.0, sampleRate, amplitude = 0.8),
            // Verbatim fallback and large Rice parameters.
            "noise" to TestSignals.noise(1.0, sampleRate, amplitude = 0.9),
            // Constant subframes interleaved with signal.
            "bursts" to TestSignals.burstsAndSilence(0.4, 0.4, 4, sampleRate),
            // Two independent channels.
            "stereo" to AudioBuffer(
                sampleRate,
                arrayOf(
                    TestSignals.sine(440.0, 1.0, sampleRate, amplitude = 0.7)[0],
                    TestSignals.sine(1310.0, 1.0, sampleRate, amplitude = 0.4)[0],
                ),
            ),
            // A length that is not a multiple of the block size, forcing a partial final frame.
            "partial" to TestSignals.sine(300.0, 0.0, sampleRate).let {
                AudioBuffer(sampleRate, arrayOf(FloatArray(4096 * 2 + 137) { i ->
                    (0.6 * kotlin.math.sin(2 * Math.PI * 300 * i / sampleRate)).toFloat()
                }))
            },
        )

        for ((name, buffer) in cases) {
            File(directory, "$name.flac").outputStream().buffered().use { out ->
                FlacEncoder(sampleRate, buffer.channelCount, bitsPerSample = 16).encode(buffer, out)
            }
            // The reference is written at 16-bit too, so the comparison isolates the FLAC
            // bitstream rather than re-testing float-to-integer quantisation.
            File(directory, "$name.wav").outputStream().buffered().use { out ->
                WavWriter.write(buffer, out, WavBitDepth.PCM_16)
            }
        }

        assertTrue(
            directory.listFiles()!!.count { it.extension == "flac" } == cases.size,
            "every fixture should have been written",
        )
    }
}
