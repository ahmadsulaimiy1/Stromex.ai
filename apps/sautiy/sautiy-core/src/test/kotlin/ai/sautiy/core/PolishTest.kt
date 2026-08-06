package ai.sautiy.core

import ai.sautiy.core.audio.AudioBuffer
import ai.sautiy.core.design.Radius
import ai.sautiy.core.design.Sizes
import ai.sautiy.core.design.Space
import ai.sautiy.core.dsp.Biquad
import ai.sautiy.core.dsp.VoiceOutcome
import ai.sautiy.core.dsp.VoiceStudio
import ai.sautiy.core.workspace.Workflows
import kotlin.math.PI
import kotlin.math.abs
import kotlin.math.log10
import kotlin.math.sin
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Phase Ω — the polish that can be enforced rather than reviewed.
 *
 * Craftsmanship is mostly invisible individually and unmistakable in aggregate. What a test can
 * hold is the aggregate: that no size was invented, that no workflow grew a step, that no two
 * presets are hard to tell apart. What a test cannot hold is whether the result feels premium, and
 * that is stated as unproven rather than claimed.
 */
class ConsistencyTest {

    @Test
    fun `every component size is on the grid or a deliberate exception`() {
        // 4 dp grid, chapter 5. The exceptions are named rather than tolerated: a hairline is 1 dp
        // because it is one pixel of intent, and a 2 dp stroke is the thinnest line that survives
        // being drawn on a canvas at low density.
        val exceptions = setOf(Sizes.HAIRLINE, Sizes.BORDER_SELECTED, Space.XXS)
        for (size in Sizes.all) {
            assertTrue(
                "$size dp is neither on the 4 dp grid nor a named exception",
                Space.isOnGrid(size) || size in exceptions,
            )
        }
    }

    @Test
    fun `there is exactly one size for each job`() {
        // The defect this exists to prevent: icons at 20, 22, 24 and 26 dp in four files. Three icon
        // sizes is a scale; four is an accident. Each must be clearly distinct or they are not
        // three decisions, they are one decision made badly three times.
        val icons = listOf(Sizes.ICON_SMALL, Sizes.ICON_MEDIUM, Sizes.ICON_LARGE)
        assertEquals("three icon sizes, no more", 3, icons.distinct().size)
        for ((smaller, larger) in icons.zipWithNext()) {
            assertTrue(
                "$smaller and $larger are too close to be separate decisions",
                larger - smaller >= 4,
            )
        }
    }

    @Test
    fun `nothing interactive can be smaller than a thumb`() {
        assertEquals(PerformanceBudget.MIN_TOUCH_TARGET_DP, Sizes.MIN_TOUCH_TARGET)
        assertTrue("48 dp is the floor, chapter 17", Sizes.MIN_TOUCH_TARGET >= 48)
        // The transport controls are the ones a thumb finds without looking.
        assertTrue(Sizes.TRANSPORT >= Sizes.MIN_TOUCH_TARGET)
        assertTrue(
            "the record control must be the largest target on screen",
            Sizes.TRANSPORT_PRIMARY > Sizes.TRANSPORT,
        )
    }

    @Test
    fun `radii form a scale rather than a collection`() {
        val scale = listOf(Radius.XS, Radius.S, Radius.M, Radius.L, Radius.XL, Radius.SHEET)
        for ((smaller, larger) in scale.zipWithNext()) {
            assertTrue("$smaller then $larger is not ascending", larger > smaller)
        }
        // A corner that differs by less than 4 dp from the next is not a distinguishable choice.
        for ((smaller, larger) in scale.dropLast(1).zipWithNext()) {
            assertTrue("$smaller and $larger are indistinguishable", larger - smaller >= 4)
        }
    }
}

/** Friction, counted. Phase Ω directive 2: count every tap, remove every unnecessary decision. */
class WorkflowFrictionTest {

    @Test
    fun `every common workflow is within its tap budget`() {
        val over = Workflows.all.filterNot { it.isWithinBudget }
        assertTrue(
            "these workflows grew: " + over.joinToString { "${it.name} takes ${it.taps}, budget ${it.budget}" },
            over.isEmpty(),
        )
    }

    @Test
    fun `recording is one tap and can never become two`() {
        // The most important number in the product. A recorder that asks anything before recording
        // has already lost the thought the user was trying to capture.
        assertEquals(1, Workflows.record.taps)
        assertEquals(1, Workflows.record.budget)
    }

