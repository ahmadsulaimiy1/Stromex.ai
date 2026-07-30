package com.sajjil.core.quran

enum class RevelationPlace { MECCAN, MEDINAN }

data class SurahInfo(
    val number: Int,
    val transliteratedName: String,
    val ayahCount: Int,
    val revelationPlace: RevelationPlace,
)

data class JuzBoundary(
    val juzNumber: Int,
    val startSurah: Int,
    val startAyah: Int,
)

/**
 * Static reference data for Qur'an Creator Suite organisation: Surah list
 * with ayah counts (standard Hafs riwayah numbering) and the 30 Juz start
 * boundaries, used to drive Surah/Ayah/Juz markers on the recitation
 * waveform and recitation library filing. Verify against a printed mushaf
 * before shipping to a Qur'an institution — this ships as a best-effort
 * reference dataset, not a religiously authoritative source.
 */
object QuranMetadata {

    val surahs: List<SurahInfo> = listOf(
        SurahInfo(1, "Al-Fatihah", 7, RevelationPlace.MECCAN),
        SurahInfo(2, "Al-Baqarah", 286, RevelationPlace.MEDINAN),
        SurahInfo(3, "Aal-E-Imran", 200, RevelationPlace.MEDINAN),
        SurahInfo(4, "An-Nisa", 176, RevelationPlace.MEDINAN),
        SurahInfo(5, "Al-Ma'idah", 120, RevelationPlace.MEDINAN),
        SurahInfo(6, "Al-An'am", 165, RevelationPlace.MECCAN),
        SurahInfo(7, "Al-A'raf", 206, RevelationPlace.MECCAN),
        SurahInfo(8, "Al-Anfal", 75, RevelationPlace.MEDINAN),
        SurahInfo(9, "At-Tawbah", 129, RevelationPlace.MEDINAN),
        SurahInfo(10, "Yunus", 109, RevelationPlace.MECCAN),
        SurahInfo(11, "Hud", 123, RevelationPlace.MECCAN),
        SurahInfo(12, "Yusuf", 111, RevelationPlace.MECCAN),
        SurahInfo(13, "Ar-Ra'd", 43, RevelationPlace.MEDINAN),
        SurahInfo(14, "Ibrahim", 52, RevelationPlace.MECCAN),
        SurahInfo(15, "Al-Hijr", 99, RevelationPlace.MECCAN),
        SurahInfo(16, "An-Nahl", 128, RevelationPlace.MECCAN),
        SurahInfo(17, "Al-Isra", 111, RevelationPlace.MECCAN),
        SurahInfo(18, "Al-Kahf", 110, RevelationPlace.MECCAN),
        SurahInfo(19, "Maryam", 98, RevelationPlace.MECCAN),
        SurahInfo(20, "Ta-Ha", 135, RevelationPlace.MECCAN),
        SurahInfo(21, "Al-Anbiya", 112, RevelationPlace.MECCAN),
        SurahInfo(22, "Al-Hajj", 78, RevelationPlace.MEDINAN),
        SurahInfo(23, "Al-Mu'minun", 118, RevelationPlace.MECCAN),
        SurahInfo(24, "An-Nur", 64, RevelationPlace.MEDINAN),
        SurahInfo(25, "Al-Furqan", 77, RevelationPlace.MECCAN),
        SurahInfo(26, "Ash-Shu'ara", 227, RevelationPlace.MECCAN),
        SurahInfo(27, "An-Naml", 93, RevelationPlace.MECCAN),
        SurahInfo(28, "Al-Qasas", 88, RevelationPlace.MECCAN),
        SurahInfo(29, "Al-Ankabut", 69, RevelationPlace.MECCAN),
        SurahInfo(30, "Ar-Rum", 60, RevelationPlace.MECCAN),
        SurahInfo(31, "Luqman", 34, RevelationPlace.MECCAN),
        SurahInfo(32, "As-Sajdah", 30, RevelationPlace.MECCAN),
        SurahInfo(33, "Al-Ahzab", 73, RevelationPlace.MEDINAN),
        SurahInfo(34, "Saba", 54, RevelationPlace.MECCAN),
        SurahInfo(35, "Fatir", 45, RevelationPlace.MECCAN),
        SurahInfo(36, "Ya-Sin", 83, RevelationPlace.MECCAN),
        SurahInfo(37, "As-Saffat", 182, RevelationPlace.MECCAN),
        SurahInfo(38, "Sad", 88, RevelationPlace.MECCAN),
        SurahInfo(39, "Az-Zumar", 75, RevelationPlace.MECCAN),
        SurahInfo(40, "Ghafir", 85, RevelationPlace.MECCAN),
        SurahInfo(41, "Fussilat", 54, RevelationPlace.MECCAN),
        SurahInfo(42, "Ash-Shura", 53, RevelationPlace.MECCAN),
        SurahInfo(43, "Az-Zukhruf", 89, RevelationPlace.MECCAN),
        SurahInfo(44, "Ad-Dukhan", 59, RevelationPlace.MECCAN),
        SurahInfo(45, "Al-Jathiyah", 37, RevelationPlace.MECCAN),
        SurahInfo(46, "Al-Ahqaf", 35, RevelationPlace.MECCAN),
        SurahInfo(47, "Muhammad", 38, RevelationPlace.MEDINAN),
        SurahInfo(48, "Al-Fath", 29, RevelationPlace.MEDINAN),
        SurahInfo(49, "Al-Hujurat", 18, RevelationPlace.MEDINAN),
        SurahInfo(50, "Qaf", 45, RevelationPlace.MECCAN),
        SurahInfo(51, "Adh-Dhariyat", 60, RevelationPlace.MECCAN),
        SurahInfo(52, "At-Tur", 49, RevelationPlace.MECCAN),
        SurahInfo(53, "An-Najm", 62, RevelationPlace.MECCAN),
        SurahInfo(54, "Al-Qamar", 55, RevelationPlace.MECCAN),
        SurahInfo(55, "Ar-Rahman", 78, RevelationPlace.MEDINAN),
        SurahInfo(56, "Al-Waqi'ah", 96, RevelationPlace.MECCAN),
        SurahInfo(57, "Al-Hadid", 29, RevelationPlace.MEDINAN),
        SurahInfo(58, "Al-Mujadilah", 22, RevelationPlace.MEDINAN),
        SurahInfo(59, "Al-Hashr", 24, RevelationPlace.MEDINAN),
        SurahInfo(60, "Al-Mumtahanah", 13, RevelationPlace.MEDINAN),
        SurahInfo(61, "As-Saf", 14, RevelationPlace.MEDINAN),
        SurahInfo(62, "Al-Jumu'ah", 11, RevelationPlace.MEDINAN),
        SurahInfo(63, "Al-Munafiqun", 11, RevelationPlace.MEDINAN),
        SurahInfo(64, "At-Taghabun", 18, RevelationPlace.MEDINAN),
        SurahInfo(65, "At-Talaq", 12, RevelationPlace.MEDINAN),
        SurahInfo(66, "At-Tahrim", 12, RevelationPlace.MEDINAN),
        SurahInfo(67, "Al-Mulk", 30, RevelationPlace.MECCAN),
        SurahInfo(68, "Al-Qalam", 52, RevelationPlace.MECCAN),
        SurahInfo(69, "Al-Haqqah", 52, RevelationPlace.MECCAN),
        SurahInfo(70, "Al-Ma'arij", 44, RevelationPlace.MECCAN),
        SurahInfo(71, "Nuh", 28, RevelationPlace.MECCAN),
        SurahInfo(72, "Al-Jinn", 28, RevelationPlace.MECCAN),
        SurahInfo(73, "Al-Muzzammil", 20, RevelationPlace.MECCAN),
        SurahInfo(74, "Al-Muddaththir", 56, RevelationPlace.MECCAN),
        SurahInfo(75, "Al-Qiyamah", 40, RevelationPlace.MECCAN),
        SurahInfo(76, "Al-Insan", 31, RevelationPlace.MEDINAN),
        SurahInfo(77, "Al-Mursalat", 50, RevelationPlace.MECCAN),
        SurahInfo(78, "An-Naba", 40, RevelationPlace.MECCAN),
        SurahInfo(79, "An-Nazi'at", 46, RevelationPlace.MECCAN),
        SurahInfo(80, "Abasa", 42, RevelationPlace.MECCAN),
        SurahInfo(81, "At-Takwir", 29, RevelationPlace.MECCAN),
        SurahInfo(82, "Al-Infitar", 19, RevelationPlace.MECCAN),
        SurahInfo(83, "Al-Mutaffifin", 36, RevelationPlace.MECCAN),
        SurahInfo(84, "Al-Inshiqaq", 25, RevelationPlace.MECCAN),
        SurahInfo(85, "Al-Buruj", 22, RevelationPlace.MECCAN),
        SurahInfo(86, "At-Tariq", 17, RevelationPlace.MECCAN),
        SurahInfo(87, "Al-A'la", 19, RevelationPlace.MECCAN),
        SurahInfo(88, "Al-Ghashiyah", 26, RevelationPlace.MECCAN),
        SurahInfo(89, "Al-Fajr", 30, RevelationPlace.MECCAN),
        SurahInfo(90, "Al-Balad", 20, RevelationPlace.MECCAN),
        SurahInfo(91, "Ash-Shams", 15, RevelationPlace.MECCAN),
        SurahInfo(92, "Al-Layl", 21, RevelationPlace.MECCAN),
        SurahInfo(93, "Ad-Duha", 11, RevelationPlace.MECCAN),
        SurahInfo(94, "Ash-Sharh", 8, RevelationPlace.MECCAN),
        SurahInfo(95, "At-Tin", 8, RevelationPlace.MECCAN),
        SurahInfo(96, "Al-Alaq", 19, RevelationPlace.MECCAN),
        SurahInfo(97, "Al-Qadr", 5, RevelationPlace.MECCAN),
        SurahInfo(98, "Al-Bayyinah", 8, RevelationPlace.MEDINAN),
        SurahInfo(99, "Az-Zalzalah", 8, RevelationPlace.MEDINAN),
        SurahInfo(100, "Al-Adiyat", 11, RevelationPlace.MECCAN),
        SurahInfo(101, "Al-Qari'ah", 11, RevelationPlace.MECCAN),
        SurahInfo(102, "At-Takathur", 8, RevelationPlace.MECCAN),
        SurahInfo(103, "Al-Asr", 3, RevelationPlace.MECCAN),
        SurahInfo(104, "Al-Humazah", 9, RevelationPlace.MECCAN),
        SurahInfo(105, "Al-Fil", 5, RevelationPlace.MECCAN),
        SurahInfo(106, "Quraysh", 4, RevelationPlace.MECCAN),
        SurahInfo(107, "Al-Ma'un", 7, RevelationPlace.MECCAN),
        SurahInfo(108, "Al-Kawthar", 3, RevelationPlace.MECCAN),
        SurahInfo(109, "Al-Kafirun", 6, RevelationPlace.MECCAN),
        SurahInfo(110, "An-Nasr", 3, RevelationPlace.MEDINAN),
        SurahInfo(111, "Al-Masad", 5, RevelationPlace.MECCAN),
        SurahInfo(112, "Al-Ikhlas", 4, RevelationPlace.MECCAN),
        SurahInfo(113, "Al-Falaq", 5, RevelationPlace.MECCAN),
        SurahInfo(114, "An-Nas", 6, RevelationPlace.MECCAN),
    )

