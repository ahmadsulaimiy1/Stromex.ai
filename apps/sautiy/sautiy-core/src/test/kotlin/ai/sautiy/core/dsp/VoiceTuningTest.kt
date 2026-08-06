package ai.sautiy.core.dsp

import ai.sautiy.core.audio.AudioBuffer
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * The tuning loop: what a listener says, and what the engine does about it.
 *
 * These tests are the reason the loop can be trusted without an engineer in the room. A listener
 * taps "too bright" and something has to get less bright — not differently bright, not brighter,
 * and not nothing. Every note is checked for direction, for size, and for not wandering into
 * controls it has no business touching.
 */
class VoiceTuningTest {

    private val rate = 48_000

    /** A voice-like signal with adjustable tonal balance, so the advisor can be given real cases. */
    private fun voice(
        seconds: Double = 3.0,
        amplitude: Double = 0.4,
        brightBoost: Double = 1.0,
        lowBoost: Double = 1.0,
        hissAmplitude: Double = 0.0,
        seed: Long = 7L,
    ): AudioBuffer {
        val frames = (seconds * rate).toInt()
        val samples = FloatArray(frames)
        val random = java.util.Random(seed)
        val partials = listOf(
            120.0 to 0.40 * lowBoost,
            240.0 to 0.26 * lowBoost,
            700.0 to 0.16,
            1_600.0 to 0.10,
            3_200.0 to 0.08 * brightBoost,
            7_500.0 to 0.05 * brightBoost,
        )
        for ((frequency, level) in partials) {
            val step = 2.0 * Math.PI * frequency / rate
            for (i in 0 until frames) samples[i] += (amplitude * level * kotlin.math.sin(step * i)).toFloat()
        }
        if (hissAmplitude > 0.0) {
            for (i in 0 until frames) samples[i] += (random.nextGaussian() * hissAmplitude).toFloat()
        }
        return AudioBuffer.mono(samples, rate)
    }

    // --- Listener notes ----------------------------------------------------------------------

    private fun aVoiceWithARoom() = VoiceSpacePreset.LECTURE_HALL.settings

    @Test
    fun `too bright makes it less bright, and too dark makes it brighter`() {
        val start = aVoiceWithARoom()
        val darker = ListenerNote.TOO_BRIGHT.applyTo(start)
        val brighter = ListenerNote.TOO_DARK.applyTo(start)

        assertTrue(darker.refinement.air < start.refinement.air)
        assertTrue(darker.refinement.brightness < start.refinement.brightness)
        assertTrue("The room's top end moves too", darker.ambience.brightness < start.ambience.brightness)

        assertTrue(brighter.refinement.air > start.refinement.air)
        assertTrue(brighter.refinement.brightness > start.refinement.brightness)
        assertTrue(brighter.ambience.brightness > start.ambience.brightness)
    }

    @Test
    fun `the two brightness notes undo each other`() {
        // A listener who taps the wrong word must be able to get back by tapping the other one.
        val start = aVoiceWithARoom()
        val there = ListenerNote.TOO_BRIGHT.applyTo(start)
        val back = ListenerNote.TOO_DARK.applyTo(there)

        assertEquals(start.refinement.air, back.refinement.air, 1e-9)
        assertEquals(start.refinement.brightness, back.refinement.brightness, 1e-9)
        assertEquals(start.ambience.brightness, back.ambience.brightness, 1e-9)
    }

    @Test
    fun `too much room takes room away and too little adds it`() {
        val start = aVoiceWithARoom()
        assertTrue(ListenerNote.TOO_MUCH_AMBIENCE.applyTo(start).ambience.wetDryMix < start.ambience.wetDryMix)
        assertTrue(ListenerNote.TOO_LITTLE_AMBIENCE.applyTo(start).ambience.wetDryMix > start.ambience.wetDryMix)
    }

