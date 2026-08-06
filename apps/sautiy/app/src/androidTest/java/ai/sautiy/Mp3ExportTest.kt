package ai.sautiy

import ai.sautiy.core.audio.AudioBuffer
import ai.sautiy.core.codec.Encoders
import ai.sautiy.core.codec.ExportFormat
import ai.sautiy.core.codec.ExportMetadata
import ai.sautiy.export.Mp3Encoder
import ai.sautiy.export.PlatformEncoders
import android.media.MediaCodec
import android.media.MediaExtractor
import android.media.MediaFormat
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.ByteArrayOutputStream
import java.io.File
import kotlin.math.abs
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

/**
 * MP3 export, verified with Android's own decoder.
 *
 * MP3 is a release blocker, so "it produced some bytes" is not a result. The file has to be one
 * another program will open — so these tests hand it to `MediaExtractor` and `MediaCodec`, which
 * is literally the code every other Android application uses to open an audio file. If the
 * platform decoder reports the right MIME type, the right duration and the right channel layout,
 * and then decodes real PCM out of it, the file is a valid MP3 by the only definition that
 * matters to a user.
 *
 * It also asserts that MP3 is *present*. A build where the native encoder was silently left out
 * would still pass a test that skipped when it was missing, and the user would find out by
 * looking for MP3 in the export panel and not seeing it.
 */
@RunWith(AndroidJUnit4::class)
class Mp3ExportTest {

    private val context = InstrumentationRegistry.getInstrumentation().targetContext
    private val workspace: File = File(context.cacheDir, "mp3-test").apply {
        deleteRecursively()
        mkdirs()
    }

    @Before
    fun registerPlatformEncoders() {
        PlatformEncoders.registerAll()
    }

    @After
    fun tearDown() {
        workspace.deleteRecursively()
    }

    /** A tone at a known frequency, so the decoded audio can be checked for being the same sound. */
    private fun tone(seconds: Double, sampleRate: Int = 44_100, hz: Double = 440.0): AudioBuffer {
        val frames = (seconds * sampleRate).toInt()
        val samples = FloatArray(frames)
        val step = 2.0 * Math.PI * hz / sampleRate
        for (i in 0 until frames) samples[i] = (0.6 * kotlin.math.sin(step * i)).toFloat()
        return AudioBuffer.mono(samples, sampleRate)
    }

    private fun encodeMp3(audio: AudioBuffer, name: String, metadata: ExportMetadata): File {
        val file = File(workspace, name)
        file.outputStream().use { out ->
            Encoders.create(ExportFormat.MP3).encode(audio, out, metadata) {}
        }
        return file
    }

    /** What the platform decoder makes of a file: MIME, duration, rate, channels, decoded frames. */
    private data class Decoded(
        val mime: String,
        val durationSeconds: Double,
        val sampleRate: Int,
        val channelCount: Int,
        val pcmFrames: Long,
        val peak: Float,
    )

