package ai.sautiy

import ai.sautiy.core.audio.AudioBuffer
import ai.sautiy.core.audio.CaptureQuality
import ai.sautiy.core.codec.ExportFormat
import ai.sautiy.core.codec.Encoders
import ai.sautiy.core.codec.ExportJob
import ai.sautiy.core.codec.WavCodec
import ai.sautiy.core.codec.WavStreamReader
import ai.sautiy.core.dsp.VoiceSpacePreset
import ai.sautiy.core.edit.AppendRecording
import ai.sautiy.core.edit.EditHistory
import ai.sautiy.core.edit.Layer
import ai.sautiy.core.edit.Source
import ai.sautiy.core.edit.SourceProvider
import ai.sautiy.core.edit.Timeline
import ai.sautiy.export.PlatformEncoders
import ai.sautiy.play.AudioPlayer
import ai.sautiy.record.AudioCapture
import android.Manifest
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.rule.GrantPermissionRule
import java.io.ByteArrayOutputStream
import java.io.File
import java.util.concurrent.atomic.AtomicInteger
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeoutOrNull
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/**
 * The device layer, exercised on a running Android.
 *
 * `AudioRecord`, `AudioTrack` and `MediaCodec` have no meaningful stand-in on the JVM, so every
 * claim about them has to come from here. Until this file existed, the entire Android half of
 * SAUTIY was "source complete" — written carefully, compiled, launched, and never once observed
 * to move a sample.
 *
 * The emulator has no microphone in front of it, so what is captured is near-silence. That is
 * fine: what these tests establish is that the device opens, that frames arrive, that the file
 * on disk is a real WAV of the right length, that playback runs, and that an export writes a
 * file another program could open. Whether the room sounded good is not a thing a CI runner can
 * tell you, and nothing here pretends otherwise.
 */
@RunWith(AndroidJUnit4::class)
class DeviceAudioTest {

    @get:Rule
    val permissions: GrantPermissionRule = GrantPermissionRule.grant(Manifest.permission.RECORD_AUDIO)

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val context = InstrumentationRegistry.getInstrumentation().targetContext
    private val workspace: File = File(context.cacheDir, "device-audio-test").apply {
        deleteRecursively()
        mkdirs()
    }

    @After
    fun tearDown() {
        scope.cancel()
        workspace.deleteRecursively()
    }

    /** Records for [seconds] and returns the file, the frames reported, and the blocks delivered. */
    private fun record(
        seconds: Double,
        quality: CaptureQuality = CaptureQuality.STUDIO,
    ): Triple<File, Long, Int> {
        val file = File(workspace, "take-${System.nanoTime()}.wav")
        val capture = AudioCapture(quality, scope)
        val blocks = AtomicInteger()
        capture.onBlock = { blocks.incrementAndGet() }

        val failure = capture.start(file)
        assertNull("The microphone did not open: $failure", failure)
        assertTrue("Capture did not report itself as recording", capture.isRecording)

        val wanted = (seconds * quality.format.sampleRate).toLong()
        val frames = runBlocking {
            withTimeoutOrNull((seconds * 4000).toLong() + 5_000) {
                capture.framesWritten.first { it >= wanted }
            }
            capture.stop()
        }
        return Triple(file, frames, blocks.get())
    }

    // --- Phase A: recording ------------------------------------------------------------------

    @Test
    fun recordingOpensTheDeviceAndWritesAPlayableFile() {
        val (file, frames, blocks) = record(1.5)

        assertTrue("No frames were captured", frames > 0)
        assertTrue("No blocks reached the waveform", blocks > 0)
        assertTrue("The take file was not written", file.isFile)

        val info = WavCodec.probe(file)
        assertEquals(CaptureQuality.STUDIO.format.sampleRate, info.format.sampleRate)
        assertEquals(CaptureQuality.STUDIO.format.channelCount, info.format.channelCount)
        assertEquals("The header does not agree with what capture reported", frames, info.frameCount)
        assertEquals("About 1.5 seconds should have been captured", 1.5, info.durationSeconds, 0.6)
    }

