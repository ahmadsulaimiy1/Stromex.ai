package com.sajjil.core.readiness

import com.sajjil.core.quran.AyahRange
import com.sajjil.core.quran.QuranMetadata
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class ProductionReadinessCalculatorTest {

    private val alFatihah = QuranMetadata.surahByNumber(1) // 7 ayahs

    @Test
    fun `fully covered clean project scores 100 with no issues`() {
        val takes = listOf(
            ReadinessTake(
                recordingId = 1L,
                title = "Al-Fatihah Take 1",
                surahNumber = 1,
                ayahRange = AyahRange(1, 7),
                hasClipping = false,
                noiseScore = 90,
                integratedLoudnessLufs = -18.0,
            ),
        )

        val report = ProductionReadinessCalculator.evaluate(listOf(alFatihah), takes)

        assertEquals(100, report.score)
        assertEquals(7, report.totalAyahs)
        assertEquals(7, report.coveredAyahs)
        assertTrue(report.issues.isEmpty())
    }

    @Test
    fun `missing ayat lowers score to match coverage percentage`() {
        val takes = listOf(
            ReadinessTake(
                recordingId = 1L,
                title = "Al-Fatihah Partial",
                surahNumber = 1,
                ayahRange = AyahRange(1, 5),
                hasClipping = false,
            ),
        )

        val report = ProductionReadinessCalculator.evaluate(listOf(alFatihah), takes)

        assertEquals(5, report.coveredAyahs)
        assertEquals(71, report.score) // round(100 * 5/7)
        assertTrue(report.issues.any { it.category == "Missing Ayat" && it.severity == ReadinessSeverity.CRITICAL })
    }

    @Test
    fun `overlapping takes on the same surah are flagged as a possible duplicate`() {
        val takes = listOf(
            ReadinessTake(1L, "Take A", 1, AyahRange(1, 7), hasClipping = false),
            ReadinessTake(2L, "Take B", 1, AyahRange(4, 7), hasClipping = false),
        )

        val report = ProductionReadinessCalculator.evaluate(listOf(alFatihah), takes)

        assertEquals(100, report.percentComplete.toInt())
        assertTrue(report.issues.any { it.category == "Possible Duplicate" && it.severity == ReadinessSeverity.WARNING })
        assertEquals(95, report.score) // 100 - 5 (one warning)
    }

    @Test
    fun `clipping is a critical issue that costs 15 points`() {
        val takes = listOf(
            ReadinessTake(1L, "Al-Fatihah Take 1", 1, AyahRange(1, 7), hasClipping = true),
        )

        val report = ProductionReadinessCalculator.evaluate(listOf(alFatihah), takes)

        assertTrue(report.issues.any { it.category == "Clipping" && it.severity == ReadinessSeverity.CRITICAL })
        assertEquals(85, report.score)
    }

    @Test
    fun `low noise score produces a warning`() {
        val takes = listOf(
            ReadinessTake(1L, "Al-Fatihah Take 1", 1, AyahRange(1, 7), hasClipping = false, noiseScore = 30),
        )

        val report = ProductionReadinessCalculator.evaluate(listOf(alFatihah), takes)

        assertTrue(report.issues.any { it.category == "Noise" && it.severity == ReadinessSeverity.WARNING })
        assertEquals(95, report.score)
    }

    @Test
    fun `noise score at or above threshold produces no noise warning`() {
        val takes = listOf(
            ReadinessTake(1L, "Al-Fatihah Take 1", 1, AyahRange(1, 7), hasClipping = false, noiseScore = 50),
        )

        val report = ProductionReadinessCalculator.evaluate(listOf(alFatihah), takes)

        assertFalse(report.issues.any { it.category == "Noise" })
    }

    @Test
    fun `inconsistent loudness across takes produces a warning`() {
        val takes = listOf(
            ReadinessTake(1L, "Take A", 1, AyahRange(1, 3), hasClipping = false, integratedLoudnessLufs = -30.0),
            ReadinessTake(2L, "Take B", 1, AyahRange(4, 7), hasClipping = false, integratedLoudnessLufs = -10.0),
        )

        val report = ProductionReadinessCalculator.evaluate(listOf(alFatihah), takes)

        assertTrue(report.issues.any { it.category == "Loudness Consistency" && it.severity == ReadinessSeverity.WARNING })
    }

    @Test
    fun `consistent loudness across takes produces no warning`() {
        val takes = listOf(
            ReadinessTake(1L, "Take A", 1, AyahRange(1, 3), hasClipping = false, integratedLoudnessLufs = -18.0),
            ReadinessTake(2L, "Take B", 1, AyahRange(4, 7), hasClipping = false, integratedLoudnessLufs = -17.0),
        )

        val report = ProductionReadinessCalculator.evaluate(listOf(alFatihah), takes)

        assertFalse(report.issues.any { it.category == "Loudness Consistency" })
    }

    @Test
    fun `untagged recording produces a metadata warning and does not count toward coverage`() {
        val takes = listOf(
            ReadinessTake(1L, "Al-Fatihah Take 1", 1, AyahRange(1, 7), hasClipping = false),
            ReadinessTake(2L, "Random Recording", surahNumber = null, ayahRange = null, hasClipping = false),
        )

        val report = ProductionReadinessCalculator.evaluate(listOf(alFatihah), takes)

        assertEquals(100, report.percentComplete.toInt())
        assertTrue(report.issues.any { it.category == "Metadata" && it.message.contains("Random Recording") })
    }

    @Test
    fun `blank title produces a metadata warning`() {
        val takes = listOf(
            ReadinessTake(1L, "", 1, AyahRange(1, 7), hasClipping = false),
        )

        val report = ProductionReadinessCalculator.evaluate(listOf(alFatihah), takes)

        assertTrue(report.issues.any { it.category == "Metadata" && it.message.contains("no title") })
    }

    @Test
    fun `two different recordings sharing a title are flagged as a naming collision`() {
        val takes = listOf(
            ReadinessTake(1L, "Al-Fatihah Take 1", 1, AyahRange(1, 7), hasClipping = false),
            ReadinessTake(20L, "My Recording", surahNumber = null, ayahRange = null, hasClipping = false),
            ReadinessTake(21L, "My Recording", surahNumber = null, ayahRange = null, hasClipping = false),
        )

        val report = ProductionReadinessCalculator.evaluate(listOf(alFatihah), takes)

        val namingIssue = report.issues.single { it.category == "Naming Consistency" }
        assertEquals(ReadinessSeverity.INFO, namingIssue.severity)
        assertTrue(namingIssue.message.contains("My Recording"))
    }

    @Test
    fun `empty takes list yields zero coverage and a missing ayat issue`() {
        val report = ProductionReadinessCalculator.evaluate(listOf(alFatihah), emptyList())

        assertEquals(0, report.coveredAyahs)
        assertEquals(7, report.totalAyahs)
        assertEquals(0, report.score)
        assertTrue(report.issues.any { it.category == "Missing Ayat" })
    }

    @Test
    fun `label formats the score for display`() {
        val takes = listOf(
            ReadinessTake(1L, "Al-Fatihah Take 1", 1, AyahRange(1, 7), hasClipping = false),
        )

        val report = ProductionReadinessCalculator.evaluate(listOf(alFatihah), takes)

        assertEquals("Production Readiness: 100/100", report.label)
    }
}
