package com.sajjil.core.quran

/** An inclusive 1-indexed ayah range within a single Surah. */
data class AyahRange(val start: Int, val end: Int) {
    init {
        require(start <= end) { "start ($start) must be <= end ($end)" }
    }

    val length: Int get() = end - start + 1

    fun overlaps(other: AyahRange): Boolean = start <= other.end && other.start <= end
}

/** One recorded take covering a range of ayahs, optionally scored (e.g. `studioReadinessScore`). */
data class RecordedTake(val ayahRange: AyahRange, val qualityScore: Int? = null)

data class SurahProgress(
    val surah: SurahInfo,
    val totalAyahs: Int,
    val coveredAyahs: Int,
    val percentComplete: Double,
    val missingRanges: List<AyahRange>,
    val averageQualityScore: Double?,
    val isComplete: Boolean,
)

/**
 * The Qur'an Production Suite's core algorithm: given every take recorded
 * so far for a Surah, work out exactly which ayahs are still missing —
 * "you've recorded 1-40 and 45-60, ayahs 41-44 and 61-88 are left" — rather
 * than making a Qari track that by hand across dozens of takes and
 * re-recordings.
 */
object SurahProgressCalculator {

    fun compute(surah: SurahInfo, takes: List<RecordedTake>): SurahProgress {
        val totalAyahs = surah.ayahCount
        val merged = mergeRanges(takes.map { it.ayahRange }, totalAyahs)
        val coveredAyahs = merged.sumOf { it.length }
        val missing = complement(merged, totalAyahs)

        val averageQualityScore = weightedAverageQuality(takes)

        return SurahProgress(
            surah = surah,
            totalAyahs = totalAyahs,
            coveredAyahs = coveredAyahs,
            percentComplete = if (totalAyahs == 0) 0.0 else 100.0 * coveredAyahs / totalAyahs,
            missingRanges = missing,
            averageQualityScore = averageQualityScore,
            isComplete = coveredAyahs >= totalAyahs,
        )
    }

    /** Merges overlapping or touching ranges, clipped to `[1, totalAyahs]`. */
    private fun mergeRanges(ranges: List<AyahRange>, totalAyahs: Int): List<AyahRange> {
        if (ranges.isEmpty()) return emptyList()
        val clipped = ranges
            .map { AyahRange(it.start.coerceIn(1, totalAyahs), it.end.coerceIn(1, totalAyahs)) }
            .sortedBy { it.start }

        val merged = mutableListOf<AyahRange>()
        var current = clipped.first()
        for (next in clipped.drop(1)) {
            current = if (next.start <= current.end + 1) {
                AyahRange(current.start, maxOf(current.end, next.end))
            } else {
                merged.add(current)
                next
            }
        }
        merged.add(current)
        return merged
    }

    private fun complement(merged: List<AyahRange>, totalAyahs: Int): List<AyahRange> {
        if (totalAyahs == 0) return emptyList()
        val gaps = mutableListOf<AyahRange>()
        var cursor = 1
        for (range in merged) {
            if (range.start > cursor) gaps.add(AyahRange(cursor, range.start - 1))
            cursor = range.end + 1
        }
        if (cursor <= totalAyahs) gaps.add(AyahRange(cursor, totalAyahs))
        return gaps
    }

    /** Ayah-count-weighted mean of scored takes, so a 2-ayah touch-up doesn't outweigh a 40-ayah take. */
    private fun weightedAverageQuality(takes: List<RecordedTake>): Double? {
        val scored = takes.filter { it.qualityScore != null }
        if (scored.isEmpty()) return null
        val totalWeight = scored.sumOf { it.ayahRange.length }
        if (totalWeight == 0) return null
        val weightedSum = scored.sumOf { it.qualityScore!! * it.ayahRange.length }
        return weightedSum.toDouble() / totalWeight
    }
}

data class JuzProgress(
    val juzNumber: Int,
    val segments: List<Pair<SurahInfo, AyahRange>>,
    val isComplete: Boolean,
    val percentComplete: Double,
)

/**
 * "Juz Completed" means every segment the Juz spans is fully recorded —
 * a Juz frequently starts partway through one Surah and ends partway
 * through another (see [QuranMetadata.juzSpan]), so this checks each
 * segment against that Surah's own recorded takes rather than treating
 * "some recording exists somewhere in this Juz" as completion.
 */
object JuzProgressCalculator {

    fun compute(juzNumber: Int, takesBySurah: Map<Int, List<RecordedTake>>): JuzProgress {
        val span = QuranMetadata.juzSpan(juzNumber)
        var totalAyahs = 0
        var coveredAyahs = 0
        val segmentInfo = mutableListOf<Pair<SurahInfo, AyahRange>>()

        for ((surahNumber, segmentRange) in span) {
            val surah = QuranMetadata.surahByNumber(surahNumber)
            segmentInfo.add(surah to segmentRange)
            totalAyahs += segmentRange.length

            val surahProgress = SurahProgressCalculator.compute(surah, takesBySurah[surahNumber].orEmpty())
            val uncoveredInSegment = surahProgress.missingRanges.filter { it.overlaps(segmentRange) }
            coveredAyahs += segmentRange.length - overlapLength(uncoveredInSegment, segmentRange)
        }

        val percent = if (totalAyahs == 0) 0.0 else 100.0 * coveredAyahs / totalAyahs
        return JuzProgress(juzNumber, segmentInfo, isComplete = coveredAyahs >= totalAyahs, percentComplete = percent)
    }

    private fun overlapLength(ranges: List<AyahRange>, within: AyahRange): Int =
        ranges.sumOf { (minOf(it.end, within.end) - maxOf(it.start, within.start) + 1).coerceAtLeast(0) }
}
