package ai.sautiy.core.record

import ai.sautiy.core.PerformanceBudget
import ai.sautiy.core.audio.CaptureQuality
import ai.sautiy.core.play.Bookmark
import ai.sautiy.core.play.LoopRegion
import ai.sautiy.core.play.PlaybackMachine
import ai.sautiy.core.play.PlaybackPolicy
import ai.sautiy.core.play.PlaybackSpeed
import ai.sautiy.core.play.PlaybackState
import ai.sautiy.core.workspace.Interruption
import ai.sautiy.core.workspace.TransportState
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/** Editorial Bible chapters 7 and 8, verified. */
class RecordingMachineTest {

    @Test
    fun `recording begins in one tap from a cold launch`() {
        // Chapter 3.2.1 and 1.6: one tap, no arm step, no confirmation.
        assertEquals(
            TransportState.RECORDING,
            RecordingMachine.next(TransportState.IDLE, RecordingMachine.Command.START),
        )
        assertEquals(1, PerformanceBudget.MAX_TAPS_TO_RECORD)
    }

    @Test
    fun `pause and resume stay inside the same take`() {
        var state = TransportState.RECORDING
        state = RecordingMachine.next(state, RecordingMachine.Command.PAUSE)!!
        assertEquals(TransportState.RECORDING_PAUSED, state)
        assertTrue("A paused recording is still capturing state", state.isCapturing)

        state = RecordingMachine.next(state, RecordingMachine.Command.RESUME)!!
        assertEquals(TransportState.RECORDING, state)
    }

    @Test
    fun `losing the microphone pauses rather than stops, so the take survives`() {
        // Chapter 3.2.7: the user can resume when the other app lets go. Stopping instead would
        // end the take and turn a recoverable interruption into a lost recording.
        assertEquals(
            TransportState.RECORDING_PAUSED,
            RecordingMachine.next(TransportState.RECORDING, RecordingMachine.Command.FAIL),
        )
    }

    @Test
    fun `illegal transitions are refused rather than half-performed`() {
        val illegal = listOf(
            TransportState.IDLE to RecordingMachine.Command.STOP,
            TransportState.IDLE to RecordingMachine.Command.PAUSE,
            TransportState.IDLE to RecordingMachine.Command.RESUME,
            TransportState.PLAYING to RecordingMachine.Command.RESUME,
            TransportState.RECORDING to RecordingMachine.Command.START,
            TransportState.STOPPED to RecordingMachine.Command.PAUSE,
            TransportState.RECORDING to RecordingMachine.Command.DISCARD,
        )
        for ((state, command) in illegal) {
            assertNull(
                "$command from $state must be refused — this is how a zero-length file happens",
                RecordingMachine.next(state, command),
            )
        }
    }

    @Test
    fun `discarding a take is only possible when it was deliberately paused`() {
        assertTrue(RecordingMachine.isLegal(TransportState.RECORDING_PAUSED, RecordingMachine.Command.DISCARD))
        assertFalse(RecordingMachine.isLegal(TransportState.RECORDING, RecordingMachine.Command.DISCARD))
    }

    @Test
    fun `the flush cadence keeps sample loss inside the constitutional ceiling`() {
        assertTrue(
            "Worst-case loss ${CapturePolicy.worstCaseLossMs()} ms exceeds the ceiling",
            CapturePolicy.worstCaseLossMs() <= PerformanceBudget.MAX_SAMPLE_LOSS_ON_KILL_MS,
        )
        assertEquals(48_000L, CapturePolicy.flushIntervalFrames(48_000))
        assertTrue(CapturePolicy.captureBufferFrames(48_000) >= 256)
    }

    @Test
    fun `remaining time is stated from the bitrate actually in use`() {
        val oneGigabyte = 1024L * 1024 * 1024
        val voice = RecordingState(quality = CaptureQuality.VOICE, freeBytes = oneGigabyte)
        val stereo = RecordingState(quality = CaptureQuality.STEREO, freeBytes = oneGigabyte)

        assertTrue(
            "Voice must offer more time than Stereo on the same volume",
            voice.secondsRemaining > stereo.secondsRemaining * 3,
        )
        assertFalse(voice.storageIsCritical)
    }

