package ai.sautiy.core.dsp

import ai.sautiy.core.TestSignals
import ai.sautiy.core.analysis.Loudness
import ai.sautiy.core.audio.AudioBuffer
import kotlin.math.abs
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * The Voice Studio as one instrument.
 *
 * Two claims carry the whole feature and are tested first: that the live preview is the same
 * processing as the export, and that a preview fed in small blocks is identical to one fed in
 * large ones. Everything else — what each control does, what each space sounds like — is only
 * worth measuring once those hold.
 */
class VoiceStudioTest {

    private val rate = 48_000

    /** A voice-like test signal: a fundamental with harmonics and sibilant energy on top. */
    private fun voice(seconds: Double = 1.0, channels: Int = 1): AudioBuffer {
        val frames = (seconds * rate).toInt()
        val buffer = AudioBuffer.silence(channels, frames, rate)
        val partials = listOf(140.0 to 0.35, 280.0 to 0.22, 560.0 to 0.14, 1_400.0 to 0.09, 6_800.0 to 0.05)
        for (c in 0 until channels) {
            val channel = buffer.channels[c]
            for ((frequency, amplitude) in partials) {
                val step = 2.0 * Math.PI * frequency / rate
                val phase = c * 0.31
                for (i in channel.indices) {
                    channel[i] += (amplitude * kotlin.math.sin(step * i + phase)).toFloat()
                }
            }
        }
        return buffer
    }

    /** Settings with both offline stages switched off, so live and render must agree exactly. */
    private fun realtimeOnly() = VoiceStudioSettings(
        cleanup = CleanupStage(highPassHz = 80.0, humHz = 50.0),
        dynamics = DynamicsStage(
            compressor = DynamicsStage.CompressorSettings(thresholdDb = -22.0, ratio = 3.0),
            deEsser = DynamicsStage.DeEsserSettings(),
        ),
        refinement = VoiceRefinement(clarity = 0.4, warmth = 0.2, presence = 0.3, air = 0.25, depth = 0.3),
        ambience = VoiceSpacePreset.LECTURE_HALL.settings.ambience,
        loudness = LoudnessStage(target = null, limiterCeilingDb = null),
        outputGainDb = -1.0,
    )

    private fun runLive(studio: VoiceStudio, source: AudioBuffer, block: Int): AudioBuffer {
        val output = source.copy()
        val live = studio.live(output.sampleRate, output.channelCount)
        var position = 0
        while (position < output.frameCount) {
            val frames = minOf(block, output.frameCount - position)
            val slice = output.slice(position, position + frames)
            live.process(slice)
            for (c in 0 until output.channelCount) {
                slice.channels[c].copyInto(output.channels[c], position)
            }
            position += frames
        }
        return output
    }

    // --- The two claims the feature stands on ------------------------------------------------

    @Test
    fun `what you hear in preview is exactly what gets rendered`() {
        val settings = realtimeOnly()
        val studio = VoiceStudio(settings)
        val source = voice(1.0, channels = 2)

        val rendered = studio.render(source).audio
        val previewed = runLive(studio, source, block = 1_920)

        assertTrue("Nothing should be deferred here", studio.deferredStages.isEmpty())
        for (c in 0 until 2) {
            for (i in 0 until rendered.frameCount) {
                assertEquals("channel $c frame $i", rendered.channels[c][i], previewed.channels[c][i], 0f)
            }
        }
    }

    @Test
    fun `the preview is identical however small the audio callback's blocks are`() {
        val studio = VoiceStudio(realtimeOnly())
        val source = voice(0.8, channels = 2)

        val large = runLive(studio, source, block = 4_096)
        val small = runLive(studio, source, block = 97)

        for (c in 0 until 2) {
            for (i in 0 until large.frameCount) {
                assertEquals("channel $c frame $i", large.channels[c][i], small.channels[c][i], 0f)
            }
        }
    }

    @Test
    fun `the stages a preview cannot run are named rather than faked`() {
        val offline = VoiceStudioSettings(
            cleanup = CleanupStage(noiseReduction = 1.4),
            loudness = LoudnessStage(target = "PODCAST", limiterCeilingDb = -1.0),
        )
        assertEquals(
            listOf("Noise reduction", "Loudness normalisation", "Limiter"),
            VoiceStudio(offline).deferredStages,
        )
        assertTrue(VoiceStudio(realtimeOnly()).deferredStages.isEmpty())
    }