    private fun decodeWithAndroid(file: File): Decoded {
        val extractor = MediaExtractor()
        extractor.setDataSource(file.absolutePath)
        assertTrue("The platform found no tracks in the file", extractor.trackCount > 0)

        val format = extractor.getTrackFormat(0)
        val mime = format.getString(MediaFormat.KEY_MIME) ?: ""
        val sampleRate = format.getInteger(MediaFormat.KEY_SAMPLE_RATE)
        val channels = format.getInteger(MediaFormat.KEY_CHANNEL_COUNT)
        val durationUs = if (format.containsKey(MediaFormat.KEY_DURATION)) {
            format.getLong(MediaFormat.KEY_DURATION)
        } else {
            0L
        }
        extractor.selectTrack(0)

        val codec = MediaCodec.createDecoderByType(mime)
        codec.configure(format, null, null, 0)
        codec.start()

        var decodedFrames = 0L
        var peak = 0f
        val info = MediaCodec.BufferInfo()
        var sawInputEnd = false
        var sawOutputEnd = false
        var outputChannels = channels

        while (!sawOutputEnd) {
            if (!sawInputEnd) {
                val index = codec.dequeueInputBuffer(10_000)
                if (index >= 0) {
                    val buffer = codec.getInputBuffer(index)!!
                    val size = extractor.readSampleData(buffer, 0)
                    if (size < 0) {
                        codec.queueInputBuffer(index, 0, 0, 0, MediaCodec.BUFFER_FLAG_END_OF_STREAM)
                        sawInputEnd = true
                    } else {
                        codec.queueInputBuffer(index, 0, size, extractor.sampleTime, 0)
                        extractor.advance()
                    }
                }
            }

            val outIndex = codec.dequeueOutputBuffer(info, 10_000)
            when {
                outIndex >= 0 -> {
                    val buffer = codec.getOutputBuffer(outIndex)!!
                    val shorts = buffer.order(java.nio.ByteOrder.LITTLE_ENDIAN).asShortBuffer()
                    val count = info.size / 2
                    for (i in 0 until count) {
                        val value = abs(shorts.get(i).toFloat() / Short.MAX_VALUE)
                        if (value > peak) peak = value
                    }
                    decodedFrames += (count / outputChannels).toLong()
                    codec.releaseOutputBuffer(outIndex, false)
                    if (info.flags and MediaCodec.BUFFER_FLAG_END_OF_STREAM != 0) sawOutputEnd = true
                }

                outIndex == MediaCodec.INFO_OUTPUT_FORMAT_CHANGED -> {
                    outputChannels = codec.outputFormat.getInteger(MediaFormat.KEY_CHANNEL_COUNT)
                }
            }
        }

        codec.stop()
        codec.release()
        extractor.release()

        return Decoded(mime, durationUs / 1_000_000.0, sampleRate, channels, decodedFrames, peak)
    }

    // --- The release blocker -------------------------------------------------------------------

    @Test
    fun mp3IsPresentInThisBuild() {
        // Not "skip if missing". An APK without the encoder is a build the user cannot export
        // MP3 from, and that is a failure, not a configuration.
        assertTrue(
            "The native MP3 encoder did not load. MP3 export is a release blocker; see " +
                "app/src/main/cpp/README.md and the CI workflow's LAME step. " +
                "Reason: ${Mp3Encoder.unavailableReason ?: "none reported"}",
            Mp3Encoder.isAvailable,
        )
        assertTrue("MP3 is not registered, so it would not appear in the export panel", Encoders.isAvailable(ExportFormat.MP3))
        assertTrue("MP3 is missing from the export panel's list", ExportFormat.MP3 in Encoders.available())
    }

    @Test
    fun anExportedMp3OpensInThePlatformDecoder() {
        val source = tone(2.0)
        val file = encodeMp3(source, "tone.mp3", ExportMetadata(title = "SAUTIY test tone"))

        assertTrue("Nothing was written", file.length() > 1_000)
        val decoded = decodeWithAndroid(file)

        assertEquals("The platform did not recognise this as MP3", "audio/mpeg", decoded.mime)
        assertEquals(44_100, decoded.sampleRate)
        assertEquals(1, decoded.channelCount)
    }

    @Test
    fun anExportedMp3KeepsItsDuration() {
        val source = tone(3.0)
        val file = encodeMp3(source, "duration.mp3", ExportMetadata(title = "Duration"))
        val decoded = decodeWithAndroid(file)

        // MP3 pads to a whole frame and the encoder's own delay adds a little, so exactness is
        // not available; a recording that came back a second short would be.
        assertEquals("Declared duration is wrong", 3.0, decoded.durationSeconds, 0.15)
        assertEquals(
            "Decoded length is wrong: ${decoded.pcmFrames} frames at ${decoded.sampleRate} Hz",
            3.0,
            decoded.pcmFrames.toDouble() / decoded.sampleRate,
            0.15,
        )
    }

    @Test
    fun anExportedMp3ContainsTheAudioAndNotSilence() {
        val source = tone(1.5)
        val file = encodeMp3(source, "audible.mp3", ExportMetadata(title = "Audible"))
        val decoded = decodeWithAndroid(file)

        // The source peaks at 0.6. A file that decoded to silence would still have the right
        // duration and the right headers, and would be useless.
        assertTrue("The MP3 decoded to silence, peak was ${decoded.peak}", decoded.peak > 0.3f)
        assertTrue("The MP3 decoded to something clipped, peak was ${decoded.peak}", decoded.peak <= 1.0f)
    }

