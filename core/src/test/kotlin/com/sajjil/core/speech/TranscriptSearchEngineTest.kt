package com.sajjil.core.speech

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull
import kotlin.test.assertTrue

class TranscriptSearchEngineTest {

    private fun segment(text: String, startMs: Long = 0, endMs: Long = 1000) =
        TranscriptSegment(startMs = startMs, endMs = endMs, text = text)

    @Test
    fun `direct substring match returns a match range`() {
        val transcript = Transcript(
            recordingId = 1L,
            language = TranscriptLanguage.ENGLISH,
            segments = listOf(segment("In the name of the Most Merciful")),
            engineId = "test",
        )

        val results = TranscriptSearchEngine.search(listOf(transcript), "Merciful")

        assertEquals(1, results.size)
        val result = results.first()
        assertEquals(1L, result.recordingId)
        assertEquals(24 until 32, result.matchRange)
    }

    @Test
    fun `match is case insensitive`() {
        val transcript = Transcript(
            recordingId = 2L,
            language = TranscriptLanguage.ENGLISH,
            segments = listOf(segment("Bismillah Al-Rahman Al-Raheem")),
            engineId = "test",
        )

        val results = TranscriptSearchEngine.search(listOf(transcript), "rahman")

        assertEquals(1, results.size)
        assertTrue(results.first().matchRange != null)
    }

    @Test
    fun `arabic query without diacritics matches segment text with diacritics`() {
        val transcript = Transcript(
            recordingId = 3L,
            language = TranscriptLanguage.ARABIC,
            segments = listOf(segment("الرَّحْمَن الرَّحِيم")),
            engineId = "test",
        )

        val results = TranscriptSearchEngine.search(listOf(transcript), "الرحمن")

        assertEquals(1, results.size)
        assertNull(results.first().matchRange)
    }

    @Test
    fun `arabic query with diacritics matches segment text without diacritics`() {
        val transcript = Transcript(
            recordingId = 4L,
            language = TranscriptLanguage.ARABIC,
            segments = listOf(segment("بسم الله الرحمن الرحيم")),
            engineId = "test",
        )

        val results = TranscriptSearchEngine.search(listOf(transcript), "الرَّحْمَن")

        assertEquals(1, results.size)
        assertNull(results.first().matchRange)
    }

    @Test
    fun `direct match is preferred over normalized-only match when both would apply`() {
        val transcript = Transcript(
            recordingId = 5L,
            language = TranscriptLanguage.ARABIC,
            segments = listOf(segment("الرحمن الرحيم")),
            engineId = "test",
        )

        val results = TranscriptSearchEngine.search(listOf(transcript), "الرحمن")

        assertEquals(1, results.size)
        assertTrue(results.first().matchRange != null)
    }

    @Test
    fun `blank query returns no results`() {
        val transcript = Transcript(
            recordingId = 6L,
            language = TranscriptLanguage.ENGLISH,
            segments = listOf(segment("Some lecture content")),
            engineId = "test",
        )

        assertTrue(TranscriptSearchEngine.search(listOf(transcript), "").isEmpty())
        assertTrue(TranscriptSearchEngine.search(listOf(transcript), "   ").isEmpty())
    }

    @Test
    fun `no match returns empty list`() {
        val transcript = Transcript(
            recordingId = 7L,
            language = TranscriptLanguage.ENGLISH,
            segments = listOf(segment("Some lecture content")),
            engineId = "test",
        )

        assertTrue(TranscriptSearchEngine.search(listOf(transcript), "nonexistent").isEmpty())
    }

    @Test
    fun `search spans multiple transcripts and segments`() {
        val transcripts = listOf(
            Transcript(
                recordingId = 8L,
                language = TranscriptLanguage.ENGLISH,
                segments = listOf(segment("first segment about mercy", 0, 1000), segment("second segment about patience", 1000, 2000)),
                engineId = "test",
            ),
            Transcript(
                recordingId = 9L,
                language = TranscriptLanguage.ENGLISH,
                segments = listOf(segment("another recording mentions mercy too")),
                engineId = "test",
            ),
        )

        val results = TranscriptSearchEngine.search(transcripts, "mercy")

        assertEquals(2, results.size)
        assertEquals(setOf(8L, 9L), results.map { it.recordingId }.toSet())
    }

    @Test
    fun `transcript fullText joins segments with spaces`() {
        val transcript = Transcript(
            recordingId = 10L,
            language = TranscriptLanguage.ENGLISH,
            segments = listOf(segment("hello", 0, 500), segment("world", 500, 1000)),
            engineId = "test",
        )

        assertEquals("hello world", transcript.fullText)
    }
}