    @Test
    fun `asking for more room when there is none creates one`() {
        // Otherwise the note appears to do nothing and the control reads as broken.
        val roomless = VoiceSpacePreset.PURE_STUDIO.settings
        assertTrue(roomless.ambience.isBypassed)

        val withRoom = ListenerNote.TOO_LITTLE_AMBIENCE.applyTo(roomless)
        assertFalse("Asking for room produced no room", withRoom.ambience.isBypassed)
        assertTrue(withRoom.ambience.wetDryMix > 0.0)
    }

    @Test
    fun `too harsh pulls presence back and tightens the de-esser`() {
        // Harshness is presence *and* sibilance. Moving only one leaves the listener saying it
        // again, which is how a tuning cycle stops converging.
        val start = aVoiceWithARoom()
        val softer = ListenerNote.TOO_HARSH.applyTo(start)

        assertTrue(softer.refinement.presence < start.refinement.presence)
        val deEsser = softer.dynamics.deEsser
        assertNotNull("Harshness must engage a de-esser", deEsser)
        val before = start.dynamics.deEsser
        if (before != null) {
            assertTrue("The de-esser must reach further down", deEsser!!.thresholdDb < before.thresholdDb)
        }
    }

    @Test
    fun `too muddy clears the low mids and gets the room out of the way of the words`() {
        val start = aVoiceWithARoom()
        val clearer = ListenerNote.TOO_MUDDY.applyTo(start)

        assertTrue(clearer.refinement.warmth < start.refinement.warmth)
        assertTrue(clearer.refinement.richness < start.refinement.richness)
        assertTrue(clearer.refinement.clarity > start.refinement.clarity)
        assertTrue("The room must step out of the consonant band", clearer.ambience.presence > start.ambience.presence)
        assertTrue(clearer.ambience.speechPriority > start.ambience.speechPriority)
    }

    @Test
    fun `excellent changes nothing at all`() {
        val start = aVoiceWithARoom()
        assertEquals(start, ListenerNote.EXCELLENT.applyTo(start))
    }

    @Test
    fun `every note leaves a legal voice, however many times it is tapped`() {
        // A listener will lean on a word. Twenty taps must not produce a setting the engine
        // refuses to build, and must not throw on the way there.
        for (note in ListenerNote.entries) {
            var settings = aVoiceWithARoom()
            repeat(20) { settings = note.applyTo(settings) }
            // Constructing the engine is what validates the values.
            settings.build().live(rate, 1)
            settings.effectiveAmbience.build(rate, 1)
        }
    }

    @Test
    fun `a note is audible on a direct comparison but never a jump`() {
        val start = aVoiceWithARoom()
        val source = voice(1.0)
        val before = VoiceStudio(start).render(source).audio
        val after = VoiceStudio(ListenerNote.TOO_BRIGHT.applyTo(start)).render(source).audio

        var difference = 0.0
        var reference = 0.0
        for (i in 0 until source.frameCount) {
            difference += kotlin.math.abs(after.channels[0][i] - before.channels[0][i]).toDouble()
            reference += kotlin.math.abs(before.channels[0][i]).toDouble()
        }
        val relative = difference / reference.coerceAtLeast(1e-9)

        assertTrue("One note changed nothing audible: $relative", relative > 0.005)
        assertTrue("One note changed too much to be one step: $relative", relative < 0.6)
    }

    // --- The panel ---------------------------------------------------------------------------

    @Test
    fun `one listener is an opinion and four agreeing is a defect`() {
        var panel = ListeningPanel()
        panel = panel.record(ListenerNote.TOO_BRIGHT)
        panel = panel.record(ListenerNote.EXCELLENT)
        panel = panel.record(ListenerNote.EXCELLENT)
        panel = panel.record(ListenerNote.EXCELLENT)

        assertEquals(4, panel.listeners)
        assertTrue("Three of four called it right", panel.isAccepted())
        assertTrue("One person's brightness note is not consensus", panel.consensus().isEmpty())

        var agreed = ListeningPanel()
        repeat(3) { agreed = agreed.record(ListenerNote.TOO_MUDDY) }
        agreed = agreed.record(ListenerNote.EXCELLENT)
        assertEquals(listOf(ListenerNote.TOO_MUDDY), agreed.consensus())
        assertFalse(agreed.isAccepted())
    }

