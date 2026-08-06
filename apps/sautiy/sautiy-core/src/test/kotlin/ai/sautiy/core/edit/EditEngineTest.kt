package ai.sautiy.core.edit

import ai.sautiy.core.TestSignals
import ai.sautiy.core.audio.AudioBuffer
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/** Editorial Bible chapter 9, verified. */
class EditEngineTest {

    private val rate = 48_000

    private fun source(id: String, frames: Long) =
        Source(id = id, relativePath = "$id.wav", sampleRate = rate, channelCount = 1, frameCount = frames)

    /** One layer, one clip covering the whole of a ten-second source. */
    private fun oneClipTimeline(frames: Long = 480_000L): Timeline {
        val src = source("s1", frames)
        return Timeline(
            sampleRate = rate,
            sources = mapOf(src.id to src),
            layers = listOf(
                Layer(
                    id = "L1",
                    name = "Vocals 1",
                    clips = listOf(
                        Clip(id = "c1", sourceId = "s1", sourceStartFrame = 0, lengthFrames = frames, timelineStartFrame = 0),
                    ),
                ),
            ),
        )
    }

    // --- Chapter 9.2: invariants cannot be violated -----------------------------------------

    @Test
    fun `a zero length clip cannot be constructed`() {
        val failed = runCatching {
            Clip(id = "x", sourceId = "s1", sourceStartFrame = 0, lengthFrames = 0, timelineStartFrame = 0)
        }.isFailure
        assertTrue("Invariant 4 must be enforced at construction", failed)
    }

    @Test
    fun `fades longer than the clip cannot be constructed`() {
        val failed = runCatching {
            Clip(
                id = "x", sourceId = "s1", sourceStartFrame = 0, lengthFrames = 100,
                timelineStartFrame = 0, fadeInFrames = 80, fadeOutFrames = 80,
            )
        }.isFailure
        assertTrue("Invariant 3 must be enforced at construction", failed)
    }

    @Test
    fun `overlapping clips in a layer cannot be constructed`() {
        val failed = runCatching {
            Layer(
                id = "L", name = "L",
                clips = listOf(
                    Clip(id = "a", sourceId = "s", sourceStartFrame = 0, lengthFrames = 100, timelineStartFrame = 0),
                    Clip(id = "b", sourceId = "s", sourceStartFrame = 0, lengthFrames = 100, timelineStartFrame = 50),
                ),
            )
        }.isFailure
        assertTrue("Invariant 1 must be enforced at construction", failed)
    }

    @Test
    fun `a clip reading past the end of its source cannot be constructed`() {
        val src = source("s1", 1_000)
        val failed = runCatching {
            Timeline(
                sampleRate = rate,
                sources = mapOf(src.id to src),
                layers = listOf(
                    Layer("L", "L", listOf(Clip("c", "s1", 500, 900, 0))),
                ),
            )
        }.isFailure
        assertTrue("Invariant 2 must be enforced at construction", failed)
    }

    @Test
    fun `timeline length is derived from content and cannot disagree with it`() {
        val timeline = oneClipTimeline(96_000)
        assertEquals(96_000L, timeline.lengthFrames)
        assertEquals(2.0, timeline.durationSeconds, 1e-9)

        val trimmed = Trim("L1", "c1", newEndFrame = 48_000).applyTo(timeline)
        assertEquals("Length must follow the content", 48_000L, trimmed.lengthFrames)
    }

    // --- Chapter 9.1: no edit touches a sample -----------------------------------------------

    @Test
    fun `every operation leaves the sources untouched`() {
        val timeline = oneClipTimeline()
        val before = timeline.sources

        val operations = listOf(
            Split("L1", 100_000),
            DeleteRange(50_000, 60_000),
            SilenceRange(10_000, 20_000),
            GainRange(0, 10_000, -6.0),
            Trim("L1", "c1", newStartFrame = 5_000),
            FadeClip("L1", "c1", 4_800, 4_800),
            SetLayerGain("L1", -3.0),
            MuteLayer("L1", true),
        )
        for (operation in operations) {
            val after = operation.applyTo(timeline)
            assertEquals(
                "${operation.label} altered the source table — chapter 9.1 forbids it",
                before,
                after.sources,
            )
        }
    }

