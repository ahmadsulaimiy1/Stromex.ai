package com.sajjil.core.assistant

enum class QualityComparison { BELOW, ABOVE }

/**
 * What the SAJJIL Assistant understood from a request — a closed, small
 * set of intents, not an open-ended representation of meaning. There is
 * no natural-language-understanding model behind this: see
 * [AssistantIntentParser] for what "understood" actually means here.
 */
sealed interface AssistantIntent {
    data class FindBySurah(val surahQuery: String) : AssistantIntent
    data class FindByKeyword(val keyword: String) : AssistantIntent
    data object ReadCurrentTranscript : AssistantIntent
    data class FilterByQuality(val comparison: QualityComparison, val threshold: Int) : AssistantIntent
    /** Nothing in the known pattern set matched — the caller should say so plainly rather than guess. */
    data class Unrecognized(val rawText: String) : AssistantIntent
}