    @Test
    fun `playing is one tap`() {
        assertEquals(1, Workflows.play.taps)
    }

    @Test
    fun `recalling a saved sound costs less than building one`() {
        // The whole justification for Voice DNA. If recalling were not cheaper than choosing a
        // preset and adjusting it, the feature would be decoration.
        assertTrue(
            "recall (${Workflows.recallSound.taps}) must beat save (${Workflows.saveSound.taps})",
            Workflows.recallSound.taps < Workflows.saveSound.taps,
        )
        assertTrue(Workflows.recallSound.taps <= Workflows.refine.taps)
    }

    @Test
    fun `sharing does not require exporting first`() {
        // Making the user export and then share would write the same file twice and add a step
        // whose reason they cannot see.
        assertTrue(
            "share (${Workflows.share.taps}) must not cost more than export (${Workflows.export.taps})",
            Workflows.share.taps <= Workflows.export.taps,
        )
    }

    @Test
    fun `every step states why it cannot be removed`() {
        // A step with a weak justification is the next one to delete. Writing the justification
        // down is what makes that visible.
        for (workflow in Workflows.all) {
            // A zero-step workflow is the best possible outcome, not a malformed one: `improve`
            // costs nothing because the app does it. It is listed so that adding a tap to it has to
            // be argued against a number.
            assertTrue("${workflow.name} has no stated goal", workflow.goal.length > 10)
            for (step in workflow.steps) {
                assertTrue("a step with no label in ${workflow.name}", step.tap.isNotBlank())
                assertTrue(
                    "'${step.tap}' in ${workflow.name} does not say why it exists",
                    step.because.length > 20,
                )
            }
        }
    }

    @Test
    fun `the total friction across the product is recorded`() {
        // One number to watch across releases. Not a limit — a tripwire: if this climbs, something
        // was added that nobody argued for.
        assertEquals(
            "total taps across every common workflow changed; that needs an argument, not a commit",
            14,
            Workflows.totalTaps,
        )
    }
}

/**
 * Phase Ω directive 8: every preset must be worth keeping.
 *
 * "If two presets are difficult to distinguish, merge or redesign them." That is testable, and it is
 * the one place a listening judgement has a measurable proxy: render the same phrase through two
 * presets and compare what came out. If the difference is below what anybody could hear, the two
 * presets are one preset with two names, and a list of ten names for eight sounds is worse than a
 * list of eight.
 */
class PresetDistinctnessTest {

    /** A phrase with speech-like structure: pitch, formants, sibilance and gaps. */
    private fun phrase(rate: Int = 48_000, seconds: Double = 2.5): AudioBuffer {
        val frames = (seconds * rate).toInt()
        val samples = FloatArray(frames)
        for (i in 0 until frames) {
            val t = i.toDouble() / rate
            val phase = (t * 1000).toInt() % 700
            if (phase >= 480) continue
            val envelope = 0.5 * (1 - kotlin.math.cos(2 * PI * (phase / 480.0)))
            samples[i] = (
                0.22 * sin(2 * PI * 132.0 * t) +
                    0.13 * sin(2 * PI * 560.0 * t) +
                    0.07 * sin(2 * PI * 1_900.0 * t) +
                    0.04 * sin(2 * PI * 4_200.0 * t) +
                    0.02 * sin(2 * PI * 7_800.0 * t)
                ).toFloat() * envelope.toFloat()
        }
        return AudioBuffer(arrayOf(samples), rate)
    }

    /**
     * How different two presets sound, in decibels, across the bands speech lives in.
     *
     * Band energy plus tail length. Not a perceptual model — a proxy, and named as one. What it can
     * honestly detect is two presets that do nearly the same arithmetic, which is the failure mode
     * a list of ten names has.
     */
    private fun difference(a: AudioBuffer, b: AudioBuffer): Double {
        val bands = listOf(
            80.0 to 250.0, 250.0 to 800.0, 800.0 to 2_500.0,
            2_500.0 to 6_000.0, 6_000.0 to 12_000.0,
        )
        var worst = 0.0
        for ((low, high) in bands) {
            worst = maxOf(worst, abs(bandDb(a, low, high) - bandDb(b, low, high)))
        }
        // How much room there is, measured directly.
        //
        // The first version of this compared the moment the signal fell below a fixed threshold,
        // which is a single brittle sample and read a 30%-wet hall as barely different from a dry
        // recording. Reverb is mostly the *same spectrum* as the voice that caused it, so band
        // energy alone cannot see it either — and loudness normalisation then flattens what little
        // remains. The energy that arrives *in the gaps between words* is the room and nothing but
        // the room, so that is what to compare.
        val room = abs(roomEnergyDb(a) - roomEnergyDb(b))
        return maxOf(worst, room)
    }