    @Test
    fun aRecordingIsCompleteOnDiskBeforeItIsStopped() {
        // Chapter 1.3.5: after every flush the file is a complete, playable WAV. This is what
        // makes a battery pull cost seconds rather than the whole lecture.
        val file = File(workspace, "durable.wav")
        val capture = AudioCapture(CaptureQuality.STUDIO, scope)
        assertNull(capture.start(file))

        runBlocking {
            withTimeoutOrNull(8_000) {
                capture.framesWritten.first { it >= CaptureQuality.STUDIO.format.sampleRate * 2L }
            }
        }

        // Read it while capture is still running, exactly as a recovery pass would.
        val midFlight = WavCodec.probe(file)
        assertTrue("Nothing was readable mid-recording", midFlight.frameCount > 0)

        val total = capture.stop()
        assertTrue("The file lost frames when it was closed", WavCodec.probe(file).frameCount >= midFlight.frameCount)
        assertTrue(total >= midFlight.frameCount)
    }

    @Test
    fun pauseAndResumeDoNotEndTheRecording() {
        val file = File(workspace, "paused.wav")
        val capture = AudioCapture(CaptureQuality.STUDIO, scope)
        assertNull(capture.start(file))

        runBlocking { withTimeoutOrNull(5_000) { capture.framesWritten.first { it > 0 } } }
        capture.pause()
        val atPause = capture.framesWritten.value

        // One read may already be in flight when pause is called, and that block holds audio
        // captured *before* the tap. Throwing it away to make the count freeze exactly would
        // lose audio the user did record, which is the one thing SAUTIY may not do. So the
        // contract is: pause stops promptly, and then stays stopped.
        Thread.sleep(400)
        val settled = capture.framesWritten.value
        val oneBuffer = CaptureQuality.STUDIO.format.sampleRate / 5L // 200 ms, generously
        assertTrue(
            "Pause let $atPause frames become $settled — that is more than one read in flight",
            settled - atPause <= oneBuffer,
        )

        Thread.sleep(400)
        assertEquals("Capture did not stay paused", settled, capture.framesWritten.value)
        assertTrue("Pausing ended the recording", capture.isRecording)

        capture.resume()
        runBlocking { withTimeoutOrNull(5_000) { capture.framesWritten.first { it > settled } } }
        assertTrue("Resuming did not resume", capture.framesWritten.value > settled)
        assertTrue(capture.stop() > settled)
    }

    @Test
    fun aSecondRecordingOpensAfterTheFirstIsStopped() {
        // A leaked AudioEffect keeps the audio session alive and the next recording fails to
        // open — a defect that only ever appears on the second take.
        val (_, first, _) = record(0.4)
        val (_, second, _) = record(0.4)
        assertTrue("The first recording captured nothing", first > 0)
        assertTrue("The second recording could not open the device", second > 0)
    }

    /**
     * A take written directly, with no microphone involved.
     *
     * Playback and export are tested against this rather than against a recording on purpose:
     * if the emulator's audio input is unavailable, that must fail the recording tests only. A
     * microphone problem hiding an encoder problem is how a whole layer goes unverified.
     */
    private fun syntheticTake(seconds: Double = 1.0, sampleRate: Int = 48_000): File {
        val frames = (seconds * sampleRate).toInt()
        val samples = FloatArray(frames)
        val step = 2.0 * Math.PI * 220.0 / sampleRate
        for (i in 0 until frames) samples[i] = (0.5 * kotlin.math.sin(step * i)).toFloat()

        val file = File(workspace, "synthetic-${System.nanoTime()}.wav")
        WavCodec.write(file, AudioBuffer.mono(samples, sampleRate))
        return file
    }

    // --- Phase B: playback -------------------------------------------------------------------

