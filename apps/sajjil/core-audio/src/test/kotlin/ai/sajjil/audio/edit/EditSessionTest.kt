package ai.sajjil.audio.edit

import ai.sajjil.audio.AudioBuffer
import ai.sajjil.audio.TestSignals
import kotlin.math.abs
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNull
import kotlin.test.assertTrue

class EditSessionTest {

    private val sampleRate = 48000

    /** A ramp, so any frame's original position is identifiable from its value. */
    private fun ramp(frames: Int): AudioBuffer =
        AudioBuffer(sampleRate, arrayOf(FloatArray(frames) { it.toFloat() / frames }))

    @Test
    fun `deleting removes exactly the requested span`() {
        val session = EditSession(ramp(10000))
        session.delete(FrameRange(2000, 5000))
        assertEquals(7000, session.frameCount)
    }

    @Test
    fun `undo restores the audio bit for bit`() {
        val original = ramp(10000)
        val session = EditSession(original.copy())

        session.delete(FrameRange(2000, 5000))
        assertTrue(session.canUndo)
        assertTrue(session.undo())

        assertEquals(original.frameCount, session.frameCount)
        assertEquals(
            0.0,
            TestSignals.maxAbsoluteDifference(original, session.buffer),
            "undo must restore the original samples exactly, including the de-clicked joins",
        )
    }

    @Test
    fun `undo and redo survive a long chain of mixed edits`() {
        val original = ramp(40000)
        val session = EditSession(original.copy())

        session.delete(FrameRange(1000, 2000))
        session.insertSilence(500, 300)
        session.copy(FrameRange(0, 400)) // copying is not an edit and adds no history
        session.paste(1000)
        session.applyGain(-6.0, FrameRange(2000, 3000))
        session.fadeIn(FrameRange(0, 500))

        val afterAll = session.buffer.copy()
        val editCount = 5

        repeat(editCount) { assertTrue(session.undo(), "undo step $it should succeed") }
        assertFalse(session.canUndo)
        assertEquals(
            0.0,
            TestSignals.maxAbsoluteDifference(original, session.buffer),
            "unwinding every edit must land back on the original",
        )

        repeat(editCount) { assertTrue(session.redo(), "redo step $it should succeed") }
        assertEquals(
            0.0,
            TestSignals.maxAbsoluteDifference(afterAll, session.buffer),
            "replaying every edit must land back on the edited version",
        )
    }

    @Test
    fun `a new edit clears the redo branch`() {
        val session = EditSession(ramp(5000))
        session.delete(FrameRange(0, 1000))
        session.undo()
        assertTrue(session.canRedo)

        session.delete(FrameRange(0, 500))
        assertFalse(session.canRedo, "editing after an undo must discard the abandoned branch")
    }

    @Test
    fun `cut then paste moves audio without changing the total length`() {
        val session = EditSession(ramp(10000))
        val originalLength = session.frameCount

        session.cut(FrameRange(1000, 3000))
        assertEquals(originalLength - 2000, session.frameCount)

        assertTrue(session.paste(5000))
        assertEquals(originalLength, session.frameCount)
    }

    @Test
    fun `pasting with an empty clipboard reports failure instead of throwing`() {
        val session = EditSession(ramp(1000))
        assertFalse(session.paste(500))
    }

    @Test
    fun `trimming keeps only the selection`() {
        val session = EditSession(ramp(10000))
        session.selection = FrameRange(3000, 6000)
        session.trimTo()
        assertEquals(3000, session.frameCount)
        assertNull(session.selection, "the selection is meaningless after a trim")
    }

    @Test
    fun `inserting silence lengthens the recording and is silent`() {
        val session = EditSession(TestSignals.sine(440.0, 1.0, sampleRate))
        val before = session.frameCount
        session.insertSilence(sampleRate / 2, 4800)

        assertEquals(before + 4800, session.frameCount)
        // Sample the middle of the inserted region, clear of the de-click shoulders.
        val inserted = session.buffer.slice(sampleRate / 2 + 500, sampleRate / 2 + 4300)
        assertEquals(0f, inserted.peak(), "inserted silence should be silent")
    }

    @Test
    fun `splits are markers and do not modify audio`() {
        val original = ramp(10000)
        val session = EditSession(original.copy())
        session.split(3000)
        session.split(7000)

        assertEquals(listOf(3000, 7000), session.splitPoints)
        assertEquals(
            0.0,
            TestSignals.maxAbsoluteDifference(original, session.buffer),
            "splitting must not touch the audio",
        )
        assertFalse(session.canUndo, "a split is not an undoable audio edit")
    }