    @Test
    fun `the panel applies what it agreed on, once, not once per listener`() {
        val start = aVoiceWithARoom()
        var panel = ListeningPanel()
        repeat(5) { panel = panel.record(ListenerNote.TOO_BRIGHT) }

        val byPanel = panel.applyTo(start)
        val byOneNote = ListenerNote.TOO_BRIGHT.applyTo(start)
        assertEquals(
            "Five listeners agreeing is one correction, not five",
            byOneNote.refinement.air,
            byPanel.refinement.air,
            1e-9,
        )
    }

    @Test
    fun `an empty panel accepts nothing and demands nothing`() {
        val empty = ListeningPanel()
        assertFalse("Nobody has listened yet, so nothing is accepted", empty.isAccepted())
        assertTrue(empty.consensus().isEmpty())
        assertEquals(aVoiceWithARoom(), empty.applyTo(aVoiceWithARoom()))
    }

    /**
     * Speech with gaps, which is what a noise floor is measured in.
     *
     * A continuous tone has no quiet passage, so the quietest half-second still contains the
     * whole signal and the measured "floor" is the voice itself. Any recording used to test noise
     * handling has to have silence in it, exactly as real speech does.
     */
    private fun speechWithGaps(
        seconds: Double = 6.0,
        amplitude: Double = 0.4,
        hissAmplitude: Double = 0.0,
        seed: Long = 11L,
    ): AudioBuffer {
        val frames = (seconds * rate).toInt()
        val samples = FloatArray(frames)
        val random = java.util.Random(seed)
        val partials = listOf(120.0 to 0.40, 240.0 to 0.26, 700.0 to 0.16, 1_600.0 to 0.10, 3_200.0 to 0.08)

        for (i in 0 until frames) {
            // 700 ms of speech, 500 ms of room, repeating.
            val speaking = (i % (1.2 * rate).toInt()) < (0.7 * rate).toInt()
            if (speaking) {
                var value = 0.0
                for ((frequency, level) in partials) {
                    value += amplitude * level * kotlin.math.sin(2.0 * Math.PI * frequency * i / rate)
                }
                samples[i] = value.toFloat()
            }
            if (hissAmplitude > 0.0) samples[i] += (random.nextGaussian() * hissAmplitude).toFloat()
        }
        return AudioBuffer.mono(samples, rate)
    }

    // --- Adaptive enhancement ----------------------------------------------------------------

    @Test
    fun `a noisy recording gets noise reduction and a clean one does not`() {
        val noisy = VoiceAnalysis.of(speechWithGaps(amplitude = 0.25, hissAmplitude = 0.02))
        val clean = VoiceAnalysis.of(speechWithGaps(amplitude = 0.5))

        assertTrue("The noisy take should read as noisy", noisy.signalToNoiseDb < clean.signalToNoiseDb)
        assertNotNull("A noisy recording needs cleaning", VoiceAdvisor.enhance(noisy).cleanup.noiseReduction)
        assertNull(
            "Spectral subtraction always costs something; on a clean recording the honest " +
                "amount is none",
            VoiceAdvisor.enhance(clean).cleanup.noiseReduction,
        )
    }

    @Test
    fun `a dull recording is given presence and a forward one is not`() {
        val dull = VoiceAnalysis.of(voice(3.0, brightBoost = 0.15))
        val forward = VoiceAnalysis.of(voice(3.0, brightBoost = 4.0))

        assertTrue(dull.presenceTiltDb < forward.presenceTiltDb)
        assertTrue(
            "A dull recording should be brought forward more than a forward one",
            VoiceAdvisor.enhance(dull).refinement.presence >
                VoiceAdvisor.enhance(forward).refinement.presence,
        )
    }