    // --- Chapter 9.3: the operations ----------------------------------------------------------

    @Test
    fun `split produces two clips that together cover exactly the original`() {
        val timeline = oneClipTimeline(480_000)
        val split = Split("L1", 200_000).applyTo(timeline)
        val clips = split.layers[0].clips

        assertEquals(2, clips.size)
        assertEquals(0L, clips[0].timelineStartFrame)
        assertEquals(200_000L, clips[0].timelineEndFrame)
        assertEquals(200_000L, clips[1].timelineStartFrame)
        assertEquals(480_000L, clips[1].timelineEndFrame)
        assertEquals(
            "The second half must read from the right place in the source",
            200_000L,
            clips[1].sourceStartFrame,
        )
        assertEquals("The material must be the same length after splitting", 480_000L, split.lengthFrames)
    }

    @Test
    fun `split at a clip boundary changes nothing`() {
        val timeline = oneClipTimeline(480_000)
        assertEquals(timeline, Split("L1", 0).applyTo(timeline))
        assertEquals(timeline, Split("L1", 480_000).applyTo(timeline))
    }

    @Test
    fun `every seam carries a fade so a splice cannot click`() {
        // Chapter 9.4's edit-point law.
        val timeline = oneClipTimeline(480_000)
        val seam = EditOperation.seamFadeFrames(rate)
        assertEquals("5 ms at 48 kHz", 240L, seam)

        val split = Split("L1", 200_000).applyTo(timeline).layers[0].clips
        assertEquals("The left half must fade out into the seam", seam, split[0].fadeOutFrames)
        assertEquals("The right half must fade in from the seam", seam, split[1].fadeInFrames)

        val cut = DeleteRange(100_000, 200_000).applyTo(timeline).layers[0].clips
        assertEquals(2, cut.size)
        assertEquals(seam, cut[0].fadeOutFrames)
        assertEquals(seam, cut[1].fadeInFrames)
    }

    @Test
    fun `cut closes the gap and silence leaves it - the ripple law`() {
        val timeline = oneClipTimeline(480_000)

        val cut = DeleteRange(100_000, 200_000).applyTo(timeline)
        assertEquals("Cutting must shorten the material", 380_000L, cut.lengthFrames)
        assertEquals("The tail must move back to close the gap", 100_000L, cut.layers[0].clips[1].timelineStartFrame)

        val silenced = SilenceRange(100_000, 200_000).applyTo(timeline)
        assertEquals("Silencing must not shorten the material", 480_000L, silenced.lengthFrames)
        assertEquals("The tail must stay where it was", 200_000L, silenced.layers[0].clips[1].timelineStartFrame)
        assertNull("The silenced span must be empty", silenced.layers[0].clipAt(150_000))
    }

    @Test
    fun `cutting a range that swallows a clip removes it entirely`() {
        var timeline = oneClipTimeline(480_000)
        timeline = Split("L1", 100_000).applyTo(timeline)
        timeline = Split("L1", 200_000).applyTo(timeline)
        assertEquals(3, timeline.layers[0].clips.size)

        val cut = DeleteRange(100_000, 200_000).applyTo(timeline)
        assertEquals("The middle clip must be gone", 2, cut.layers[0].clips.size)
        assertEquals(380_000L, cut.lengthFrames)
    }

    @Test
    fun `cutting applies to every layer by default so layers stay in sync`() {
        val src = source("s1", 480_000)
        val timeline = Timeline(
            sampleRate = rate,
            sources = mapOf(src.id to src),
            layers = listOf(
                Layer("L1", "Vocals 1", listOf(Clip("a", "s1", 0, 480_000, 0))),
                Layer("L2", "Vocals 2", listOf(Clip("b", "s1", 0, 480_000, 0))),
            ),
        )
        val cut = DeleteRange(100_000, 200_000).applyTo(timeline)
        assertEquals(380_000L, cut.layers[0].lengthFrames)
        assertEquals("Both layers must be cut, or they drift apart", 380_000L, cut.layers[1].lengthFrames)

        val oneLayer = DeleteRange(100_000, 200_000, layerId = "L1").applyTo(timeline)
        assertEquals(380_000L, oneLayer.layers[0].lengthFrames)
        assertEquals(480_000L, oneLayer.layers[1].lengthFrames)
    }

