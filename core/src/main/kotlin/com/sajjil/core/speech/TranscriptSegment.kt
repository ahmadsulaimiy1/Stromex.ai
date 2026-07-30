package com.sajjil.core.speech

enum class TranscriptLanguage(val bcp47: String, val displayName: String) {
    ARABIC("ar-SA", "Arabic"),
    ENGLISH("en-US", "English"),
}

/**
 * One timed piece of a transcript. `confidence` is whatever the recognizer
 * reported (0-1) — null when the engine didn't supply one. This is a data
 * carrier only; nothing here claims to *be* the recognizer.
 */
data class TranscriptSegment(
    val startMs: Long,
    val endMs: Long,
    val text: String,
    val confidence: Float? = null,
)

data class Transcript(
    val recordingId: Long,
    val language: TranscriptLanguage,
    val segments: List<TranscriptSegment>,
    val engineId: String,
) {
    val fullText: String get() = segments.joinToString(" ") { it.text }
}