    @Test
    fun `a sibilant recording gets a de-esser and a dark one does not`() {
        val sibilant = VoiceAnalysis.of(voice(3.0, brightBoost = 6.0, hissAmplitude = 0.01))
        val dark = VoiceAnalysis.of(voice(3.0, brightBoost = 0.05))

        assertTrue(sibilant.sibilanceTiltDb > dark.sibilanceTiltDb)
        assertNotNull(VoiceAdvisor.enhance(sibilant).dynamics.deEsser)
    }

    @Test
    fun `a thin recording is given body and a thick one is not`() {
        val thin = VoiceAnalysis.of(voice(3.0, lowBoost = 0.1))
        val thick = VoiceAnalysis.of(voice(3.0, lowBoost = 3.0))

        assertTrue(thin.lowTiltDb < thick.lowTiltDb)
        assertTrue(VoiceAdvisor.enhance(thin).refinement.body > VoiceAdvisor.enhance(thick).refinement.body)
        assertTrue(
            "A thick recording needs more taken out from underneath",
            VoiceAdvisor.enhance(thick).cleanup.highPassHz!! >= VoiceAdvisor.enhance(thin).cleanup.highPassHz!!,
        )
    }

    @Test
    fun `Enhance Voice adds no room and Studio Voice does`() {
        val analysis = VoiceAnalysis.of(voice(3.0))
        assertTrue(
            "A room nobody asked for is the change most likely to be wrong",
            VoiceAdvisor.enhance(analysis).ambience.isBypassed,
        )
        assertFalse(VoiceAdvisor.studio(analysis).ambience.isBypassed)
        assertTrue(
            VoiceAdvisor.studio(analysis).refinement.air > VoiceAdvisor.enhance(analysis).refinement.air,
        )
    }

    @Test
    fun `both one-taps improve a quiet recording without clipping it`() {
        val quiet = voice(4.0, amplitude = 0.06)
        val analysis = VoiceAnalysis.of(quiet)

        for ((name, settings) in listOf(
            "Enhance Voice" to VoiceAdvisor.enhance(analysis),
            "Studio Voice" to VoiceAdvisor.studio(analysis),
        )) {
            val rendered = VoiceStudio(settings).render(quiet)
            assertFalse("$name clipped", rendered.report.clipped)
            assertTrue(
                "$name left a quiet recording quiet: ${rendered.report.inputLufs} → " +
                    "${rendered.report.outputLufs}",
                rendered.report.outputLufs > rendered.report.inputLufs + 3.0,
            )
            for (sample in rendered.audio.channels[0]) assertTrue("$name produced $sample", sample.isFinite())
        }
    }

    // --- Voice Match -------------------------------------------------------------------------

    @Test
    fun `Voice Match moves towards a brighter reference without overshooting it`() {
        val source = VoiceAnalysis.of(voice(3.0, brightBoost = 0.3))
        val reference = VoiceAnalysis.of(voice(3.0, brightBoost = 4.0))

        val matched = VoiceAdvisor.matchTo(source, reference)
        val unmatched = VoiceAdvisor.enhance(source)

        assertTrue(
            "Matching a brighter reference should add presence",
            matched.refinement.presence > unmatched.refinement.presence,
        )
        // Halved on purpose: the reference's microphone and room are not recoverable, and
        // overshooting a target that was never reachable sounds worse than sitting short of it.
        assertTrue(matched.refinement.presence <= 1.0)
        assertTrue(matched.refinement.air <= 1.0)
    }

    @Test
    fun `Voice Match moves towards a darker reference too`() {
        val source = VoiceAnalysis.of(voice(3.0, brightBoost = 4.0))
        val reference = VoiceAnalysis.of(voice(3.0, brightBoost = 0.3))

        assertTrue(
            VoiceAdvisor.matchTo(source, reference).refinement.presence <
                VoiceAdvisor.enhance(source).refinement.presence,
        )
    }