    /**
     * Energy in the pauses, relative to energy during speech, in decibels.
     *
     * A dry recording is near-silent between words. A hall is not. This is the one measurement that
     * corresponds to what a listener means by "how big is the room", and it is immune to loudness
     * normalisation because it is a ratio within the same file.
     */
    private fun roomEnergyDb(buffer: AudioBuffer): Double {
        val samples = buffer.channels[0]
        val rate = buffer.sampleRate
        // The fixture speaks for 480 ms in every 700 ms. The last 150 ms of each cycle is a gap in
        // the *input*, so anything there came from the processing.
        var gap = 0.0
        var gapCount = 0
        var speech = 0.0
        var speechCount = 0
        for (i in samples.indices) {
            val msInCycle = (i.toDouble() / rate * 1000).toInt() % 700
            val value = samples[i].toDouble()
            if (msInCycle in 550..690) {
                gap += value * value
                gapCount++
            } else if (msInCycle in 100..400) {
                speech += value * value
                speechCount++
            }
        }
        if (gapCount == 0 || speechCount == 0) return -120.0
        val gapMean = (gap / gapCount).coerceAtLeast(1e-20)
        val speechMean = (speech / speechCount).coerceAtLeast(1e-20)
        return 10.0 * log10(gapMean / speechMean)
    }

    private fun bandDb(buffer: AudioBuffer, low: Double, high: Double): Double {
        val rate = buffer.sampleRate
        val filters = listOf(
            Biquad.highPass(low, rate), Biquad.highPass(low, rate),
            Biquad.lowPass(minOf(high, rate * 0.45), rate),
            Biquad.lowPass(minOf(high, rate * 0.45), rate),
        )
        var energy = 0.0
        for (sample in buffer.channels[0]) {
            var value = sample.toDouble()
            for (filter in filters) value = filter.processSample(value)
            energy += value * value
        }
        return 10.0 * log10((energy / buffer.frameCount).coerceAtLeast(1e-20))
    }

    @Test
    fun `no two outcomes are difficult to distinguish`() {
        val source = phrase()
        val rendered = VoiceOutcome.entries.associateWith { VoiceStudio(it.settings).render(source).audio }

        // 1.5 dB, or a quarter-second of tail. Below that, two presets are one preset with two
        // names — and a list of ten names for eight sounds is worse than a list of eight.
        val floor = 1.5
        val tooClose = mutableListOf<String>()
        val outcomes = VoiceOutcome.entries.toList()
        for (i in outcomes.indices) {
            for (j in i + 1 until outcomes.size) {
                val delta = difference(rendered.getValue(outcomes[i]), rendered.getValue(outcomes[j]))
                if (delta < floor) {
                    tooClose += "${outcomes[i].displayName} vs ${outcomes[j].displayName}: " +
                        "%.2f dB".format(delta)
                }
            }
        }
        assertTrue(
            "these presets are hard to tell apart and should be merged or redesigned:\n" +
                tooClose.joinToString("\n") { "  $it" },
            tooClose.isEmpty(),
        )
    }

    @Test
    fun `every outcome states a distinct purpose and audience`() {
        // Directive 8: a distinct purpose, a distinct sound, a distinct audience. The sound is
        // measured above; the words are checked here, because two presets whose descriptions could
        // be swapped without anybody noticing are two presets nobody can choose between.
        val purposes = VoiceOutcome.entries.map { it.purpose.lowercase() }
        assertEquals("two outcomes share a description", purposes.size, purposes.distinct().size)
        for (outcome in VoiceOutcome.entries) {
            assertTrue(
                "${outcome.displayName} does not say what it is for",
                outcome.purpose.length > 20,
            )
        }
        // Groups exist so the ten are four short lists rather than one long one.
        val groups = VoiceOutcome.entries.groupBy { it.group }
        assertTrue("a group with more than four members is a list again", groups.values.all { it.size <= 4 })
    }
}


