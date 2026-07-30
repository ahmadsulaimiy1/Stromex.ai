package com.sajjil.core.assistant

/**
 * Turns a typed or spoken request into an [AssistantIntent] by matching a
 * fixed set of keyword/regex patterns — **not** natural-language
 * understanding, not an LLM, not a model of any kind. This is the same
 * honesty line the rest of SAJJIL holds: it is useful for the phrasings
 * it recognizes and says so plainly (`Unrecognized`) for anything else,
 * rather than guessing and presenting a wrong guess as understanding.
 *
 * The pattern set is intentionally small and covers the four request
 * shapes the Phase 5 directive gave as examples: find recordings by
 * Surah, find recordings/transcripts by topic, read the current
 * transcript aloud, and filter the library by quality.
 */
object AssistantIntentParser {

    private const val DEFAULT_LOW_QUALITY_THRESHOLD = 60
    private const val DEFAULT_HIGH_QUALITY_THRESHOLD = 80

    private val READ_WORD = Regex("""\bread\b""", RegexOption.IGNORE_CASE)
    private val TRANSCRIPT_CONTEXT = Regex("""\b(transcript|this|it)\b""", RegexOption.IGNORE_CASE)
    private val SURAH_PATTERN = Regex("""surah\s+([a-zA-Z][a-zA-Z'-]*)""", RegexOption.IGNORE_CASE)
    private val DISCUSS_PATTERN = Regex(
        """(?:discussed|discuss|talked about|mentioned|explained|about)\s+(.+)""",
        RegexOption.IGNORE_CASE,
    )
    private val QUALITY_WORD = Regex("""\bquality\b""", RegexOption.IGNORE_CASE)
    private val POOR_QUALITY_WORDS = listOf("poor", "bad", "low", "worst", "weak")
    private val GOOD_QUALITY_WORDS = listOf("good", "high", "best", "great", "strong")
    private val FIND_TRIGGERS = listOf("search for", "show me", "look for", "look up", "find", "search")
    private val FILLER_WORDS = setOf("me", "the", "my", "a", "an", "recordings", "recording", "recitations", "recitation")

    fun parse(text: String): AssistantIntent {
        val trimmed = text.trim()
        if (trimmed.isEmpty()) return AssistantIntent.Unrecognized(trimmed)
        val lower = trimmed.lowercase()

        if (READ_WORD.containsMatchIn(lower) && TRANSCRIPT_CONTEXT.containsMatchIn(lower)) {
            return AssistantIntent.ReadCurrentTranscript
        }

        if (QUALITY_WORD.containsMatchIn(lower)) {
            if (POOR_QUALITY_WORDS.any { lower.contains(it) }) {
                return AssistantIntent.FilterByQuality(QualityComparison.BELOW, DEFAULT_LOW_QUALITY_THRESHOLD)
            }
            if (GOOD_QUALITY_WORDS.any { lower.contains(it) }) {
                return AssistantIntent.FilterByQuality(QualityComparison.ABOVE, DEFAULT_HIGH_QUALITY_THRESHOLD)
            }
        }

        SURAH_PATTERN.find(trimmed)?.let { match ->
            return AssistantIntent.FindBySurah(match.groupValues[1].trim())
        }

        DISCUSS_PATTERN.find(trimmed)?.let { match ->
            val keyword = cleanKeyword(match.groupValues[1])
            if (keyword.isNotBlank()) return AssistantIntent.FindByKeyword(keyword)
        }

        val trigger = FIND_TRIGGERS.firstOrNull { lower.contains(it) }
        if (trigger != null) {
            val index = lower.indexOf(trigger)
            val keyword = cleanKeyword(trimmed.substring(index + trigger.length))
            if (keyword.isNotBlank()) return AssistantIntent.FindByKeyword(keyword)
        }

        return AssistantIntent.Unrecognized(trimmed)
    }

    private fun cleanKeyword(raw: String): String {
        val words = raw.trim().trim('.', '?', '!').split(Regex("\\s+")).filter { it.isNotBlank() }
        return words.filter { it.lowercase() !in FILLER_WORDS }.joinToString(" ").trim()
    }
}
