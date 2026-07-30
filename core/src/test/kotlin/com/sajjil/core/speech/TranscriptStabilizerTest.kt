package com.sajjil.core.speech

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith

class TranscriptStabilizerTest {

    @Test
    fun `fewer updates than window size keeps everything as draft`() {
        val stabilizer = TranscriptStabilizer(windowSize = 3)

        val first = stabilizer.update("hello")
        assertEquals("", first.stableText)
        assertEquals("hello", first.draftText)

        val second = stabilizer.update("hello world")
        assertEquals("", second.stableText)
        assertEquals("hello world", second.draftText)
    }

    @Test
    fun `prefix promotes to stable once it survives the full window unchanged`() {
        val stabilizer = TranscriptStabilizer(windowSize = 2)

        stabilizer.update("hello")
        val second = stabilizer.update("hello world")
        assertEquals("hello", second.stableText)
        assertEquals("world", second.draftText)

        val third = stabilizer.update("hello world there")
        assertEquals("hello world", third.stableText)
        assertEquals("there", third.draftText)
    }

    @Test
    fun `a correction to an earlier word resets that word to draft`() {
        val stabilizer = TranscriptStabilizer(windowSize = 2)

        stabilizer.update("he said")
        val corrected = stabilizer.update("she said")
        assertEquals("", corrected.stableText)
        assertEquals("she said", corrected.draftText)
    }

    @Test
    fun `window size one stabilizes every update immediately`() {
        val stabilizer = TranscriptStabilizer(windowSize = 1)

        val result = stabilizer.update("this is immediately stable")
        assertEquals("this is immediately stable", result.stableText)
        assertEquals("", result.draftText)
    }

    @Test
    fun `commitFinal marks the whole text stable and clears history`() {
        val stabilizer = TranscriptStabilizer(windowSize = 3)
        stabilizer.update("partial")
        stabilizer.update("partial text")

        val final = stabilizer.commitFinal("partial text here")
        assertEquals("partial text here", final.stableText)
        assertEquals("", final.draftText)

        // History was cleared, so the next utterance starts fresh as draft-only.
        val next = stabilizer.update("new utterance")
        assertEquals("", next.stableText)
        assertEquals("new utterance", next.draftText)
    }

    @Test
    fun `reset clears history without producing a final result`() {
        val stabilizer = TranscriptStabilizer(windowSize = 2)
        stabilizer.update("hello")
        stabilizer.update("hello world")
        stabilizer.reset()

        val afterReset = stabilizer.update("hello world")
        assertEquals("", afterReset.stableText)
        assertEquals("hello world", afterReset.draftText)
    }

    @Test
    fun `fullText joins stable and draft with a single space`() {
        val text = StabilizedText(stableText = "hello world", draftText = "there")
        assertEquals("hello world there", text.fullText)
    }

    @Test
    fun `fullText handles an empty stable or draft side without a stray space`() {
        assertEquals("hello", StabilizedText(stableText = "hello", draftText = "").fullText)
        assertEquals("hello", StabilizedText(stableText = "", draftText = "hello").fullText)
        assertEquals("", StabilizedText(stableText = "", draftText = "").fullText)
    }

    @Test
    fun `blank partial text produces an all-draft empty result`() {
        val stabilizer = TranscriptStabilizer(windowSize = 2)
        val result = stabilizer.update("   ")
        assertEquals("", result.stableText)
        assertEquals("", result.draftText)
    }

    @Test
    fun `invalid window size is rejected`() {
        assertFailsWith<IllegalArgumentException> { TranscriptStabilizer(windowSize = 0) }
    }
}