    @Test
    fun `render leaves the caller's audio untouched`() {
        val source = voice(0.3)
        val before = source.channels[0].copyOf()
        VoiceSpacePreset.LARGE_HALL.studio().render(source)
        assertTrue("render must not modify its input", before.contentEquals(source.channels[0]))
    }

    // --- The twelve spaces -------------------------------------------------------------------

    @Test
    fun `every space is complete, named and appears in the panel exactly once`() {
        assertEquals(12, VoiceSpacePreset.entries.size)
        assertEquals(12, VoiceSpacePreset.cardOrder.size)
        assertEquals(VoiceSpacePreset.entries.toSet(), VoiceSpacePreset.cardOrder.toSet())

        val names = VoiceSpacePreset.entries.map { it.displayName }
        assertEquals("Two spaces share a name", names.size, names.toSet().size)
        for (preset in VoiceSpacePreset.entries) {
            assertTrue(preset.displayName.isNotBlank())
            assertTrue("${preset.displayName} has no summary", preset.summary.length > 15)
        }
    }

    @Test
    fun `the twelve spaces named in the brief all exist`() {
        val expected = listOf(
            "Dry Studio", "Vocal Booth", "Broadcast Studio", "Warm Studio", "Podcast Studio",
            "Lecture Hall", "Auditorium", "Large Hall", "Prestige Recitation",
            "Majestic Recitation", "Natural Presence", "Cinematic Voice",
        )
        assertEquals(expected.toSet(), VoiceSpacePreset.entries.map { it.displayName }.toSet())
    }

    @Test
    fun `every space renders finite, unclipped audio that is audibly not the original`() {
        val source = voice(1.5, channels = 2)
        for (preset in VoiceSpacePreset.entries) {
            val rendered = preset.studio().render(source)

            for (c in 0 until 2) {
                for (sample in rendered.audio.channels[c]) {
                    assertTrue("${preset.displayName} produced $sample", sample.isFinite())
                }
            }
            assertFalse("${preset.displayName} clipped", rendered.report.clipped)

            var difference = 0.0
            for (i in 0 until source.frameCount) {
                difference += abs(rendered.audio.channels[0][i] - source.channels[0][i]).toDouble()
            }
            assertTrue("${preset.displayName} changed nothing", difference / source.frameCount > 1e-4)
        }
    }

    @Test
    fun `only Dry Studio and the safe one-tap have no room at all`() {
        val roomless = VoiceSpacePreset.entries.filter { it.settings.ambience.isBypassed }
        assertEquals(listOf(VoiceSpacePreset.DRY_STUDIO), roomless)
        assertTrue(OneTap.enhanceVoice().ambience.isBypassed)
        assertFalse(OneTap.studioVoice().ambience.isBypassed)
    }

    @Test
    fun `a space that states a delivery standard actually reaches it`() {
        // Loudness is measured after the room, which is the only order that can be true: adding
        // ambience changes the programme loudness, so normalising before it would miss.
        val source = voice(3.0)
        for (preset in VoiceSpacePreset.entries) {
            val targetName = preset.settings.loudness.target ?: continue
            val target = Loudness.Target.entries.first { it.name == targetName }
            val rendered = preset.studio().render(source)

            assertEquals(
                "${preset.displayName} aims at ${target.displayName} (${target.lufs} LUFS)",
                target.lufs,
                rendered.report.outputLufs,
                2.0,
            )
            assertTrue(
                "${preset.displayName} exceeded its true-peak ceiling",
                rendered.report.outputTruePeakDb <= target.truePeakCeilingDb + 0.5,
            )
        }
    }