    val juzBoundaries: List<JuzBoundary> = listOf(
        JuzBoundary(1, 1, 1), JuzBoundary(2, 2, 142), JuzBoundary(3, 2, 253),
        JuzBoundary(4, 3, 93), JuzBoundary(5, 4, 24), JuzBoundary(6, 4, 148),
        JuzBoundary(7, 5, 82), JuzBoundary(8, 6, 111), JuzBoundary(9, 7, 88),
        JuzBoundary(10, 8, 41), JuzBoundary(11, 9, 93), JuzBoundary(12, 11, 6),
        JuzBoundary(13, 12, 53), JuzBoundary(14, 15, 1), JuzBoundary(15, 17, 1),
        JuzBoundary(16, 18, 75), JuzBoundary(17, 21, 1), JuzBoundary(18, 23, 1),
        JuzBoundary(19, 25, 21), JuzBoundary(20, 27, 56), JuzBoundary(21, 29, 46),
        JuzBoundary(22, 33, 31), JuzBoundary(23, 36, 28), JuzBoundary(24, 39, 32),
        JuzBoundary(25, 41, 47), JuzBoundary(26, 46, 1), JuzBoundary(27, 51, 31),
        JuzBoundary(28, 58, 1), JuzBoundary(29, 67, 1), JuzBoundary(30, 78, 1),
    )

