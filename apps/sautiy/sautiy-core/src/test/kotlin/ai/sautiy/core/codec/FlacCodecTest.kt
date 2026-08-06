package ai.sautiy.core.codec

import ai.sautiy.core.TestSignals
import ai.sautiy.core.audio.AudioBuffer
import java.io.ByteArrayOutputStream
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * A lossless codec that has only been eyeballed is not a lossless codec. Every test here
 * decodes what the encoder wrote and compares sample for sample.
 */
class FlacCodecTest {

    private val rate = 48_000

    private fun roundTrip(audio: AudioBuffer, encoder: FlacEncoder = FlacEncoder()): Pair<AudioBuffer, Int> {
        val out = ByteArrayOutputStream()
        encoder.encode(audio, out)
        val bytes = out.toByteArray()
        return FlacDecoder.decode(bytes) to bytes.size
    }

    /** Quantises to the same grid the encoder uses, so comparisons are like for like. */
    private fun quantised(audio: AudioBuffer, bits: Int = 16): AudioBuffer {
        val scale = (1 shl (bits - 1)).toFloat()
        val limit = 1 shl (bits - 1)
        return AudioBuffer(
            Array(audio.channelCount) { c ->
                FloatArray(audio.frameCount) { i ->
                    Math.round(audio.channels[c][i].coerceIn(-1f, 1f) * scale)
                        .coerceIn(-limit, limit - 1) / scale
                }
            },
            audio.sampleRate,
        )
    }

    @Test
    fun `a tone round trips bit exactly`() {
        val original = TestSignals.sine(440.0, 1.0, rate, amplitude = 0.7)
        val (decoded, _) = roundTrip(original)
        val expected = quantised(original)

        assertEquals(expected.frameCount, decoded.frameCount)
        for (i in 0 until expected.frameCount) {
            assertEquals("Sample $i differs", expected.channels[0][i], decoded.channels[0][i], 0f)
        }
    }

    @Test
    fun `noise round trips bit exactly, which is the hardest case for a predictor`() {
        val original = TestSignals.noise(0.7, rate, amplitude = 0.6, seed = 4_242)
        val (decoded, _) = roundTrip(original)
        val expected = quantised(original)

        for (i in 0 until expected.frameCount) {
            assertEquals("Sample $i differs", expected.channels[0][i], decoded.channels[0][i], 0f)
        }
    }

    @Test
    fun `stereo round trips bit exactly with the channels kept apart`() {
        val left = TestSignals.sine(300.0, 0.5, rate, amplitude = 0.5).channels[0]
        val right = TestSignals.sine(2_500.0, 0.5, rate, amplitude = 0.3).channels[0]
        val original = AudioBuffer(arrayOf(left, right), rate)

        val (decoded, _) = roundTrip(original)
        val expected = quantised(original)

        assertEquals(2, decoded.channelCount)
        for (c in 0 until 2) {
            for (i in 0 until expected.frameCount) {
                assertEquals("Channel $c sample $i", expected.channels[c][i], decoded.channels[c][i], 0f)
            }
        }
    }

    @Test
    fun `silence round trips and costs almost nothing`() {
        val silence = TestSignals.silence(2.0, rate)
        val (decoded, size) = roundTrip(silence)

        assertEquals(silence.frameCount, decoded.frameCount)
        assertEquals(0f, decoded.peak(), 0f)
        assertTrue(
            "Two seconds of silence took $size bytes — the constant-subframe path is not working",
            size < 2_000,
        )
    }

    @Test
    fun `speech-like material compresses well below the equivalent wav`() {
        // The reason FLAC is in the product: a reciter keeping thirty takes should not have to
        // choose between quality and storage.
        val seconds = 3.0
        val frames = (seconds * rate).toInt()
        val samples = FloatArray(frames)
        val random = java.util.Random(9)
        for (i in 0 until frames) {
            val t = i.toDouble() / rate
            val envelope = if ((t * 2).toInt() % 2 == 0) 0.4 else 0.05
            samples[i] = (
                envelope * (
                    kotlin.math.sin(2 * Math.PI * 160 * t) +
                        0.4 * kotlin.math.sin(2 * Math.PI * 480 * t)
                    ) / 1.4 + random.nextGaussian() * 0.002
                ).toFloat()
        }
        val original = AudioBuffer.mono(samples, rate)

        val (decoded, size) = roundTrip(original)
        val wavBytes = frames * 2

        for (i in 0 until frames) {
            assertEquals(quantised(original).channels[0][i], decoded.channels[0][i], 0f)
        }
        assertTrue(
            "FLAC produced $size bytes against $wavBytes for WAV — no compression achieved",
            size < wavBytes * 0.75,
        )
    }

    @Test
    fun `a block that is not a whole multiple of the block size still round trips`() {
        // The last block of a real recording is almost never a full 4096 frames.
        val original = TestSignals.sine(1_000.0, 0.0, rate).let {
            TestSignals.noise(4_097.0 / rate, rate, amplitude = 0.5, seed = 3)
        }
        val (decoded, _) = roundTrip(original)
        assertEquals(original.frameCount, decoded.frameCount)
        val expected = quantised(original)
        for (i in 0 until expected.frameCount) {
            assertEquals(expected.channels[0][i], decoded.channels[0][i], 0f)
        }
    }

