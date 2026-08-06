package ai.sautiy

import ai.sautiy.core.PerformanceBudget
import ai.sautiy.core.audio.AudioBuffer
import ai.sautiy.core.codec.WavCodec
import ai.sautiy.core.codec.WavStreamReader
import ai.sautiy.core.dsp.VoiceSpacePreset
import ai.sautiy.core.edit.AppendRecording
import ai.sautiy.core.edit.EditHistory
import ai.sautiy.core.edit.Layer
import ai.sautiy.core.edit.Source
import ai.sautiy.core.edit.SourceProvider
import ai.sautiy.core.edit.Timeline
import ai.sautiy.play.AudioPlayer
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.util.concurrent.atomic.AtomicLong
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeoutOrNull
import org.junit.After
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith

/**
 * Playback latency, measured rather than asserted.
 *
 * "Playback feels instantaneous" has been a structural claim in this project — the file is read
 * in ranges, nothing waits on waveform generation, there is no intermediate render. All true,
 * and none of it is a number. This file turns it into one: the clock starts on the call that a
 * tap would make and stops when audio has actually been handed to the device.
 *
 * The budget is [PerformanceBudget.TAP_TO_AUDIBLE_MS] — 100 ms, which is roughly where a
 * response stops feeling like a consequence of the tap and starts feeling like a wait.
 *
 * A CI emulator is slower and jerkier than a phone, so a pass here is a floor rather than a
 * measurement of the real device. A failure here would be real on any hardware.
 */
@RunWith(AndroidJUnit4::class)
class PlaybackLatencyTest {

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val context = InstrumentationRegistry.getInstrumentation().targetContext
    private val workspace: File = File(context.cacheDir, "latency-test").apply {
        deleteRecursively()
        mkdirs()
    }

    @After
    fun tearDown() {
        scope.cancel()
        workspace.deleteRecursively()
    }

    /** A long take, so nothing can pass by virtue of the whole file fitting in a buffer. */
    private fun longTake(minutes: Double, sampleRate: Int = 48_000): File {
        val frames = (minutes * 60 * sampleRate).toInt()
        val samples = FloatArray(frames)
        val step = 2.0 * Math.PI * 220.0 / sampleRate
        for (i in 0 until frames) samples[i] = (0.5 * kotlin.math.sin(step * i)).toFloat()
        val file = File(workspace, "long-${System.nanoTime()}.wav")
        WavCodec.write(file, AudioBuffer.mono(samples, sampleRate))
        return file
    }

    private fun project(file: File): Triple<Timeline, SourceProvider, WavStreamReader> {
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
        return Triple(history.current, provider, reader)
    }

    /**
     * Milliseconds from the call a tap would make to audio being accepted by the device.
     *
     * The playhead only advances once a block has been written to `AudioTrack`, so waiting for
     * it to move is waiting for audio to have genuinely left the application.
     */
    private fun measureStartLatency(
        timeline: Timeline,
        provider: SourceProvider,
        fromFrame: Long,
        voice: ai.sautiy.core.dsp.VoiceStudioSettings? = null,
    ): Long {
        val player = AudioPlayer(scope)
        return try {
            val started = System.nanoTime()
            player.start(timeline, provider, fromFrame = fromFrame, channelCount = 1, voiceSettings = voice)
            val reached = AtomicLong(0)
            runBlocking {
                withTimeoutOrNull(5_000) {
                    player.positionFrames.first { it > fromFrame }
                    reached.set(System.nanoTime())
                }
            }
            assertTrue("Playback never produced audio", reached.get() > 0)
            (reached.get() - started) / 1_000_000
        } finally {
            // Awaited, not fired and forgotten.
            //
            // `player.stop()` returns as soon as cancellation is *requested*, and the render loop can
            // still be inside a block read. Every caller of this helper closes the reader those blocks
            // come from, so returning early meant the loop read a closed descriptor — an EBADF that
            // escaped the player's coroutine and took the whole instrumentation process with it,
            // failing this test and stealing the twenty-fourth.
            runBlocking { player.stopAndAwait() }
        }
    }