/**
 * The Trust Principle, in the one place it can be enforced rather than promised.
 *
 * Four of the five prohibitions are properties of the interface and are checked by reading it. The
 * second — never pretend an improvement happened when it did not — is arithmetic, and arithmetic can
 * be tested: the app's claim and the app's audio have to agree.
 */
class TrustPrincipleTest {

    @Test
    fun `a recording that needed nothing is never described as improved`() {
        // The claim the interface makes comes from `Restraint`. If a transparent recording's own
        // summary boasted, the label would inherit the boast.
        val clean = ai.sautiy.core.dsp.Restraint.of(
            ai.sautiy.core.dsp.VoiceAnalysis(
                integratedLufs = -21.0,
                truePeakDb = -6.0,
                loudnessRangeLu = 6.0,
                noiseFloorDb = -64.0,
                lowTiltDb = -8.0,
                presenceTiltDb = -12.0,
                sibilanceTiltDb = -16.0,
            ),
        )
        assertTrue("this fixture is supposed to need almost nothing", clean.isTransparent)
        val summary = clean.summary.lowercase()
        assertTrue("the summary must say the recording was already clean", summary.contains("already clean"))
        for (boast in listOf("improved", "enhanced", "better", "professional", "studio quality")) {
            assertTrue("a transparent recording claimed to be '$boast': ${clean.summary}", !summary.contains(boast))
        }
    }

    @Test
    fun `the work reported is the work done`() {
        // Restraint drives both the label and the chain, so a recording that reports no work must
        // also receive none. Two numbers that could drift apart are one lie waiting to happen.
        val clean = ai.sautiy.core.dsp.Restraint.of(
            ai.sautiy.core.dsp.VoiceAnalysis(-21.0, -6.0, 6.0, -64.0, -8.0, -12.0, -16.0),
        )
        val settings = ai.sautiy.core.dsp.VoiceAdvisor.enhance(
            ai.sautiy.core.dsp.VoiceAnalysis(-21.0, -6.0, 6.0, -64.0, -8.0, -12.0, -16.0),
        )
        assertTrue(clean.isTransparent)
        assertTrue("reported no work but compressed anyway", settings.dynamics.compressor == null)
        assertTrue("reported no work but shaped the tone anyway", settings.refinement.isNeutral)
        assertTrue("reported no work but added a room anyway", settings.ambience.isBypassed)
    }

    @Test
    fun `nothing automatic is irreversible`() {
        // The only automatic change in the product is cleanup, and it is a `VoiceStudioSettings`
        // applied at playback and export. Reverting is dropping it, which is why the original file
        // can never be affected: `VoiceStudio.render` copies its input and leaves the caller's audio
        // untouched, and that is asserted in VoiceStudioTest.
        val enhanced = ai.sautiy.core.dsp.VoiceAdvisor.enhance(
            ai.sautiy.core.dsp.VoiceAnalysis(-34.0, -12.0, 15.0, -46.0, -14.0, -24.0, -6.0),
        )
        assertTrue("the enhanced chain must be a value, not a mutation", !enhanced.isTransparent)

        // What "revert" actually is, corrected by this test.
        //
        // The first version asserted that the *default* settings are transparent. They are not: the
        // default carries a −1 dBTP limiter ceiling, which is right for anything being exported and
        // is still processing. Naming that value "untouched" would have been the exact category of
        // small untruth this class exists to catch.
        //
        // Reverting in the app is not a transparent chain — it is *no chain*: `revertPreset` sets
        // the voice to null and the player stops applying anything. So the guarantee to assert is
        // that a provably-transparent value is *constructible*, which is what makes "no processing"
        // a state the engine can represent rather than a claim the UI makes.
        val untouched = ai.sautiy.core.dsp.VoiceStudioSettings(
            loudness = ai.sautiy.core.dsp.LoudnessStage(target = null, limiterCeilingDb = null),
        )
        assertTrue(
            "there must be a representable setting that provably does nothing",
            untouched.isTransparent,
        )
        assertTrue(
            "the default chain is not transparent — it limits — and must not be described as such",
            !ai.sautiy.core.dsp.VoiceStudioSettings().isTransparent,
        )
    }
}