    @Test
    fun `the stream announces itself correctly to any decoder`() {
        val out = ByteArrayOutputStream()
        FlacEncoder().encode(TestSignals.sine(440.0, 0.2, rate), out)
        val bytes = out.toByteArray()

        assertEquals("fLaC", String(bytes, 0, 4, Charsets.US_ASCII))
        assertEquals("First metadata block must be STREAMINFO", 0x00, bytes[4].toInt() and 0xFF)
        // STREAMINFO is always exactly 34 bytes.
        val length = ((bytes[5].toInt() and 0xFF) shl 16) or
            ((bytes[6].toInt() and 0xFF) shl 8) or (bytes[7].toInt() and 0xFF)
        assertEquals(34, length)
    }

    @Test
    fun `sample rate and channel count survive the header`() {
        for (sampleRate in listOf(24_000, 44_100, 48_000)) {
            for (channels in listOf(1, 2)) {
                val original = TestSignals.sine(440.0, 0.2, sampleRate, amplitude = 0.4, channels = channels)
                val (decoded, _) = roundTrip(original)
                assertEquals("$sampleRate Hz", sampleRate, decoded.sampleRate)
                assertEquals("$channels channels", channels, decoded.channelCount)
            }
        }
    }

    @Test
    fun `metadata is written as a vorbis comment`() {
        val out = ByteArrayOutputStream()
        FlacEncoder().encode(
            TestSignals.sine(440.0, 0.2, rate),
            out,
            ExportMetadata(title = "Al-Fatihah", artist = "Imam Ahmad Sulaimiy", year = 2026),
        )
        val text = String(out.toByteArray(), Charsets.UTF_8)

        assertTrue("Title must be written", text.contains("TITLE=Al-Fatihah"))
        assertTrue("Artist must be written", text.contains("ARTIST=Imam Ahmad Sulaimiy"))
        assertTrue("Every file must be traceable to what made it", text.contains("ENCODER=SAUTIY"))
    }

    @Test
    fun `full scale material does not overflow the predictor`() {
        // Fixed predictors of order 4 can produce residuals several times the sample range;
        // this is the case that finds an encoder that assumed otherwise.
        val samples = FloatArray(8_192)
        for (i in samples.indices) samples[i] = if (i % 2 == 0) 1.0f else -1.0f
        val original = AudioBuffer.mono(samples, rate)

        val (decoded, _) = roundTrip(original)
        val expected = quantised(original)
        for (i in 0 until expected.frameCount) {
            assertEquals("Sample $i", expected.channels[0][i], decoded.channels[0][i], 0f)
        }
    }

    @Test
    fun `a corrupt stream is refused rather than decoded into noise`() {
        val failure = runCatching { FlacDecoder.decode("this is not audio".toByteArray()) }.exceptionOrNull()
        assertTrue(failure is FlacDecoder.FlacFormatException)
    }

    @Test
    fun `the encoder reports real progress`() {
        val steps = mutableListOf<Double>()
        FlacEncoder().encode(TestSignals.noise(1.0, rate), ByteArrayOutputStream()) { steps += it }

        assertTrue("Progress must be reported more than once", steps.size > 2)
        assertTrue("Progress must be monotonic", steps.zipWithNext().all { it.first <= it.second })
        assertEquals("Progress must finish at one", 1.0, steps.last(), 1e-9)
    }
}

class ExportRegistryTest {

    @Test
    fun `the panel only ever offers formats that can actually be written`() {
        for (format in Encoders.available()) {
            val encoder = Encoders.create(format)
            assertEquals(format, encoder.format)
        }
    }

    @Test
    fun `asking for an unregistered format fails loudly rather than writing nothing`() {
        // Listing a format and then silently producing no file is the worst possible outcome.
        if (!Encoders.isAvailable(ExportFormat.MP3)) {
            val failure = runCatching { Encoders.create(ExportFormat.MP3) }.exceptionOrNull()
            assertTrue(failure != null)
            assertTrue(failure!!.message!!.contains("must not offer"))
        }
    }

    @Test
    fun `a platform encoder can register itself without the core knowing about it`() {
        val fake = object : AudioEncoder {
            override val format: ExportFormat get() = ExportFormat.M4A
            override fun encode(
                audio: AudioBuffer,
                output: java.io.OutputStream,
                metadata: ExportMetadata,
                progress: (Double) -> Unit,
            ) {
                output.write(0)
                progress(1.0)
            }
        }
        Encoders.register(ExportFormat.M4A) { fake }
        assertTrue(Encoders.isAvailable(ExportFormat.M4A))
        assertEquals(ExportFormat.M4A, Encoders.create(ExportFormat.M4A).format)
    }

    @Test
    fun `every format explains itself in terms a person can choose between`() {
        for (format in ExportFormat.entries) {
            assertTrue(format.displayName.isNotBlank())
            assertTrue(format.extension.isNotBlank())
            assertTrue(format.mimeType.contains("/"))
            assertTrue(
                "${format.displayName} needs a summary that answers 'which one do I want?'",
                format.summary.length > 25,
            )
        }
        assertEquals("MP3 first: it is the answer for most people", ExportFormat.MP3, ExportFormat.panelOrder.first())
    }

    @Test
    fun `wav export round trips through the encoder interface`() {
        val original = TestSignals.sine(440.0, 0.3, 48_000, amplitude = 0.6)
        val out = java.io.ByteArrayOutputStream()
        Encoders.create(ExportFormat.WAV).encode(original, out)

        val file = java.io.File.createTempFile("sautiy", ".wav")
        file.writeBytes(out.toByteArray())
        try {
            val read = WavCodec.read(file)
            assertEquals(original.frameCount, read.frameCount)
            assertTrue(TestSignals.snrDb(original, read) > 110.0)
        } finally {
            file.delete()
        }
    }
}