    @Test
    fun `Voice Match compresses harder when the reference moves less`() {
        // A reference with a narrow loudness range was compressed harder than the source.
        // Long enough for the loudness range's three-second windows to see both levels, and
        // with the quiet passages well above the −20 LU relative gate so they are not simply
        // excluded from the measurement.
        val even = voice(14.0, amplitude = 0.4)
        val moving = AudioBuffer.mono(
            FloatArray((14 * rate)) { i ->
                val loud = (i / (4 * rate)) % 2 == 0
                val envelope = if (loud) 0.55 else 0.12
                (envelope * kotlin.math.sin(2.0 * Math.PI * 180.0 * i / rate)).toFloat()
            },
            rate,
        )

        val source = VoiceAnalysis.of(moving)
        val reference = VoiceAnalysis.of(even)
        assertTrue("The moving take should read as wider", source.loudnessRangeLu > reference.loudnessRangeLu)

        val matched = VoiceAdvisor.matchTo(source, reference)
        assertTrue(
            "Matching an evener reference should compress more",
            matched.dynamics.compressor!!.ratio > 2.2,
        )
    }

    @Test
    fun `Voice Match says what it will do and admits what it cannot`() {
        val source = VoiceAnalysis.of(voice(3.0, brightBoost = 0.3, amplitude = 0.1))
        val reference = VoiceAnalysis.of(voice(3.0, brightBoost = 4.0, amplitude = 0.5))

        val explanation = VoiceAdvisor.matchExplanation(source, reference)
        assertTrue("The match explained nothing", explanation.size > 1)
        assertTrue(
            "A feature called match must say what it cannot do, at the moment of use",
            explanation.last().contains("cannot be copied"),
        )
    }

    @Test
    fun `matching a recording to itself asks for almost nothing`() {
        val analysis = VoiceAnalysis.of(voice(3.0))
        val matched = VoiceAdvisor.matchTo(analysis, analysis)
        val plain = VoiceAdvisor.enhance(analysis)

        assertEquals(plain.refinement.presence, matched.refinement.presence, 0.02)
        assertEquals(plain.refinement.air, matched.refinement.air, 0.02)
        assertEquals(plain.refinement.body, matched.refinement.body, 0.02)
    }

    // --- Outcome names ----------------------------------------------------------------------

    @Test
    fun `the presets a user sees are named for outcomes, grouped by what they are for`() {
        val expected = listOf(
            "Clear Speech", "Warm Voice", "Rich Narration",
            "Studio", "Broadcast", "Podcast", "Lecture",
            "Prestige Recitation",
            "Grand Space", "Immersive",
        )
        assertEquals(expected, VoiceOutcome.cardOrder.map { it.displayName })
        assertEquals("Ten. One that is right beats a list nobody can tell apart.", 10, VoiceOutcome.entries.size)

        for (outcome in VoiceOutcome.entries) {
            assertTrue("${outcome.displayName} has no stated purpose", outcome.purpose.length > 15)
            // Named for the job, not the acoustics: nobody picks a preset by reverberation time.
            assertFalse(
                "${outcome.displayName} is named after a building",
                listOf("Mosque", "Hall", "Booth", "Auditorium", "Room").any { outcome.displayName.contains(it) },
            )
        }

        // Every group is used, and the cards arrive in group order so a person scans to their
        // situation and reads three names rather than reading ten and deciding.
        assertEquals(
            VoiceOutcomeGroup.entries.toSet(),
            VoiceOutcome.entries.map { it.group }.toSet(),
        )
        assertEquals(
            VoiceOutcome.cardOrder.map { it.group },
            VoiceOutcome.cardOrder.map { it.group }.sortedBy { it.ordinal },
        )
    }

