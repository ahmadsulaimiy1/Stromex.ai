package ai.sautiy.core.dsp

import ai.sautiy.core.audio.AudioBuffer
import ai.sautiy.core.record.RecordingAdvisor
import kotlin.math.PI
import kotlin.math.abs
import kotlin.math.sin
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertSame
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * The house style, and the machinery that makes it hold everywhere.
 *
 * The most valuable test in this file is [every_shipped_preset_is_inside_the_house_style]: it is
 * the one that turns "SAUTIY has a signature sound" from a claim into a property of the build. A
 * preset added later that breaks the rules fails here rather than shipping.
 */
class SignatureSoundTest {

    @Test
    fun `every shipped preset is inside the house style`() {
        val everything: List<Pair<String, VoiceStudioSettings>> =
            VoiceSpacePreset.entries.map { "acoustic ${it.displayName}" to it.settings } +
                VoiceOutcome.entries.map { "outcome ${it.displayName}" to it.settings } +
                RecitationProfile.entries.map { "recitation ${it.displayName}" to it.settings } +
                AcousticSpace.entries.map {
                    "space ${it.displayName}" to it.applyTo(VoiceOutcome.STUDIO.settings)
                }

        val broken = everything.mapNotNull { (name, settings) ->
            val violations = SignatureSound.verify(settings)
            if (violations.isEmpty()) null else name to violations
        }

        assertTrue(
            "These break the SAUTIY house style:\n" + broken.joinToString("\n") { (name, v) ->
                "  $name\n" + v.joinToString("\n") { "    ${it.rule} — ${it.heardAs}" }
            },
            broken.isEmpty(),
        )
    }

    @Test
    fun `the house style holds at every intensity, not just the one it was written at`() {
        // A signature that only survives at Refined is not a signature. Turning Voice Space up is
        // the single most common thing a user will do, and it multiplies the room's level.
        val stops = listOf(
            VoiceCharacter.NATURAL, VoiceCharacter.REFINED, VoiceCharacter.RICH,
            VoiceCharacter.GRAND, VoiceCharacter.IMMERSIVE,
        )
        val broken = mutableListOf<String>()
        for (outcome in VoiceOutcome.entries) {
            for (stop in stops) {
                val at = outcome.settings.copy(character = VoiceCharacter(stop))
                for (violation in SignatureSound.verify(at)) {
                    broken += "${outcome.displayName} at ${(stop * 100).toInt()}%: ${violation.rule}"
                }
            }
        }
        assertTrue(broken.joinToString("\n"), broken.isEmpty())
    }

    @Test
    fun `a hand-edited voice outside the rules is brought back inside them`() {
        // Somebody dragging every slider to the end is the case this exists for. What comes out
        // must be inside the house style, and must still be recognisably what they were reaching
        // for — large and wet, just not a different app's sound.
        val extreme = VoiceOutcome.IMMERSIVE.settings.copy(
            ambience = VoiceOutcome.IMMERSIVE.settings.ambience.copy(
                wetDryMix = 0.95,
                preDelayMs = 0.0,
                speechPriority = 0.0,
                brightness = 1.0,
            ),
            refinement = VoiceRefinement(presence = 1.0, air = 1.0, warmth = -1.0),
            character = VoiceCharacter(VoiceCharacter.IMMERSIVE),
            loudness = LoudnessStage(target = null, limiterCeilingDb = null),
        )

        assertFalse("this fixture is supposed to break the rules", SignatureSound.holds(extreme))

        val fixed = SignatureSound.applyTo(extreme)
        assertTrue(
            SignatureSound.verify(fixed).joinToString("\n") { it.rule },
            SignatureSound.holds(fixed),
        )
        // Still a large space: clamping is not the same as removing.
        assertFalse("clamping must not delete the room", fixed.effectiveAmbience.isBypassed)
        assertTrue(
            "a room clamped to the house maximum should still be a big one",
            fixed.effectiveAmbience.wetDryMix > 0.25,
        )
    }

