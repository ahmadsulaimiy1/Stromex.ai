package ai.sajjil.audio.codec

import ai.sajjil.audio.AudioBuffer
import ai.sajjil.audio.TestSignals
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class BitWriterTest {

    @Test
    fun `bits are written most significant first`() {
        val writer = BitWriter()
        writer.writeBits(0b101L, 3)
        writer.writeBits(0b11010L, 5)
        val bytes = writer.toByteArray()
        assertEquals(1, bytes.size)
        assertEquals(0b10111010, bytes[0].toInt() and 0xFF)
    }

    @Test
    fun `values spanning byte boundaries are preserved`() {
        val writer = BitWriter()
        writer.writeBits(0xABCDEFL, 24)
        val bytes = writer.toByteArray()
        assertEquals(0xAB, bytes[0].toInt() and 0xFF)
        assertEquals(0xCD, bytes[1].toInt() and 0xFF)
        assertEquals(0xEF, bytes[2].toInt() and 0xFF)
    }

    @Test
    fun `negative values are written in twos complement at the requested width`() {
        val writer = BitWriter()
        writer.writeBits((-1).toLong(), 16)
        val bytes = writer.toByteArray()
        assertEquals(0xFF, bytes[0].toInt() and 0xFF)
        assertEquals(0xFF, bytes[1].toInt() and 0xFF)
    }

    @Test
    fun `alignment pads with zeroes and reports how many`() {
        val writer = BitWriter()
        writer.writeBits(0b1L, 1)
        assertEquals(7, writer.alignToByte())
        assertTrue(writer.isByteAligned)
        assertEquals(0b10000000, writer.toByteArray()[0].toInt() and 0xFF)
    }

    @Test
    fun `long runs of zeroes are handled`() {
        val writer = BitWriter()
        writer.writeZeroes(100)
        writer.writeBit(1)
        writer.alignToByte()
        assertEquals(101L + 3, writer.bitCount)
    }

    @Test
    fun `reading out an unaligned stream is refused rather than silently truncated`() {
        val writer = BitWriter()
        writer.writeBits(0b1L, 1)
        val error = runCatching { writer.toByteArray() }.exceptionOrNull()
        assertTrue(error is IllegalStateException)
    }
}

class CrcTest {

    @Test
    fun `CRC-8 matches known values for the FLAC polynomial`() {
        assertEquals(0x00, Crc.crc8(byteArrayOf(0)))
        // Independently computed with the bitwise definition of the same polynomial.
        assertEquals(bitwiseCrc8(byteArrayOf(0xFF.toByte(), 0xF8.toByte(), 0x69)), Crc.crc8(byteArrayOf(0xFF.toByte(), 0xF8.toByte(), 0x69)))
    }

    @Test
    fun `CRC-16 matches a bitwise implementation`() {
        val data = ByteArray(64) { (it * 7 + 3).toByte() }
        assertEquals(bitwiseCrc16(data), Crc.crc16(data))
    }

    /** Straightforward bit-at-a-time reference, used only to check the table-driven versions. */
    private fun bitwiseCrc8(data: ByteArray): Int {
        var crc = 0
        for (byte in data) {
            crc = crc xor (byte.toInt() and 0xFF)
            repeat(8) {
                crc = if (crc and 0x80 != 0) ((crc shl 1) xor 0x07) and 0xFF else (crc shl 1) and 0xFF
            }
        }
        return crc
    }

    private fun bitwiseCrc16(data: ByteArray): Int {
        var crc = 0
        for (byte in data) {
            crc = crc xor ((byte.toInt() and 0xFF) shl 8)
            repeat(8) {
                crc = if (crc and 0x8000 != 0) ((crc shl 1) xor 0x8005) and 0xFFFF else (crc shl 1) and 0xFFFF
            }
        }
        return crc
    }
}

class WavTest {

    private val sampleRate = 48000