    @Test
    fun `the acoustic space appears only as an Advanced Mode disclosure`() {
        // One naming system on screen. The room is transparency for a professional who wants it,
        // not a second thing for everyone else to choose between.
        for (outcome in VoiceOutcome.entries) {
            assertTrue(
                "${outcome.displayName} should disclose what it is based on",
                outcome.advancedDetail.startsWith("Based on: "),
            )
            assertTrue(outcome.advancedDetail.contains(outcome.basedOn.displayName))
        }

        // Two outcomes share a name with the space that produces them, which is fine: the space
        // name is never on screen unless Advanced Mode is on. What matters is that the visible
        // list contains no name a user would have to interpret as an acoustic term.
        val visible = VoiceOutcome.cardOrder.map { it.displayName }
        assertFalse(
            "A room name reached the card list",
            visible.any { name -> listOf("Mosque", "Booth", "Auditorium", "Hall", "Room").any(name::contains) },
        )
    }

    @Test
    fun `each outcome arrives at its own character position`() {
        assertEquals(VoiceCharacter.NATURAL, VoiceOutcome.CLEAR_SPEECH.character, 0.0)
        assertEquals(VoiceCharacter.IMMERSIVE, VoiceOutcome.IMMERSIVE.character, 0.0)
        // Rich Narration used to be asserted as the higher intensity of the two, which encoded an
        // assumption that turned out to be wrong: its richness belongs to the *voice*, not to a
        // room. Audiobooks are recorded close and dry, and the preset sat in a 2.2-second hall
        // until a distinctness test made that visible. What must be true is the thing the name
        // promises — more weight than Warm Voice, and not more room.
        val narration = VoiceOutcome.RICH_NARRATION.settings
        val warm = VoiceOutcome.WARM_VOICE.settings
        assertTrue(
            "Rich Narration must carry more body than Warm Voice",
            narration.refinement.richness + narration.refinement.body >
                warm.refinement.richness + warm.refinement.body,
        )
        assertTrue(
            "Rich Narration must not be roomier than Warm Voice",
            narration.effectiveAmbience.wetDryMix <= warm.effectiveAmbience.wetDryMix + 1e-9,
        )

        // And the character reaches the audio: the same space at two positions is two sounds.
        val source = voice(1.5)
        val natural = VoiceStudio(VoiceOutcome.GRAND_SPACE.settings.copy(character = VoiceCharacter(VoiceCharacter.NATURAL)))
            .render(source).audio
        val immersive = VoiceStudio(VoiceOutcome.GRAND_SPACE.settings.copy(character = VoiceCharacter(VoiceCharacter.IMMERSIVE)))
            .render(source).audio

        var difference = 0.0
        for (i in 0 until source.frameCount) {
            difference += kotlin.math.abs(immersive.channels[0][i] - natural.channels[0][i]).toDouble()
        }
        assertTrue("The character control did not reach the audio", difference / source.frameCount > 1e-4)
    }

    @Test
    fun `every outcome renders finite, unclipped audio that is not the original`() {
        val source = voice(2.0)
        for (outcome in VoiceOutcome.entries) {
            val rendered = outcome.studio().render(source)
            assertFalse("${outcome.displayName} clipped", rendered.report.clipped)
            for (sample in rendered.audio.channels[0]) {
                assertTrue("${outcome.displayName} produced $sample", sample.isFinite())
            }
            var difference = 0.0
            for (i in 0 until source.frameCount) {
                difference += kotlin.math.abs(rendered.audio.channels[0][i] - source.channels[0][i]).toDouble()
            }
            assertTrue("${outcome.displayName} changed nothing", difference / source.frameCount > 1e-5)
        }
    }

    @Test
    fun `only Clear Speech is roomless, and Immersive is the largest`() {
        assertTrue(VoiceOutcome.CLEAR_SPEECH.settings.ambience.isBypassed)
        val roomed = VoiceOutcome.entries.filterNot { it.settings.ambience.isBypassed }
        val largest = roomed.maxBy { it.settings.effectiveAmbience.wetDryMix }
        assertEquals(VoiceOutcome.IMMERSIVE, largest)
    }
}

