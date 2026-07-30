package com.sajjil.core.analysis

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertTrue

class AnalyticsCalculatorTest {

    @Test
    fun `empty library reports zeros and nulls, not crashes`() {
        val analytics = AnalyticsCalculator.compute(emptyList())
        assertEquals(0.0, analytics.totalRecordingHours)
        assertEquals(0, analytics.surahsRecorded)
        assertEquals(0, analytics.juzCompleted)
        assertNull(analytics.averageQualityScore)
        assertNull(analytics.improvementTrend)
        assertEquals(0, analytics.librarySize)
    }

    @Test
    fun `recording hours sum durations across the library`() {
        val recordings = listOf(
            RecordingSummary(durationMs = 30 * 60_000L, createdAtEpochMs = 1),
            RecordingSummary(durationMs = 90 * 60_000L, createdAtEpochMs = 2),
        )
        val analytics = AnalyticsCalculator.compute(recordings)
        assertEquals(2.0, analytics.totalRecordingHours, 0.001) // 30min + 90min = 2 hours
    }

    @Test
    fun `distinct surahs are counted once regardless of how many takes`() {
        val recordings = listOf(
            RecordingSummary(durationMs = 1, createdAtEpochMs = 1, surahNumber = 1, ayahStart = 1, ayahEnd = 3),
            RecordingSummary(durationMs = 1, createdAtEpochMs = 2, surahNumber = 1, ayahStart = 4, ayahEnd = 7),
            RecordingSummary(durationMs = 1, createdAtEpochMs = 3, surahNumber = 112, ayahStart = 1, ayahEnd = 4),
        )
        assertEquals(2, AnalyticsCalculator.compute(recordings).surahsRecorded)
    }

    @Test
    fun `a fully covered Juz counts toward Juz completed`() {
        // Juz 2 = Al-Baqarah 142-252.
        val recordings = listOf(
            RecordingSummary(durationMs = 1, createdAtEpochMs = 1, surahNumber = 2, ayahStart = 142, ayahEnd = 252),
        )
        assertEquals(1, AnalyticsCalculator.compute(recordings).juzCompleted)
    }

    @Test
    fun `a partially covered Juz does not count as completed`() {
        val recordings = listOf(
            RecordingSummary(durationMs = 1, createdAtEpochMs = 1, surahNumber = 2, ayahStart = 142, ayahEnd = 200),
        )
        assertEquals(0, AnalyticsCalculator.compute(recordings).juzCompleted)
    }

    @Test
    fun `average quality score ignores unscored recordings`() {
        val recordings = listOf(
            RecordingSummary(durationMs = 1, createdAtEpochMs = 1, studioReadinessScore = 80),
            RecordingSummary(durationMs = 1, createdAtEpochMs = 2, studioReadinessScore = 60),
            RecordingSummary(durationMs = 1, createdAtEpochMs = 3, studioReadinessScore = null),
        )
        assertEquals(70.0, AnalyticsCalculator.compute(recordings).averageQualityScore)
    }

    @Test
    fun `improvement trend is null with too little history`() {
        val recordings = (1..5).map { RecordingSummary(durationMs = 1, createdAtEpochMs = it.toLong(), studioReadinessScore = 50) }
        assertNull(AnalyticsCalculator.compute(recordings, trendWindowSize = 10).improvementTrend)
    }

    @Test
    fun `improvement trend is positive when recent recordings score higher than older ones`() {
        val older = (1..10).map { RecordingSummary(durationMs = 1, createdAtEpochMs = it.toLong(), studioReadinessScore = 50) }
        val recent = (11..20).map { RecordingSummary(durationMs = 1, createdAtEpochMs = it.toLong(), studioReadinessScore = 80) }
        val trend = AnalyticsCalculator.compute(older + recent, trendWindowSize = 10).improvementTrend
        assertNotNull(trend, "expected a trend value, got null")
        assertEquals(30.0, trend, 0.001)
    }

    @Test
    fun `storage usage and library size are straightforward sums and counts`() {
        val recordings = listOf(
            RecordingSummary(durationMs = 1, createdAtEpochMs = 1, fileSizeBytes = 1_000_000L),
            RecordingSummary(durationMs = 1, createdAtEpochMs = 2, fileSizeBytes = 2_500_000L),
        )
        val analytics = AnalyticsCalculator.compute(recordings)
        assertEquals(2, analytics.librarySize)
        assertEquals(3_500_000L, analytics.totalStorageBytes)
    }
}
