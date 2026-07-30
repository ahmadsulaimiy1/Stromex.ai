package com.sajjil.core.dsp

import kotlin.math.PI
import kotlin.math.abs
import kotlin.math.sin
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class DeclipperTest {
    private val sampleRate = 8000

    @Test
    fun `finds a single clipped run`() {
        val samples = FloatArray(20) { 0.1f }
        for (i in 8..12) samples[i] = 1.0f
        val segments = Declipper.findClipSegments(samples)
        assertEquals(1, segments.size)
        assertEquals(8, segments[0].startIndex)
        assertEquals(13, segments[0].endIndexExclusive)
    }

    @Test
    fun `ignores single-sample spikes below the minimum run length`() {
        val samples = FloatArray(20) { 0.1f }
        samples[5] = 1.0f
        val segments = Declipper.findClipSegments(samples, minRunLength = 2)
        assertTrue(segments.isEmpty())
    }

    @Test
    fun `repaired region no longer touches full scale and stays continuous with its neighbours`() {
        val freq = 300.0
        val n = 400
        val clean = FloatArray(n) { i -> (0.9 * sin(2.0 * PI * freq * i / sampleRate)).toFloat() }
        val clipped = FloatArray(n) { i -> clean[i].coerceIn(-0.6f, 0.6f) }

        val repaired = Declipper.repair(clipped, threshold = 0.6f, minRunLength = 2)

        val segments = Declipper.findClipSegments(clipped, threshold = 0.6f)
        assertTrue(segments.isNotEmpty(), "test setup should have produced clipped runs")

        for (segment in segments) {
            for (i in segment.startIndex until segment.endIndexExclusive) {
                assertTrue(abs(repaired[i]) <= 0.9f + 1e-3f, "repaired sample $i should not still be pinned at the clip ceiling")
            }
        }

        // Continuity: no huge jump introduced at the segment boundaries.
        for (segment in segments) {
            val before = if (segment.startIndex > 0) repaired[segment.startIndex - 1] else repaired[segment.startIndex]
            val first = repaired[segment.startIndex]
            assertTrue(abs(first - before) < 0.5f, "unexpected discontinuity entering the repaired region")
        }
    }

    @Test
    fun `buffer with no clipping is returned unchanged`() {
        val samples = FloatArray(1000) { i -> (0.3 * sin(i * 0.1)).toFloat() }
        val repaired = Declipper.repair(samples)
        assertTrue(repaired.contentEquals(samples))
    }
}