    @Test
    fun `a 16-bit round trip preserves the audio within one bit`() {
        val original = TestSignals.sine(440.0, 0.5, sampleRate, amplitude = 0.8)
        val bytes = ByteArrayOutputStream()
        WavWriter.write(original, bytes, WavBitDepth.PCM_16)
        val decoded = WavReader.read(ByteArrayInputStream(bytes.toByteArray()))

        assertEquals(original.sampleRate, decoded.sampleRate)
        assertEquals(original.frameCount, decoded.frameCount)
        assertTrue(
            TestSignals.maxAbsoluteDifference(original, decoded) < 1.0 / 32768 * 2,
            "16-bit quantisation should cost at most a bit or so",
        )
    }

    @Test
    fun `24-bit is more accurate than 16-bit`() {
        val original = TestSignals.sine(440.0, 0.2, sampleRate, amplitude = 0.8)
        val error16 = roundTripError(original, WavBitDepth.PCM_16)
        val error24 = roundTripError(original, WavBitDepth.PCM_24)
        assertTrue(error24 < error16 / 100, "24-bit ($error24) should be far cleaner than 16-bit ($error16)")
    }

    @Test
    fun `32-bit float is exactly lossless`() {
        val original = TestSignals.sine(440.0, 0.2, sampleRate, amplitude = 0.8)
        assertEquals(0.0, roundTripError(original, WavBitDepth.FLOAT_32))
    }

    @Test
    fun `stereo channels stay in their own lanes`() {
        val left = TestSignals.sine(440.0, 0.2, sampleRate, amplitude = 0.7)[0]
        val right = TestSignals.sine(880.0, 0.2, sampleRate, amplitude = 0.3)[0]
        val original = AudioBuffer(sampleRate, arrayOf(left, right))

        val bytes = ByteArrayOutputStream()
        WavWriter.write(original, bytes, WavBitDepth.PCM_16)
        val decoded = WavReader.read(ByteArrayInputStream(bytes.toByteArray()))

        assertEquals(2, decoded.channelCount)
        assertTrue(decoded[0].max() > 0.6f, "left channel level was not preserved")
        assertTrue(decoded[1].max() < 0.35f, "right channel picked up the left channel's level")
    }

    @Test
    fun `headers alone report duration without reading audio`() {
        val original = TestSignals.sine(440.0, 1.5, sampleRate)
        val bytes = ByteArrayOutputStream()
        WavWriter.write(original, bytes, WavBitDepth.PCM_16)
        val data = bytes.toByteArray()

        val info = WavReader.readInfo(ByteArrayInputStream(data), data.size.toLong())
        assertEquals(sampleRate, info.sampleRate)
        assertEquals(1, info.channelCount)
        assertEquals(original.frameCount, info.frameCount)
    }

    @Test
    fun `unknown chunks are skipped rather than rejected`() {
        // Phone recorders routinely add LIST/INFO chunks. Refusing to open those files would be
        // a support nightmare and there is no reason for it.
        val original = TestSignals.sine(440.0, 0.1, sampleRate)
        val body = ByteArrayOutputStream()
        WavWriter.write(original, body, WavBitDepth.PCM_16)
        val plain = body.toByteArray()

        val withExtra = ByteArrayOutputStream()
        withExtra.write(plain, 0, 12) // RIFF....WAVE
        withExtra.write("LIST".toByteArray())
        withExtra.write(byteArrayOf(4, 0, 0, 0))
        withExtra.write("INFO".toByteArray())
        withExtra.write(plain, 12, plain.size - 12) // fmt + data

        // The RIFF size is now stale, which the reader is expected to tolerate.
        val decoded = WavReader.read(ByteArrayInputStream(withExtra.toByteArray()))
        assertEquals(original.frameCount, decoded.frameCount)
    }

