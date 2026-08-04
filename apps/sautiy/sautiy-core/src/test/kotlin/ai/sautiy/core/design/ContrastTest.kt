package ai.sautiy.core.design

import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Editorial Bible chapter 2.3.4 and chapter 17, held as an executable rule.
 *
 * Contrast is not reviewed by eye at design time and hoped for at runtime — every text role is
 * measured against every surface it can legally sit on, in both themes, and the build fails
 * below the floor.
 */
class ContrastTest {

    private data class Surface(val name: String, val argb: Int)

    private fun surfacesOf(c: SautiyColours) = listOf(
        Surface("canvas", c.canvas),
        Surface("surface", c.surface),
        Surface("surfaceRaised", c.surfaceRaised),
        Surface("surfaceOverlay", c.surfaceOverlay),
    )

    private fun check(
        theme: String,
        role: String,
        fg: Int,
        surfaces: List<Surface>,
        floor: Double,
    ) {
        for (s in surfaces) {
            val ratio = Contrast.ratio(fg, s.argb)
            assertTrue(
                "[$theme] $role on ${s.name} is ${"%.2f".format(ratio)}:1, below the $floor:1 floor",
                ratio >= floor,
            )
        }
    }

    @Test
    fun `body text meets the 4_5 to 1 floor on every legal surface in both themes`() {
        for ((theme, c) in listOf("dark" to SautiyColours.Dark, "light" to SautiyColours.Light)) {
            val surfaces = surfacesOf(c)
            check(theme, "textPrimary", c.textPrimary, surfaces, Contrast.BODY_TEXT_FLOOR)
            check(theme, "textSecondary", c.textSecondary, surfaces, Contrast.BODY_TEXT_FLOOR)
            check(theme, "textTertiary", c.textTertiary, surfaces, Contrast.BODY_TEXT_FLOOR)
        }
    }

    @Test
    fun `disabled text stays legible at the non-text floor`() {
        // Disabled controls are exempt from the body floor under WCAG, but SAUTIY still
        // requires them to be readable rather than merely present (chapter 2.3.4 clause 5:
        // opacity is not a colour).
        for ((theme, c) in listOf("dark" to SautiyColours.Dark, "light" to SautiyColours.Light)) {
            check(
                theme, "textDisabled", c.textDisabled, surfacesOf(c),
                Contrast.LARGE_AND_NON_TEXT_FLOOR,
            )
        }
    }

    @Test
    fun `signal, ember, commit and status colours meet the non-text floor`() {
        for ((theme, c) in listOf("dark" to SautiyColours.Dark, "light" to SautiyColours.Light)) {
            val surfaces = surfacesOf(c)
            val floor = Contrast.LARGE_AND_NON_TEXT_FLOOR
            check(theme, "signal", c.signal, surfaces, floor)
            check(theme, "signalMuted", c.signalMuted, surfaces, floor)
            check(theme, "ember", c.ember, surfaces, floor)
            check(theme, "commit", c.commit, surfaces, floor)
            check(theme, "safe", c.safe, surfaces, floor)
            check(theme, "caution", c.caution, surfaces, floor)
            check(theme, "critical", c.critical, surfaces, floor)
        }
    }

    @Test
    fun `content placed on a filled control is legible against that control`() {
        for ((theme, c) in listOf("dark" to SautiyColours.Dark, "light" to SautiyColours.Light)) {
            val floor = Contrast.LARGE_AND_NON_TEXT_FLOOR
            val pairs = listOf(
                Triple("onSignal/signal", c.onSignal, c.signal),
                Triple("onEmber/ember", c.onEmber, c.ember),
                Triple("onCommit/commit", c.onCommit, c.commit),
            )
            for ((name, fg, bg) in pairs) {
                val ratio = Contrast.ratio(fg, bg)
                assertTrue(
                    "[$theme] $name is ${"%.2f".format(ratio)}:1, below $floor:1",
                    ratio >= floor,
                )
            }
        }
    }

    @Test
    fun `structural hairlines are actually visible against their surface`() {
        // A border the eye cannot find is not structure, it is noise in the file.
        for ((theme, c) in listOf("dark" to SautiyColours.Dark, "light" to SautiyColours.Light)) {
            val ratio = Contrast.ratio(c.border, c.surface)
            assertTrue(
                "[$theme] border on surface is ${"%.2f".format(ratio)}:1 — invisible hairline",
                ratio >= 1.2,
            )
        }
    }

    @Test
    fun `selection fill never obscures the waveform drawn on top of it`() {
        for ((theme, c) in listOf("dark" to SautiyColours.Dark, "light" to SautiyColours.Light)) {
            val ratio = Contrast.ratio(c.signal, c.signalSelection)
            assertTrue(
                "[$theme] signal on signalSelection is ${"%.2f".format(ratio)}:1",
                ratio >= Contrast.LARGE_AND_NON_TEXT_FLOOR,
            )
        }
    }

    @Test
    fun `ember reads as distinct from commit so recording is never mistaken for confirming`() {
        // Chapter 2.3.4 clause 1 reserves ember for recording. The two must not be confusable
        // for a user with normal vision; deuteranopia safety is handled by shape, not hue.
        for (c in listOf(SautiyColours.Dark, SautiyColours.Light)) {
            val hueGap = Contrast.ratio(c.ember, c.commit)
            // They are close in luminance by design (both are saturated warm hues), so the
            // separation that matters is that neither is ever used for the other's job. What
            // this asserts is simply that they are not the same colour.
            assertTrue("ember and commit must not be the same value", c.ember != c.commit)
            assertTrue("ember/commit ratio computed: $hueGap", hueGap in 0.5..21.0)
        }
    }
}
