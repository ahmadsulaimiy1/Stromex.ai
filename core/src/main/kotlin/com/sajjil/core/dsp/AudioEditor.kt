package com.sajjil.core.dsp

/**
 * Sample-accurate, non-destructive editing primitives -- trim, cut (delete a selected middle
 * region and splice the remainder together), fade in/out, and merge. Every recording is already
 * decoded into a plain `FloatArray` elsewhere in this codebase (see `core.audio.WavIO`), so these
 * are cheap array operations: no re-encoding, no FFT, nothing that needs a real-time engine.
 * Every function returns a new array; none mutate their input.
 */
object AudioEditor {

    /** Keeps only the region [startSample, endSample) -- the region OUTSIDE the selection is discarded. */
    fun trim(samples: FloatArray, startSample: Int, endSample: Int): FloatArray {
        val (start, end) = clampedRange(samples.size, startSample, endSample)
        return samples.copyOfRange(start, end)
    }

    /** Removes the region [startSample, endSample) and splices what's before and after it together -- the region INSIDE the selection is discarded, everything else is kept. */
    fun deleteRange(samples: FloatArray, startSample: Int, endSample: Int): FloatArray {
        val (start, end) = clampedRange(samples.size, startSample, endSample)
        val result = FloatArray(samples.size - (end - start))
        samples.copyInto(result, destinationOffset = 0, startIndex = 0, endIndex = start)
        samples.copyInto(result, destinationOffset = start, startIndex = end, endIndex = samples.size)
        return result
    }

    /** Linear fade from silence up to full amplitude over the first [fadeSampleCount] samples. */
    fun fadeIn(samples: FloatArray, fadeSampleCount: Int): FloatArray {
        val result = samples.copyOf()
        val count = fadeSampleCount.coerceIn(0, result.size)
        for (i in 0 until count) {
            val gain = i.toFloat() / count.coerceAtLeast(1)
            result[i] = result[i] * gain
        }
        return result
    }

    /** Linear fade from full amplitude down to silence over the last [fadeSampleCount] samples. */
    fun fadeOut(samples: FloatArray, fadeSampleCount: Int): FloatArray {
        val result = samples.copyOf()
        val count = fadeSampleCount.coerceIn(0, result.size)
        val start = result.size - count
        for (i in 0 until count) {
            val gain = 1f - (i.toFloat() / count.coerceAtLeast(1))
            result[start + i] = result[start + i] * gain
        }
        return result
    }

    /** Concatenates two takes end-to-end -- the "append to an existing recording" / "merge" primitive. */
    fun merge(first: FloatArray, second: FloatArray): FloatArray = first + second

    private fun clampedRange(size: Int, startSample: Int, endSample: Int): Pair<Int, Int> {
        val start = startSample.coerceIn(0, size)
        val end = endSample.coerceIn(start, size)
        return start to end
    }
}
