package ai.sautiy.core.codec

import ai.sautiy.core.TestSignals
import ai.sautiy.core.analysis.PeakBuilder
import ai.sautiy.core.audio.SampleEncoding
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

/**
 * The reader that playback actually uses.
 *
 * Its whole reason to exist is speed, so the tests have two jobs: prove it returns *exactly*
 * what the plain [WavCodec.readRange] path returns — a fast reader that is subtly wrong is worse
 * than a slow one — and prove that the edges behave, because playback and the waveform both ask
 * for ranges that run past the material.
 */
class WavStreamReaderTest {

    @get:Rule
    val folder: TemporaryFolder = TemporaryFolder()

    @Test
    fun `every block matches the reference reader, sample for sample`() {
        val source = TestSignals.noise(1.3, 48_000, amplitude = 0.6, channels = 2)
        val file = folder.newFile("blocks.wav")
        WavCodec.write(file, source, SampleEncoding.PCM_16_LE)

        val block = 1_920 // 40 ms at 48 kHz — the real playback block size.
        WavStreamReader(file).use { reader ->
            var position = 0L
            while (position < reader.frameCount) {
                val frames = minOf(block.toLong(), reader.frameCount - position).toInt()
                val fast = reader.read(position, frames)
                val reference = WavCodec.readRange(file, position, frames.toLong())

                assertEquals("frame count at $position", reference.frameCount, fast.frameCount)
                for (c in 0 until reference.channelCount) {
                    for (i in 0 until reference.frameCount) {
                        assertEquals(
                            "channel $c, frame ${position + i}",
                            reference.channels[c][i],
                            fast.channels[c][i],
                            0f,
                        )
                    }
                }
                position += frames
            }
            assertEquals(source.frameCount.toLong(), position)
        }
    }

    @Test
    fun `reads are independent of the order they are made in`() {
        // The reader keeps one seekable handle and one reused scratch buffer. If either leaked
        // state between calls, a seek backwards would return the previous block's audio.
        val source = TestSignals.sine(300.0, 0.5, 44_100, amplitude = 0.8)
        val file = folder.newFile("seek.wav")
        WavCodec.write(file, source, SampleEncoding.PCM_24_LE)

        WavStreamReader(file).use { reader ->
            val forward = (0 until 10).map { reader.read(it * 1_000L, 512) }
            val backward = (9 downTo 0).map { reader.read(it * 1_000L, 512) }.reversed()

            for (b in forward.indices) {
                for (i in 0 until 512) {
                    assertEquals(
                        "block $b frame $i",
                        forward[b].channels[0][i],
                        backward[b].channels[0][i],
                        0f,
                    )
                }
            }
        }
    }

    @Test
    fun `a large read followed by a small one does not leak the tail of the large one`() {
        // The scratch buffer only ever grows, so a short read leaves stale bytes beyond its
        // length. Decoding must respect the length, not the buffer's capacity.
        val source = TestSignals.noise(0.4, 48_000, amplitude = 0.9)
        val file = folder.newFile("scratch.wav")
        WavCodec.write(file, source, SampleEncoding.PCM_16_LE)

        WavStreamReader(file).use { reader ->
            reader.read(0, 8_000)
            val small = reader.read(100, 64)
            val reference = WavCodec.readRange(file, 100, 64)

            assertEquals(64, small.frameCount)
            for (i in 0 until 64) {
                assertEquals(reference.channels[0][i], small.channels[0][i], 0f)
            }
        }
    }

    @Test
    fun `a read running past the end is padded with silence rather than failing`() {
        val source = TestSignals.sine(440.0, 0.1, 48_000, amplitude = 0.5)
        val file = folder.newFile("tail.wav")
        WavCodec.write(file, source, SampleEncoding.PCM_16_LE)

        WavStreamReader(file).use { reader ->
            val total = reader.frameCount.toInt() // 4 800
            val overrun = reader.read(total - 100L, 500)

            assertEquals(500, overrun.frameCount)
            // The 100 real frames are the file's last 100.
            val reference = WavCodec.readRange(file, total - 100L, 100)
            for (i in 0 until 100) {
                assertEquals(reference.channels[0][i], overrun.channels[0][i], 0f)
            }
            for (i in 100 until 500) {
                assertEquals("frame $i past the end", 0f, overrun.channels[0][i], 0f)
            }
        }
    }

    @Test
    fun `a read starting entirely past the end is silence of the requested length`() {
        val file = folder.newFile("short.wav")
        WavCodec.write(file, TestSignals.sine(440.0, 0.05, 48_000), SampleEncoding.PCM_16_LE)

        WavStreamReader(file).use { reader ->
            val beyond = reader.read(reader.frameCount + 10_000, 256)
            assertEquals(256, beyond.frameCount)
            assertEquals(0f, beyond.peak(), 0f)
        }
    }