    @Test
    fun `a space that sets a ceiling respects it`() {
        val source = voice(2.0).applyGain(2.0f)
        for (preset in VoiceSpacePreset.entries) {
            val ceiling = preset.settings.loudness.limiterCeilingDb ?: continue
            val rendered = preset.studio().render(source)
            val peakDb = ai.sautiy.core.audio.Decibels.fromLinear(rendered.audio.peak().toDouble())
            assertTrue(
                "${preset.displayName} peaked at $peakDb dBFS against a $ceiling dBFS ceiling",
                peakDb <= ceiling + 0.3,
            )
        }
    }

    @Test
    fun `recitation keeps its dynamics, which is the one thing a reciter will not forgive`() {
        // A voice with quiet and loud passages, so there are dynamics to lose in the first place.
        val frames = rate * 6
        val samples = FloatArray(frames)
        for (i in 0 until frames) {
            val t = i.toDouble() / rate
            val envelope = if (t % 2.0 < 1.0) 0.35 else 0.06
            samples[i] = (envelope * kotlin.math.sin(2 * Math.PI * 180 * t)).toFloat()
        }
        val source = AudioBuffer.mono(samples, rate)

        val recitation = VoiceSpacePreset.PRESTIGE_RECITATION.studio().render(source).audio
        val broadcast = VoiceSpacePreset.BROADCAST_STUDIO.studio().render(source).audio

        val recitationRange = Loudness.loudnessRange(recitation)
        val broadcastRange = Loudness.loudnessRange(broadcast)
        assertTrue(
            "Recitation range $recitationRange LU should exceed broadcast range $broadcastRange LU",
            recitationRange > broadcastRange,
        )
    }

    @Test
    fun `a voice survives serialisation, which is what makes it a recipe and not a render`() {
        val json = kotlinx.serialization.json.Json { prettyPrint = false }
        for (preset in VoiceSpacePreset.entries) {
            val encoded = json.encodeToString(VoiceStudioSettings.serializer(), preset.settings)
            val decoded = json.decodeFromString(VoiceStudioSettings.serializer(), encoded)
            assertEquals(preset.name, preset.settings, decoded)
        }
        for (settings in listOf(OneTap.enhanceVoice(), OneTap.studioVoice())) {
            val encoded = json.encodeToString(VoiceStudioSettings.serializer(), settings)
            assertEquals(settings, json.decodeFromString(VoiceStudioSettings.serializer(), encoded))
        }
    }

    @Test
    fun `the larger spaces really are larger`() {
        // Ordered by the size of the room, which is not the same axis as the panel order:
        // Natural Presence is a small ordinary room with very little of it, while Vocal Booth
        // is a genuinely tiny space heard clearly.
        val order = listOf(
            VoiceSpacePreset.VOCAL_BOOTH,
            VoiceSpacePreset.NATURAL_PRESENCE,
            VoiceSpacePreset.PODCAST_STUDIO,
            VoiceSpacePreset.LECTURE_HALL,
            VoiceSpacePreset.AUDITORIUM,
            VoiceSpacePreset.MAJESTIC_RECITATION,
        )
        for (i in 1 until order.size) {
            val smaller = order[i - 1].settings.effectiveAmbience
            val larger = order[i].settings.effectiveAmbience
            assertTrue(
                "${order[i].displayName} should decay longer than ${order[i - 1].displayName}",
                larger.decaySeconds > smaller.decaySeconds,
            )
            assertTrue(
                "${order[i].displayName} should sit further back than ${order[i - 1].displayName}",
                larger.preDelayMs > smaller.preDelayMs,
            )
        }
    }

    // --- The eight refinement controls -------------------------------------------------------

    private fun toneOnly(refinement: VoiceRefinement) = VoiceStudioSettings(
        cleanup = CleanupStage(highPassHz = null),
        dynamics = DynamicsStage(),
        refinement = refinement,
        ambience = AmbienceSettings.NONE,
        loudness = LoudnessStage(limiterCeilingDb = null),
    )

    private fun responseDbAt(refinement: VoiceRefinement, frequency: Double): Double {
        val source = TestSignals.sine(frequency, 0.5, rate, amplitude = 0.4)
        val processed = VoiceStudio(toneOnly(refinement)).render(source).audio
        // Skip the filters' settling time, so what is measured is the steady-state response.
        val settled = TestSignals.trimEdges(processed, rate / 20)
        val reference = TestSignals.trimEdges(source, rate / 20)
        return TestSignals.magnitudeDbAt(settled, frequency) - TestSignals.magnitudeDbAt(reference, frequency)
    }