    @Test
    fun `a setting already inside the rules is not touched`() {
        // Idempotence matters because `applyTo` runs on every save. A function that drifts a
        // sound a little each time it is written would slowly change work the user finished.
        for (outcome in VoiceOutcome.entries) {
            val once = SignatureSound.applyTo(outcome.settings)
            val twice = SignatureSound.applyTo(once)
            assertEquals("${outcome.displayName} is not stable under the house style", once, twice)
        }
    }

    @Test
    fun `every rule says what it sounds like`() {
        // A rule whose consequence cannot be described to a listener was invented for the code.
        val broken = VoiceOutcome.IMMERSIVE.settings.copy(
            ambience = VoiceOutcome.IMMERSIVE.settings.ambience.copy(preDelayMs = 0.0, wetDryMix = 0.99),
            refinement = VoiceRefinement(presence = 1.0, air = 1.0),
            loudness = LoudnessStage(limiterCeilingDb = null),
        )
        val violations = SignatureSound.verify(broken)
        assertTrue("expected several violations", violations.size >= 4)
        for (violation in violations) {
            assertTrue("a rule with no rule text: $violation", violation.rule.isNotBlank())
            assertTrue("a rule with no audible consequence: ${violation.rule}", violation.heardAs.length > 30)
        }
    }

    @Test
    fun `a small room may answer soon and a large one may not`() {
        // The rule is the relationship, not a single number. A vocal booth answering in 6 ms is
        // what a vocal booth *is*; forcing it to 12 would make it a different room. A 3.6-second
        // hall answering in 6 ms is a voice smeared with a hall.
        val booth = AmbienceSettings(decaySeconds = 0.3, preDelayMs = 6.0, wetDryMix = 0.07)
        val hall = AmbienceSettings(decaySeconds = 3.6, preDelayMs = 6.0, wetDryMix = 0.2)

        assertTrue(
            "a booth must be allowed to be close",
            booth.preDelayMs >= SignatureSound.minPreDelayMs(booth.decaySeconds),
        )
        assertTrue(
            "a hall must not be allowed to be that close",
            hall.preDelayMs < SignatureSound.minPreDelayMs(hall.decaySeconds),
        )
        // Monotonic: a longer tail can never be allowed to answer sooner.
        var previous = 0.0
        var decay = 0.1
        while (decay <= 8.0) {
            val soonest = SignatureSound.minPreDelayMs(decay)
            assertTrue("the floor fell as the room grew, at $decay s", soonest >= previous - 1e-12)
            previous = soonest
            decay += 0.1
        }
    }

    @Test
    fun `turning Voice Space to the top cannot drown the voice`() {
        // The defect this caught: an already-wet preset at 100% reached 73% room against 65%
        // ducking. Somebody asking for a bigger space did not ask to be buried in one, and the
        // control has to be safe to use at its maximum or its maximum is a trap.
        for (outcome in VoiceOutcome.entries) {
            val loudest = outcome.settings.copy(character = VoiceCharacter(VoiceCharacter.IMMERSIVE))
            val room = loudest.effectiveAmbience
            if (room.isBypassed) continue
            assertTrue(
                "${outcome.displayName} reaches ${room.wetDryMix} of room",
                room.wetDryMix <= SignatureSound.MAX_WET_DRY + 1e-9,
            )
            assertTrue(
                "${outcome.displayName}: ${room.wetDryMix} of room with only " +
                    "${room.speechPriority} of protection",
                room.speechPriority >= SignatureSound.requiredProtection(room.wetDryMix) - 1e-9,
            )
        }
    }

    @Test
    fun `every decibel of room buys a matching amount of standing back`() {
        // The central law, asserted directly: the relationship must be monotonic, or a preset
        // could add room and require less protection than a quieter one.
        var previous = -1.0
        var mix = 0.0
        while (mix <= 1.0) {
            val required = SignatureSound.requiredProtection(mix)
            assertTrue("protection fell as room rose, at $mix", required >= previous - 1e-12)
            assertTrue(required in 0.0..0.92)
            previous = required
            mix += 0.01
        }
        assertEquals("a nearly-dry room needs no protection", 0.0, SignatureSound.requiredProtection(0.1), 1e-9)
        assertTrue(
            "the loudest allowed room must duck by about half",
            SignatureSound.requiredProtection(SignatureSound.MAX_WET_DRY) > 0.45,
        )
    }