    @Test
    fun `a truncated recording still yields the audio that was written`() {
        // This is the shape of a file left behind when recording is killed by the system.
        val original = TestSignals.sine(440.0, 1.0, sampleRate)
        val bytes = ByteArrayOutputStream()
        WavWriter.write(original, bytes, WavBitDepth.PCM_16)
        val full = bytes.toByteArray()
        val truncated = full.copyOf(full.size / 2)

        val decoded = WavReader.read(ByteArrayInputStream(truncated))
        val expectedFrames = (truncated.size - WavWriter.HEADER_BYTES) / 2
        assertEquals(expectedFrames, decoded.frameCount)
        assertTrue(decoded.frameCount > 0, "half a recording is much better than none")
    }

    @Test
    fun `header repair rewrites both size fields`() {
        val original = TestSignals.sine(440.0, 1.0, sampleRate)
        val bytes = ByteArrayOutputStream()
        WavWriter.write(original, bytes, WavBitDepth.PCM_16)
        val full = bytes.toByteArray()

        val truncated = full.copyOf(full.size / 2)
        val header = truncated.copyOf(WavWriter.HEADER_BYTES)
        val dataBytes = WavWriter.repairTruncated(header, truncated.size.toLong())
        header.copyInto(truncated, 0, 0, WavWriter.HEADER_BYTES)

        assertEquals((truncated.size - WavWriter.HEADER_BYTES).toLong(), dataBytes)
        val info = WavReader.readInfo(ByteArrayInputStream(truncated), truncated.size.toLong())
        assertEquals((dataBytes / 2).toInt(), info.frameCount)
    }

    @Test
    fun `a file that is not a WAV is refused with an explainable message`() {
        val notAWav = "This is a text file, not audio at all.".toByteArray()
        val error = runCatching { WavReader.read(ByteArrayInputStream(notAWav)) }.exceptionOrNull()
        assertTrue(error is MalformedAudioException)
        assertTrue(
            error.message!!.contains("WAV"),
            "the message should tell the user what SAJJIL can actually open",
        )
    }

    @Test
    fun `samples beyond full scale are clamped rather than wrapped`() {
        // Wrapping would turn a loud peak into a full-scale click in the opposite direction.
        val hot = AudioBuffer(sampleRate, arrayOf(floatArrayOf(1.5f, -1.5f, 0.5f)))
        val bytes = ByteArrayOutputStream()
        WavWriter.write(hot, bytes, WavBitDepth.PCM_16)
        val decoded = WavReader.read(ByteArrayInputStream(bytes.toByteArray()))

        assertTrue(decoded[0][0] > 0.99f, "positive overshoot should clamp near +1")
        assertTrue(decoded[0][1] < -0.99f, "negative overshoot should clamp near -1")
    }

    private fun roundTripError(original: AudioBuffer, depth: WavBitDepth): Double {
        val bytes = ByteArrayOutputStream()
        WavWriter.write(original, bytes, depth)
        val decoded = WavReader.read(ByteArrayInputStream(bytes.toByteArray()))
        return TestSignals.maxAbsoluteDifference(original, decoded)
    }
}

class FlacEncoderTest {

    private val sampleRate = 48000

    @Test
    fun `output begins with the FLAC signature and a STREAMINFO block`() {
        val bytes = encode(TestSignals.sine(440.0, 0.5, sampleRate))

        assertEquals("fLaC", String(bytes.copyOfRange(0, 4), Charsets.US_ASCII))
        // Metadata block header: last-block flag set, type 0, length 34.
        assertEquals(0x80, bytes[4].toInt() and 0xFF, "STREAMINFO should be the last metadata block")
        val length = ((bytes[5].toInt() and 0xFF) shl 16) or
            ((bytes[6].toInt() and 0xFF) shl 8) or (bytes[7].toInt() and 0xFF)
        assertEquals(34, length)
    }