    @Test
    fun `each refinement control moves its own range and leaves the far end alone`() {
        // frequency the control owns, a frequency it must not disturb, and the control itself
        val cases = listOf(
            Triple("clarity", 2_400.0, VoiceRefinement(clarity = 1.0)),
            Triple("presence", 4_000.0, VoiceRefinement(presence = 1.0)),
            Triple("richness", 420.0, VoiceRefinement(richness = 1.0)),
            Triple("body", 90.0, VoiceRefinement(body = 1.0)),
            Triple("air", 15_000.0, VoiceRefinement(air = 1.0)),
            Triple("brightness", 10_000.0, VoiceRefinement(brightness = 1.0)),
        )
        for ((name, frequency, refinement) in cases) {
            val lift = responseDbAt(refinement, frequency)
            assertTrue("$name at +1 lifted ${frequency}Hz by only $lift dB", lift > 2.0)

            val cut = responseDbAt(
                when (name) {
                    "clarity" -> VoiceRefinement(clarity = -1.0)
                    "presence" -> VoiceRefinement(presence = -1.0)
                    "richness" -> VoiceRefinement(richness = -1.0)
                    "body" -> VoiceRefinement(body = -1.0)
                    "air" -> VoiceRefinement(air = -1.0)
                    else -> VoiceRefinement(brightness = -1.0)
                },
                frequency,
            )
            assertTrue("$name at −1 cut ${frequency}Hz by only $cut dB", cut < -2.0)
        }
    }

    @Test
    fun `warmth adds weight below and softens above, which is what the word means`() {
        assertTrue(responseDbAt(VoiceRefinement(warmth = 1.0), 120.0) > 2.5)
        assertTrue(responseDbAt(VoiceRefinement(warmth = 1.0), 12_000.0) < -1.0)
    }

    @Test
    fun `clarity clears the mud it lifts the consonants over`() {
        // Lifting presence without clearing the boxiness underneath just makes the mud louder.
        assertTrue(responseDbAt(VoiceRefinement(clarity = 1.0), 2_400.0) > 2.5)
        assertTrue(responseDbAt(VoiceRefinement(clarity = 1.0), 320.0) < -1.5)
    }

    @Test
    fun `a centred control is exactly transparent, not nearly`() {
        assertTrue(VoiceRefinement().isNeutral)
        assertTrue(VoiceRefinement().bands().isEmpty())

        val source = voice(0.4)
        val settings = toneOnly(VoiceRefinement())
        assertTrue(settings.isTransparent)
        val rendered = VoiceStudio(settings).render(source).audio
        for (i in 0 until source.frameCount) {
            assertEquals(source.channels[0][i], rendered.channels[0][i], 0f)
        }
    }

    @Test
    fun `depth moves the listener back by driving the room, and says nothing when there is none`() {
        val room = VoiceSpacePreset.LECTURE_HALL.settings.ambience
        val near = VoiceStudioSettings(ambience = room, refinement = VoiceRefinement(depth = 0.0))
        val far = VoiceStudioSettings(ambience = room, refinement = VoiceRefinement(depth = 1.0))

        assertTrue(far.effectiveAmbience.wetDryMix > near.effectiveAmbience.wetDryMix)
        assertTrue(far.effectiveAmbience.preDelayMs > near.effectiveAmbience.preDelayMs)
        assertTrue(far.effectiveAmbience.roomSize > near.effectiveAmbience.roomSize)

        // With no room to move within, depth changes nothing rather than inventing a room.
        val roomless = VoiceStudioSettings(
            ambience = AmbienceSettings.NONE,
            refinement = VoiceRefinement(depth = 1.0),
        )
        assertTrue(roomless.effectiveAmbience.isBypassed)
    }

