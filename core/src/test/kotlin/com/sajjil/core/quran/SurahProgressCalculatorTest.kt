package com.sajjil.core.quran

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class SurahProgressCalculatorTest {
    // Al-Fatihah: 7 ayahs. Al-Ikhlas: 4 ayahs. Good small surahs for exact arithmetic.
    private val fatihah = QuranMetadata.surahByNumber(1)
    private val ikhlas = QuranMetadata.surahByNumber(112)

    @Test
    fun `no takes means fully missing and zero percent`() {
        val progress = SurahProgressCalculator.compute(fatihah, emptyList())
        assertEquals(0, progress.coveredAyahs)
        assertEquals(0.0, progress.percentComplete)
        assertEquals(listOf(AyahRange(1, 7)), progress.missingRanges)
        assertFalse(progress.isComplete)
        assertEquals(null, progress.averageQualityScore)
    }

    @Test
    fun `full coverage in one take is complete`() {
        val progress = SurahProgressCalculator.compute(ikhlas, listOf(RecordedTake(AyahRange(1, 4), 90)))
        assertEquals(4, progress.coveredAyahs)
        assertEquals(100.0, progress.percentComplete)
        assertTrue(progress.missingRanges.isEmpty())
        assertTrue(progress.isComplete)
        assertEquals(90.0, progress.averageQualityScore)
    }

    @Test
    fun `gaps between disjoint takes are reported precisely`() {
        val takes = listOf(RecordedTake(AyahRange(1, 2)), RecordedTake(AyahRange(5, 7)))
        val progress = SurahProgressCalculator.compute(fatihah, takes)
        assertEquals(5, progress.coveredAyahs) // 1-2 (2) + 5-7 (3)
        assertEquals(listOf(AyahRange(3, 4)), progress.missingRanges)
        assertFalse(progress.isComplete)
    }

    @Test
    fun `overlapping and touching takes merge into one covered span`() {
        val takes = listOf(RecordedTake(AyahRange(1, 3)), RecordedTake(AyahRange(3, 5)), RecordedTake(AyahRange(6, 7)))
        val progress = SurahProgressCalculator.compute(fatihah, takes)
        assertEquals(7, progress.coveredAyahs)
        assertTrue(progress.missingRanges.isEmpty())
        assertTrue(progress.isComplete)
    }

    @Test
    fun `average quality is weighted by how many ayahs each take covers`() {
        // A 40-ayah take at 60 shouldn't be dragged down to 75 by a 2-ayah touch-up at 90 the same as an unweighted mean would.
        val surah40 = QuranMetadata.surahByNumber(32) // As-Sajdah, 30 ayahs — use a range within it
        val takes = listOf(
            RecordedTake(AyahRange(1, 28), qualityScore = 60),
            RecordedTake(AyahRange(29, 30), qualityScore = 90),
        )
        val progress = SurahProgressCalculator.compute(surah40, takes)
        val expected = (60.0 * 28 + 90.0 * 2) / 30.0
        assertEquals(expected, progress.averageQualityScore!!, 0.001)
    }

    @Test
    fun `out of range takes are clipped to the surah's actual ayah count`() {
        val takes = listOf(RecordedTake(AyahRange(1, 999)))
        val progress = SurahProgressCalculator.compute(ikhlas, takes)
        assertEquals(4, progress.coveredAyahs)
        assertTrue(progress.isComplete)
    }
}
