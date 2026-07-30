package com.sajjil.core.analysis

import com.sajjil.core.quran.AyahRange
import com.sajjil.core.quran.JuzProgressCalculator
import com.sajjil.core.quran.RecordedTake

/** A recording reduced to just what Executive Analytics needs — keeps this module free of any Room/Android dependency. */
data class RecordingSummary(
    val durationMs: Long,
    val createdAtEpochMs: Long,
    val surahNumber: Int? = null,
    val ayahStart: Int? = null,
    val ayahEnd: Int? = null,
    val studioReadinessScore: Int? = null,
    val fileSizeBytes: Long = 0,
)

data class ExecutiveAnalytics(
    val totalRecordingHours: Double,
    val surahsRecorded: Int,
    val juzCompleted: Int,
    val averageQualityScore: Double?,
    /** Recent-window average score minus the prior window's — positive means improving. Null with too little history. */
    val improvementTrend: Double?,
    val librarySize: Int,
    val totalStorageBytes: Long,
)

/**
 * SAJJIL Executive Analytics: the numbers a Qari or production lead
 * actually wants to see across their whole library, computed once from a
 * flat recording list rather than scattered ad hoc queries.
 */
object AnalyticsCalculator {

    fun compute(recordings: List<RecordingSummary>, trendWindowSize: Int = 10): ExecutiveAnalytics {
        val totalHours = recordings.sumOf { it.durationMs } / 3_600_000.0
        val surahsRecorded = recordings.mapNotNull { it.surahNumber }.toSet().size

        val takesBySurah = recordings
            .filter { it.surahNumber != null && it.ayahStart != null && it.ayahEnd != null }
            .groupBy(
                keySelector = { it.surahNumber!! },
                valueTransform = { RecordedTake(AyahRange(it.ayahStart!!, it.ayahEnd!!), it.studioReadinessScore) },
            )
        val juzCompleted = (1..30).count { JuzProgressCalculator.compute(it, takesBySurah).isComplete }

        val scored = recordings.mapNotNull { it.studioReadinessScore }
        val averageQualityScore = if (scored.isEmpty()) null else scored.average()

        return ExecutiveAnalytics(
            totalRecordingHours = totalHours,
            surahsRecorded = surahsRecorded,
            juzCompleted = juzCompleted,
            averageQualityScore = averageQualityScore,
            improvementTrend = computeTrend(recordings, trendWindowSize),
            librarySize = recordings.size,
            totalStorageBytes = recordings.sumOf { it.fileSizeBytes },
        )
    }

    private fun computeTrend(recordings: List<RecordingSummary>, windowSize: Int): Double? {
        val sortedScored = recordings
            .filter { it.studioReadinessScore != null }
            .sortedBy { it.createdAtEpochMs }
        if (sortedScored.size < windowSize * 2) return null

        val recent = sortedScored.takeLast(windowSize).map { it.studioReadinessScore!! }.average()
        val previous = sortedScored.dropLast(windowSize).takeLast(windowSize).map { it.studioReadinessScore!! }.average()
        return recent - previous
    }
}
