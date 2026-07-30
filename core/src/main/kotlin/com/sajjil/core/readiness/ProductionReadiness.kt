package com.sajjil.core.readiness

import com.sajjil.core.quran.AyahRange
import com.sajjil.core.quran.RecordedTake
import com.sajjil.core.quran.SurahInfo
import com.sajjil.core.quran.SurahProgressCalculator
import kotlin.math.roundToInt
import kotlin.math.sqrt

/** A single take reduced to what Production Readiness needs — no Room/Android dependency. */
data class ReadinessTake(
    val recordingId: Long,
    val title: String,
    val surahNumber: Int?,
    val ayahRange: AyahRange?,
    val hasClipping: Boolean,
    val noiseScore: Int? = null,
    val integratedLoudnessLufs: Double? = null,
    val isPrimaryVersion: Boolean = true,
)

enum class ReadinessSeverity { INFO, WARNING, CRITICAL }

data class ReadinessIssue(
    val severity: ReadinessSeverity,
    val category: String,
    val message: String,
)

data class ProductionReadinessReport(
    val score: Int,
    val totalAyahs: Int,
    val coveredAyahs: Int,
    val percentComplete: Double,
    val issues: List<ReadinessIssue>,
) {
    val label: String get() = "Production Readiness: $score/100"
}

/**
 * Turns a set of recorded takes for a project (one Surah, a handful of
 * Surahs, a Juz, or the whole Qur'an — the caller decides the scope by
 * what it passes in) into a single readiness score plus a checklist of
 * concrete problems, instead of leaving a Qari to eyeball a file list for
 * gaps, clipping, or a stray duplicate before publishing.
 *
 * This is a heuristic aggregator over data already computed elsewhere
 * (SurahProgressCalculator for coverage, AudioQualityScorer's outputs fed
 * in as noiseScore/hasClipping) — it does not re-analyze audio itself.
 */
object ProductionReadinessCalculator {

    private const val CRITICAL_PENALTY = 15
    private const val WARNING_PENALTY = 5
    private const val LOW_NOISE_SCORE_THRESHOLD = 50
    private const val LOUDNESS_INCONSISTENCY_STDDEV_LUFS = 3.0

    fun evaluate(surahs: List<SurahInfo>, takes: List<ReadinessTake>): ProductionReadinessReport {
        val takesBySurah = takes.filter { it.surahNumber != null }.groupBy { it.surahNumber!! }

        var totalAyahs = 0
        var coveredAyahs = 0
        val issues = mutableListOf<ReadinessIssue>()

        for (surah in surahs) {
            val surahTakes = takesBySurah[surah.number].orEmpty()
            val recordedTakes = surahTakes
                .filter { it.ayahRange != null }
                .map { RecordedTake(it.ayahRange!!, qualityScore = null) }
            val progress = SurahProgressCalculator.compute(surah, recordedTakes)
            totalAyahs += progress.totalAyahs
            coveredAyahs += progress.coveredAyahs

            if (!progress.isComplete) {
                val missingCount = progress.totalAyahs - progress.coveredAyahs
                issues.add(
                    ReadinessIssue(
                        severity = ReadinessSeverity.CRITICAL,
                        category = "Missing Ayat",
                        message = "${surah.transliteratedName}: $missingCount ayah(s) not yet recorded (${progress.missingRanges.joinToString { "${it.start}-${it.end}" }}).",
                    ),
                )
            }

            issues += findOverlapIssues(surah, surahTakes)
        }

        issues += findClippingIssues(takes)
        issues += findNoiseIssues(takes)
        issues += findLoudnessConsistencyIssue(takes)
        issues += findMetadataIssues(takes)
        issues += findNamingCollisionIssues(takes)

        val percentComplete = if (totalAyahs == 0) 0.0 else 100.0 * coveredAyahs / totalAyahs
        val penalty = issues.sumOf {
            when (it.severity) {
                ReadinessSeverity.CRITICAL -> CRITICAL_PENALTY
                ReadinessSeverity.WARNING -> WARNING_PENALTY
                ReadinessSeverity.INFO -> 0
            }
        }
        // Missing-ayah issues are CRITICAL and already drag percentComplete down;
        // don't double-penalize coverage gaps on top of the score they already cost.
        val missingAyahIssueCount = issues.count { it.category == "Missing Ayat" }
        val nonCoveragePenalty = penalty - missingAyahIssueCount * CRITICAL_PENALTY
        val score = (percentComplete.roundToInt() - nonCoveragePenalty).coerceIn(0, 100)

        return ProductionReadinessReport(
            score = score,
            totalAyahs = totalAyahs,
            coveredAyahs = coveredAyahs,
            percentComplete = percentComplete,
            issues = issues,
        )
    }

