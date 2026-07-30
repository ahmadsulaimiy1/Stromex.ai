package com.sajjil.core.speech

data class TranscriptSearchResult(
    val recordingId: Long,
    val segment: TranscriptSegment,
    /** Character offsets into `segment.text` for highlighting — null when only the diacritic-normalized form matched. */
    val matchRange: IntRange?,
)

/**
 * Searches transcript text, not just recording titles/notes — the payoff
 * for actually storing timed segments instead of one blob of text: a hit
 * carries the timestamp to jump playback to.
 *
 * Arabic search is diacritic-insensitive: harakat (tashkeel) are stripped
 * before matching, so a query typed without diacritics ("الرحمن") still
 * matches recognizer output that includes them ("الرَّحْمَن"), and vice
 * versa. This is plain Unicode range stripping, not language modeling.
 */
object TranscriptSearchEngine {

    fun search(transcripts: List<Transcript>, query: String): List<TranscriptSearchResult> {
        val needle = query.trim()
        if (needle.isEmpty()) return emptyList()
        val normalizedNeedle = normalize(needle)

        val results = mutableListOf<TranscriptSearchResult>()
        for (transcript in transcripts) {
            for (segment in transcript.segments) {
                val directIndex = segment.text.indexOf(needle, ignoreCase = true)
                if (directIndex >= 0) {
                    results.add(TranscriptSearchResult(transcript.recordingId, segment, directIndex until directIndex + needle.length))
                    continue
                }
                if (normalize(segment.text).contains(normalizedNeedle, ignoreCase = true)) {
                    results.add(TranscriptSearchResult(transcript.recordingId, segment, matchRange = null))
                }
            }
        }
        return results
    }

    /** Strips Arabic diacritics (harakat/tashkeel) and folds case for matching purposes only. */
    private fun normalize(text: String): String {
        val builder = StringBuilder(text.length)
        for (ch in text) {
            if (ch.code !in ARABIC_DIACRITIC_RANGES) builder.append(ch.lowercaseChar())
        }
        return builder.toString()
    }

    private val ARABIC_DIACRITIC_RANGES: Set<Int> = buildSet {
        addAll(0x064B..0x0655) // Arabic combining harakat (fatha, damma, kasra, shadda, sukun, etc.)
        add(0x0670) // superscript alef
        addAll(0x0610..0x061A) // Qur'anic annotation marks
        addAll(0x06D6..0x06DC) // small high marks used in Qur'anic text
        addAll(0x06DF..0x06E8)
        addAll(0x06EA..0x06ED)
    }
}
