package ai.sautiy.core.audio

import ai.sautiy.core.TestSignals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class PcmCodecTest {

    @Test
    fun `every encoding survives a round trip within its own quantisation step`() {
        val source = TestSignals.sine(1_000.0, 0.05, 48_000, amplitude = 0.8)

        val tolerances = mapOf(
            SampleEncoding.PCM_8_UNSIGNED to 1.0 / 128,
            SampleEncoding.PCM_16_LE to 1.0 / 32768,
            SampleEncoding.PCM_24_LE to 1.0 / 8388608,
            SampleEncoding.PCM_32_LE to 1e-7,
            SampleEncoding.FLOAT_32_LE to 0.0,
            SampleEncoding.FLOAT_64_LE to 0.0,
        )

        for ((encoding, tolerance) in tolerances) {
            val bytes = PcmCodec.encode(source, encoding)
            val format = AudioFormat(source.sampleRate, source.channelCount, encoding)
            val decoded = PcmCodec.decode(bytes, format)

            assertEquals("$encoding changed the frame count", source.frameCount, decoded.frameCount)
            for (i in 0 until source.frameCount) {
                val error = kotlin.math.abs(source.channels[0][i] - decoded.channels[0][i])
                assertTrue(
                    "$encoding error $error at frame $i exceeds one quantisation step $tolerance",
                    error <= tolerance + 1e-9,
                )
            }
        }
    }

    @Test
    fun `full scale positive never wraps to full scale negative`() {
        // The classic conversion bug: scaling by 32768 makes +1.0 become -32768, turning the
        // loudest moment of a recording into a maximally negative sample — a single sample
        // click at exactly the peak, on every peak.
        val fullScale = AudioBuffer.mono(floatArrayOf(1.0f, 0.999999f, -1.0f, 0.0f), 48_000)

        for (encoding in listOf(SampleEncoding.PCM_16_LE, SampleEncoding.PCM_24_LE, SampleEncoding.PCM_32_LE)) {
            val bytes = PcmCodec.encode(fullScale, encoding)
            val decoded = PcmCodec.decode(bytes, AudioFormat(48_000, 1, encoding))

            assertTrue("$encoding wrapped +1.0 to a negative sample", decoded.channels[0][0] > 0.99f)
            assertTrue("$encoding wrapped a near-full-scale sample", decoded.channels[0][1] > 0.99f)
            assertTrue("$encoding mishandled -1.0", decoded.channels[0][2] < -0.99f)
            assertEquals(0.0f, decoded.channels[0][3], 1e-6f)
        }
    }

    @Test
    fun `values beyond full scale are clamped, not wrapped`() {
        val hot = AudioBuffer.mono(floatArrayOf(2.5f, -3.0f), 48_000)
        val bytes = PcmCodec.encode(hot, SampleEncoding.PCM_16_LE)
        val decoded = PcmCodec.decode(bytes, AudioFormat(48_000, 1, SampleEncoding.PCM_16_LE))
        assertTrue(decoded.channels[0][0] > 0.99f)
        assertTrue(decoded.channels[0][1] < -0.99f)
    }

    @Test
    fun `stereo interleaving keeps the channels apart`() {
        val left = FloatArray(4) { it * 0.1f }
        val right = FloatArray(4) { -it * 0.1f }
        val stereo = AudioBuffer(arrayOf(left, right), 48_000)

        val bytes = PcmCodec.encode(stereo, SampleEncoding.FLOAT_32_LE)
        val decoded = PcmCodec.decode(bytes, AudioFormat(48_000, 2, SampleEncoding.FLOAT_32_LE))

        assertEquals(2, decoded.channelCount)
        for (i in 0 until 4) {
            assertEquals(left[i], decoded.channels[0][i], 1e-7f)
            assertEquals(right[i], decoded.channels[1][i], 1e-7f)
        }
    }

    @Test
    fun `the capture hot path decodes device shorts identically to the byte path`() {
        val shorts = ShortArray(8) { ((it - 4) * 4096).toShort() }
        val viaShorts = PcmCodec.decodeInt16(shorts, shorts.size, channelCount = 2, sampleRate = 48_000)

        val bytes = ByteArray(shorts.size * 2)
        for (i in shorts.indices) {
            bytes[i * 2] = (shorts[i].toInt() and 0xFF).toByte()
            bytes[i * 2 + 1] = ((shorts[i].toInt() shr 8) and 0xFF).toByte()
        }
        val viaBytes = PcmCodec.decode(bytes, AudioFormat(48_000, 2, SampleEncoding.PCM_16_LE))

        assertEquals(viaBytes.frameCount, viaShorts.frameCount)
        for (c in 0 until 2) {
            for (i in 0 until viaBytes.frameCount) {
                assertEquals(viaBytes.channels[c][i], viaShorts.channels[c][i], 0f)
            }
        }
    }

    @Test
    fun `interleave and split are exact inverses`() {
        val original = TestSignals.sine(440.0, 0.01, 48_000, channels = 2)
        val round = AudioBuffer.fromInterleaved(original.interleave(), 2, 48_000)
        assertEquals(original.frameCount, round.frameCount)
        for (c in 0 until 2) {
            for (i in 0 until original.frameCount) {
                assertEquals(original.channels[c][i], round.channels[c][i], 0f)
            }
        }
    }
}

