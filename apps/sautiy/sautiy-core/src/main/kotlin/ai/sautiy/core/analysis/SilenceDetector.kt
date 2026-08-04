package ai.sautiy.core.analysis

import ai.sautiy.core.audio.AudioBuffer
import ai.sautiy.core.audio.Decibels
import kotlin.math.sqrt

/**
 * Editorial Bible chapter 9.7 — silence detection.
 *
 * Two decisions here are what separate a usable feature from one people turn off after their
 * first attempt:
 *
 * **The threshold is relative to the recording's own noise floor**, not a fixed constant. A
 * lecture hall with air conditioning and a treated room do not share a threshold, and a fixed
 * −45 dBFS either removes nothing in the first or removes breath and room tone in the second.
 *
 * **A gap shorter than a third of a second is not silence, it is rhythm.** Removing the pauses
 * between clauses is what makes automatically edited speech sound frantic and inhuman. SAUTIY
 * removes the eight seconds of nothing before someone started talking; it does not remove the
 * breath before an important word.
 */
public object SilenceDetector {

    /** Analysis window. 20 ms is short enough to find a word boundary, long enough to be stable. */
    public const val WINDOW_MS: Double = 20.0

    /** Chapter 9.7: below this, a quiet passage is speech rhythm and is left alone. */
    public const val DEFAULT_MIN_SILENCE_MS: Long = 350

    /** Chapter 9.7: kept at each end of a removed region so word onsets are not clipped. */
    public const val DEFAULT_PADDING_MS: Long = 80

    /** Chapter 9.7: how far above the measured noise floor the threshold sits. */
    public const val DEFAULT_HEADROOM_DB: Double = 12.0

    /** An absolute floor, for the rare recording whose "noise" is already digital silence. */
    public const val ABSOLUTE_FLOOR_DB: Double = -60.0

    public data class Region(val startFrame: Long, val endFrame: Long) {
        public val lengthFrames: Long get() = endFrame - startFrame
        public fun durationSeconds(sampleRate: Int): Double = lengthFrames.toDouble() / sampleRate
    }

    public data class Analysis(
        val noiseFloorDb: Double,
        val thresholdDb: Double,
        val regions: List<Region>,
        val sampleRate: Int,
    ) {
        public val totalSilentFrames: Long get() = regions.sumOf { it.lengthFrames }
        public val totalSilentSeconds: Double get() = totalSilentFrames.toDouble() / sampleRate
    }

    /**
     * The recording's noise floor, taken as the **10th percentile** of window energies.
     *
     * A mean would be dragged up by the speech itself; a minimum would land on a single
     * anomalously quiet window, often a digital dropout. The tenth percentile is the level the
     * recording sits at when nobody is talking, which is precisely what "noise floor" means.
     */
    public fun noiseFloorDb(buffer: AudioBuffer): Double {
        val windowFrames = (WINDOW_MS * buffer.sampleRate / 1000.0).toInt().coerceAtLeast(1)
        if (buffer.frameCount < windowFrames) return Decibels.fromLinear(buffer.rms())

        val energies = ArrayList<Double>(buffer.frameCount / windowFrames + 1)
        var position = 0
        while (position + windowFrames <= buffer.frameCount) {
            energies += windowRms(buffer, position, windowFrames)
            position += windowFrames
        }
        if (energies.isEmpty()) return Decibels.fromLinear(buffer.rms())

        energies.sort()
        val percentileIndex = (energies.size * 0.10).toInt().coerceIn(0, energies.size - 1)
        return Decibels.fromLinear(energies[percentileIndex])
    }

    private fun windowRms(buffer: AudioBuffer, from: Int, frames: Int): Double {
        var energy = 0.0
        var count = 0
        for (channel in buffer.channels) {
            val end = minOf(from + frames, channel.size)
            for (i in from until end) {
                energy += channel[i].toDouble() * channel[i]
                count++
            }
        }
        return if (count == 0) 0.0 else sqrt(energy / count)
    }

    /**
     * Finds the silent regions.
     *
     * @param thresholdDb overrides the automatic threshold when the user has adjusted it
     * @param minSilenceMs gaps shorter than this are rhythm, not silence
     * @param paddingMs kept at each end of every region
     */
    public fun analyse(
        buffer: AudioBuffer,
        thresholdDb: Double? = null,
        minSilenceMs: Long = DEFAULT_MIN_SILENCE_MS,
        paddingMs: Long = DEFAULT_PADDING_MS,
        headroomDb: Double = DEFAULT_HEADROOM_DB,
    ): Analysis {
        val sampleRate = buffer.sampleRate
        val floorDb = noiseFloorDb(buffer)
        val effectiveThreshold = thresholdDb
            ?: maxOf(floorDb + headroomDb, ABSOLUTE_FLOOR_DB).coerceAtMost(-20.0)

        val windowFrames = (WINDOW_MS * sampleRate / 1000.0).toInt().coerceAtLeast(1)
        val minSilenceFrames = minSilenceMs * sampleRate / 1000
        val paddingFrames = paddingMs * sampleRate / 1000

        val regions = ArrayList<Region>()
        var runStart = -1L
        var position = 0

        while (position < buffer.frameCount) {
            val frames = minOf(windowFrames, buffer.frameCount - position)
            val level = Decibels.fromLinear(windowRms(buffer, position, frames))
            val quiet = level < effectiveThreshold

            if (quiet && runStart < 0) {
                runStart = position.toLong()
            } else if (!quiet && runStart >= 0) {
                addRegion(regions, runStart, position.toLong(), minSilenceFrames, paddingFrames)
                runStart = -1
            }
            position += frames
        }
        if (runStart >= 0) {
            addRegion(regions, runStart, buffer.frameCount.toLong(), minSilenceFrames, paddingFrames)
        }

        return Analysis(floorDb, effectiveThreshold, regions, sampleRate)
    }

    private fun addRegion(
        into: MutableList<Region>,
        start: Long,
        end: Long,
        minSilenceFrames: Long,
        paddingFrames: Long,
    ) {
        if (end - start < minSilenceFrames) return
        val paddedStart = start + paddingFrames
        val paddedEnd = end - paddingFrames
        if (paddedEnd > paddedStart) into += Region(paddedStart, paddedEnd)
    }
}
