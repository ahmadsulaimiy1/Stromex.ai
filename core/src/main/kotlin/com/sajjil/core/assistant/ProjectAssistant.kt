package com.sajjil.core.assistant

import com.sajjil.core.analysis.ExecutiveAnalytics
import com.sajjil.core.quran.AyahRange
import com.sajjil.core.quran.JuzProgress
import com.sajjil.core.quran.SurahProgress
import kotlin.math.roundToInt

enum class InsightCategory { PROGRESS, QUALITY, RECOMMENDATION }

data class ProjectInsight(val category: InsightCategory, val message: String)

data class ProjectAssistantReport(val insights: List<ProjectInsight>)

/** One scored take, reduced to what take-level outlier detection needs — see [ProjectAssistant.analyzeTakeOutliers]. */
data class TakeQualitySample(
    val recordingId: Long,
    val title: String,
    val surahName: String? = null,
    val ayahRange: AyahRange? = null,
    val score: Int,
)

/**
 * The "Intelligent Project Assistant": turns numbers SAJJIL already
 * computes (SurahProgress, JuzProgress, ExecutiveAnalytics) into plain
 * sentences a Qari can act on — "112 Surahs recorded, 2 Juz and 15 Surahs
 * remaining, quality dipped in Al-Mulk, consider re-recording it."
 *
 * Every rule here is arithmetic over existing scores, not a model — no
 * insight is generated that isn't directly traceable to a number the
 * calling screen could otherwise have shown on its own.
 */
object ProjectAssistant {

    private const val QUALITY_DROP_THRESHOLD = 10.0
    private const val NEARLY_COMPLETE_JUZ_THRESHOLD = 80.0
    private const val TAKE_QUALITY_DROP_THRESHOLD = 15.0

    fun analyze(
        surahProgresses: List<SurahProgress>,
        juzProgresses: List<JuzProgress>,
        analytics: ExecutiveAnalytics,
    ): ProjectAssistantReport {
        val insights = mutableListOf<ProjectInsight>()

        if (surahProgresses.isEmpty() || analytics.librarySize == 0) {
            insights.add(
                ProjectInsight(
                    InsightCategory.PROGRESS,
                    "No recordings yet. Start with Surah Al-Fatihah to begin your Qur'an Production project.",
                ),
            )
            return ProjectAssistantReport(insights)
        }

        insights += progressInsight(surahProgresses, juzProgresses)
        trendInsight(analytics)?.let { insights.add(it) }
        insights += lowQualitySurahInsights(surahProgresses)
        insights += nearlyCompleteJuzInsights(juzProgresses)

        return ProjectAssistantReport(insights)
    }

    private fun progressInsight(surahProgresses: List<SurahProgress>, juzProgresses: List<JuzProgress>): ProjectInsight {
        val completeSurahs = surahProgresses.count { it.isComplete }
        val totalSurahs = surahProgresses.size
        val remainingSurahs = totalSurahs - completeSurahs
        val completeJuz = juzProgresses.count { it.isComplete }
        val remainingJuz = juzProgresses.size - completeJuz

        val remainderText = if (remainingSurahs == 0 && remainingJuz == 0) {
            "The whole set is complete."
        } else {
            "Remaining: $remainingJuz Juz and $remainingSurahs Surah(s)."
        }
        return ProjectInsight(
            InsightCategory.PROGRESS,
            "You have recorded $completeSurahs of $totalSurahs Surah(s). $remainderText",
        )
    }

    private fun trendInsight(analytics: ExecutiveAnalytics): ProjectInsight? {
        val trend = analytics.improvementTrend ?: return null
        val rounded = kotlin.math.abs(trend).roundToInt()
        return when {
            trend >= 1.0 -> ProjectInsight(
                InsightCategory.QUALITY,
                "Your recent recordings are trending $rounded point(s) higher in quality than your earlier sessions — keep it up.",
            )
            trend <= -1.0 -> ProjectInsight(
                InsightCategory.QUALITY,
                "Quality has dropped $rounded point(s) in your recent sessions — check your recording environment before continuing.",
            )
            else -> null
        }
    }

    /** Surahs whose average score sits well below the library average are worth a second take. */
    private fun lowQualitySurahInsights(surahProgresses: List<SurahProgress>): List<ProjectInsight> {
        val scored = surahProgresses.filter { it.averageQualityScore != null }
        if (scored.size < 2) return emptyList()
        val overallAverage = scored.map { it.averageQualityScore!! }.average()

        return scored
            .filter { overallAverage - it.averageQualityScore!! >= QUALITY_DROP_THRESHOLD }
            .sortedBy { it.averageQualityScore }
            .map {
                val score = it.averageQualityScore!!.roundToInt()
                val avg = overallAverage.roundToInt()
                ProjectInsight(
                    InsightCategory.RECOMMENDATION,
                    "Quality in Surah ${it.surah.transliteratedName} ($score) is below your average ($avg). Consider re-recording it.",
                )
            }
    }

    private fun nearlyCompleteJuzInsights(juzProgresses: List<JuzProgress>): List<ProjectInsight> =
        juzProgresses
            .filter { !it.isComplete && it.percentComplete >= NEARLY_COMPLETE_JUZ_THRESHOLD }
            .sortedByDescending { it.percentComplete }
            .map {
                val percent = it.percentComplete.roundToInt()
                ProjectInsight(
                    InsightCategory.RECOMMENDATION,
                    "Juz ${it.juzNumber} is $percent% complete — finish it to bank another completed Juz.",
                )
            }

    /**
     * Flags individual takes that score well below the project average —
     * finer-grained than [lowQualitySurahInsights], which only compares
     * Surah-level averages. A higher threshold than the Surah-level check
     * is used deliberately: a single take naturally varies more than a
     * Surah's ayah-weighted average of several takes, so a lower bar here
     * would flag normal variance as a problem.
     */
    fun analyzeTakeOutliers(samples: List<TakeQualitySample>): List<ProjectInsight> {
        if (samples.size < 2) return emptyList()
        val average = samples.map { it.score }.average()

        return samples
            .filter { average - it.score >= TAKE_QUALITY_DROP_THRESHOLD }
            .sortedBy { it.score }
            .map {
                val location = when {
                    it.surahName != null && it.ayahRange != null -> "${it.surahName} (Ayah ${it.ayahRange.start}-${it.ayahRange.end})"
                    it.surahName != null -> it.surahName
                    else -> "\"${it.title}\""
                }
                ProjectInsight(
                    InsightCategory.RECOMMENDATION,
                    "$location scored ${it.score}, well below your project average of ${average.roundToInt()} — consider re-recording it.",
                )
            }
    }
}