/**
 * The second layer, the Recitation Studio, and the one-tap recommendation.
 *
 * Layer two exists for someone who has decided they want a particular place. The test that
 * matters is that choosing a room changes only the room: a person who moves to a larger hall has
 * not asked for a different voice, and an environment that quietly re-tuned the tone would make
 * the two layers indistinguishable — which is the confusion the two layers exist to avoid.
 */
class VoiceSpacesTest {

    private val rate = 48_000

    private fun voice(seconds: Double = 2.0): AudioBuffer {
        val frames = (seconds * rate).toInt()
        val samples = FloatArray(frames)
        for ((frequency, level) in listOf(140.0 to 0.35, 280.0 to 0.22, 900.0 to 0.14, 3_000.0 to 0.08)) {
            for (i in 0 until frames) {
                samples[i] += (level * kotlin.math.sin(2.0 * Math.PI * frequency * i / rate)).toFloat()
            }
        }
        return AudioBuffer.mono(samples, rate)
    }

    @Test
    fun `choosing a room changes the room and nothing else`() {
        val outcome = VoiceOutcome.RICH_NARRATION.settings
        val inAHall = AcousticSpace.LARGE_HALL.applyTo(outcome)

        assertEquals("The voice must not change with the room", outcome.cleanup, inAHall.cleanup)
        assertEquals(outcome.dynamics, inAHall.dynamics)
        assertEquals(outcome.refinement, inAHall.refinement)
        assertEquals(outcome.loudness, inAHall.loudness)
        assertNotEquals(outcome.ambience, inAHall.ambience)
    }

    @Test
    fun `every acoustic space is a real, distinct room`() {
        val source = voice()
        val mixes = AcousticSpace.entries.map { it.applyTo(VoiceOutcome.STUDIO.settings).ambience.wetDryMix }
        assertEquals("Two spaces are identical", mixes.size, mixes.toSet().size)

        for (space in AcousticSpace.entries) {
            assertTrue("${space.displayName} has no summary", space.summary.length > 20)
            val rendered = VoiceStudio(space.applyTo(VoiceOutcome.STUDIO.settings)).render(source)
            assertFalse("${space.displayName} clipped", rendered.report.clipped)
            for (sample in rendered.audio.channels[0]) {
                assertTrue("${space.displayName} produced $sample", sample.isFinite())
            }
        }

        // Bigger rooms last longer, in the order a person would expect.
        assertTrue(
            AcousticSpace.GRAND_MOSQUE.applyTo(VoiceOutcome.STUDIO.settings).ambience.decaySeconds >
                AcousticSpace.SMALL_MOSQUE.applyTo(VoiceOutcome.STUDIO.settings).ambience.decaySeconds,
        )
        assertTrue(
            AcousticSpace.LARGE_HALL.applyTo(VoiceOutcome.STUDIO.settings).ambience.decaySeconds >
                AcousticSpace.SMALL_HALL.applyTo(VoiceOutcome.STUDIO.settings).ambience.decaySeconds,
        )
        assertTrue(
            AcousticSpace.VOCAL_BOOTH.applyTo(VoiceOutcome.STUDIO.settings).ambience.decaySeconds <
                AcousticSpace.SMALL_HALL.applyTo(VoiceOutcome.STUDIO.settings).ambience.decaySeconds,
        )
    }

    @Test
    fun `the Recitation Studio keeps the dynamics recitation lives on`() {
        // Flattening the delivery is the one thing a reciter will never forgive, so every profile
        // has to inherit the light-compression treatment rather than a generic chain.
        for (profile in RecitationProfile.entries) {
            val compressor = profile.settings.dynamics.compressor
            assertNotNull("${profile.displayName} has no dynamics at all", compressor)
            assertTrue(
                "${profile.displayName} compresses at ${compressor!!.ratio}:1 — too hard for recitation",
                compressor.ratio <= 2.5,
            )
            assertTrue("${profile.displayName} has no summary", profile.summary.length > 20)
        }
    }

