package com.sajjil.core.dsp

import kotlin.math.abs

data class ClipSegment(val startIndex: Int, val endIndexExclusive: Int)

/**
 * Detects clipped runs (consecutive samples pinned at/near full scale) and
 * reconstructs them with a cubic Hermite spline fitted to the unclipped
 * waveform on either side. This is a lightweight interpolation-based
 * declipper: effective for short, moderate clipping (a hot mic input
 * catching a peak), not a substitute for sparse-representation declippers
 * (iZotope RX-class tools) on heavily/long clipped material — there's
 * simply no surviving waveform information to reconstruct from in that
 * case, only plausible smoothing.
 */
object Declipper {

    fun findClipSegments(samples: FloatArray, threshold: Float = 0.98f, minRunLength: Int = 2): List<ClipSegment> {
        val segments = mutableListOf<ClipSegment>()
        var i = 0
        while (i < samples.size) {
            if (abs(samples[i]) >= threshold) {
                val start = i
                while (i < samples.size && abs(samples[i]) >= threshold) i++
                if (i - start >= minRunLength) segments.add(ClipSegment(start, i))
            } else {
                i++
            }
        }
        return segments
    }

    fun repair(samples: FloatArray, threshold: Float = 0.98f, minRunLength: Int = 2): FloatArray {
        val segments = findClipSegments(samples, threshold, minRunLength)
        if (segments.isEmpty()) return samples.copyOf()

        val result = samples.copyOf()
        for (segment in segments) interpolateSegment(result, segment)
        return result
    }

    private fun interpolateSegment(samples: FloatArray, segment: ClipSegment) {
        val p0Index = (segment.startIndex - 1).coerceAtLeast(0)
        val p3Index = segment.endIndexExclusive.coerceAtMost(samples.size - 1)
        if (p0Index == segment.startIndex || p3Index == segment.endIndexExclusive - 1) return // no room to interpolate

        val preSlopeIndex = (p0Index - 1).coerceAtLeast(0)
        val postSlopeIndex = (p3Index + 1).coerceAtMost(samples.size - 1)

        val p0 = samples[p0Index].toDouble()
        val p3 = samples[p3Index].toDouble()
        val m0 = (samples[p0Index] - samples[preSlopeIndex]).toDouble()
        val m3 = (samples[postSlopeIndex] - samples[p3Index]).toDouble()

        val span = p3Index - p0Index
        for (offset in 1 until span) {
            val t = offset.toDouble() / span
            samples[p0Index + offset] = hermite(p0, p3, m0, m3, t).toFloat().coerceIn(-1f, 1f)
        }
    }

    /** Cubic Hermite interpolation between p0 (t=0) and p1 (t=1) with tangents m0, m1. */
    private fun hermite(p0: Double, p1: Double, m0: Double, m1: Double, t: Double): Double {
        val t2 = t * t
        val t3 = t2 * t
        val h00 = 2 * t3 - 3 * t2 + 1
        val h10 = t3 - 2 * t2 + t
        val h01 = -2 * t3 + 3 * t2
        val h11 = t3 - t2
        return h00 * p0 + h10 * m0 + h01 * p1 + h11 * m1
    }
}