class AudioBufferTest {

    @Test
    fun `peak and rms report the truth for a known sine`() {
        val sine = TestSignals.sine(1_000.0, 1.0, 48_000, amplitude = 0.5)
        assertEquals("peak of a 0.5 sine", 0.5, sine.peak().toDouble(), 1e-3)
        // RMS of a sine is its amplitude over the square root of two.
        assertEquals("rms of a 0.5 sine", 0.5 / kotlin.math.sqrt(2.0), sine.rms(), 1e-3)
    }

    @Test
    fun `clipping is detected and counted honestly`() {
        val hot = AudioBuffer.mono(floatArrayOf(0.5f, 1.0f, -1.0f, 0.2f), 48_000)
        assertTrue(hot.hasClipping())
        assertEquals(2, hot.clippedSampleCount())

        val clean = AudioBuffer.mono(floatArrayOf(0.5f, 0.9f, -0.9f), 48_000)
        assertTrue(!clean.hasClipping())
        assertEquals(0, clean.clippedSampleCount())
    }

    @Test
    fun `mixing a mono layer feeds every channel of a stereo mix`() {
        val mix = AudioBuffer.silence(2, 100, 48_000)
        val layer = AudioBuffer.mono(FloatArray(50) { 0.4f }, 48_000)
        mix.mixInPlace(layer, atFrame = 10, gain = 0.5f)

        assertEquals(0f, mix.channels[0][9], 0f)
        assertEquals(0.2f, mix.channels[0][10], 1e-6f)
        assertEquals(0.2f, mix.channels[1][10], 1e-6f)
        assertEquals(0.2f, mix.channels[0][59], 1e-6f)
        assertEquals(0f, mix.channels[0][60], 0f)
    }

    @Test
    fun `mixing past the end discards rather than growing or crashing`() {
        val mix = AudioBuffer.silence(1, 10, 48_000)
        val layer = AudioBuffer.mono(FloatArray(100) { 1f }, 48_000)
        mix.mixInPlace(layer, atFrame = 8)
        assertEquals(10, mix.frameCount)
        assertEquals(1f, mix.channels[0][9], 1e-6f)
    }

    @Test
    fun `slicing and concatenating reconstruct the original exactly`() {
        val original = TestSignals.noise(0.05, 48_000)
        val parts = listOf(
            original.slice(0, 100),
            original.slice(100, 900),
            original.slice(900, original.frameCount),
        )
        val rebuilt = AudioBuffer.concat(parts)
        assertEquals(original.frameCount, rebuilt.frameCount)
        for (i in 0 until original.frameCount) {
            assertEquals(original.channels[0][i], rebuilt.channels[0][i], 0f)
        }
    }

    @Test
    fun `copy is deep so non-destructive editing is actually non-destructive`() {
        val original = TestSignals.sine(440.0, 0.01, 48_000)
        val copy = original.copy()
        copy.applyGain(0.0f)
        assertTrue("Mutating a copy changed the original", original.peak() > 0.4f)
        assertEquals(0f, copy.peak(), 0f)
    }

    @Test
    fun `decibel conversion has a real floor and formats with a true minus sign`() {
        assertEquals(0.0, Decibels.fromLinear(1.0), 1e-9)
        assertEquals(-6.0206, Decibels.fromLinear(0.5), 1e-3)
        assertEquals(Decibels.FLOOR_DB, Decibels.fromLinear(0.0), 0.0)
        assertTrue("Silence must not read as negative infinity", Decibels.fromLinear(0.0).isFinite())

        assertEquals("−6.0 dB", Decibels.format(-6.0))
        assertEquals("+3.0 dB", Decibels.format(3.0))
        assertEquals("−∞ dB", Decibels.format(-200.0))
    }

    @Test
    fun `capture quality states remaining time from the real bitrate`() {
        val oneGigabyte = 1024L * 1024 * 1024
        for (quality in CaptureQuality.entries) {
            val seconds = quality.secondsAvailable(oneGigabyte)
            val expected = (oneGigabyte - CaptureQuality.SAFETY_MARGIN_BYTES) / quality.bytesPerSecond
            assertEquals(quality.name, expected, seconds)
            assertTrue("${quality.name} must report a usable duration", seconds > 60)
        }
        // Voice is the smallest, Stereo the largest — the ordering the user is promised.
        assertTrue(
            CaptureQuality.VOICE.bytesPerSecond < CaptureQuality.STUDIO.bytesPerSecond,
        )
        assertTrue(
            CaptureQuality.MASTER.bytesPerSecond < CaptureQuality.STEREO.bytesPerSecond,
        )
    }

    @Test
    fun `an almost full volume promises nothing`() {
        assertEquals(0L, CaptureQuality.STUDIO.secondsAvailable(1024))
    }
}