    @Test
    fun anExportedMp3StartsWithAValidId3TagAndThenAFrameSync() {
        val file = encodeMp3(tone(0.5), "tagged.mp3", ExportMetadata(title = "SAUTIY", artist = "Test"))
        val bytes = file.readBytes()

        assertEquals('I'.code.toByte(), bytes[0])
        assertEquals('D'.code.toByte(), bytes[1])
        assertEquals('3'.code.toByte(), bytes[2])

        // The synchsafe size tells us where the audio starts; the first two bytes there must be
        // an MPEG frame sync. A tag whose size is wrong is the classic way a file plays in one
        // application and not in another.
        var tagSize = 0
        for (i in 6..9) tagSize = (tagSize shl 7) or (bytes[i].toInt() and 0x7F)
        val audioStart = 10 + tagSize
        assertTrue("The tag claims to be longer than the file", audioStart < bytes.size - 4)

        val sync = ((bytes[audioStart].toInt() and 0xFF) shl 3) or
            ((bytes[audioStart + 1].toInt() and 0xE0) shr 5)
        assertEquals("No MPEG frame sync where the ID3 tag says the audio begins", 0x7FF, sync)
    }

    @Test
    fun stereoAndEveryOfferedSampleRateSurviveTheRoundTrip() {
        // 44 100 and 48 000 are what SAUTIY records at; both must come back correctly, in mono
        // and in stereo, or "export to MP3" is conditional on settings the user never chose.
        for (rate in listOf(44_100, 48_000)) {
            for (channels in listOf(1, 2)) {
                val mono = tone(1.0, rate)
                val source = if (channels == 1) mono else mono.toStereo()
                val file = encodeMp3(source, "rt-$rate-$channels.mp3", ExportMetadata(title = "Round trip"))
                val decoded = decodeWithAndroid(file)

                assertEquals("$rate Hz / $channels ch: wrong rate", rate, decoded.sampleRate)
                assertEquals("$rate Hz / $channels ch: wrong channel count", channels, decoded.channelCount)
                assertEquals(
                    "$rate Hz / $channels ch: wrong duration",
                    1.0,
                    decoded.pcmFrames.toDouble() / decoded.sampleRate,
                    0.15,
                )
                assertTrue("$rate Hz / $channels ch: decoded to silence", decoded.peak > 0.3f)
            }
        }
    }

    @Test
    fun theExportedFileCanBeHandedToAnotherApplication() {
        // Sharing goes through the declared FileProvider as a content:// URI — a file path would
        // be rejected by every Android since Nougat. This is that path, end to end.
        val file = File(context.filesDir, "exports").apply { mkdirs() }.resolve("shared.mp3")
        file.outputStream().use { out ->
            Encoders.create(ExportFormat.MP3).encode(tone(1.0), out, ExportMetadata(title = "Shared")) {}
        }

        val uri = androidx.core.content.FileProvider.getUriForFile(
            context,
            "${context.packageName}.files",
            file,
        )
        assertEquals("content", uri.scheme)

        // The receiving application opens it exactly like this.
        context.contentResolver.openInputStream(uri).use { stream ->
            val head = ByteArray(3)
            assertEquals(3, stream!!.read(head))
            assertEquals("The shared file is not the MP3 that was written", "ID3", String(head))
        }
        assertEquals("audio/mpeg", ExportFormat.MP3.mimeType)

        file.delete()
    }

    @Test
    fun encodingAndDecodingALongRecordingDoesNotLeakOrStall() {
        // Ninety-minute lectures are the point of this application. Two minutes is enough to
        // catch a leak or a quadratic loop while keeping the test honest about its runtime.
        val source = tone(120.0)
        val started = System.currentTimeMillis()
        val sink = ByteArrayOutputStream()
        var lastProgress = 0.0
        Encoders.create(ExportFormat.MP3).encode(source, sink, ExportMetadata(title = "Long")) { p ->
            assertTrue("Progress went backwards", p >= lastProgress - 1e-9)
            lastProgress = p
        }
        val elapsed = System.currentTimeMillis() - started

        assertEquals(1.0, lastProgress, 1e-9)
        assertTrue("Two minutes of audio produced only ${sink.size()} bytes", sink.size() > 100_000)
        // At 128 kbps, two minutes is about 1.9 MB. Encoding must be far faster than real time
        // or a lecture would take longer to export than it took to record.
        assertTrue("Encoding two minutes took ${elapsed}ms — slower than a quarter of real time", elapsed < 30_000)
    }
}