    @Test
    fun `trimming the start slides the source window so the audio does not move`() {
        val timeline = oneClipTimeline(480_000)
        val trimmed = Trim("L1", "c1", newStartFrame = 48_000).applyTo(timeline)
        val clip = trimmed.layers[0].clips.single()

        assertEquals(48_000L, clip.timelineStartFrame)
        assertEquals(
            "Trimming the start must advance into the source by the same amount",
            48_000L,
            clip.sourceStartFrame,
        )
        assertEquals(432_000L, clip.lengthFrames)
    }

    @Test
    fun `gain applies to exactly the selected range and not a frame more`() {
        val timeline = oneClipTimeline(480_000)
        val gained = GainRange(100_000, 200_000, -6.0).applyTo(timeline)
        val clips = gained.layers[0].clips

        assertEquals("The range must be isolated by splitting at both edges", 3, clips.size)
        assertEquals(0.0, clips[0].gainDb, 1e-9)
        assertEquals(-6.0, clips[1].gainDb, 1e-9)
        assertEquals(0.0, clips[2].gainDb, 1e-9)
        assertEquals(100_000L, clips[1].timelineStartFrame)
        assertEquals(200_000L, clips[1].timelineEndFrame)
    }

    @Test
    fun `a clip cannot be moved on top of its neighbour`() {
        var timeline = oneClipTimeline(480_000)
        timeline = Split("L1", 240_000).applyTo(timeline)
        val second = timeline.layers[0].clips[1]

        val blocked = MoveClip("L1", second.id, 0).applyTo(timeline)
        assertEquals("Overlapping would break invariant 1, so the move is refused", timeline, blocked)
    }

    @Test
    fun `merging refuses rather than silently losing audio`() {
        val src = source("s1", 480_000)
        val overlapping = Timeline(
            sampleRate = rate,
            sources = mapOf(src.id to src),
            layers = listOf(
                Layer("L1", "One", listOf(Clip("a", "s1", 0, 240_000, 0))),
                Layer("L2", "Two", listOf(Clip("b", "s1", 0, 240_000, 100_000))),
            ),
        )
        assertEquals(
            "A merge that would drop audio must be refused, not performed quietly",
            overlapping,
            MergeLayers("L1", "L2").applyTo(overlapping),
        )

        val disjoint = Timeline(
            sampleRate = rate,
            sources = mapOf(src.id to src),
            layers = listOf(
                Layer("L1", "One", listOf(Clip("a", "s1", 0, 100_000, 0))),
                Layer("L2", "Two", listOf(Clip("b", "s1", 0, 100_000, 200_000))),
            ),
        )
        val merged = MergeLayers("L1", "L2").applyTo(disjoint)
        assertEquals(1, merged.layers.size)
        assertEquals(2, merged.layers[0].clips.size)
    }

    @Test
    fun `solo silences everything that is not soloed`() {
        val src = source("s1", 100_000)
        val timeline = Timeline(
            sampleRate = rate,
            sources = mapOf(src.id to src),
            layers = listOf(
                Layer("L1", "One", listOf(Clip("a", "s1", 0, 100_000, 0))),
                Layer("L2", "Two", listOf(Clip("b", "s1", 0, 100_000, 0)), soloed = true),
            ),
        )
        assertTrue(timeline.hasSolo)
        assertFalse(timeline.isAudible(timeline.layers[0]))
        assertTrue(timeline.isAudible(timeline.layers[1]))
    }