    @Test
    fun `segments describe the ranges between splits`() {
        val session = EditSession(ramp(10000))
        session.split(3000)
        session.split(7000)
        assertEquals(
            listOf(FrameRange(0, 3000), FrameRange(3000, 7000), FrameRange(7000, 10000)),
            session.segments(),
        )
    }

    @Test
    fun `split markers follow the audio when earlier material is deleted`() {
        val session = EditSession(ramp(10000))
        session.split(6000)
        session.delete(FrameRange(1000, 3000))
        // The marker sat 3000 frames after the deleted span, so it should now be at 4000.
        assertEquals(listOf(4000), session.splitPoints)
    }

    @Test
    fun `split markers inside deleted audio are dropped`() {
        val session = EditSession(ramp(10000))
        session.split(2000)
        session.delete(FrameRange(1000, 3000))
        assertTrue(session.splitPoints.isEmpty(), "a marker in deleted audio refers to nothing")
    }

    @Test
    fun `the selection follows the audio it refers to`() {
        val session = EditSession(ramp(10000))
        session.selection = FrameRange(6000, 7000)
        session.delete(FrameRange(1000, 3000))
        assertEquals(FrameRange(4000, 5000), session.selection)
    }

    @Test
    fun `the undo history is bounded`() {
        val session = EditSession(ramp(50000), maximumUndoSteps = 4)
        repeat(10) { session.delete(FrameRange(0, 100)) }

        var undone = 0
        while (session.undo()) undone++
        assertEquals(4, undone, "only the most recent four steps should be retained")
    }

    @Test
    fun `edits reject ranges beyond the end of the recording`() {
        val session = EditSession(ramp(1000))
        val error = runCatching { session.delete(FrameRange(500, 5000)) }.exceptionOrNull()
        assertTrue(error is IllegalArgumentException, "expected a clear failure, got $error")
    }

    @Test
    fun `operations needing a selection say so when there is none`() {
        val session = EditSession(ramp(1000))
        val error = runCatching { session.delete() }.exceptionOrNull()
        assertTrue(error is IllegalStateException)
    }

    @Test
    fun `joins are softened so an edit does not click`() {
        // Two DC levels spliced together would step from +0.5 to -0.5 in one sample.
        val high = AudioBuffer(sampleRate, arrayOf(FloatArray(sampleRate) { 0.5f }))
        val low = AudioBuffer(sampleRate, arrayOf(FloatArray(sampleRate) { -0.5f }))
        val session = EditSession(AudioBuffer.concat(listOf(high, low)))

        session.delete(FrameRange(sampleRate - 100, sampleRate + 100))

        var largestStep = 0f
        val data = session.buffer[0]
        for (i in 1 until data.size) {
            largestStep = maxOf(largestStep, abs(data[i] - data[i - 1]))
        }
        assertTrue(largestStep < 0.05f, "the join stepped by $largestStep, which would click")
    }

    @Test
    fun `appending extends the recording and is undoable`() {
        val session = EditSession(TestSignals.sine(440.0, 1.0, sampleRate))
        val before = session.frameCount
        session.append("Continue recording", TestSignals.sine(440.0, 0.5, sampleRate))

        assertEquals(before + sampleRate / 2, session.frameCount)
        assertEquals("Continue recording", session.undoLabel)
        session.undo()
        assertEquals(before, session.frameCount)
    }
}

class SilenceDetectorTest {

    private val sampleRate = 48000

    @Test
    fun `finds the gaps between bursts`() {
        val signal = TestSignals.burstsAndSilence(
            burstSeconds = 0.5, silenceSeconds = 1.0, repeats = 3, sampleRate = sampleRate,
        )
        val ranges = SilenceDetector(sampleRate).detect(signal)
        assertEquals(3, ranges.size, "expected one silent gap after each of the three bursts")
        for (range in ranges) {
            val seconds = range.length.toDouble() / sampleRate
            assertTrue(abs(seconds - 1.0) < 0.1, "gap measured $seconds s, expected about 1 s")
        }
    }

    @Test
    fun `short natural pauses are left alone`() {
        val signal = TestSignals.burstsAndSilence(
            burstSeconds = 0.5, silenceSeconds = 0.2, repeats = 3, sampleRate = sampleRate,
        )
        val ranges = SilenceDetector(sampleRate)
            .detect(signal, SilenceSettings(minimumSilenceMs = 700.0))
        assertTrue(ranges.isEmpty(), "200 ms pauses are speech rhythm, not silence to remove")
    }

