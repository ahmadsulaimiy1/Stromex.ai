package com.sajjil.core.assistant

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertIs

class AssistantIntentParserTest {

    @Test
    fun `show me surah recordings resolves to FindBySurah`() {
        val intent = AssistantIntentParser.parse("Show me Surah Al-Kahf recordings.")
        val found = assertIs<AssistantIntent.FindBySurah>(intent)
        assertEquals("Al-Kahf", found.surahQuery)
    }

    @Test
    fun `find where I discussed topic resolves to FindByKeyword`() {
        val intent = AssistantIntentParser.parse("Find where I discussed zakat.")
        val found = assertIs<AssistantIntent.FindByKeyword>(intent)
        assertEquals("zakat", found.keyword)
    }

    @Test
    fun `find the lecture where I explained topic resolves to FindByKeyword`() {
        val intent = AssistantIntentParser.parse("Find the lecture where I explained fasting.")
        val found = assertIs<AssistantIntent.FindByKeyword>(intent)
        assertEquals("fasting", found.keyword)
    }

    @Test
    fun `read this transcript resolves to ReadCurrentTranscript`() {
        assertEquals(AssistantIntent.ReadCurrentTranscript, AssistantIntentParser.parse("Read this transcript."))
    }

    @Test
    fun `read it resolves to ReadCurrentTranscript`() {
        assertEquals(AssistantIntent.ReadCurrentTranscript, AssistantIntentParser.parse("Please read it to me."))
    }

    @Test
    fun `which recordings have poor quality resolves to a below-threshold filter`() {
        val intent = AssistantIntentParser.parse("Which recordings have poor quality?")
        val filter = assertIs<AssistantIntent.FilterByQuality>(intent)
        assertEquals(QualityComparison.BELOW, filter.comparison)
    }

    @Test
    fun `which recordings have the best quality resolves to an above-threshold filter`() {
        val intent = AssistantIntentParser.parse("Show me recordings with the best quality.")
        val filter = assertIs<AssistantIntent.FilterByQuality>(intent)
        assertEquals(QualityComparison.ABOVE, filter.comparison)
    }

    @Test
    fun `generic find trigger extracts a keyword after stripping filler words`() {
        val intent = AssistantIntentParser.parse("Find my tajweed notes")
        val found = assertIs<AssistantIntent.FindByKeyword>(intent)
        assertEquals("tajweed notes", found.keyword)
    }

    @Test
    fun `unrelated sentence is unrecognized rather than guessed`() {
        val intent = AssistantIntentParser.parse("What time is it in Makkah?")
        assertIs<AssistantIntent.Unrecognized>(intent)
    }

    @Test
    fun `blank input is unrecognized`() {
        val intent = AssistantIntentParser.parse("   ")
        val unrecognized = assertIs<AssistantIntent.Unrecognized>(intent)
        assertEquals("", unrecognized.rawText)
    }

    @Test
    fun `surah pattern takes priority over the generic find trigger`() {
        // "Show me" alone would match the generic find-trigger fallback; the Surah-specific
        // pattern should win so the query stays structured (a Surah name) rather than falling
        // back to an unstructured keyword search.
        val intent = AssistantIntentParser.parse("Show me Surah Yaseen")
        assertIs<AssistantIntent.FindBySurah>(intent)
    }
}