    private fun timelineFor(file: File): Pair<Timeline, SourceProvider> {
        val info = WavCodec.probe(file)
        val source = Source(
            id = file.nameWithoutExtension,
            relativePath = file.name,
            sampleRate = info.format.sampleRate,
            channelCount = info.format.channelCount,
            frameCount = info.frameCount,
        )
        val timeline = Timeline(sampleRate = info.format.sampleRate, layers = listOf(Layer("L1", "Take")))
        val history = EditHistory.of(timeline)
            .apply(AppendRecording(layerId = "L1", source = source, atFrame = 0, clipId = "clip"))

        val reader = WavStreamReader(file)
        val provider = object : SourceProvider {
            override fun read(sourceId: String, startFrame: Long, frameCount: Int): AudioBuffer =
                reader.read(startFrame, frameCount)
        }
        return history.current to provider
    }

    @Test
    fun playbackStartsAndTheHeadAdvances() {
        val (timeline, provider) = timelineFor(syntheticTake(1.5))

        val player = AudioPlayer(scope)
        try {
            player.start(timeline, provider, fromFrame = 0, channelCount = 1)
            val advanced = runBlocking {
                withTimeoutOrNull(8_000) { player.positionFrames.first { it > 0 } }
                player.positionFrames.value
            }
            assertTrue("The playhead never moved", advanced > 0)
        } finally {
            player.stop()
        }
    }

    @Test
    fun playbackThroughAVoiceSpaceDoesNotStallOrCrash() {
        // Live preview runs the whole Voice Studio inside the render loop. If any stage
        // allocated per block, threw, or blocked, it would show up here and nowhere else.
        val (timeline, provider) = timelineFor(syntheticTake(2.0))

        val player = AudioPlayer(scope)
        try {
            player.start(
                timeline = timeline,
                provider = provider,
                fromFrame = 0,
                channelCount = 1,
                voiceSettings = VoiceSpacePreset.MAJESTIC_RECITATION.settings,
            )
            val quarterSecond = timeline.sampleRate / 4L
            val advanced = runBlocking {
                withTimeoutOrNull(10_000) { player.positionFrames.first { it > quarterSecond } }
                player.positionFrames.value
            }
            assertTrue("Playback stalled with a space applied", advanced > quarterSecond)

            // Changing the room mid-playback must not stop it.
            player.setVoice(VoiceSpacePreset.DRY_STUDIO.settings)
            Thread.sleep(300)
            assertTrue("Changing the space stopped playback", player.playing.value)
        } finally {
            player.stop()
        }
    }

    @Test
    fun stoppingMidBlockDoesNotTakeTheProcessWithIt() {
        // The first run of these tests found this: AudioTrack.write with WRITE_BLOCKING does
        // not respond to coroutine cancellation, so releasing the track from stop() freed the
        // native pointer underneath a write still in flight, and the IllegalStateException
        // killed the process. Stopping at an awkward moment is the ordinary case, not an edge.
        val (timeline, provider) = timelineFor(syntheticTake(3.0))

        repeat(6) {
            val player = AudioPlayer(scope)
            player.start(timeline, provider, fromFrame = 0, channelCount = 1)
            runBlocking { withTimeoutOrNull(5_000) { player.positionFrames.first { it > 0 } } }
            // Straight into a stop, while the render loop is inside a blocking write.
            player.stop()
        }

        // The process is still here, and can still play.
        val player = AudioPlayer(scope)
        try {
            player.start(timeline, provider, fromFrame = 0, channelCount = 1)
            runBlocking { withTimeoutOrNull(6_000) { player.positionFrames.first { it > 0 } } }
            assertTrue("Playback did not survive being stopped repeatedly", player.positionFrames.value > 0)
        } finally {
            player.stop()
        }
    }