    @Test
    fun `removing silence shortens the recording but keeps a beat`() {
        val signal = TestSignals.burstsAndSilence(
            burstSeconds = 0.5, silenceSeconds = 1.5, repeats = 3, sampleRate = sampleRate,
        )
        val settings = SilenceSettings(minimumSilenceMs = 700.0, keepMs = 250.0)
        val result = SilenceDetector(sampleRate).removeSilence(signal, settings)

        assertTrue(result.frameCount < signal.frameCount, "nothing was removed")
        // Three gaps of 1.5 s cut down to 0.25 s each saves about 3.75 s.
        val savedSeconds = (signal.frameCount - result.frameCount).toDouble() / sampleRate
        assertTrue(abs(savedSeconds - 3.75) < 0.3, "removed $savedSeconds s, expected about 3.75 s")
    }

    @Test
    fun `trimming ends keeps the audio between them`() {
        val leading = AudioBuffer.silence(sampleRate, 1, sampleRate)
        val speech = TestSignals.sine(440.0, 1.0, sampleRate, amplitude = 0.5)
        val trailing = AudioBuffer.silence(sampleRate, 1, sampleRate)
        val signal = AudioBuffer.concat(listOf(leading, speech, trailing))

        val trimmed = SilenceDetector(sampleRate).trimEnds(signal, paddingMs = 100.0)
        val seconds = trimmed.durationSeconds
        // One second of tone plus 100 ms of padding at each end.
        assertTrue(abs(seconds - 1.2) < 0.1, "trimmed to $seconds s, expected about 1.2 s")
    }

    @Test
    fun `a fully silent recording trims to nothing rather than failing`() {
        val silence = AudioBuffer.silence(sampleRate, 1, sampleRate * 3)
        assertEquals(0, SilenceDetector(sampleRate).trimEnds(silence).frameCount)
    }
}

class FadesTest {

    private val sampleRate = 48000

    @Test
    fun `a fade in starts at silence and ends at full level`() {
        val signal = TestSignals.sine(440.0, 1.0, sampleRate, amplitude = 0.8)
        Fades.fadeIn(signal, sampleRate / 2)
        assertTrue(abs(signal[0][0]) < 1e-6, "a fade in must start from silence")
        assertTrue(signal.slice(sampleRate / 2, signal.frameCount).peak() > 0.79)
    }

    @Test
    fun `a fade out ends at silence`() {
        val signal = TestSignals.sine(440.0, 1.0, sampleRate, amplitude = 0.8)
        Fades.fadeOut(signal, sampleRate / 2)
        assertTrue(abs(signal[0][signal.frameCount - 1]) < 1e-3, "a fade out must reach silence")
    }

    @Test
    fun `every fade shape is monotonic`() {
        for (shape in FadeShape.entries) {
            val signal = AudioBuffer(sampleRate, arrayOf(FloatArray(1000) { 1f }))
            Fades.fadeIn(signal, 1000, shape)
            for (i in 1 until 1000) {
                assertTrue(
                    signal[0][i] >= signal[0][i - 1] - 1e-6,
                    "$shape dipped at sample $i, which would be heard as a wobble",
                )
            }
        }
    }

    @Test
    fun `a crossfade holds a steady level across the join`() {
        // Equal-power is the right law for joining two different takes, which are uncorrelated.
        // Its defining property is that the *energy* stays constant through the overlap; a linear
        // crossfade of uncorrelated material sags about 3 dB in the middle, which is audible.
        val a = TestSignals.noise(2.0, sampleRate, amplitude = 0.5, seed = 1)
        val b = TestSignals.noise(2.0, sampleRate, amplitude = 0.5, seed = 2)
        val overlap = sampleRate
        val result = Fades.crossfade(a, b, overlap)

        val overlapStart = a.frameCount - overlap
        val referenceRms = a.slice(0, sampleRate / 2).rms()
        // Sample the RMS at several points through the overlap.
        for (fraction in listOf(0.1, 0.3, 0.5, 0.7, 0.9)) {
            val at = overlapStart + (overlap * fraction).toInt()
            val rms = result.slice(at - 2000, at + 2000).rms()
            assertTrue(
                abs(rms - referenceRms) / referenceRms < 0.12,
                "at ${fraction * 100}% through the crossfade the level was $rms, " +
                    "against a reference of $referenceRms",
            )
        }
    }

    @Test
    fun `crossfading shortens the total by the overlap`() {
        val a = TestSignals.sine(440.0, 1.0, sampleRate)
        val b = TestSignals.sine(440.0, 1.0, sampleRate)
        val result = Fades.crossfade(a, b, sampleRate / 2)
        assertEquals(a.frameCount + b.frameCount - sampleRate / 2, result.frameCount)
    }
}
