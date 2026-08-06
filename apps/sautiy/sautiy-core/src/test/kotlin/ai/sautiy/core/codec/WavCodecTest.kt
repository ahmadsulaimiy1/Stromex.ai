package ai.sautiy.core.codec

import ai.sautiy.core.TestSignals
import ai.sautiy.core.audio.AudioFormat
import ai.sautiy.core.audio.SampleEncoding
import java.io.File
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

class WavCodecTest {

    @get:Rule
    val folder: TemporaryFolder = TemporaryFolder()

    @Test
    fun `a written file reads back as the same audio`() {
        val source = TestSignals.sine(440.0, 0.25, 48_000, amplitude = 0.7)
        val file = folder.newFile("tone.wav")

        WavCodec.write(file, source, SampleEncoding.PCM_16_LE)
        val read = WavCodec.read(file)

        assertEquals(source.frameCount, read.frameCount)
        assertEquals(48_000, read.sampleRate)
        assertTrue(
            "Round trip through 16-bit should be near-transparent, was ${TestSignals.snrDb(source, read)} dB",
            TestSignals.snrDb(source, read) > 85.0,
        )
    }

    @Test
    fun `probe reports duration and shape without reading the audio`() {
        val source = TestSignals.sine(440.0, 2.0, 44_100, channels = 2)
        val file = folder.newFile("stereo.wav")
        WavCodec.write(file, source, SampleEncoding.PCM_24_LE)

        val info = WavCodec.probe(file)
        assertEquals(44_100, info.format.sampleRate)
        assertEquals(2, info.format.channelCount)
        assertEquals(SampleEncoding.PCM_24_LE, info.format.encoding)
        assertEquals(source.frameCount.toLong(), info.frameCount)
        assertEquals(2.0, info.durationSeconds, 1e-6)
    }

    @Test
    fun `twenty four bit survives the round trip`() {
        val source = TestSignals.noise(0.1, 48_000, amplitude = 0.3)
        val file = folder.newFile("deep.wav")
        WavCodec.write(file, source, SampleEncoding.PCM_24_LE)

        val snr = TestSignals.snrDb(source, WavCodec.read(file))
        assertTrue("24-bit round trip SNR was $snr dB", snr > 120.0)
    }

    @Test
    fun `float files round trip bit exactly`() {
        val source = TestSignals.noise(0.05, 48_000, amplitude = 0.9)
        val file = folder.newFile("float.wav")
        WavCodec.write(file, source, SampleEncoding.FLOAT_32_LE)

        val read = WavCodec.read(file)
        for (i in 0 until source.frameCount) {
            assertEquals(source.channels[0][i], read.channels[0][i], 0f)
        }
    }

    @Test
    fun `a range read returns exactly the requested frames`() {
        val source = TestSignals.sine(1_000.0, 1.0, 48_000)
        val file = folder.newFile("range.wav")
        WavCodec.write(file, source, SampleEncoding.PCM_16_LE)

        val slice = WavCodec.readRange(file, startFrame = 24_000, maxFrames = 4_800)
        assertEquals(4_800, slice.frameCount)

        val expected = source.slice(24_000, 28_800)
        assertTrue(TestSignals.snrDb(expected, slice) > 85.0)
    }

    @Test
    fun `a range read past the end returns silence rather than throwing`() {
        val file = folder.newFile("short.wav")
        WavCodec.write(file, TestSignals.sine(440.0, 0.01, 48_000), SampleEncoding.PCM_16_LE)

        val past = WavCodec.readRange(file, startFrame = 1_000_000, maxFrames = 100)
        assertEquals(0, past.frameCount)
    }

    // --- The capture contract ------------------------------------------------------------

    @Test
    fun `the streaming writer leaves a valid file after every flush`() {
        val file = folder.newFile("live.wav")
        val format = AudioFormat(48_000, 1, SampleEncoding.PCM_16_LE)
        val block = TestSignals.sine(440.0, 0.1, 48_000, amplitude = 0.6)

        WavCodec.StreamingWriter(file, format).use { writer ->
            repeat(5) { index ->
                writer.append(block)
                writer.flush()

                // The whole promise of chapter 1.3.5: at this instant, mid-recording, the file
                // on disk is already a complete and playable WAV of everything so far.
                val info = WavCodec.probe(file)
                assertEquals(
                    "After flush ${index + 1} the file must contain every frame written",
                    block.frameCount.toLong() * (index + 1),
                    info.frameCount,
                )
                assertEquals(0.1 * (index + 1), info.durationSeconds, 1e-6)
                WavCodec.read(file)
            }
        }
    }