    @Test
    fun aRecordingMadeOnThisDeviceCanBePlayedBackOnIt() {
        // The two halves joined: what capture wrote is what playback reads.
        val (file, frames, _) = record(1.0)
        assertTrue("Nothing was recorded", frames > 0)
        val (timeline, provider) = timelineFor(file)
        assertEquals("The timeline is not the length of the take", frames, timeline.lengthFrames)

        val player = AudioPlayer(scope)
        try {
            player.start(timeline, provider, fromFrame = 0, channelCount = 1)
            runBlocking { withTimeoutOrNull(8_000) { player.positionFrames.first { it > 0 } } }
            assertTrue("A recording made here would not play here", player.positionFrames.value > 0)
        } finally {
            player.stop()
        }
    }

    // --- Phase E: export ---------------------------------------------------------------------

    @Test
    fun exportWritesAFileForEveryFormatItOffers() {
        PlatformEncoders.registerAll()
        val (timeline, provider) = timelineFor(syntheticTake(1.0))

        // Only what is registered. A format with no encoder is absent from the panel rather
        // than present and broken, and `available()` is exactly what the panel lists.
        val offered = Encoders.available()
        assertTrue("Nothing at all can be exported", offered.isNotEmpty())
        assertTrue("WAV must always be writable", ExportFormat.WAV in offered)

        for (format in offered) {
            val sink = ByteArrayOutputStream()
            val result = ExportJob(
                timeline = timeline,
                provider = provider,
                format = format,
                voice = VoiceSpacePreset.PODCAST_STUDIO.settings,
                channelCount = 1,
            ).run(sink)

            assertTrue("${format.displayName} wrote nothing", result.bytesWritten > 0)
            assertEquals("${format.displayName} lost bytes", result.bytesWritten, sink.size().toLong())
            assertTrue("${format.displayName} exported no audio", result.durationFrames > 0)
        }
    }

    @Test
    fun anExportedWavReopensAsTheSameRecording() {
        val (timeline, provider) = timelineFor(syntheticTake(1.0))

        val exported = File(workspace, "exported.wav")
        exported.outputStream().use { stream ->
            ExportJob(timeline, provider, ExportFormat.WAV, channelCount = 1).run(stream)
        }

        assertTrue("The export is not on disk", exported.isFile)
        val info = WavCodec.probe(exported)
        assertEquals(timeline.sampleRate, info.format.sampleRate)
        assertEquals("The export is a different length from the project", timeline.lengthFrames, info.frameCount)
    }

    @Test
    fun exportReportsProgressFromZeroToOneWithoutGoingBackwards() {
        val (timeline, provider) = timelineFor(syntheticTake(1.0))

        val seen = mutableListOf<Double>()
        ExportJob(
            timeline, provider, ExportFormat.WAV,
            voice = VoiceSpacePreset.BROADCAST_STUDIO.settings,
            channelCount = 1,
        ).run(ByteArrayOutputStream()) { fraction, _ -> seen += fraction }

        assertTrue("No progress was reported", seen.size > 2)
        assertTrue("Progress went backwards", seen.zipWithNext().all { it.first <= it.second + 1e-9 })
        assertEquals(0.0, seen.first(), 1e-9)
        assertEquals(1.0, seen.last(), 1e-9)
    }

    @Test
    fun platformEncodersRegisterTheFormatsTheyCanActuallyProduce() {
        PlatformEncoders.registerAll()

        // M4A comes from MediaCodec, which every Android since API 16 has.
        assertTrue("M4A should be available through MediaCodec", Encoders.isAvailable(ExportFormat.M4A))
        assertNotNull(Encoders.create(ExportFormat.M4A))

        // And a format with no encoder must fail loudly rather than write a broken file.
        for (format in ExportFormat.entries) {
            if (Encoders.isAvailable(format)) continue
            assertTrue(
                "${format.displayName} is unavailable but did not refuse",
                runCatching { Encoders.create(format) }.isFailure,
            )
        }
    }
}