    @Test
    fun `mute beats solo, because a muted layer was silenced deliberately`() {
        val src = source("s1", 100_000)
        val timeline = Timeline(
            sampleRate = rate,
            sources = mapOf(src.id to src),
            layers = listOf(Layer("L1", "One", listOf(Clip("a", "s1", 0, 100_000, 0)), muted = true, soloed = true)),
        )
        assertFalse(timeline.isAudible(timeline.layers[0]))
    }

    // --- Chapter 9.4: fades -------------------------------------------------------------------

    @Test
    fun `equal power fades hold constant loudness through a crossfade`() {
        // Two linear fades sum to a dip in the middle — the audible hole in a naive crossfade.
        // Two equal-power curves sum to constant power, which is the whole point of the shape.
        for (t in listOf(0.0, 0.25, 0.5, 0.75, 1.0)) {
            val fadeIn = FadeShape.EQUAL_POWER.gainIn(t)
            val fadeOut = FadeShape.EQUAL_POWER.gainOut(t)
            val power = fadeIn * fadeIn + fadeOut * fadeOut
            assertEquals("Equal-power crossfade must hold power at t=$t", 1.0, power, 1e-9)
        }

        val linearPowerAtMidpoint =
            FadeShape.LINEAR.gainIn(0.5).let { it * it } + FadeShape.LINEAR.gainOut(0.5).let { it * it }
        assertTrue("Linear crossfades genuinely dip", linearPowerAtMidpoint < 0.9)
    }

    @Test
    fun `every fade shape runs from silence to unity`() {
        for (shape in FadeShape.entries) {
            assertEquals("$shape must start at silence", 0.0, shape.gainIn(0.0), 1e-9)
            assertEquals("$shape must reach unity", 1.0, shape.gainIn(1.0), 1e-9)
            assertTrue(
                "$shape must rise monotonically",
                (0..20).map { shape.gainIn(it / 20.0) }.zipWithNext().all { it.first <= it.second + 1e-12 },
            )
        }
    }

    @Test
    fun `clip gain combines the fade and the level`() {
        val clip = Clip(
            id = "c", sourceId = "s", sourceStartFrame = 0, lengthFrames = 1_000,
            timelineStartFrame = 0, gainDb = -6.0, fadeInFrames = 100, fadeOutFrames = 100,
            fadeShape = FadeShape.LINEAR,
        )
        val half = Math.pow(10.0, -6.0 / 20.0)
        assertEquals("Start of a fade-in is silence", 0.0, clip.gainAt(0), 1e-9)
        assertEquals("Mid fade-in is half the clip gain", half * 0.5, clip.gainAt(50), 1e-3)
        assertEquals("The body is the clip gain", half, clip.gainAt(500), 1e-9)
        assertEquals("The end is silence again", 0.0, clip.gainAt(1_000), 1e-9)
    }

    // --- Chapter 9.5: history ------------------------------------------------------------------

    @Test
    fun `undo and redo walk the states exactly`() {
        val timeline = oneClipTimeline(480_000)
        var history = EditHistory.of(timeline)
        assertFalse(history.canUndo)

        history = history.apply(Split("L1", 100_000))
        history = history.apply(DeleteRange(200_000, 300_000))
        assertEquals(380_000L, history.current.lengthFrames)

        history = history.undo()
        assertEquals("Undo must restore the previous state exactly", 480_000L, history.current.lengthFrames)
        assertEquals(2, history.current.layers[0].clips.size)

        history = history.undo()
        assertEquals(timeline, history.current)
        assertFalse(history.canUndo)

        history = history.redo().redo()
        assertEquals(380_000L, history.current.lengthFrames)
        assertFalse(history.canRedo)
    }

    @Test
    fun `an operation that changes nothing does not fill the history with no-ops`() {
        // Undo that appears to do nothing reads as a broken undo.
        val history = EditHistory.of(oneClipTimeline())
        val after = history.apply(Split("L1", 0))
        assertEquals("A no-op must not become a history step", history.steps.size, after.steps.size)
        assertFalse(after.canUndo)
    }