    @Test
    fun `a read starting before zero is padded at the front, not shifted`() {
        // A timeline scrolled left of the origin asks for negative positions. The real audio
        // must land at its true offset in the returned block, or playback drifts.
        val source = TestSignals.noise(0.2, 48_000, amplitude = 0.7)
        val file = folder.newFile("lead.wav")
        WavCodec.write(file, source, SampleEncoding.PCM_16_LE)

        WavStreamReader(file).use { reader ->
            val block = reader.read(-64L, 256)
            assertEquals(256, block.frameCount)
            for (i in 0 until 64) {
                assertEquals("lead-in frame $i", 0f, block.channels[0][i], 0f)
            }
            val reference = WavCodec.readRange(file, 0, 192)
            for (i in 0 until 192) {
                assertEquals("frame ${i + 64}", reference.channels[0][i], block.channels[0][i + 64], 0f)
            }
        }
    }

    @Test
    fun `a zero-length read is empty, not an error`() {
        val file = folder.newFile("empty-read.wav")
        WavCodec.write(file, TestSignals.sine(440.0, 0.05, 48_000), SampleEncoding.PCM_16_LE)

        WavStreamReader(file).use { reader ->
            assertEquals(0, reader.read(0, 0).frameCount)
            assertEquals(0, reader.read(0, -5).frameCount)
        }
    }

    @Test
    fun `streamed peaks equal peaks built from the whole file in memory`() {
        // This is the fix for a saved recording opening with no waveform. It is only a fix if
        // the streamed envelope is the same envelope the one-shot builder produces.
        val source = TestSignals.noise(2.0, 48_000, amplitude = 0.8, channels = 2)
        val file = folder.newFile("peaks.wav")
        WavCodec.write(file, source, SampleEncoding.PCM_16_LE)

        val expected = PeakBuilder().apply { append(WavCodec.read(file)) }.finish()

        WavStreamReader(file).use { reader ->
            // A block size that is deliberately not a multiple of the bucket size, so a bucket
            // straddles a block boundary and any per-block reset would show up.
            val streamed = reader.buildPeaks(blockFrames = 1_000)

            assertEquals(expected.bucketCount, streamed.bucketCount)
            assertEquals(expected.framesPerBucket, streamed.framesPerBucket)
            for (b in 0 until expected.bucketCount) {
                assertEquals("min at bucket $b", expected.minima[b], streamed.minima[b], 0f)
                assertEquals("max at bucket $b", expected.maxima[b], streamed.maxima[b], 0f)
                assertEquals("rms at bucket $b", expected.rms[b], streamed.rms[b], 1e-6f)
            }
        }
    }

    @Test
    fun `peak building reports monotonic progress and finishes at one`() {
        val file = folder.newFile("progress.wav")
        WavCodec.write(file, TestSignals.noise(1.0, 48_000), SampleEncoding.PCM_16_LE)

        val reported = ArrayList<Double>()
        WavStreamReader(file).use { it.buildPeaks(blockFrames = 4_096) { p -> reported.add(p) } }

        assertTrue("Progress was never reported", reported.isNotEmpty())
        for (i in 1 until reported.size) {
            assertTrue("Progress went backwards at $i", reported[i] >= reported[i - 1])
        }
        assertEquals(1.0, reported.last(), 1e-9)
    }

    @Test
    fun `the pyramid covers the whole recording and keeps the loudest sample`() {
        // A transient that survives to the coarsest level is the difference between a waveform
        // that shows a clip and one that hides it.
        val samples = FloatArray(48_000 * 3) { 0.05f }
        samples[100_000] = 0.97f
        val file = folder.newFile("pyramid.wav")
        WavCodec.write(
            file,
            ai.sautiy.core.audio.AudioBuffer.mono(samples, 48_000),
            SampleEncoding.FLOAT_32_LE,
        )

        WavStreamReader(file).use { reader ->
            val pyramid = reader.buildPyramid()
            assertEquals(reader.frameCount, pyramid.totalFrames)
            assertEquals(48_000, pyramid.sampleRate)

            val whole = pyramid.columns(0, pyramid.totalFrames, 320)
            assertEquals(0.97f, whole.maxima.max(), 1e-6f)
        }
    }

    @Test
    fun `probing happens once, so the header is not re-parsed per read`() {
        // The defect this class replaces was invisible because the slow path is still correct.
        // What can be asserted cheaply is the property that makes it fast: the reader answers
        // shape questions from state it already holds, and reading does not reopen the file.
        val file = folder.newFile("once.wav")
        WavCodec.write(file, TestSignals.sine(440.0, 0.5, 44_100, channels = 2), SampleEncoding.PCM_16_LE)

        WavStreamReader(file).use { reader ->
            val info = reader.info
            reader.read(0, 512)
            reader.read(4_096, 512)
            assertTrue("probe must be a stable value, not re-run per call", info === reader.info)
            assertEquals(44_100, reader.sampleRate)
            assertEquals(2, reader.channelCount)
            assertNotEquals(0L, reader.frameCount)
        }
    }

    @Test
    fun `closing twice is harmless`() {
        val file = folder.newFile("close.wav")
        WavCodec.write(file, TestSignals.sine(440.0, 0.05, 48_000), SampleEncoding.PCM_16_LE)

        val reader = WavStreamReader(file)
        reader.read(0, 128)
        reader.close()
        reader.close()
    }
}