    @Test
    fun `audio survives a process death that never closed the file`() {
        // Simulates a kill: bytes were appended and flushed, but close() never ran, so the
        // header was last patched one flush ago.
        val file = folder.newFile("killed.wav")
        val format = AudioFormat(48_000, 1, SampleEncoding.PCM_16_LE)
        val block = TestSignals.sine(440.0, 0.5, 48_000, amplitude = 0.6)

        val writer = WavCodec.StreamingWriter(file, format)
        writer.append(block)
        writer.flush()
        writer.append(block) // captured, but no flush and no close follows

        val recovered = WavCodec.read(file)
        assertTrue(
            "Recovery lost audio: only ${recovered.frameCount} of ${block.frameCount * 2} frames",
            recovered.frameCount >= block.frameCount,
        )
        assertTrue("Recovered audio must not be silence", recovered.peak() > 0.5f)
    }

    @Test
    fun `a header claiming zero length still yields every recorded frame`() {
        // A crash before the very first flush leaves the initial data size of 0 in place.
        // Trusting that field would tell the user their recording was empty, which is both
        // false and the worst possible thing to tell them.
        val file = folder.newFile("unpatched.wav")
        val format = AudioFormat(48_000, 1, SampleEncoding.PCM_16_LE)
        val block = TestSignals.sine(440.0, 0.25, 48_000, amplitude = 0.6)

        val writer = WavCodec.StreamingWriter(file, format)
        writer.append(block)
        // No flush, no close at all.

        val info = WavCodec.probe(file)
        assertEquals(block.frameCount.toLong(), info.frameCount)
        assertTrue(WavCodec.read(file).peak() > 0.5f)
    }

    @Test
    fun `the streaming writer tracks its own duration as it goes`() {
        val file = folder.newFile("counting.wav")
        val format = AudioFormat(48_000, 2, SampleEncoding.PCM_16_LE)
        val block = TestSignals.sine(440.0, 0.2, 48_000, channels = 2)

        WavCodec.StreamingWriter(file, format).use { writer ->
            assertEquals(0L, writer.frameCount)
            writer.append(block)
            assertEquals(block.frameCount.toLong(), writer.frameCount)
            assertEquals(0.2, writer.durationSeconds, 1e-9)
        }
    }

    // --- Robustness against real-world files ------------------------------------------------

    @Test
    fun `unknown chunks are skipped rather than rejected`() {
        // Recorders routinely write LIST, bext, id3 and iXML chunks. A reader that stops at the
        // first thing it does not recognise cannot open half the files on a working phone.
        val source = TestSignals.sine(440.0, 0.05, 48_000)
        val plain = folder.newFile("plain.wav")
        WavCodec.write(plain, source, SampleEncoding.PCM_16_LE)
        val bytes = plain.readBytes()

        val fmtEnd = 36 // RIFF(12) + fmt header(8) + fmt body(16)
        val listChunk = byteArrayOf(
            'L'.code.toByte(), 'I'.code.toByte(), 'S'.code.toByte(), 'T'.code.toByte(),
            6, 0, 0, 0,
            'I'.code.toByte(), 'N'.code.toByte(), 'F'.code.toByte(), 'O'.code.toByte(), 0, 0,
        )
        val withList = bytes.copyOfRange(0, fmtEnd) + listChunk + bytes.copyOfRange(fmtEnd, bytes.size)

        val file = folder.newFile("extra-chunks.wav")
        file.writeBytes(withList)

        val read = WavCodec.read(file)
        assertEquals(source.frameCount, read.frameCount)
        assertTrue(TestSignals.snrDb(source, read) > 85.0)
    }

    @Test
    fun `an odd sized chunk is word aligned correctly`() {
        val source = TestSignals.sine(440.0, 0.05, 48_000)
        val plain = folder.newFile("plain-odd.wav")
        WavCodec.write(plain, source, SampleEncoding.PCM_16_LE)
        val bytes = plain.readBytes()

        val fmtEnd = 36
        // A 5-byte body followed by one pad byte, as the RIFF specification requires.
        val oddChunk = byteArrayOf(
            'n'.code.toByte(), 'o'.code.toByte(), 't'.code.toByte(), 'e'.code.toByte(),
            5, 0, 0, 0,
            1, 2, 3, 4, 5, 0,
        )
        val file = folder.newFile("odd-chunk.wav")
        file.writeBytes(bytes.copyOfRange(0, fmtEnd) + oddChunk + bytes.copyOfRange(fmtEnd, bytes.size))

        assertEquals(source.frameCount.toLong(), WavCodec.probe(file).frameCount)
    }

    @Test
    fun `a file that is not a wav is rejected with a clear reason`() {
        val file = folder.newFile("not-audio.txt")
        file.writeText("This is not a RIFF file at all, it is prose.")

        val failure = runCatching { WavCodec.probe(file) }.exceptionOrNull()
        assertTrue("Expected a WavFormatException, got $failure", failure is WavCodec.WavFormatException)
        assertTrue(failure!!.message!!.contains("RIFF"))
    }

    @Test
    fun `an empty file is rejected rather than read as silence`() {
        val file: File = folder.newFile("empty.wav")
        val failure = runCatching { WavCodec.probe(file) }.exceptionOrNull()
        assertTrue(failure is WavCodec.WavFormatException)
    }
}