    @Test
    fun `the voice is always in front of the room`() {
        // The single most recognisable thing in the house style, asserted directly rather than
        // only through the rule table.
        for (space in AcousticSpace.entries) {
            val room = space.applyTo(VoiceOutcome.STUDIO.settings).effectiveAmbience
            assertTrue(
                "${space.displayName} arrives at ${room.preDelayMs} ms with a " +
                    "${room.decaySeconds} s tail",
                room.preDelayMs >= SignatureSound.minPreDelayMs(room.decaySeconds),
            )
            assertTrue(
                "${space.displayName} does not stand back (${room.speechPriority})",
                room.speechPriority >= SignatureSound.MIN_SPEECH_PRIORITY,
            )
        }
    }
}

/** Saving a sound, recalling it, and the things that must survive an update. */
class VoiceDnaTest {

    private fun dna(name: String, settings: VoiceStudioSettings = VoiceOutcome.PODCAST.settings) =
        VoiceDna.of("id-$name", name, settings, createdAtEpochMs = 1_000L, basedOn = "Podcast")

    @Test
    fun `a saved sound restores the complete instrument, not a preset reference`() {
        // The point of Voice DNA: every stage comes back, including the hand edits that were the
        // reason for saving in the first place.
        val hand = VoiceOutcome.PRESTIGE_RECITATION.settings.copy(
            refinement = VoiceRefinement(warmth = 0.31, richness = 0.22, clarity = 0.17),
            character = VoiceCharacter(0.62),
            outputGainDb = -1.5,
        )
        val saved = dna("My Qur'an Voice", hand)
        val text = VoiceDnaLibrary.encode(VoiceDnaLibrary().save(saved))
        val restored = VoiceDnaLibrary.decode(text).find(saved.id)

        assertNotNull(restored)
        val settings = restored!!.settings
        assertEquals(0.31, settings.refinement.warmth, 1e-9)
        assertEquals(0.22, settings.refinement.richness, 1e-9)
        assertEquals(0.62, settings.character.position, 1e-9)
        assertEquals(-1.5, settings.outputGainDb, 1e-9)
        assertEquals(hand.ambience, settings.ambience)
        assertEquals(hand.dynamics, settings.dynamics)
        assertEquals(hand.cleanup, settings.cleanup)
        assertEquals(hand.loudness.target, settings.loudness.target)
    }

    @Test
    fun `saving puts the sound inside the house style`() {
        val outside = VoiceOutcome.IMMERSIVE.settings.copy(
            refinement = VoiceRefinement(presence = 1.0, air = 1.0),
        )
        val saved = dna("Wild", outside)
        assertTrue(
            SignatureSound.verify(saved.settings).joinToString("\n") { it.rule },
            SignatureSound.holds(saved.settings),
        )
    }

    @Test
    fun `a file written by an older version still loads`() {
        // Simulates an update adding a field: the stored JSON lacks it. Losing someone's saved
        // Qur'an voice on an app update is unforgivable and entirely preventable.
        val partial = """{"entries":[{"id":"a","name":"My Lecture Voice","settings":{},"createdAtEpochMs":7}]}"""
        val library = VoiceDnaLibrary.decode(partial)
        assertEquals(1, library.entries.size)
        assertEquals("My Lecture Voice", library.entries[0].name)
        assertEquals(7L, library.entries[0].createdAtEpochMs)
    }

    @Test
    fun `a corrupt file loses the presets and not the app`() {
        assertEquals(VoiceDnaLibrary(), VoiceDnaLibrary.decode("{ this is not json"))
        assertEquals(VoiceDnaLibrary(), VoiceDnaLibrary.decode(""))
    }

    @Test
    fun `saving over an existing sound replaces it rather than duplicating it`() {
        val first = dna("My Podcast Voice")
        val edited = first.copy(settings = VoiceOutcome.BROADCAST.settings)
        val library = VoiceDnaLibrary().save(first).save(edited)
        assertEquals(1, library.entries.size)
        assertEquals(VoiceOutcome.BROADCAST.settings.ambience, library.entries[0].settings.ambience)
    }

