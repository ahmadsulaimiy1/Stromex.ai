package ai.sautiy.core.analysis

import ai.sautiy.core.TestSignals
import ai.sautiy.core.audio.AudioBuffer
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/** Editorial Bible chapter 9.7, verified. */
class SilenceDetectorTest {

    private val rate = 48_000

    /** Speech-like blocks separated by gaps, over a quiet noise floor. */
    private fun speechWithGaps(
        segments: List<Pair<Double, Boolean>>,
        noiseAmplitude: Double = 0.002,
    ): AudioBuffer {
        val parts = segments.map { (seconds, loud) ->
            val block = TestSignals.noise(seconds, rate, amplitude = if (loud) 0.25 else noiseAmplitude, seed = 42)
            block
        }
        return AudioBuffer.concat(parts)
    }

    @Test
    fun `the noise floor is measured from the recording, not assumed`() {
        val quiet = TestSignals.noise(2.0, rate, amplitude = 0.001)
        val noisy = TestSignals.noise(2.0, rate, amplitude = 0.05)

        val quietFloor = SilenceDetector.noiseFloorDb(quiet)
        val noisyFloor = SilenceDetector.noiseFloorDb(noisy)

        assertTrue("A quiet room must measure quieter than a noisy one", quietFloor < noisyFloor - 20)
        assertTrue("A padded room's floor should be well below -50 dBFS", quietFloor < -50)
    }

    @Test
    fun `the threshold follows the room, so the same setting works in both`() {
        val quiet = speechWithGaps(listOf(1.0 to true, 1.0 to false, 1.0 to true), noiseAmplitude = 0.0005)
        val hall = speechWithGaps(listOf(1.0 to true, 1.0 to false, 1.0 to true), noiseAmplitude = 0.02)

        val quietAnalysis = SilenceDetector.analyse(quiet)
        val hallAnalysis = SilenceDetector.analyse(hall)

        assertTrue(
            "A noisier room must get a higher threshold, or nothing is ever detected in it",
            hallAnalysis.thresholdDb > quietAnalysis.thresholdDb,
        )
        assertEquals("The gap must be found in a quiet room", 1, quietAnalysis.regions.size)
        assertEquals("...and in a noisy hall too", 1, hallAnalysis.regions.size)
    }

    @Test
    fun `a real gap is found with the right boundaries`() {
        val buffer = speechWithGaps(listOf(1.0 to true, 2.0 to false, 1.0 to true))
        val analysis = SilenceDetector.analyse(buffer)

        assertEquals(1, analysis.regions.size)
        val region = analysis.regions.single()
        val padding = SilenceDetector.DEFAULT_PADDING_MS * rate / 1000

        assertEquals("Region must begin after the padding", (rate + padding).toDouble(), region.startFrame.toDouble(), rate * 0.05)
        assertEquals("Region must end before the padding", (3 * rate - padding).toDouble(), region.endFrame.toDouble(), rate * 0.05)
    }

    @Test
    fun `pauses shorter than the minimum are treated as rhythm, not silence`() {
        // Chapter 9.7. Removing the breath between clauses is what makes edited speech sound
        // frantic; this is the rule that stops SAUTIY doing it.
        val buffer = speechWithGaps(
            listOf(1.0 to true, 0.15 to false, 1.0 to true, 0.20 to false, 1.0 to true),
        )
        val analysis = SilenceDetector.analyse(buffer)
        assertTrue(
            "Speech rhythm was mistaken for silence: ${analysis.regions.size} regions found",
            analysis.regions.isEmpty(),
        )
    }

    @Test
    fun `padding keeps word onsets from being clipped`() {
        val buffer = speechWithGaps(listOf(1.0 to true, 2.0 to false, 1.0 to true))

        val padded = SilenceDetector.analyse(buffer, paddingMs = 200).regions.single()
        val unpadded = SilenceDetector.analyse(buffer, paddingMs = 0).regions.single()

        assertTrue("More padding must remove less", padded.startFrame > unpadded.startFrame)
        assertTrue(padded.endFrame < unpadded.endFrame)
        assertEquals(
            "Padding must be applied at both ends equally",
            (padded.startFrame - unpadded.startFrame),
            (unpadded.endFrame - padded.endFrame),
        )
    }

