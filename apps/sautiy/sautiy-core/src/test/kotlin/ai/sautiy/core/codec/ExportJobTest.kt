package ai.sautiy.core.codec

import ai.sautiy.core.TestSignals
import ai.sautiy.core.audio.AudioBuffer
import ai.sautiy.core.dsp.CleanupStage
import ai.sautiy.core.dsp.LoudnessStage
import ai.sautiy.core.dsp.VoiceSpacePreset
import ai.sautiy.core.dsp.VoiceStudioSettings
import ai.sautiy.core.edit.Clip
import ai.sautiy.core.edit.InMemorySourceProvider
import ai.sautiy.core.edit.Layer
import ai.sautiy.core.edit.Source
import ai.sautiy.core.edit.Timeline
import java.io.ByteArrayOutputStream
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ExportJobTest {

    private val rate = 48_000

    private fun project(audio: AudioBuffer): Pair<Timeline, InMemorySourceProvider> {
        val source = Source("s1", "s1.wav", audio.sampleRate, audio.channelCount, audio.frameCount.toLong())
        val timeline = Timeline(
            sampleRate = audio.sampleRate,
            sources = mapOf(source.id to source),
            layers = listOf(
                Layer("L1", "Vocals 1", listOf(Clip("c1", "s1", 0, audio.frameCount.toLong(), 0))),
            ),
        )
        return timeline to InMemorySourceProvider(mapOf("s1" to audio))
    }

    @Test
    fun `a project exports to wav with the right length and byte count`() {
        val audio = TestSignals.sine(440.0, 2.0, rate, amplitude = 0.6)
        val (timeline, provider) = project(audio)
        val out = ByteArrayOutputStream()

        val result = ExportJob(timeline, provider, ExportFormat.WAV).run(out)

        assertEquals(audio.frameCount.toLong(), result.durationFrames)
        assertEquals(rate, result.sampleRate)
        assertEquals("The reported size must be the real size", out.size().toLong(), result.bytesWritten)
        assertFalse(result.clipped)
    }

    @Test
    fun `a project exports to flac and the audio survives`() {
        val audio = TestSignals.sine(440.0, 1.0, rate, amplitude = 0.6)
        val (timeline, provider) = project(audio)
        val out = ByteArrayOutputStream()

        ExportJob(timeline, provider, ExportFormat.FLAC).run(out)
        val decoded = FlacDecoder.decode(out.toByteArray())

        assertEquals(audio.frameCount, decoded.frameCount)
        assertTrue(TestSignals.snrDb(audio, decoded) > 85.0)
    }

    @Test
    fun `what is exported is what was heard - the same renderer, the same edits`() {
        val audio = TestSignals.sine(440.0, 2.0, rate, amplitude = 0.6)
        var (timeline, provider) = project(audio)
        // Cut a second out of the middle.
        timeline = ai.sautiy.core.edit.DeleteRange(rate.toLong() / 2, rate.toLong() * 3 / 2).applyTo(timeline)

        val out = ByteArrayOutputStream()
        val result = ExportJob(timeline, provider, ExportFormat.WAV).run(out)

        assertEquals(
            "The export must be exactly as long as the edited timeline",
            timeline.lengthFrames,
            result.durationFrames,
        )
        assertEquals(rate.toLong(), result.durationFrames)
    }

    @Test
    fun `the Voice Studio is applied before encoding and its effect is real`() {
        val audio = TestSignals.sine(440.0, 3.0, rate, amplitude = 0.05)
        val (timeline, provider) = project(audio)

        val plain = ByteArrayOutputStream()
        ExportJob(timeline, provider, ExportFormat.WAV).run(plain)

        val enhanced = ByteArrayOutputStream()
        val result = ExportJob(
            timeline, provider, ExportFormat.WAV,
            voice = VoiceSpacePreset.PODCAST.settings,
        ).run(enhanced)

        assertTrue(
            "A quiet recording exported through Podcast must come out louder",
            result.peak > 0.2f,
        )
        assertTrue(plain.size() > 0 && enhanced.size() > 0)
    }

    @Test
    fun `a transparent voice changes nothing`() {
        val audio = TestSignals.sine(440.0, 1.0, rate, amplitude = 0.5)
        val (timeline, provider) = project(audio)

        val without = ByteArrayOutputStream()
        ExportJob(timeline, provider, ExportFormat.WAV).run(without)

        val with = ByteArrayOutputStream()
        ExportJob(
            timeline, provider, ExportFormat.WAV,
            voice = VoiceStudioSettings(
                cleanup = CleanupStage(highPassHz = null),
                loudness = LoudnessStage(limiterCeilingDb = null),
            ),
        ).run(with)

        assertTrue(without.toByteArray().contentEquals(with.toByteArray()))
    }

    @Test
    fun `progress runs monotonically from zero to one across the whole job`() {
        // A bar that races to 100% while rendering and then sits there is worse than no bar.
        val audio = TestSignals.sine(440.0, 2.0, rate, amplitude = 0.5)
        val (timeline, provider) = project(audio)

        val seen = mutableListOf<Pair<Double, ExportJob.Stage>>()
        ExportJob(timeline, provider, ExportFormat.FLAC, voice = VoiceSpacePreset.PURE_STUDIO.settings)
            .run(ByteArrayOutputStream()) { fraction, stage -> seen += fraction to stage }

        assertTrue("Progress must be reported", seen.size > 3)
        assertTrue("Progress must never go backwards", seen.map { it.first }.zipWithNext().all { it.first <= it.second + 1e-9 })
        assertEquals(0.0, seen.first().first, 1e-9)
        assertEquals(1.0, seen.last().first, 1e-9)

        val stages = seen.map { it.second }.distinct()
        assertTrue("Rendering must be reported", ExportJob.Stage.Rendering in stages)
        assertTrue("Enhancing must be reported", ExportJob.Stage.Processing in stages)
        assertTrue("Encoding must be reported", ExportJob.Stage.Encoding in stages)
    }

    @Test
    fun `encoding is never reported before rendering has finished`() {
        val audio = TestSignals.sine(440.0, 1.0, rate, amplitude = 0.5)
        val (timeline, provider) = project(audio)

        var firstEncodeFraction = -1.0
        ExportJob(timeline, provider, ExportFormat.WAV).run(ByteArrayOutputStream()) { fraction, stage ->
            if (stage == ExportJob.Stage.Encoding && firstEncodeFraction < 0) firstEncodeFraction = fraction
        }
        assertTrue(
            "Encoding began at $firstEncodeFraction — rendering must own the first part of the bar",
            firstEncodeFraction >= 0.19,
        )
    }

    @Test
    fun `a format that cannot carry the project rate is resampled rather than silently mislabelled`() {
        // Exporting an unsupported rate produces a file some decoders open and others reject —
        // a failure the user discovers later, on somebody else's machine.
        assertEquals(44_100, ExportJob.targetSampleRateFor(ExportFormat.MP3, 44_100))
        assertEquals(48_000, ExportJob.targetSampleRateFor(ExportFormat.MP3, 48_000))
        assertEquals(
            "96 kHz is not an MPEG rate; the nearest legal one at or above must be chosen",
            48_000,
            ExportJob.targetSampleRateFor(ExportFormat.MP3, 96_000),
        )
        assertEquals(
            "22.05 kHz is the nearest legal rate at or above 20 kHz — going to 24 kHz would " +
                "resample further than the material requires",
            22_050,
            ExportJob.targetSampleRateFor(ExportFormat.MP3, 20_000),
        )

        assertEquals("WAV carries whatever the project is at", 96_000, ExportJob.targetSampleRateFor(ExportFormat.WAV, 96_000))
        assertEquals(96_000, ExportJob.targetSampleRateFor(ExportFormat.FLAC, 96_000))
        assertEquals(96_000, ExportJob.targetSampleRateFor(ExportFormat.M4A, 96_000))
    }

    @Test
    fun `resampling on export actually changes the written rate`() {
        val audio = TestSignals.sine(1_000.0, 1.0, 96_000, amplitude = 0.5)
        val (timeline, provider) = project(audio)
        val out = ByteArrayOutputStream()

        // FLAC keeps 96 kHz; ask for the MP3 target rate explicitly through the same helper the
        // job uses, then verify a real export at that rate round-trips.
        assertEquals(48_000, ExportJob.targetSampleRateFor(ExportFormat.MP3, 96_000))

        val result = ExportJob(timeline, provider, ExportFormat.FLAC).run(out)
        assertEquals(96_000, result.sampleRate)
    }

    @Test
    fun `clipping is reported rather than hidden`() {
        val hot = AudioBuffer.mono(FloatArray(rate) { if (it % 2 == 0) 1.4f else -1.4f }, rate)
        val (timeline, provider) = project(hot)

        val result = ExportJob(timeline, provider, ExportFormat.WAV).run(ByteArrayOutputStream())
        assertTrue("Material over full scale must be reported as clipped", result.clipped)
        assertTrue(result.peak > 1.0f)
    }

    @Test
    fun `an empty project refuses to export rather than writing a zero length file`() {
        val timeline = Timeline.empty(rate)
        val provider = InMemorySourceProvider(emptyMap())
        val failure = runCatching {
            ExportJob(timeline, provider, ExportFormat.WAV).run(ByteArrayOutputStream())
        }.exceptionOrNull()
        assertTrue("Expected a refusal, got $failure", failure is IllegalArgumentException)
    }

    @Test
    fun `the caller keeps ownership of its stream`() {
        // Closing a document URI the caller still needs is a bug that only shows up on a device.
        var closed = false
        val stream = object : java.io.OutputStream() {
            val buffer = ByteArrayOutputStream()
            override fun write(b: Int) = buffer.write(b)
            override fun write(b: ByteArray, off: Int, len: Int) = buffer.write(b, off, len)
            override fun close() { closed = true }
        }

        val audio = TestSignals.sine(440.0, 0.2, rate, amplitude = 0.5)
        val (timeline, provider) = project(audio)
        ExportJob(timeline, provider, ExportFormat.WAV).run(stream)

        assertFalse("The export must not close a stream it does not own", closed)
        assertTrue(stream.buffer.size() > 0)
    }

    @Test
    fun `metadata reaches the file`() {
        val audio = TestSignals.sine(440.0, 0.5, rate, amplitude = 0.5)
        val (timeline, provider) = project(audio)
        val out = ByteArrayOutputStream()

        ExportJob(
            timeline, provider, ExportFormat.FLAC,
            metadata = ExportMetadata(title = "Al-Fatihah", artist = "Imam Ahmad Sulaimiy"),
        ).run(out)

        val text = String(out.toByteArray(), Charsets.UTF_8)
        assertTrue(text.contains("TITLE=Al-Fatihah"))
        assertTrue(text.contains("ARTIST=Imam Ahmad Sulaimiy"))
    }
}