    @Test
    fun `the list orders itself by what the user reaches for`() {
        var library = VoiceDnaLibrary()
            .save(dna("Rarely").copy(createdAtEpochMs = 5_000))
            .save(dna("Often").copy(createdAtEpochMs = 1_000))
        repeat(4) { library = library.recall("id-Often")!!.first }

        assertEquals(listOf("Often", "Rarely"), library.ordered.map { it.name })
    }

    @Test
    fun `two lecture series can both be saved`() {
        // Refusing a duplicate name makes the user solve a problem the app invented.
        val existing = listOf(dna("My Lecture Voice"))
        assertEquals("My Lecture Voice 2", VoiceDna.uniqueName("My Lecture Voice", existing))
        assertEquals("My Qur'an Voice", VoiceDna.uniqueName("My Qur'an Voice", existing))
        assertEquals("My Voice", VoiceDna.uniqueName("   ", emptyList()))
    }

    @Test
    fun `the summary describes the sound it is attached to and cannot disagree with it`() {
        val dry = dna("Dry", VoiceOutcome.CLEAR_SPEECH.settings)
        assertTrue(dry.summary, dry.summary.contains("no room"))

        val wet = dna("Wet", VoiceOutcome.GRAND_SPACE.settings)
        assertTrue(wet.summary, wet.summary.contains("Voice Space"))
        assertTrue(wet.summary, wet.summary.contains("Podcast")) // the basedOn provenance
    }

    @Test
    fun `a sound cannot be saved without a name`() {
        val threw = runCatching { dna("   ") }.isFailure
        assertTrue("a blank name should be refused at construction", threw)
    }

    @Test
    fun `the four suggested names are occasions, not settings`() {
        assertEquals(4, VoiceDna.suggestedNames.size)
        for (name in VoiceDna.suggestedNames) {
            assertTrue("$name should be possessive and human", name.startsWith("My "))
            assertFalse("$name names a setting", name.contains("%"))
        }
    }
}

/** Guidance before the take, and the promise that it stays quiet when nothing is wrong. */
class RecordingAdvisorTest {

    @Test
    fun `a good signal produces no advice at all`() {
        // If this ever fires on decent material it is a bug: advice that always appears is
        // wallpaper, and wallpaper is not read when it matters.
        val guidance = RecordingAdvisor.assess(peakDb = -8.0, rmsDb = -20.0, noiseFloorDb = -62.0)
        assertTrue("said: ${guidance.action}", guidance.isSilent)
        assertNull(guidance.action)
    }

    @Test
    fun `clipping is called out above everything else`() {
        val guidance = RecordingAdvisor.assess(peakDb = -0.1, rmsDb = -12.0, noiseFloorDb = -30.0)
        assertEquals(RecordingAdvisor.Weight.WARNING, guidance.weight)
        assertTrue(guidance.action!!, guidance.action!!.contains("back") || guidance.action!!.contains("softer"))
        // Noise is also wrong here, but only one thing is said.
        assertFalse(guidance.action!!.contains("fan"))
    }

    @Test
    fun `too far away is a warning and says what to do physically`() {
        val guidance = RecordingAdvisor.assess(peakDb = -30.0, rmsDb = -44.0, noiseFloorDb = -66.0)
        assertEquals(RecordingAdvisor.Weight.WARNING, guidance.weight)
        assertTrue(guidance.action!!, guidance.action!!.contains("closer"))
        // The advice is an action, not a setting.
        assertFalse(guidance.action!!.contains("dB"))
        assertFalse(guidance.action!!.contains("gain"))
    }

    @Test
    fun `a noisy room is a suggestion rather than a warning`() {
        val guidance = RecordingAdvisor.assess(peakDb = -10.0, rmsDb = -22.0, noiseFloorDb = -40.0)
        assertEquals(RecordingAdvisor.Weight.SUGGESTION, guidance.weight)
        assertTrue(guidance.action!!, guidance.action!!.contains("quieter"))
    }

    @Test
    fun `too close warns about plosives`() {
        val guidance = RecordingAdvisor.assess(peakDb = -1.5, rmsDb = -14.0, noiseFloorDb = -70.0)
        assertEquals(RecordingAdvisor.Weight.SUGGESTION, guidance.weight)
        assertTrue(guidance.because!!, guidance.because!!.contains("p and b"))
    }

