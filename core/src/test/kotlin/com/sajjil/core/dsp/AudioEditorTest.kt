package com.sajjil.core.dsp

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class AudioEditorTest {

    @Test
    fun `trim keeps only the selected region`() {
        val samples = FloatArray(100) { it.toFloat() }
        val trimmed = AudioEditor.trim(samples, 10, 20)
        assertEquals(10, trimmed.size)
        assertEquals(10f, trimmed.first())
        assertEquals(19f, trimmed.last())
    }

    @Test
    fun `trim clamps an out-of-range selection instead of crashing`() {
        val samples = FloatArray(10) { it.toFloat() }
        val trimmed = AudioEditor.trim(samples, -5, 1000)
        assertEquals(10, trimmed.size)
        assertTrue(trimmed.contentEquals(samples))
    }

    @Test
    fun `trim with a reversed range yields an empty result, not a crash`() {
        val samples = FloatArray(10) { it.toFloat() }
        val trimmed = AudioEditor.trim(samples, 8, 2)
        assertEquals(0, trimmed.size)
    }

    @Test
    fun `deleteRange removes the middle and splices the remainder together`() {
        val samples = FloatArray(10) { it.toFloat() } // 0..9
        val result = AudioEditor.deleteRange(samples, 3, 7) // remove 3,4,5,6
        assertEquals(6, result.size)
        assertTrue(result.contentEquals(floatArrayOf(0f, 1f, 2f, 7f, 8f, 9f)))
    }

    @Test
    fun `trim and deleteRange are complementary in length`() {
        val samples = FloatArray(50) { it.toFloat() }
        val kept = AudioEditor.trim(samples, 10, 30)
        val removed = AudioEditor.deleteRange(samples, 10, 30)
        assertEquals(samples.size, kept.size + removed.size)
    }

    @Test
    fun `fadeIn ramps from silence up to the original amplitude`() {
        val samples = FloatArray(100) { 1f }
        val faded = AudioEditor.fadeIn(samples, 10)
        assertEquals(0f, faded[0])
        assertTrue(faded[5] in 0.4f..0.6f, "midpoint of the fade should be roughly half amplitude, was ${faded[5]}")
        assertEquals(1f, faded[50], "samples after the fade window must be untouched")
    }

    @Test
    fun `fadeOut ramps the tail down to silence`() {
        val samples = FloatArray(100) { 1f }
        val faded = AudioEditor.fadeOut(samples, 10)
        assertEquals(1f, faded[0], "samples before the fade window must be untouched")
        assertTrue(faded[95] in 0.4f..0.6f, "midpoint of the fade should be roughly half amplitude, was ${faded[95]}")
        assertTrue(faded[99] < 0.15f, "last sample should be near silence, was ${faded[99]}")
    }

    @Test
    fun `fade functions do not mutate the input array`() {
        val samples = FloatArray(20) { 1f }
        val original = samples.copyOf()
        AudioEditor.fadeIn(samples, 5)
        AudioEditor.fadeOut(samples, 5)
        assertTrue(samples.contentEquals(original), "AudioEditor functions must not mutate their input")
    }

    @Test
    fun `merge concatenates two takes end to end`() {
        val first = floatArrayOf(1f, 2f, 3f)
        val second = floatArrayOf(4f, 5f)
        val merged = AudioEditor.merge(first, second)
        assertTrue(merged.contentEquals(floatArrayOf(1f, 2f, 3f, 4f, 5f)))
    }
}