    /** Two takes on the same Surah whose ayah ranges overlap — likely an accidental duplicate recording. */
    private fun findOverlapIssues(surah: SurahInfo, surahTakes: List<ReadinessTake>): List<ReadinessIssue> {
        val ranged = surahTakes.filter { it.ayahRange != null }
        val issues = mutableListOf<ReadinessIssue>()
        for (i in ranged.indices) {
            for (j in i + 1 until ranged.size) {
                val a = ranged[i]
                val b = ranged[j]
                if (a.ayahRange!!.overlaps(b.ayahRange!!)) {
                    issues.add(
                        ReadinessIssue(
                            severity = ReadinessSeverity.WARNING,
                            category = "Possible Duplicate",
                            message = "${surah.transliteratedName}: \"${a.title}\" and \"${b.title}\" both cover overlapping ayahs — review before publishing.",
                        ),
                    )
                }
            }
        }
        return issues
    }

    private fun findClippingIssues(takes: List<ReadinessTake>): List<ReadinessIssue> =
        takes.filter { it.hasClipping }.map {
            ReadinessIssue(
                severity = ReadinessSeverity.CRITICAL,
                category = "Clipping",
                message = "\"${it.title}\" contains clipped audio — re-record or repair before publishing.",
            )
        }

    private fun findNoiseIssues(takes: List<ReadinessTake>): List<ReadinessIssue> =
        takes.filter { it.noiseScore != null && it.noiseScore < LOW_NOISE_SCORE_THRESHOLD }.map {
            ReadinessIssue(
                severity = ReadinessSeverity.WARNING,
                category = "Noise",
                message = "\"${it.title}\" has a low noise score (${it.noiseScore}/100) — consider re-recording in a quieter space.",
            )
        }

    /** Flags when loudness varies a lot across takes, which reads as jarring in a published sequence. */
    private fun findLoudnessConsistencyIssue(takes: List<ReadinessTake>): List<ReadinessIssue> {
        val values = takes.mapNotNull { it.integratedLoudnessLufs }
        if (values.size < 2) return emptyList()
        val mean = values.average()
        val variance = values.sumOf { (it - mean) * (it - mean) } / values.size
        val stddev = sqrt(variance)
        if (stddev <= LOUDNESS_INCONSISTENCY_STDDEV_LUFS) return emptyList()
        return listOf(
            ReadinessIssue(
                severity = ReadinessSeverity.WARNING,
                category = "Loudness Consistency",
                message = "Loudness varies by ${"%.1f".format(stddev)} LUFS across takes — run Adaptive Mastering or normalize before publishing.",
            ),
        )
    }

    private fun findMetadataIssues(takes: List<ReadinessTake>): List<ReadinessIssue> {
        val issues = mutableListOf<ReadinessIssue>()
        for (take in takes) {
            if (take.title.isBlank()) {
                issues.add(ReadinessIssue(ReadinessSeverity.WARNING, "Metadata", "Recording ${take.recordingId} has no title."))
            }
            if (take.surahNumber == null || take.ayahRange == null) {
                issues.add(ReadinessIssue(ReadinessSeverity.WARNING, "Metadata", "\"${take.title}\" is missing Surah/ayah tagging."))
            }
        }
        return issues
    }

    /** Two different recordings sharing an identical title is almost always a copy-paste rename mistake. */
    private fun findNamingCollisionIssues(takes: List<ReadinessTake>): List<ReadinessIssue> {
        val duplicateTitles = takes
            .filter { it.title.isNotBlank() }
            .groupBy { it.title }
            .filter { (_, group) -> group.size > 1 && group.map { it.recordingId }.toSet().size > 1 }

        return duplicateTitles.map { (title, group) ->
            ReadinessIssue(
                severity = ReadinessSeverity.INFO,
                category = "Naming Consistency",
                message = "\"$title\" is used by ${group.size} different recordings — rename to avoid confusion.",
            )
        }
    }
}