    @Test
    fun `silence produces nothing rather than advice about silence`() {
        val guidance = RecordingAdvisor.assess(peakDb = -90.0, rmsDb = -95.0, noiseFloorDb = -96.0)
        assertTrue(guidance.isSilent)
        assertNull(guidance.suggestedIntensity)
    }

    @Test
    fun `a noisy room is never told to add a large space`() {
        // Ambience is a delay line fed by whatever the microphone heard. A big room on a noisy
        // recording gives the noise a tail, which is worse than either problem alone.
        val noisy = RecordingAdvisor.suggestedIntensity(noiseFloorDb = -36.0, snrDb = 14.0)
        val clean = RecordingAdvisor.suggestedIntensity(noiseFloorDb = -68.0, snrDb = 40.0)
        assertTrue("noisy got $noisy", noisy <= VoiceCharacter.NATURAL)
        assertTrue("clean got $clean", clean >= VoiceCharacter.RICH)
        assertTrue(clean > noisy)
    }

    @Test
    fun `the level gauge puts the ideal level in the middle`() {
        assertEquals(0.5, RecordingAdvisor.levelPosition(RecordingAdvisor.IDEAL_RMS_DB), 0.02)
        assertEquals(0.0, RecordingAdvisor.levelPosition(-60.0), 1e-9)
        assertEquals(1.0, RecordingAdvisor.levelPosition(0.0), 1e-9)
        // Monotonic, or the arc jumps backwards while somebody speaks.
        var previous = -1.0
        var db = -60.0
        while (db <= 0.0) {
            val position = RecordingAdvisor.levelPosition(db)
            assertTrue("gauge went backwards at $db dB", position >= previous - 1e-12)
            previous = position
            db += 0.5
        }
    }
}

/** Restraint: the promise that a good recording comes out sounding like itself. */
class AdaptiveEnhancementTest {

    /** A clean, close, well-levelled voice: two formants, gaps between phrases, no noise. */
    private fun cleanSpeech(seconds: Double = 4.0, rate: Int = 48_000): AudioBuffer {
        val frames = (seconds * rate).toInt()
        val samples = FloatArray(frames)
        for (i in 0 until frames) {
            val t = i.toDouble() / rate
            // 500 ms of speech, 250 ms of silence, so the noise floor is measured on real gaps.
            val phase = (t * 1000).toInt() % 750
            if (phase >= 500) continue
            val envelope = 0.5 * (1 - kotlin.math.cos(2 * PI * (phase / 500.0)))
            samples[i] = (
                0.20 * sin(2 * PI * 145.0 * t) +
                    0.11 * sin(2 * PI * 620.0 * t) +
                    0.05 * sin(2 * PI * 2_400.0 * t) +
                    0.015 * sin(2 * PI * 6_500.0 * t)
                ).toFloat() * envelope.toFloat()
        }
        return AudioBuffer(arrayOf(samples), rate)
    }

    @Test
    fun `a clean recording is left almost exactly as it was`() {
        val clean = cleanSpeech()
        val analysis = VoiceAnalysis.of(clean)
        val restraint = Restraint.of(analysis)

        assertTrue(
            "clean speech was judged to need ${restraint.percent}% of work: ${restraint.summary}",
            restraint.isTransparent,
        )

        val settings = VoiceAdvisor.enhance(analysis)
        assertNull("a clean recording must not be compressed", settings.dynamics.compressor)
        assertNull("a clean recording must not be de-essed", settings.dynamics.deEsser)
        assertNull("a clean recording must not be noise-reduced", settings.cleanup.noiseReduction)
        assertTrue("a clean recording must not be tone-shaped", settings.refinement.isNeutral)
        assertTrue("a clean recording must not be given a room", settings.ambience.isBypassed)
    }

