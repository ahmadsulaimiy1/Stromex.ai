package ai.sautiy.core.design

import ai.sautiy.core.PerformanceBudget
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Editorial Bible chapters 2.4, 5 and 6, held as executable rules.
 */
class DesignSystemTest {

    @Test
    fun `every spacing token sits on the four dp rhythm`() {
        val tokens = listOf(
            "XS" to Space.XS, "S" to Space.S, "M" to Space.M, "L" to Space.L,
            "XL" to Space.XL, "XXL" to Space.XXL, "H3" to Space.H3, "H4" to Space.H4,
            "H5" to Space.H5, "H6" to Space.H6,
            "PAGE_INSET" to Space.PAGE_INSET, "SECTION_GAP" to Space.SECTION_GAP,
        )
        for ((name, dp) in tokens) {
            assertTrue("Space.$name = $dp is off the ${Space.UNIT} dp grid", Space.isOnGrid(dp))
        }
    }

    @Test
    fun `every number that changes in place uses tabular figures`() {
        // Chapter 2.4.2 clause 1. A timer whose width jitters as digits change is a defect.
        val mustBeTabular = listOf("timerHero", "timerInline", "numeric")
        for (name in mustBeTabular) {
            val style = TypeScale.all.first { it.first == name }.second
            assertTrue("$name must use tabular figures", style.tabularFigures)
        }
    }

    @Test
    fun `line height always exceeds font size`() {
        for ((name, style) in TypeScale.all) {
            assertTrue(
                "$name has line height ${style.lineHeightSp} <= size ${style.sizeSp}",
                style.lineHeightSp > style.sizeSp,
            )
        }
    }

    @Test
    fun `quranic arabic is given generous leading and never set below the reading minimum`() {
        // Chapter 2.4.2 clause 5.
        val ayah = TypeScale.quranAyah
        assertEquals(TypeFamily.QURANIC_ARABIC, ayah.family)
        assertTrue("Qur'anic text must be at least 24 sp", ayah.sizeSp >= 24)
        assertTrue(
            "Qur'anic leading must be at least 1.8x the size",
            ayah.lineHeightSp >= (ayah.sizeSp * 1.8).toInt(),
        )
        assertEquals("Qur'anic text is never tracked", 0.0, ayah.trackingSp, 0.0)
    }

    @Test
    fun `no motion duration exceeds the large surface ceiling`() {
        val durations = listOf(
            Motion.INSTANT_MS, Motion.FAST_MS, Motion.STANDARD_MS,
            Motion.EMPHASISED_MS, Motion.LARGE_MS,
        )
        for (d in durations) {
            assertTrue("$d ms exceeds the ${Motion.MAX_DURATION_MS} ms ceiling", d <= Motion.MAX_DURATION_MS)
        }
        assertTrue("motion tiers must be strictly increasing", durations.zipWithNext().all { it.first < it.second })
    }

    @Test
    fun `motion never bounces`() {
        assertTrue(
            "SAUTIY permits at most 3% overshoot (chapter 2.6)",
            Motion.MAX_OVERSHOOT_FRACTION <= 0.03,
        )
        // Standard and emphasised easings must both end flat — a curve whose final control
        // point y exceeds 1.0 overshoots by construction.
        for (easing in listOf(Motion.STANDARD_EASING, Motion.EMPHASISED_EASING, Motion.EXIT_EASING)) {
            assertEquals(4, easing.size)
            assertTrue("easing y2 must not exceed 1.0", easing[3] <= 1.0f)
            assertTrue("easing y1 must not exceed 1.0", easing[1] <= 1.0f)
        }
    }

    @Test
    fun `meter ballistics are honest - instant attack, controlled release`() {
        // Chapter 1.4 principle 5. A meter that lags the signal under-reports peaks.
        assertEquals("attack must be instantaneous", 0, Motion.METER_ATTACK_MS)
        assertTrue("release must be finite and gradual", Motion.METER_RELEASE_DB_PER_SEC in 10.0..30.0)
        assertTrue("peak hold must dwell long enough to be read", Motion.PEAK_HOLD_DWELL_MS >= 1_000)
    }

    @Test
    fun `capture flush cadence keeps sample loss inside the constitutional ceiling`() {
        // Chapter 1.3.5 / 1.6: at most two seconds may be lost to a process kill, and the
        // flush interval must leave headroom for one in-flight buffer.
        assertTrue(
            "flush interval ${PerformanceBudget.CAPTURE_FLUSH_INTERVAL_MS} ms must be under " +
                "half the ${PerformanceBudget.MAX_SAMPLE_LOSS_ON_KILL_MS} ms loss ceiling",
            PerformanceBudget.CAPTURE_FLUSH_INTERVAL_MS * 2 <= PerformanceBudget.MAX_SAMPLE_LOSS_ON_KILL_MS,
        )
    }

    @Test
    fun `touch targets meet the constitutional minimum`() {
        assertTrue(PerformanceBudget.MIN_TOUCH_TARGET_DP >= 48)
    }

    @Test
    fun `the record path stays one tap and the export path stays within three`() {
        assertEquals(1, PerformanceBudget.MAX_TAPS_TO_RECORD)
        assertTrue(PerformanceBudget.MAX_TAPS_TO_EXPORT <= 3)
    }
}
