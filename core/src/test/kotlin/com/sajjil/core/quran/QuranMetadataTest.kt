package com.sajjil.core.quran

import kotlin.test.Test
import kotlin.test.assertEquals

class QuranMetadataTest {
    @Test
    fun `contains all 114 surahs numbered sequentially`() {
        assertEquals(114, QuranMetadata.surahs.size)
        QuranMetadata.surahs.forEachIndexed { index, surah -> assertEquals(index + 1, surah.number) }
    }

    @Test
    fun `Al-Fatihah has 7 ayahs and An-Nas has 6`() {
        assertEquals(7, QuranMetadata.surahByNumber(1).ayahCount)
        assertEquals(6, QuranMetadata.surahByNumber(114).ayahCount)
    }

    @Test
    fun `has 30 juz boundaries starting with juz 1 at 1 to 1`() {
        assertEquals(30, QuranMetadata.juzBoundaries.size)
        assertEquals(JuzBoundary(1, 1, 1), QuranMetadata.juzBoundaries.first())
    }

    @Test
    fun `juz lookup resolves a known reference point`() {
        // Juz 16 begins at Al-Kahf 18:75, so 18:74 is still Juz 15.
        assertEquals(15, QuranMetadata.juzForSurahAyah(18, 74))
        assertEquals(16, QuranMetadata.juzForSurahAyah(18, 75))
    }
}