    @Test
    fun `restraint on a clean recording is audibly restraint`() {
        // The claim is not "few stages are enabled" but "it sounds like itself". Measured as
        // band energy before and after, which is the closest a machine can get to that sentence.
        val clean = cleanSpeech()
        val settings = VoiceAdvisor.enhance(VoiceAnalysis.of(clean))
        val processed = VoiceStudio(settings.copy(loudness = LoudnessStage(target = null, limiterCeilingDb = -1.0)))
            .render(clean).audio

        for ((low, high) in listOf(200.0 to 800.0, 800.0 to 3_000.0, 3_000.0 to 9_000.0)) {
            val before = bandDb(clean, low, high)
            val after = bandDb(processed, low, high)
            assertTrue(
                "the $low–$high Hz band moved ${"%.2f".format(after - before)} dB, which is audible",
                abs(after - before) < 1.0,
            )
        }
    }

    @Test
    fun `a recording that needs work gets it`() {
        // The other half of the claim. Restraint must not become inertia.
        val noisy = VoiceAnalysis(
            integratedLufs = -34.0,
            truePeakDb = -12.0,
            loudnessRangeLu = 15.0,
            noiseFloorDb = -46.0,
            lowTiltDb = -14.0,
            presenceTiltDb = -24.0,
            sibilanceTiltDb = -6.0,
        )
        val restraint = Restraint.of(noisy)
        assertFalse("a bad recording should not be left alone", restraint.isTransparent)
        assertTrue("expected substantial work, got ${restraint.percent}%", restraint.strength > 0.5)
        assertNotNull("the panel should be able to name the main problem", restraint.principal)

        val settings = VoiceAdvisor.enhance(noisy)
        assertNotNull(settings.dynamics.compressor)
        assertNotNull(settings.cleanup.noiseReduction)
        assertNotNull(settings.dynamics.deEsser)
        assertTrue(settings.refinement.presence > 0.1)
    }

    @Test
    fun `four small imperfections are not one large problem`() {
        // A recording slightly short of ideal in several ways must not be heavily processed. This
        // is the arithmetic reason a mean is used rather than a sum, asserted rather than assumed.
        val slightlyOff = VoiceAnalysis(
            integratedLufs = -27.0,
            truePeakDb = -9.0,
            loudnessRangeLu = 10.0,
            noiseFloorDb = -52.0,
            lowTiltDb = -10.0,
            presenceTiltDb = -15.5,
            sibilanceTiltDb = -12.0,
        )
        val strength = Restraint.of(slightlyOff).strength
        assertTrue("four small faults produced $strength of work", strength < 0.35)
    }

    @Test
    fun `strength never leaves its range and the summary always says something`() {
        val extremes = listOf(
            VoiceAnalysis(-70.0, -30.0, 40.0, -20.0, 6.0, -40.0, 10.0),
            VoiceAnalysis(-8.0, -0.2, 0.0, -100.0, -30.0, -2.0, -40.0),
        )
        for (analysis in extremes) {
            val restraint = Restraint.of(analysis)
            assertTrue(restraint.strength in 0.0..1.0)
            assertTrue(restraint.summary.isNotBlank())
            assertTrue(restraint.percent in 0..100)
        }
    }

    private fun bandDb(buffer: AudioBuffer, low: Double, high: Double): Double {
        val mono = if (buffer.channelCount == 1) buffer else buffer.toMono()
        val filters = listOf(
            Biquad.highPass(low, buffer.sampleRate), Biquad.highPass(low, buffer.sampleRate),
            Biquad.lowPass(high, buffer.sampleRate), Biquad.lowPass(high, buffer.sampleRate),
        )
        var energy = 0.0
        for (sample in mono.channels[0]) {
            var value = sample.toDouble()
            for (filter in filters) value = filter.processSample(value)
            energy += value * value
        }
        return 10.0 * kotlin.math.log10((energy / mono.frameCount).coerceAtLeast(1e-20))
    }
}

/** The tally that lets real listeners tune the presets, and the limits that keep it safe. */
class ListeningDatabaseTest {

    private fun withNotes(preset: String, vararg notes: Pair<ListenerNote, Int>): ListeningDatabase {
        var database = ListeningDatabase()
        for ((note, count) in notes) repeat(count) { database = database.record(preset, note) }
        return database
    }

    @Test
    fun `one listener never moves a preset`() {
        // One note is a person's taste, their headphones, and possibly a mistap.
        val database = withNotes("Studio", ListenerNote.TOO_BRIGHT to 1)
        val settings = VoiceOutcome.STUDIO.settings
        assertSame(settings, database.tuned("Studio", settings))
        assertTrue(database.consensus("Studio").isEmpty())
        assertNull(database.approval("Studio"))
        assertNull(database.evidence("Studio"))
    }