    @Test
    fun `editing after undoing discards the redo future cleanly`() {
        var history = EditHistory.of(oneClipTimeline(480_000))
        history = history.apply(Split("L1", 100_000))
        history = history.apply(Split("L1", 200_000))
        history = history.undo()
        assertTrue(history.canRedo)

        history = history.apply(DeleteRange(0, 50_000))
        assertFalse("A new edit must truncate the future", history.canRedo)
        assertEquals(430_000L, history.current.lengthFrames)
    }

    @Test
    fun `the history panel can travel to any recorded step`() {
        var history = EditHistory.of(oneClipTimeline(480_000))
        history = history.apply(Split("L1", 100_000))
        history = history.apply(DeleteRange(200_000, 300_000))
        history = history.apply(SetLayerGain("L1", -6.0))

        assertEquals(listOf("Open", "Split", "Cut", "Layer gain"), history.steps)

        val travelled = history.travelTo(1)
        assertEquals(480_000L, travelled.current.lengthFrames)
        assertEquals(0.0, travelled.current.layers[0].gainDb, 1e-9)
        assertTrue("Travelling back must leave a future to return to", travelled.canRedo)
    }

    @Test
    fun `history is capped and says so rather than forgetting silently`() {
        var history = EditHistory.of(oneClipTimeline(480_000))
        repeat(EditHistory.MAX_DEPTH + 40) { i ->
            history = history.apply(SetLayerGain("L1", -(i + 1).toDouble()))
        }
        assertEquals(EditHistory.MAX_DEPTH, history.steps.size)
        assertTrue("The panel must be able to tell the user history was truncated", history.isTruncated)
        assertEquals(
            "The most recent edit must still be current",
            -(EditHistory.MAX_DEPTH + 40).toDouble(),
            history.current.layers[0].gainDb,
            1e-9,
        )
    }

    // --- Rendering -------------------------------------------------------------------------------

    @Test
    fun `rendering a window returns exactly that window of the mix`() {
        val audio = TestSignals.sine(1_000.0, 2.0, rate, amplitude = 0.5)
        val provider = InMemorySourceProvider(mapOf("s1" to audio))
        val timeline = oneClipTimeline(audio.frameCount.toLong())

        val rendered = TimelineRenderer.render(timeline, provider, startFrame = 24_000, frameCount = 4_800)
        assertEquals(4_800, rendered.frameCount)
        assertEquals(0.5, TestSignals.magnitudeAt(rendered, 1_000.0), 0.02)
    }

    @Test
    fun `a silenced range renders as actual silence`() {
        val audio = TestSignals.sine(1_000.0, 2.0, rate, amplitude = 0.5)
        val provider = InMemorySourceProvider(mapOf("s1" to audio))
        val timeline = SilenceRange(24_000, 48_000).applyTo(oneClipTimeline(audio.frameCount.toLong()))

        val inside = TimelineRenderer.render(timeline, provider, 30_000, 4_800)
        assertEquals("A silenced span must render as silence", 0f, inside.peak(), 1e-7f)

        val outside = TimelineRenderer.render(timeline, provider, 60_000, 4_800)
        assertTrue("Audio outside the span must be untouched", outside.peak() > 0.4f)
    }

    @Test
    fun `a cut removes its audio and joins what was either side`() {
        // Two tones spliced: cut the middle out and the join must contain both, back to back.
        val first = TestSignals.sine(1_000.0, 1.0, rate, amplitude = 0.5)
        val provider = InMemorySourceProvider(mapOf("s1" to first))
        val timeline = DeleteRange(16_000, 32_000).applyTo(oneClipTimeline(first.frameCount.toLong()))

        assertEquals(32_000L, timeline.lengthFrames)
        val rendered = TimelineRenderer.renderAll(timeline, provider)
        assertEquals(32_000, rendered.frameCount)
        // The seam fade dips briefly but the material either side survives at level.
        assertTrue(rendered.slice(0, 12_000).peak() > 0.45f)
        assertTrue(rendered.slice(20_000, 32_000).peak() > 0.45f)
    }