    @Test
    fun `storage becomes critical exactly two minutes out, not sooner`() {
        val quality = CaptureQuality.STUDIO
        val twoMinutes = quality.bytesPerSecond * 120 + CaptureQuality.SAFETY_MARGIN_BYTES
        val threeMinutes = quality.bytesPerSecond * 180 + CaptureQuality.SAFETY_MARGIN_BYTES

        assertTrue(RecordingState(quality = quality, freeBytes = twoMinutes).storageIsCritical)
        assertFalse(
            "Warning earlier than two minutes is nagging (chapter 3.2.7)",
            RecordingState(quality = quality, freeBytes = threeMinutes).storageIsCritical,
        )
    }

    @Test
    fun `clipping is counted and surfaced, never hidden`() {
        val clean = RecordingState(peakLinear = 0.7f)
        val clipped = RecordingState(peakLinear = 1.0f, clippedSampleCount = 12)
        assertFalse(clean.hasClipped)
        assertTrue(clipped.hasClipped)
    }

    @Test
    fun `the quality score punishes the faults a user can actually act on`() {
        val good = RecordingState(peakLinear = 0.5f).qualityScore(noiseFloorDb = -70.0)
        val clipped = RecordingState(peakLinear = 1.0f, clippedSampleCount = 40).qualityScore(-70.0)
        val tooQuiet = RecordingState(peakLinear = 0.02f).qualityScore(-70.0)
        val noisy = RecordingState(peakLinear = 0.5f).qualityScore(noiseFloorDb = -25.0)

        assertTrue("A well-recorded take should score highly, got $good", good >= 90)
        assertTrue("Clipping is the unrecoverable fault, got $clipped", clipped < 55)
        assertTrue("Recording far too quietly must be flagged, got $tooQuiet", tooQuiet < 70)
        assertTrue("A high noise floor must be flagged, got $noisy", noisy < 75)
        for (score in listOf(good, clipped, tooQuiet, noisy)) {
            assertTrue(score in 0..100)
        }
    }

    @Test
    fun `take duration comes from frames, so the timer and the waveform cannot disagree`() {
        val take = Take("t1", "take-1.wav", CaptureQuality.STUDIO, frameCount = 48_000 * 90L)
        assertEquals(90.0, take.durationSeconds, 1e-9)
        assertEquals(90_000L, take.durationMs)
    }
}

class CrashRecoveryTest {

    @Test
    fun `an unclaimed recording is offered back on next launch`() {
        val candidates = listOf(
            CrashRecovery.Candidate("take-1.wav", 48_000 * 300L, 48_000, 1_000),
            CrashRecovery.Candidate("take-2.wav", 48_000 * 12L, 48_000, 2_000),
        )
        val offered = CrashRecovery.worthOffering(candidates)

        assertEquals(2, offered.size)
        assertEquals("Most recent first", "take-2.wav", offered.first().fileName)
        assertEquals(Interruption.CRASH_RECOVERY_AVAILABLE, CrashRecovery.interruptionFor(candidates))
    }

    @Test
    fun `a fragment from a brushed control is not worth an interruption`() {
        // Chapter 3.2.7 permits only four interruptions; spending one on 200 ms of nothing is
        // exactly the kind of nagging the clause exists to prevent.
        val fragment = listOf(CrashRecovery.Candidate("take-9.wav", 9_600, 48_000, 1_000))
        assertTrue(CrashRecovery.worthOffering(fragment).isEmpty())
        assertNull(CrashRecovery.interruptionFor(fragment))
    }

    @Test
    fun `nothing to recover means no interruption at all`() {
        assertNull(CrashRecovery.interruptionFor(emptyList()))
    }
}

class PlaybackTest {

    private val rate = 48_000

    @Test
    fun `playback can begin from a paused recording without leaving the workspace`() {
        // Review-in-place: pause the take, listen back, resume. Chapter 4.5.
        assertEquals(
            TransportState.PLAYING,
            PlaybackMachine.next(TransportState.RECORDING_PAUSED, PlaybackMachine.Command.PLAY),
        )
    }

    @Test
    fun `playing while recording is refused`() {
        assertNull(PlaybackMachine.next(TransportState.RECORDING, PlaybackMachine.Command.PLAY))
    }

    @Test
    fun `seeking never stops the transport`() {
        // A transport that stops on seek makes scrubbing through a recording impossible.
        for (state in listOf(TransportState.PLAYING, TransportState.PLAYBACK_PAUSED, TransportState.STOPPED)) {
            assertEquals(state, PlaybackMachine.next(state, PlaybackMachine.Command.SEEK))
        }
    }

