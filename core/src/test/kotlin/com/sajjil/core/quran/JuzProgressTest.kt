package com.sajjil.core.quran

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class JuzProgressTest {

    @Test
    fun `Juz 1 spans Al-Fatihah entirely and Al-Baqarah up to the Juz 2 boundary`() {
        val span = QuranMetadata.juzSpan(1)
        assertEquals(listOf(1 to AyahRange(1, 7), 2 to AyahRange(1, 141)), span)
    }

    @Test
    fun `a Juz that starts and ends within a single Surah produces one segment`() {
        // Juz 2 starts at Baqarah 142, Juz 3 starts at Baqarah 253 — both inside Surah 2.
        val span = QuranMetadata.juzSpan(2)
        assertEquals(listOf(2 to AyahRange(142, 252)), span)
    }

    @Test
    fun `Juz 30 runs from An-Naba to the end of the Qur'an with no surah skipped`() {
        val span = QuranMetadata.juzSpan(30)
        assertEquals(78, span.first().first)
        assertEquals(1, span.first().second.start)
        assertEquals(114, span.last().first)
        assertEquals(6, span.last().second.end) // An-Nas has 6 ayahs
        // Every Surah from 78 to 114 must appear, each in order, none skipped.
        assertEquals((78..114).toList(), span.map { it.first })
    }

    @Test
    fun `every Juz's span is internally contiguous with no gaps or overlaps`() {
        for (juz in 1..30) {
            val span = QuranMetadata.juzSpan(juz)
            assertTrue(span.isNotEmpty(), "Juz $juz produced no segments")
            for (i in 1 until span.size) {
                val (prevSurah, prevRange) = span[i - 1]
                val (surah, range) = span[i]
                assertEquals(prevSurah + 1, surah, "Juz $juz segment $i should follow directly after the previous surah")
                assertEquals(1, range.start, "Juz $juz segment $i should start at ayah 1 of surah $surah")
                assertTrue(prevRange.end == QuranMetadata.surahByNumber(prevSurah).ayahCount, "Juz $juz should consume all of surah $prevSurah before moving on")
            }
        }
    }

    @Test
    fun `consecutive Juz boundaries are seamless across the whole Qur'an`() {
        for (juz in 1 until 30) {
            val thisSpan = QuranMetadata.juzSpan(juz)
            val nextSpan = QuranMetadata.juzSpan(juz + 1)
            val (lastSurah, lastRange) = thisSpan.last()
            val (nextSurah, nextRange) = nextSpan.first()
            if (lastSurah == nextSurah) {
                assertEquals(lastRange.end + 1, nextRange.start, "Juz $juz -> ${juz + 1} should not skip or repeat an ayah within surah $lastSurah")
            } else {
                assertEquals(lastSurah + 1, nextSurah, "Juz $juz -> ${juz + 1} should move to the very next surah")
                assertEquals(QuranMetadata.surahByNumber(lastSurah).ayahCount, lastRange.end, "Juz $juz should end exactly at the last ayah of surah $lastSurah")
                assertEquals(1, nextRange.start, "Juz ${juz + 1} should start at ayah 1 of surah $nextSurah")
            }
        }
    }

    @Test
    fun `a Juz is complete only when every one of its segments is fully recorded`() {
        // Juz 2: Al-Baqarah 142-252 only.
        val fullTakes = mapOf(2 to listOf(RecordedTake(AyahRange(142, 252), qualityScore = 80)))
        val complete = JuzProgressCalculator.compute(2, fullTakes)
        assertTrue(complete.isComplete)
        assertEquals(100.0, complete.percentComplete)

        val partialTakes = mapOf(2 to listOf(RecordedTake(AyahRange(142, 200), qualityScore = 80)))
        val partial = JuzProgressCalculator.compute(2, partialTakes)
        assertFalse(partial.isComplete)
        assertTrue(partial.percentComplete in 1.0..99.0)
    }

    @Test
    fun `a multi-surah Juz needs every segment covered, not just one`() {
        // Juz 1: Al-Fatihah (1-7) + Al-Baqarah (1-141).
        val onlyFatihah = mapOf(1 to listOf(RecordedTake(AyahRange(1, 7))))
        val progress = JuzProgressCalculator.compute(1, onlyFatihah)
        assertFalse(progress.isComplete, "recording only Al-Fatihah should not complete Juz 1")

        val both = mapOf(
            1 to listOf(RecordedTake(AyahRange(1, 7))),
            2 to listOf(RecordedTake(AyahRange(1, 141))),
        )
        assertTrue(JuzProgressCalculator.compute(1, both).isComplete)
    }

    @Test
    fun `no recordings at all means zero percent and not complete`() {
        val progress = JuzProgressCalculator.compute(15, emptyMap())
        assertFalse(progress.isComplete)
        assertEquals(0.0, progress.percentComplete)
    }
}