    @Test
    fun `STREAMINFO declares the real sample rate channels and length`() {
        val original = TestSignals.sine(440.0, 0.5, sampleRate, channels = 2)
        val bytes = encode(original, channels = 2)

        // Sample rate is 20 bits starting at bit 80 of the 34-byte block body (offset 8).
        val body = bytes.copyOfRange(8, 8 + 34)
        val rate = ((body[10].toInt() and 0xFF) shl 12) or
            ((body[11].toInt() and 0xFF) shl 4) or
            ((body[12].toInt() and 0xFF) shr 4)
        assertEquals(sampleRate, rate)

        val channels = ((body[12].toInt() shr 1) and 0x07) + 1
        assertEquals(2, channels)

        val totalSamples = ((body[13].toLong() and 0x0FL) shl 32) or
            ((body[14].toLong() and 0xFFL) shl 24) or
            ((body[15].toLong() and 0xFFL) shl 16) or
            ((body[16].toLong() and 0xFFL) shl 8) or
            (body[17].toLong() and 0xFFL)
        assertEquals(original.frameCount.toLong(), totalSamples)
    }

    @Test
    fun `encoding actually compresses a tone`() {
        val original = TestSignals.sine(440.0, 2.0, sampleRate)
        val flac = encode(original)
        val uncompressed = original.frameCount * 2
        assertTrue(
            flac.size < uncompressed * 0.6,
            "a pure tone should compress well: ${flac.size} bytes against $uncompressed raw",
        )
    }

    @Test
    fun `silence compresses to almost nothing`() {
        // Constant subframes exist for exactly this, and silence between takes is common.
        val silence = AudioBuffer.silence(sampleRate, 1, sampleRate * 5)
        val flac = encode(silence)
        assertTrue(flac.size < 4000, "five seconds of silence encoded to ${flac.size} bytes")
    }

    @Test
    fun `noise still encodes without expanding much`() {
        // Incompressible content must fall back to verbatim rather than ballooning.
        val noise = TestSignals.noise(1.0, sampleRate, amplitude = 0.9)
        val flac = encode(noise)
        val uncompressed = noise.frameCount * 2
        assertTrue(
            flac.size < uncompressed * 1.05,
            "noise expanded to ${flac.size} bytes from $uncompressed",
        )
    }

    @Test
    fun `a final partial block is encoded`() {
        // Recordings are never an exact multiple of the block size.
        val awkward = AudioBuffer(sampleRate, arrayOf(FloatArray(4096 + 137) { 0.25f }))
        val flac = encode(awkward)
        assertTrue(flac.size > 42, "the encoder produced no frames at all")
    }

    @Test
    fun `every declared bit depth is accepted`() {
        for (depth in listOf(8, 16, 24)) {
            val out = ByteArrayOutputStream()
            FlacEncoder(sampleRate, 1, bitsPerSample = depth)
                .encode(TestSignals.sine(440.0, 0.1, sampleRate), out)
            assertTrue(out.size() > 42, "$depth-bit encoding produced nothing")
        }
    }

    @Test
    fun `an unsupported bit depth is refused clearly`() {
        val error = runCatching { FlacEncoder(sampleRate, 1, bitsPerSample = 12) }.exceptionOrNull()
        assertTrue(error is IllegalArgumentException)
        assertTrue(error.message!!.contains("12"))
    }

    @Test
    fun `progress is reported and reaches one`() {
        val seen = ArrayList<Double>()
        FlacEncoder(sampleRate, 1).encode(
            TestSignals.sine(440.0, 2.0, sampleRate),
            ByteArrayOutputStream(),
        ) { seen += it }

        assertTrue(seen.isNotEmpty(), "no progress was reported")
        assertEquals(1.0, seen.last())
        assertTrue(seen.zipWithNext().all { (a, b) -> b >= a }, "progress went backwards")
    }

    private fun encode(buffer: AudioBuffer, channels: Int = 1): ByteArray {
        val out = ByteArrayOutputStream()
        FlacEncoder(sampleRate, channels).encode(buffer, out)
        return out.toByteArray()
    }
}