    @Test
    fun `a control refuses a value outside its range rather than clamping silently`() {
        assertTrue(runCatching { VoiceRefinement(clarity = 1.5) }.isFailure)
        assertTrue(runCatching { VoiceRefinement(depth = -2.0) }.isFailure)
        assertTrue(runCatching { LoudnessStage(target = "CINEMA") }.isFailure)
        assertTrue(runCatching { LoudnessStage(limiterCeilingDb = 2.0) }.isFailure)
        assertTrue(runCatching { CleanupStage(humHz = 100.0) }.isFailure)
        assertTrue(runCatching { DynamicsStage.DeEsserSettings(frequencyHz = 500.0) }.isFailure)
    }

    // --- Stage order, where it is observable -------------------------------------------------

    @Test
    fun `the compressor works on the recording, not on the equaliser's boosts`() {
        // Dynamics before tone: what the compressor reduces must not change when the tone
        // controls move. If it did, every equaliser tweak would silently re-compress the voice.
        val source = voice(1.0)
        val base = VoiceStudioSettings(
            cleanup = CleanupStage(highPassHz = null),
            dynamics = DynamicsStage(
                compressor = DynamicsStage.CompressorSettings(thresholdDb = -30.0, ratio = 4.0),
            ),
            loudness = LoudnessStage(limiterCeilingDb = null),
        )

        val flat = VoiceStudio(base).render(source).report.compressorReductionDb
        val boosted = VoiceStudio(
            base.copy(refinement = VoiceRefinement(body = 1.0, air = 1.0)),
        ).render(source).report.compressorReductionDb

        assertTrue("The compressor did nothing, so this proves nothing", flat < -0.5)
        assertEquals("Tone must not reach the compressor's detector", flat, boosted, 1e-9)
    }

    @Test
    fun `the report measures what happened rather than what was configured`() {
        val source = voice(2.0)
        val rendered = VoiceSpacePreset.BROADCAST_STUDIO.studio().render(source)

        assertTrue(rendered.report.inputLufs.isFinite())
        assertTrue(rendered.report.outputLufs.isFinite())
        assertTrue("The compressor should have worked", rendered.report.compressorReductionDb < 0.0)
        assertNotEquals(0.0, rendered.report.normalisationGainDb, 0.0)
        assertTrue(rendered.report.outputTruePeakDb <= -0.5)
    }

    // --- The de-esser, which shipped broken once ---------------------------------------------

    @Test
    fun `the de-esser cuts sibilance and leaves the vowel where it was`() {
        // The previous implementation used signal minus high-pass as its low band. Phase shift
        // leaves most of the sibilance in that band, so it reduced 7 kHz by under a decibel
        // while appearing to work. A Linkwitz-Riley crossover is the fix; this is its guard.
        fun changeDbAt(frequency: Double): Double {
            val source = TestSignals.sine(frequency, 0.5, rate, amplitude = 0.7)
            val processed = source.copy()
            StreamingDeEsser(6_000.0, -30.0, 5.0, rate, 1).process(processed)
            val settled = TestSignals.trimEdges(processed, rate / 20)
            val reference = TestSignals.trimEdges(source, rate / 20)
            return TestSignals.magnitudeDbAt(settled, frequency) - TestSignals.magnitudeDbAt(reference, frequency)
        }

        val sibilance = changeDbAt(7_000.0)
        val vowel = changeDbAt(300.0)
        assertTrue("The de-esser only reduced 7 kHz by $sibilance dB", sibilance < -3.0)
        assertTrue("The de-esser moved a 300 Hz vowel by $vowel dB", abs(vowel) < 1.0)
    }

    @Test
    fun `the de-esser is streaming too, so preview and export agree`() {
        val source = voice(0.5)
        val oneShot = source.copy()
        StreamingDeEsser(6_000.0, -28.0, 4.0, rate, 1).process(oneShot)

        val streamed = source.copy()
        val engine = StreamingDeEsser(6_000.0, -28.0, 4.0, rate, 1)
        var position = 0
        while (position < streamed.frameCount) {
            val frames = minOf(211, streamed.frameCount - position)
            val slice = streamed.slice(position, position + frames)
            engine.process(slice)
            slice.channels[0].copyInto(streamed.channels[0], position)
            position += frames
        }

        for (i in 0 until oneShot.frameCount) {
            assertEquals("frame $i", oneShot.channels[0][i], streamed.channels[0][i], 0f)
        }
    }