    @Test
    fun `leading and trailing silence are both found`() {
        // The eight seconds of nothing before someone started talking is exactly what this
        // feature exists to remove.
        val buffer = speechWithGaps(listOf(3.0 to false, 1.0 to true, 3.0 to false))
        val analysis = SilenceDetector.analyse(buffer)

        assertEquals(2, analysis.regions.size)
        assertTrue("The leading silence must start near zero", analysis.regions.first().startFrame < rate / 2)
        assertTrue(
            "The trailing silence must run to near the end",
            analysis.regions.last().endFrame > buffer.frameCount - rate / 2,
        )
    }

    @Test
    fun `continuous speech yields nothing to remove`() {
        val buffer = TestSignals.noise(4.0, rate, amplitude = 0.25)
        assertTrue(SilenceDetector.analyse(buffer).regions.isEmpty())
    }

    @Test
    fun `total removable time is reported so the user can decide before committing`() {
        val buffer = speechWithGaps(listOf(1.0 to true, 2.0 to false, 1.0 to true, 2.0 to false, 1.0 to true))
        val analysis = SilenceDetector.analyse(buffer)

        assertEquals(2, analysis.regions.size)
        val padding = 2 * SilenceDetector.DEFAULT_PADDING_MS / 1000.0
        assertEquals(
            "Two two-second gaps, less padding at each end of each",
            2 * (2.0 - padding),
            analysis.totalSilentSeconds,
            0.2,
        )
    }

    @Test
    fun `an explicit threshold overrides the automatic one`() {
        val buffer = speechWithGaps(listOf(1.0 to true, 2.0 to false, 1.0 to true))

        val strict = SilenceDetector.analyse(buffer, thresholdDb = -80.0)
        assertTrue("A threshold below the floor must find nothing", strict.regions.isEmpty())
        assertEquals(-80.0, strict.thresholdDb, 1e-9)

        val loose = SilenceDetector.analyse(buffer, thresholdDb = -20.0)
        assertTrue("A high threshold must find the gap", loose.regions.isNotEmpty())
    }

    @Test
    fun `detected regions can be removed by the edit engine in one step`() {
        // Chapter 9.3's RemoveSilence is a composite of ordinary cuts, applied back to front so
        // that each cut's ripple does not invalidate the positions of the ones still to come.
        val buffer = speechWithGaps(listOf(1.0 to true, 2.0 to false, 1.0 to true))
        val analysis = SilenceDetector.analyse(buffer)

        val source = ai.sautiy.core.edit.Source("s1", "s1.wav", rate, 1, buffer.frameCount.toLong())
        val timeline = ai.sautiy.core.edit.Timeline(
            sampleRate = rate,
            sources = mapOf(source.id to source),
            layers = listOf(
                ai.sautiy.core.edit.Layer(
                    "L1", "Vocals 1",
                    listOf(ai.sautiy.core.edit.Clip("c1", "s1", 0, buffer.frameCount.toLong(), 0)),
                ),
            ),
        )

        val removals = analysis.regions
            .sortedByDescending { it.startFrame }
            .map { ai.sautiy.core.edit.DeleteRange(it.startFrame, it.endFrame) }
        val composite = ai.sautiy.core.edit.Composite("Remove silence", removals)
        val after = composite.applyTo(timeline)

        val removedFrames = analysis.totalSilentFrames
        assertEquals(
            "The timeline must shorten by exactly the silence removed",
            buffer.frameCount.toLong() - removedFrames,
            after.lengthFrames,
        )
        assertEquals("It is one undoable step", "Remove silence", composite.label)
    }
}
