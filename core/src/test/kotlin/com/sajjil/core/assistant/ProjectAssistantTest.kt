package com.sajjil.core.assistant

import com.sajjil.core.analysis.ExecutiveAnalytics
import com.sajjil.core.quran.AyahRange
import com.sajjil.core.quran.JuzProgress
import com.sajjil.core.quran.QuranMetadata
import com.sajjil.core.quran.RevelationPlace
import com.sajjil.core.quran.SurahInfo
import com.sajjil.core.quran.SurahProgress
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class ProjectAssistantTest {

    private fun surah(number: Int, name: String, ayahCount: Int = 10) =
        SurahInfo(number, name, ayahCount, RevelationPlace.MECCAN)

    private fun progress(
        surah: SurahInfo,
        isComplete: Boolean,
        averageQualityScore: Double? = null,
        percentComplete: Double = if (isComplete) 100.0 else 50.0,
    ) = SurahProgress(
        surah = surah,
        totalAyahs = surah.ayahCount,
        coveredAyahs = if (isComplete) surah.ayahCount else surah.ayahCount / 2,
        percentComplete = percentComplete,
        missingRanges = if (isComplete) emptyList() else listOf(AyahRange(1, 1)),
        averageQualityScore = averageQualityScore,
        isComplete = isComplete,
    )

    private fun analytics(librarySize: Int, improvementTrend: Double? = null) = ExecutiveAnalytics(
        totalRecordingHours = 10.0,
        surahsRecorded = librarySize,
        juzCompleted = 0,
        averageQualityScore = 85.0,
        improvementTrend = improvementTrend,
        librarySize = librarySize,
        totalStorageBytes = 1_000_000L,
    )

    @Test
    fun `empty library yields a single starter insight`() {
        val report = ProjectAssistant.analyze(emptyList(), emptyList(), analytics(librarySize = 0))

        assertEquals(1, report.insights.size)
        assertTrue(report.insights.first().message.contains("Al-Fatihah"))
    }

    @Test
    fun `progress insight reports completed and remaining surahs and juz`() {
        val surahs = listOf(
            progress(surah(1, "Al-Fatihah"), isComplete = true),
            progress(surah(2, "Al-Baqarah"), isComplete = false),
        )
        val juz = listOf(
            JuzProgress(1, emptyList(), isComplete = true, percentComplete = 100.0),
            JuzProgress(2, emptyList(), isComplete = false, percentComplete = 40.0),
        )

        val report = ProjectAssistant.analyze(surahs, juz, analytics(librarySize = 2))

        val progressInsight = report.insights.first { it.category == InsightCategory.PROGRESS }
        assertTrue(progressInsight.message.contains("1 of 2 Surah"))
        assertTrue(progressInsight.message.contains("Remaining: 1 Juz and 1 Surah"))
    }

    @Test
    fun `fully complete set reports completion instead of a remainder count`() {
        val surahs = listOf(progress(surah(1, "Al-Fatihah"), isComplete = true))
        val juz = listOf(JuzProgress(1, emptyList(), isComplete = true, percentComplete = 100.0))

        val report = ProjectAssistant.analyze(surahs, juz, analytics(librarySize = 1))

        val progressInsight = report.insights.first { it.category == InsightCategory.PROGRESS }
        assertTrue(progressInsight.message.contains("complete"))
    }

    @Test
    fun `positive improvement trend produces an encouraging quality insight`() {
        val surahs = listOf(progress(surah(1, "Al-Fatihah"), isComplete = true))
        val report = ProjectAssistant.analyze(surahs, emptyList(), analytics(librarySize = 1, improvementTrend = 6.0))

        val trendInsight = report.insights.first { it.category == InsightCategory.QUALITY }
        assertTrue(trendInsight.message.contains("higher"))
        assertTrue(trendInsight.message.contains("6"))
    }

    @Test
    fun `negative improvement trend produces a warning quality insight`() {
        val surahs = listOf(progress(surah(1, "Al-Fatihah"), isComplete = true))
        val report = ProjectAssistant.analyze(surahs, emptyList(), analytics(librarySize = 1, improvementTrend = -8.0))

        val trendInsight = report.insights.first { it.category == InsightCategory.QUALITY }
        assertTrue(trendInsight.message.contains("dropped"))
        assertTrue(trendInsight.message.contains("8"))
    }

    @Test
    fun `null improvement trend produces no quality insight`() {
        val surahs = listOf(progress(surah(1, "Al-Fatihah"), isComplete = true))
        val report = ProjectAssistant.analyze(surahs, emptyList(), analytics(librarySize = 1, improvementTrend = null))

        assertFalse(report.insights.any { it.category == InsightCategory.QUALITY })
    }

    @Test
    fun `surah scoring well below average is recommended for re-recording`() {
        val surahs = listOf(
            progress(surah(1, "Al-Fatihah"), isComplete = true, averageQualityScore = 95.0),
            progress(surah(2, "Al-Baqarah"), isComplete = true, averageQualityScore = 96.0),
            progress(surah(67, "Al-Mulk"), isComplete = true, averageQualityScore = 70.0),
        )

        val report = ProjectAssistant.analyze(surahs, emptyList(), analytics(librarySize = 3))

        val recommendation = report.insights.first { it.category == InsightCategory.RECOMMENDATION }
        assertTrue(recommendation.message.contains("Al-Mulk"))
        assertTrue(recommendation.message.contains("re-recording"))
    }

    @Test
    fun `surahs with similar quality produce no re-recording recommendation`() {
        val surahs = listOf(
            progress(surah(1, "Al-Fatihah"), isComplete = true, averageQualityScore = 90.0),
            progress(surah(2, "Al-Baqarah"), isComplete = true, averageQualityScore = 88.0),
        )

        val report = ProjectAssistant.analyze(surahs, emptyList(), analytics(librarySize = 2))

        assertFalse(report.insights.any { it.message.contains("re-recording") })
    }

    @Test
    fun `nearly complete juz is surfaced as a recommendation`() {
        val surahs = listOf(progress(surah(1, "Al-Fatihah"), isComplete = true))
        val juz = listOf(JuzProgress(5, emptyList(), isComplete = false, percentComplete = 90.0))

        val report = ProjectAssistant.analyze(surahs, juz, analytics(librarySize = 1))

        val recommendation = report.insights.first { it.category == InsightCategory.RECOMMENDATION }
        assertTrue(recommendation.message.contains("Juz 5"))
        assertTrue(recommendation.message.contains("90%"))
    }

    @Test
    fun `real quran metadata surah lookup works end to end`() {
        val alMulk = QuranMetadata.surahByNumber(67)
        assertEquals("Al-Mulk", alMulk.transliteratedName)
    }

    @Test
    fun `a take scoring well below the project average is flagged with its ayah range`() {
        val samples = listOf(
            TakeQualitySample(1L, "Take A", "Al-Baqarah", AyahRange(1, 10), score = 90),
            TakeQualitySample(2L, "Take B", "Al-Baqarah", AyahRange(11, 20), score = 92),
            TakeQualitySample(3L, "Take C", "Al-Baqarah", AyahRange(184, 188), score = 60),
        )

        val insights = ProjectAssistant.analyzeTakeOutliers(samples)

        assertEquals(1, insights.size)
        assertEquals(InsightCategory.RECOMMENDATION, insights.first().category)
        assertTrue(insights.first().message.contains("Al-Baqarah (Ayah 184-188)"))
        assertTrue(insights.first().message.contains("60"))
    }

    @Test
    fun `takes with similar scores produce no outlier insights`() {
        val samples = listOf(
            TakeQualitySample(1L, "Take A", "Al-Baqarah", AyahRange(1, 10), score = 88),
            TakeQualitySample(2L, "Take B", "Al-Baqarah", AyahRange(11, 20), score = 90),
        )

        assertTrue(ProjectAssistant.analyzeTakeOutliers(samples).isEmpty())
    }

    @Test
    fun `untagged take falls back to its title when surah or ayah range is missing`() {
        val samples = listOf(
            TakeQualitySample(1L, "Great Take", score = 95),
            TakeQualitySample(2L, "Great Take", score = 96),
            TakeQualitySample(3L, "Rough Take", score = 50),
        )

        val insights = ProjectAssistant.analyzeTakeOutliers(samples)

        assertEquals(1, insights.size)
        assertTrue(insights.first().message.contains("\"Rough Take\""))
    }

    @Test
    fun `fewer than two takes produces no outlier insights`() {
        val samples = listOf(TakeQualitySample(1L, "Only Take", score = 40))
        assertTrue(ProjectAssistant.analyzeTakeOutliers(samples).isEmpty())
    }
}