    @Test
    fun `a preset most listeners call too bright becomes less bright`() {
        val database = withNotes(
            "Grand Space",
            ListenerNote.TOO_BRIGHT to 5,
            ListenerNote.TOO_DARK to 1,
        )
        val before = VoiceOutcome.GRAND_SPACE.settings
        val after = database.tuned("Grand Space", before)

        assertTrue(
            "brightness went from ${before.refinement.brightness} to ${after.refinement.brightness}",
            after.refinement.brightness < before.refinement.brightness,
        )
        assertTrue(after.refinement.air < before.refinement.air)
    }

    @Test
    fun `ten people saying the same thing is not ten corrections`() {
        val few = withNotes("Podcast", ListenerNote.TOO_MUDDY to 3)
        val many = withNotes("Podcast", ListenerNote.TOO_MUDDY to 40)
        val base = VoiceOutcome.PODCAST.settings
        assertEquals(
            "the size of the correction must not depend on the size of the panel",
            few.tuned("Podcast", base).refinement,
            many.tuned("Podcast", base).refinement,
        )
    }

    @Test
    fun `a preset cannot be walked off a cliff`() {
        // Every critical note in majority at once. The cap is what stops an unbounded loop.
        var database = ListeningDatabase()
        for (note in ListenerNote.order.filter { it != ListenerNote.EXCELLENT }) {
            repeat(20) { database = database.record("Immersive", note) }
        }
        val tuned = database.tuned("Immersive", VoiceOutcome.IMMERSIVE.settings)
        assertTrue(
            SignatureSound.verify(tuned).joinToString("\n") { it.rule },
            SignatureSound.holds(tuned),
        )
        assertFalse("listeners must not be able to delete the room", tuned.ambience.isBypassed)
    }

    @Test
    fun `a preset people are happy with can prove it`() {
        // If only complaints are recorded, the only evidence is complaints.
        val database = withNotes(
            "Clear Speech",
            ListenerNote.EXCELLENT to 9,
            ListenerNote.TOO_DARK to 1,
        )
        assertEquals(0.9, database.approval("Clear Speech")!!, 1e-9)
        assertEquals(10, database.listeners("Clear Speech"))
        val evidence = database.evidence("Clear Speech")!!
        assertTrue(evidence, evidence.contains("90%"))
        // One dissenting note is not a consensus, so nothing moves. Compared by value: `settings`
        // is a computed property, so identity would be testing the getter rather than the tally.
        val untouched = VoiceOutcome.CLEAR_SPEECH.settings
        assertEquals(untouched, database.tuned("Clear Speech", untouched))
    }

    @Test
    fun `unheard and disliked are never shown as the same thing`() {
        val unheard = ListeningDatabase()
        val disliked = withNotes("X", ListenerNote.TOO_HARSH to 6)
        assertNull("nobody has heard it", unheard.approval("X"))
        assertEquals("nobody liked it", 0.0, disliked.approval("X")!!, 1e-9)
    }

    @Test
    fun `the tally survives a round trip and a corrupt file`() {
        val database = withNotes("Lecture", ListenerNote.TOO_HARSH to 4, ListenerNote.EXCELLENT to 2)
        val restored = ListeningDatabase.decode(ListeningDatabase.encode(database))
        assertEquals(database, restored)
        assertEquals(6, restored.listeners("Lecture"))
        assertEquals(ListeningDatabase(), ListeningDatabase.decode("not json at all"))
    }

    @Test
    fun `evidence is only offered once there is some`() {
        var database = ListeningDatabase()
        assertNull(database.evidence("Warm Voice"))
        database = database.record("Warm Voice", ListenerNote.EXCELLENT)
        database = database.record("Warm Voice", ListenerNote.EXCELLENT)
        assertNull("two is still not evidence", database.evidence("Warm Voice"))
        database = database.record("Warm Voice", ListenerNote.EXCELLENT)
        assertNotNull("three independent notes is the smallest thing that is not one person", database.evidence("Warm Voice"))
    }
}