    // --- Cleanup -----------------------------------------------------------------------------

    @Test
    fun `hum removal takes the fundamental and its harmonics, not just the fundamental`() {
        // A 50 Hz notch on its own leaves the 100 Hz and 150 Hz buzz that made the hum
        // noticeable in the first place.
        val settings = VoiceStudioSettings(
            cleanup = CleanupStage(highPassHz = null, humHz = 50.0),
            dynamics = DynamicsStage(),
            loudness = LoudnessStage(limiterCeilingDb = null),
        )
        for (frequency in listOf(50.0, 100.0, 150.0)) {
            val source = TestSignals.sine(frequency, 1.0, rate, amplitude = 0.5)
            val processed = VoiceStudio(settings).render(source).audio
            val settled = TestSignals.trimEdges(processed, rate / 4)
            val reference = TestSignals.trimEdges(source, rate / 4)
            val change = TestSignals.magnitudeDbAt(settled, frequency) -
                TestSignals.magnitudeDbAt(reference, frequency)
            assertTrue("${frequency}Hz hum was only reduced by $change dB", change < -20.0)
        }
    }

    @Test
    fun `the high-pass removes rumble and not the voice`() {
        val settings = VoiceStudioSettings(
            cleanup = CleanupStage(highPassHz = 80.0),
            dynamics = DynamicsStage(),
            loudness = LoudnessStage(limiterCeilingDb = null),
        )
        fun changeDbAt(frequency: Double): Double {
            val source = TestSignals.sine(frequency, 1.0, rate, amplitude = 0.5)
            val processed = VoiceStudio(settings).render(source).audio
            return TestSignals.magnitudeDbAt(TestSignals.trimEdges(processed, rate / 4), frequency) -
                TestSignals.magnitudeDbAt(TestSignals.trimEdges(source, rate / 4), frequency)
        }
        assertTrue("30 Hz rumble survived", changeDbAt(30.0) < -12.0)
        assertTrue("200 Hz of voice was damaged", abs(changeDbAt(200.0)) < 1.0)
    }

    // --- The one-tap buttons -----------------------------------------------------------------

    @Test
    fun `Enhance Voice improves the recording without putting it somewhere else`() {
        val settings = OneTap.enhanceVoice()
        assertTrue("Enhance must not add a room", settings.ambience.isBypassed)
        assertFalse(settings.isTransparent)

        val source = voice(3.0).applyGain(0.25f)
        val rendered = VoiceStudio(settings).render(source)

        assertFalse("Enhance Voice clipped", rendered.report.clipped)
        assertTrue(
            "A quiet recording should come back at a usable level, was ${rendered.report.outputLufs} LUFS",
            rendered.report.outputLufs > rendered.report.inputLufs,
        )
        assertEquals(-19.0, rendered.report.outputLufs, 2.0)
    }

    @Test
    fun `Studio Voice is a finished production, room and all`() {
        val settings = OneTap.studioVoice()
        assertFalse("Studio Voice must place the voice in a room", settings.ambience.isBypassed)
        assertNotEquals(null, settings.cleanup.noiseReduction)
        assertNotEquals(null, settings.loudness.target)

        val rendered = VoiceStudio(settings).render(voice(3.0))
        assertFalse(rendered.report.clipped)
        assertEquals(-16.0, rendered.report.outputLufs, 2.0)
    }

    @Test
    fun `a live chain reset clears every filter, not most of them`() {
        val studio = VoiceStudio(realtimeOnly())
        val live = studio.live(rate, 1)
        live.process(voice(0.5))
        live.reset()

        val silence = AudioBuffer.silence(1, rate / 2, rate)
        live.process(silence)
        assertEquals("Something rang through a reset", 0f, silence.peak(), 1e-7f)
    }

    @Test
    fun `a chain refuses audio it was not built for`() {
        val live = VoiceStudio(realtimeOnly()).live(rate, 1)
        assertTrue(runCatching { live.process(AudioBuffer.silence(2, 128, rate)) }.isFailure)
        assertTrue(runCatching { live.process(AudioBuffer.silence(1, 128, 44_100)) }.isFailure)
    }
}