    @Test
    fun `every recitation profile is distinct, finite and unclipped`() {
        val source = voice(3.0)
        val decays = RecitationProfile.entries.map { it.settings.ambience.decaySeconds }
        assertEquals("Two profiles are the same room", decays.size, decays.toSet().size)

        for (profile in RecitationProfile.entries) {
            val rendered = profile.studio().render(source)
            assertFalse("${profile.displayName} clipped", rendered.report.clipped)
            for (sample in rendered.audio.channels[0]) {
                assertTrue("${profile.displayName} produced $sample", sample.isFinite())
            }
        }

        // Natural really is the smallest, and Immersive the largest.
        assertEquals(RecitationProfile.NATURAL, RecitationProfile.entries.minBy { it.settings.ambience.decaySeconds })
        assertEquals(RecitationProfile.IMMERSIVE, RecitationProfile.entries.maxBy { it.settings.ambience.decaySeconds })
    }

    @Test
    fun `the inspired profiles say what they are and are not`() {
        // The people who care most about these recordings are exactly the people a name implying
        // more than it can do would mislead.
        assertTrue(RecitationProfile.MAKKAH_INSPIRED.displayName.contains("Inspired"))
        assertTrue(RecitationProfile.MADINAH_INSPIRED.displayName.contains("Inspired"))

        val disclosure = RecitationProfile.DISCLOSURE
        assertTrue("The disclosure must deny reproduction", disclosure.contains("do not reproduce"))
        assertTrue("The disclosure must deny affiliation", disclosure.contains("not affiliated"))
    }

    @Test
    fun `intensity reads as a percentage, because more and less need no explanation`() {
        assertEquals(0, VoiceCharacter(VoiceCharacter.NATURAL).percent)
        assertEquals(50, VoiceCharacter(VoiceCharacter.RICH).percent)
        assertEquals(100, VoiceCharacter(VoiceCharacter.IMMERSIVE).percent)
        assertEquals(37, VoiceCharacter(0.37).percent)
    }

    @Test
    fun `one tap recommends something defensible and says why`() {
        fun analysisOf(buffer: AudioBuffer) = VoiceAnalysis.of(buffer)

        // Noisy: the safe answer, and no room.
        val noisy = AudioBuffer.mono(
            FloatArray(6 * rate).also { samples ->
                val random = java.util.Random(3)
                for (i in samples.indices) {
                    val speaking = (i % (1.2 * rate).toInt()) < (0.7 * rate).toInt()
                    if (speaking) samples[i] = (0.14 * kotlin.math.sin(2.0 * Math.PI * 160.0 * i / rate)).toFloat()
                    samples[i] += (random.nextGaussian() * 0.04).toFloat()
                }
            },
            rate,
        )
        // The property that matters is what the user gets, not which rule fired: a compromised
        // recording gets the plain answer and no room. Pinning the exact intensity would test the
        // rule ordering rather than the recommendation.
        val forNoisy = AutoStudio.recommend(analysisOf(noisy))
        assertEquals(VoiceOutcome.CLEAR_SPEECH, forNoisy.outcome)
        assertTrue("A compromised recording must not be given a room", forNoisy.settings.ambience.isBypassed)
        assertTrue(forNoisy.intensity <= VoiceCharacter.REFINED)

        // Every recommendation explains itself in a sentence a person can disagree with.
        for (buffer in listOf(noisy, voice(4.0))) {
            val recommendation = AutoStudio.recommend(analysisOf(buffer))
            assertTrue("A recommendation with no reason is a decision made for you", recommendation.reason.length > 30)
            assertTrue(recommendation.intensity in 0.0..1.0)
            // And it renders.
            val rendered = VoiceStudio(recommendation.settings).render(voice(2.0))
            assertFalse(rendered.report.clipped)
        }
    }
}