    fun surahByNumber(number: Int): SurahInfo = surahs.first { it.number == number }

    fun juzForSurahAyah(surah: Int, ayah: Int): Int {
        var result = 1
        for (boundary in juzBoundaries) {
            if (boundary.startSurah < surah || (boundary.startSurah == surah && boundary.startAyah <= ayah)) {
                result = boundary.juzNumber
            }
        }
        return result
    }

    /**
     * The Surah/ayah-range segments a Juz spans — a Juz frequently starts
     * partway through one Surah and ends partway through (or exactly at
     * the end of) another, so "Juz N complete" means every one of these
     * segments is fully recorded, not just "some recording exists in Juz N."
     */
    fun juzSpan(juzNumber: Int): List<Pair<Int, AyahRange>> {
        require(juzNumber in 1..30) { "Juz number must be 1-30, got $juzNumber" }
        val start = juzBoundaries[juzNumber - 1]
        val endExclusive = juzBoundaries.getOrNull(juzNumber) // null for Juz 30 -> runs to the end of the Qur'an

        val segments = mutableListOf<Pair<Int, AyahRange>>()
        var surahNumber = start.startSurah
        var ayahCursor = start.startAyah
        while (endExclusive == null || surahNumber < endExclusive.startSurah) {
            val surahAyahCount = surahByNumber(surahNumber).ayahCount
            segments.add(surahNumber to AyahRange(ayahCursor, surahAyahCount))
            surahNumber += 1
            ayahCursor = 1
            if (surahNumber > 114) break
        }
        if (endExclusive != null && surahNumber == endExclusive.startSurah && endExclusive.startAyah > 1) {
            segments.add(surahNumber to AyahRange(ayahCursor, endExclusive.startAyah - 1))
        }
        return segments
    }
}
