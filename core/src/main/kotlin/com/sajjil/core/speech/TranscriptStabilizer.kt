package com.sajjil.core.speech

data class StabilizedText(val stableText: String, val draftText: String) {
    val fullText: String
        get() = when {
            stableText.isEmpty() -> draftText
            draftText.isEmpty() -> stableText
            else -> "$stableText $draftText"
        }
}

/**
 * Turns a stream of successive partial-recognition hypotheses (each a
 * full replacement of "what the recognizer currently thinks was said,"
 * which is how `SpeechRecognizer.onPartialResults` delivers them — not a
 * delta) into a stable/draft split, so a live transcript view only has to
 * repaint the trailing tail instead of rewriting the whole line every
 * time the recognizer revises itself. Addresses "Smart Transcript
 * Stabilisation": the prefix promotes to stable once it has survived
 * unchanged across the last [windowSize] updates; the rest stays draft
 * and is expected to keep changing.
 *
 * Pure word-level history comparison — no recognizer- or
 * language-specific logic, and no claim of understanding the words
 * beyond comparing them as tokens.
 */
class TranscriptStabilizer(private val windowSize: Int = 3) {
    init {
        require(windowSize >= 1) { "windowSize must be >= 1, was $windowSize" }
    }

    private val history = ArrayDeque<List<String>>()

    /** Feed the next partial hypothesis. Returns the current stable/draft split. */
    fun update(partialText: String): StabilizedText {
        val words = tokenize(partialText)
        history.addLast(words)
        while (history.size > windowSize) history.removeFirst()

        val stableCount = if (history.size < windowSize) 0 else commonPrefixLength(history)
        return StabilizedText(
            stableText = words.take(stableCount).joinToString(" "),
            draftText = words.drop(stableCount).joinToString(" "),
        )
    }

    /** Call when the recognizer finalizes a result: the whole text becomes stable and history resets for the next utterance. */
    fun commitFinal(finalText: String): StabilizedText {
        history.clear()
        return StabilizedText(stableText = finalText.trim(), draftText = "")
    }

    /** Discards history without emitting a final result — e.g. the session was cancelled. */
    fun reset() {
        history.clear()
    }

    private fun tokenize(text: String): List<String> =
        text.trim().split(Regex("\\s+")).filter { it.isNotEmpty() }

    private fun commonPrefixLength(lists: List<List<String>>): Int {
        val shortest = lists.minOf { it.size }
        val reference = lists.first()
        var i = 0
        while (i < shortest && lists.all { it[i] == reference[i] }) i++
        return i
    }
}