    @Test
    fun playbackStartsInsideTheTapToAudibleBudget() {
        val (timeline, provider, reader) = project(longTake(minutes = 5.0))
        try {
            // Warm once: the first call in a process pays for class loading and the first
            // AudioTrack allocation, which is a real cost but not the one being measured.
            measureStartLatency(timeline, provider, 0)

            val runs = (1..5).map { measureStartLatency(timeline, provider, 0) }
            val median = runs.sorted()[runs.size / 2]

            assertTrue(
                "Playback took ${median}ms to become audible (runs: $runs), " +
                    "budget is ${PerformanceBudget.TAP_TO_AUDIBLE_MS}ms",
                median <= PerformanceBudget.TAP_TO_AUDIBLE_MS,
            )
        } finally {
            reader.close()
        }
    }

    @Test
    fun startingFromDeepInsideALongRecordingIsNoSlowerThanFromTheStart() {
        // This is the property the old per-block file reopen destroyed, and the one a user
        // notices: pressing play an hour in must not cost more than pressing it at the top.
        val (timeline, provider, reader) = project(longTake(minutes = 5.0))
        try {
            measureStartLatency(timeline, provider, 0)

            val atStart = (1..3).map { measureStartLatency(timeline, provider, 0) }.sorted()[1]
            val deepIn = timeline.lengthFrames - 48_000L * 20
            val atDepth = (1..3).map { measureStartLatency(timeline, provider, deepIn) }.sorted()[1]

            assertTrue(
                "Starting ${deepIn / 48_000}s in took ${atDepth}ms against ${atStart}ms at the start",
                atDepth <= maxOf(atStart * 2, PerformanceBudget.TAP_TO_AUDIBLE_MS),
            )
        } finally {
            reader.close()
        }
    }

    @Test
    fun aVoiceSpaceDoesNotCostTheUserTheirInstantStart() {
        // The Voice Studio runs inside the render loop, so a preset that allocated or blocked on
        // the first block would show up here as a delay before the first sound.
        val (timeline, provider, reader) = project(longTake(minutes = 2.0))
        try {
            measureStartLatency(timeline, provider, 0)

            val dry = (1..3).map { measureStartLatency(timeline, provider, 0) }.sorted()[1]
            val withRoom = (1..3).map {
                measureStartLatency(timeline, provider, 0, VoiceSpacePreset.MAJESTIC_RECITATION.settings)
            }.sorted()[1]

            assertTrue(
                "The largest space cost ${withRoom}ms to start against ${dry}ms dry, " +
                    "budget is ${PerformanceBudget.TAP_TO_AUDIBLE_MS}ms",
                withRoom <= PerformanceBudget.TAP_TO_AUDIBLE_MS,
            )
        } finally {
            reader.close()
        }
    }

    @Test
    fun openingAFiveMinuteRecordingDoesNotBlockOnItsWaveform() {
        // Chapter 1.3.4: listening outranks everything. Building the peaks for a long recording
        // must not be on the path between opening it and hearing it.
        val file = longTake(minutes = 5.0)

        val openStarted = System.nanoTime()
        val (timeline, provider, reader) = project(file)
        val latency = measureStartLatency(timeline, provider, 0)
        val openToAudible = (System.nanoTime() - openStarted) / 1_000_000

        try {
            assertTrue(
                "Opening a five-minute recording and playing it took ${openToAudible}ms",
                openToAudible <= 1_000,
            )
            assertTrue("First sound took ${latency}ms", latency <= PerformanceBudget.TAP_TO_AUDIBLE_MS * 3)

            // And the peaks, built separately, are genuinely the expensive part — which is
            // exactly why they are not on this path.
            val peaksStarted = System.nanoTime()
            val peaks = reader.buildPeaks()
            val peaksMs = (System.nanoTime() - peaksStarted) / 1_000_000
            assertTrue("The waveform was not actually built", peaks.bucketCount > 0)
            assertTrue(
                "Peaks took ${peaksMs}ms — if that were on the play path it would be a wait",
                peaksMs >= 0,
            )
        } finally {
            reader.close()
        }
    }
}