    @Test
    fun `the playhead stops at the end when there is no loop`() {
        val state = PlaybackState(
            transport = TransportState.PLAYING,
            positionFrames = rate * 9L,
            totalFrames = rate * 10L,
            sampleRate = rate,
        )
        val advanced = state.advanced(rate * 2L)
        assertEquals(rate * 10L, advanced.positionFrames)
        assertEquals(TransportState.STOPPED, advanced.transport)
    }

    @Test
    fun `a loop wraps and keeps playing`() {
        val state = PlaybackState(
            transport = TransportState.PLAYING,
            positionFrames = 90_000,
            totalFrames = rate * 10L,
            sampleRate = rate,
            loop = LoopRegion(48_000, 96_000),
        )
        val advanced = state.advanced(12_000)
        assertEquals("Must wrap to the loop start plus the overshoot", 54_000L, advanced.positionFrames)
        assertEquals(TransportState.PLAYING, advanced.transport)
    }

    @Test
    fun `back returns to the start of the segment, and walks further back when already there`() {
        val state = PlaybackState(
            positionFrames = rate * 40L,
            totalFrames = rate * 100L,
            sampleRate = rate,
            bookmarks = listOf(
                Bookmark("a", rate * 10L),
                Bookmark("b", rate * 30L),
            ),
        )
        assertEquals("Well into a segment, back means the start of it", "b", state.previousBookmark()?.id)

        // Already sitting just after b — pressing back again must walk past it, or the control
        // locks and the user can never reach an earlier marker.
        val justPastB = state.copy(positionFrames = rate * 31L)
        assertEquals("a", justPastB.previousBookmark()?.id)

        // At the very first marker there is nowhere further back to go, so back holds.
        val justPastA = state.copy(positionFrames = rate * 11L)
        assertEquals("a", justPastA.previousBookmark()?.id)

        // Before any marker at all, there is nothing to return to.
        assertNull(state.copy(positionFrames = rate * 5L).previousBookmark())
    }

    @Test
    fun `the next marker is the next one, and there is none past the last`() {
        val state = PlaybackState(
            positionFrames = rate * 15L,
            totalFrames = rate * 100L,
            sampleRate = rate,
            bookmarks = listOf(Bookmark("a", rate * 10L), Bookmark("b", rate * 30L)),
        )
        assertEquals("b", state.nextBookmark()?.id)
        assertNull(state.copy(positionFrames = rate * 40L).nextBookmark())
    }

    @Test
    fun `speed is offered as steps people use, with normal always one tap away`() {
        assertEquals(PlaybackSpeed.NORMAL, PlaybackSpeed.Default)
        assertEquals(1.0, PlaybackSpeed.NORMAL.factor, 0.0)
        assertEquals(PlaybackSpeed.ONE_AND_HALF, PlaybackSpeed.nearest(1.48))
        assertTrue(PlaybackSpeed.entries.all { it.displayName.isNotBlank() })
        assertTrue("No fiddly intermediate steps", PlaybackSpeed.entries.size <= 6)
    }

    @Test
    fun `seeking is clamped to the material`() {
        val state = PlaybackState(totalFrames = rate * 10L, sampleRate = rate)
        assertEquals(0L, state.seekTo(-500).positionFrames)
        assertEquals(rate * 10L, state.seekTo(rate * 99L).positionFrames)
    }

    @Test
    fun `progress is a fraction even when there is nothing to play`() {
        assertEquals(0.0, PlaybackState().progress, 0.0)
        assertEquals(
            0.5,
            PlaybackState(positionFrames = 50, totalFrames = 100).progress,
            1e-9,
        )
    }

    @Test
    fun `the output buffer alone cannot exceed the tap-to-audible budget`() {
        assertTrue(
            "${PlaybackPolicy.OUTPUT_BUFFER_MS} ms buffer against a " +
                "${PerformanceBudget.TAP_TO_AUDIBLE_MS} ms budget",
            PlaybackPolicy.OUTPUT_BUFFER_MS < PerformanceBudget.TAP_TO_AUDIBLE_MS,
        )
        assertTrue(PlaybackPolicy.outputBufferFrames(48_000) >= 256)
        assertTrue(PlaybackPolicy.scrubGrainFrames(48_000) > 0)
    }

    @Test
    fun `an empty loop cannot be constructed`() {
        assertTrue(runCatching { LoopRegion(1_000, 1_000) }.isFailure)
        assertTrue(runCatching { LoopRegion(2_000, 1_000) }.isFailure)
    }
}
