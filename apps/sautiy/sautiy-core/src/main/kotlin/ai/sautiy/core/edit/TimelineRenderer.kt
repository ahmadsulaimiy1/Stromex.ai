package ai.sautiy.core.edit

import ai.sautiy.core.audio.AudioBuffer

/**
 * Supplies samples for a source. The renderer never opens a file itself, which is what keeps
 * the whole edit engine free of I/O and testable on a plain JDK with in-memory sources.
 */
public fun interface SourceProvider {
    /**
     * Frames `[startFrame, startFrame + frameCount)` of [sourceId]. Reads past the end return
     * silence rather than throwing — a source can legitimately be shorter than a stale clip
     * believes, and a render is not the place to fail.
     */
    public fun read(sourceId: String, startFrame: Long, frameCount: Int): AudioBuffer
}

/**
 * Turns a [Timeline] into audio.
 *
 * This is the single point at which a description becomes samples — for playback, for export,
 * and for the analysis panel. There is no second rendering path, so what the user hears and
 * what they export cannot diverge.
 */
public object TimelineRenderer {

    /**
     * Renders frames `[startFrame, startFrame + frameCount)` of the mix.
     *
     * Rendering a *window* rather than the whole timeline is what allows playback to begin
     * instantly on a two-hour project (chapter 1.3.4): the engine renders the block it is
     * about to play, not the file it might eventually export.
     */
    public fun render(
        timeline: Timeline,
        provider: SourceProvider,
        startFrame: Long,
        frameCount: Int,
        channelCount: Int = 1,
    ): AudioBuffer {
        require(frameCount >= 0) { "Cannot render a negative number of frames" }
        val mix = AudioBuffer.silence(channelCount, frameCount, timeline.sampleRate)
        if (frameCount == 0) return mix

        val endFrame = startFrame + frameCount

        for (layer in timeline.layers) {
            if (!timeline.isAudible(layer)) continue
            val layerGain = Math.pow(10.0, layer.gainDb / 20.0).toFloat()

            for (clip in layer.clipsOverlapping(startFrame, endFrame)) {
                // The overlap between this clip and the window being rendered.
                val fromTimeline = maxOf(clip.timelineStartFrame, startFrame)
                val toTimeline = minOf(clip.timelineEndFrame, endFrame)
                val length = (toTimeline - fromTimeline).toInt()
                if (length <= 0) continue

                val offsetInClip = fromTimeline - clip.timelineStartFrame
                val sourceFrom = clip.sourceStartFrame + offsetInClip
                val audio = provider.read(clip.sourceId, sourceFrom, length)
                if (audio.frameCount == 0) continue

                val writeAt = (fromTimeline - startFrame).toInt()
                val copyable = minOf(audio.frameCount, length, frameCount - writeAt)

                for (c in 0 until channelCount) {
                    val source = audio.channels[minOf(c, audio.channelCount - 1)]
                    val destination = mix.channels[c]
                    for (i in 0 until copyable) {
                        // Clip gain and fades are evaluated per sample. A fade evaluated per
                        // block instead would step in blocks, which is audible as zipper noise
                        // on anything shorter than a second.
                        val gain = clip.gainAt(offsetInClip + i).toFloat() * layerGain
                        destination[writeAt + i] += source[i] * gain
                    }
                }
            }
        }
        return mix
    }

    /**
     * Renders the whole timeline. Used for export, and only where the result is known to fit
     * within the constitutional in-memory ceiling; longer material is exported by streaming
     * windows through [render].
     */
    public fun renderAll(
        timeline: Timeline,
        provider: SourceProvider,
        channelCount: Int = 1,
    ): AudioBuffer {
        val length = timeline.lengthFrames
        require(length <= Int.MAX_VALUE) { "Timeline is too long to render into a single buffer" }
        return render(timeline, provider, 0, length.toInt(), channelCount)
    }

    /**
     * The peak level the mix will reach, without allocating the mix.
     *
     * Export needs this to decide whether a limiter is required before encoding, and it would
     * be absurd to render a two-hour project twice to find out.
     */
    public fun estimatePeak(
        timeline: Timeline,
        provider: SourceProvider,
        blockFrames: Int = 1 shl 16,
        channelCount: Int = 1,
    ): Float {
        var peak = 0f
        var position = 0L
        val total = timeline.lengthFrames
        while (position < total) {
            val frames = minOf(blockFrames.toLong(), total - position).toInt()
            val block = render(timeline, provider, position, frames, channelCount)
            val blockPeak = block.peak()
            if (blockPeak > peak) peak = blockPeak
            position += frames
        }
        return peak
    }
}

/** A [SourceProvider] over buffers already in memory. The engine's test and preview path. */
public class InMemorySourceProvider(
    private val sources: Map<String, AudioBuffer>,
) : SourceProvider {
    override fun read(sourceId: String, startFrame: Long, frameCount: Int): AudioBuffer {
        val buffer = sources[sourceId]
            ?: return AudioBuffer.silence(1, frameCount, 48_000)
        val from = startFrame.coerceIn(0, buffer.frameCount.toLong()).toInt()
        val to = (from + frameCount).coerceAtMost(buffer.frameCount)
        if (to <= from) return AudioBuffer.silence(buffer.channelCount, frameCount, buffer.sampleRate)

        val slice = buffer.slice(from, to)
        if (slice.frameCount == frameCount) return slice

        // Short reads are padded so the renderer's arithmetic never has to special-case the
        // end of a source.
        val padded = AudioBuffer.silence(slice.channelCount, frameCount, slice.sampleRate)
        for (c in 0 until slice.channelCount) {
            slice.channels[c].copyInto(padded.channels[c], 0)
        }
        return padded
    }
}