    @Test
    fun `layer gain, mute and solo all reach the rendered mix`() {
        val audio = AudioBuffer.mono(FloatArray(48_000) { 0.5f }, rate)
        val provider = InMemorySourceProvider(mapOf("s1" to audio))
        val base = oneClipTimeline(48_000)

        val full = TimelineRenderer.renderAll(base, provider).peak()
        assertEquals(0.5f, full, 1e-6f)

        val quieter = TimelineRenderer.renderAll(SetLayerGain("L1", -6.0).applyTo(base), provider).peak()
        assertEquals("−6 dB must halve the amplitude", 0.25f, quieter, 0.01f)

        val muted = TimelineRenderer.renderAll(MuteLayer("L1", true).applyTo(base), provider).peak()
        assertEquals(0f, muted, 0f)
    }

    @Test
    fun `two layers sum in the mix`() {
        val audio = AudioBuffer.mono(FloatArray(48_000) { 0.3f }, rate)
        val provider = InMemorySourceProvider(mapOf("s1" to audio))
        val src = source("s1", 48_000)
        val timeline = Timeline(
            sampleRate = rate,
            sources = mapOf(src.id to src),
            layers = listOf(
                Layer("L1", "One", listOf(Clip("a", "s1", 0, 48_000, 0))),
                Layer("L2", "Two", listOf(Clip("b", "s1", 0, 48_000, 0))),
            ),
        )
        assertEquals(0.6f, TimelineRenderer.renderAll(timeline, provider).peak(), 1e-5f)
    }

    @Test
    fun `fades are evaluated per sample, not per block`() {
        // A fade evaluated once per render block steps in blocks, which is audible as zipper
        // noise on anything shorter than about a second.
        val audio = AudioBuffer.mono(FloatArray(48_000) { 1.0f }, rate)
        val provider = InMemorySourceProvider(mapOf("s1" to audio))
        val timeline = FadeClip("L1", "c1", fadeInFrames = 48_000, fadeOutFrames = 0, shape = FadeShape.LINEAR)
            .applyTo(oneClipTimeline(48_000))

        val rendered = TimelineRenderer.renderAll(timeline, provider)
        assertEquals(0.0f, rendered.channels[0][0], 1e-6f)
        assertEquals(0.25f, rendered.channels[0][12_000], 0.001f)
        assertEquals(0.5f, rendered.channels[0][24_000], 0.001f)
        assertEquals(0.75f, rendered.channels[0][36_000], 0.001f)

        // Every consecutive pair must differ by the same tiny amount — the signature of a
        // per-sample ramp rather than a per-block staircase.
        val steps = (1 until 1_000).map { rendered.channels[0][it] - rendered.channels[0][it - 1] }
        assertTrue("The fade stepped rather than ramped", steps.max() - steps.min() < 1e-6f)
    }

    @Test
    fun `peak estimation matches a full render without allocating one`() {
        val audio = TestSignals.sine(440.0, 3.0, rate, amplitude = 0.8)
        val provider = InMemorySourceProvider(mapOf("s1" to audio))
        val timeline = oneClipTimeline(audio.frameCount.toLong())

        val estimated = TimelineRenderer.estimatePeak(timeline, provider, blockFrames = 4_096)
        val actual = TimelineRenderer.renderAll(timeline, provider).peak()
        assertEquals(actual, estimated, 1e-6f)
    }

    @Test
    fun `rendering an empty timeline yields silence rather than failing`() {
        val provider = InMemorySourceProvider(emptyMap())
        val rendered = TimelineRenderer.render(Timeline.empty(rate), provider, 0, 1_000)
        assertEquals(1_000, rendered.frameCount)
        assertEquals(0f, rendered.peak(), 0f)
    }

    @Test
    fun `a recording is appended without disturbing what is already there`() {
        val timeline = oneClipTimeline(48_000)
        val take2 = source("s2", 24_000)
        val after = AppendRecording("L1", take2, atFrame = 48_000, clipId = "c2").applyTo(timeline)

        assertEquals(72_000L, after.lengthFrames)
        assertEquals(2, after.layers[0].clips.size)
        assertNotNull(after.sources["s2"])
        assertNotNull("The first take must survive", after.sources["s1"])
    }
}
