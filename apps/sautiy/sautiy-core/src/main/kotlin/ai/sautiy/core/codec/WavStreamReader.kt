package ai.sautiy.core.codec

import ai.sautiy.core.analysis.PeakBuilder
import ai.sautiy.core.analysis.PeakLevel
import ai.sautiy.core.analysis.Waveform
import ai.sautiy.core.analysis.WaveformPyramid
import ai.sautiy.core.audio.AudioBuffer
import ai.sautiy.core.audio.PcmCodec
import java.io.File
import java.io.RandomAccessFile

/**
 * An open handle on a WAV file, for repeated range reads.
 *
 * This exists because the obvious approach is catastrophically slow and does not look it.
 * Calling [WavCodec.readRange] per playback block re-opens the file **and re-parses every RIFF
 * chunk** on each call — at a 40 ms output buffer that is twenty-five file opens and twenty-five
 * header walks per second of audio, on the thread feeding the speaker. It plays, so it passes a
 * casual test; it just stutters and drains the battery.
 *
 * Here the header is parsed once and the descriptor stays open, so a read is a seek and a
 * `readFully`. That is the difference between playback that starts instantly and playback that
 * feels slow.
 *
 * Not thread-safe: one reader per consumer. Reads are cheap enough that sharing one across
 * threads would cost more in contention than it saves in descriptors.
 */
public class WavStreamReader(
    private val file: File,
) : AutoCloseable {

    public val info: WavCodec.WavInfo = WavCodec.probe(file)

    private val handle = RandomAccessFile(file, "r")
    private val bytesPerFrame = info.format.bytesPerFrame

    /** Scratch buffer, grown on demand and reused, so a steady playback loop stops allocating. */
    private var scratch = ByteArray(0)

    public val frameCount: Long get() = info.frameCount
    public val sampleRate: Int get() = info.format.sampleRate
    public val channelCount: Int get() = info.format.channelCount

    /**
     * Frames `[startFrame, startFrame + frames)`.
     *
     * Requests outside the file return silence for the part that does not exist, rather than
     * throwing. Both ends matter: during recording the view legitimately runs ahead of the
     * file, and a timeline scrolled left of zero asks for negative positions. A render is not
     * the place to fail, and a caller that has to special-case the edges will get it wrong.
     */
    public fun read(startFrame: Long, frames: Int): AudioBuffer {
        if (frames <= 0) return AudioBuffer.silence(channelCount, 0, sampleRate)
        require(frames.toLong() * bytesPerFrame <= Int.MAX_VALUE) {
            "Requested range is too large for one buffer"
        }

        // Where the real audio starts inside the returned buffer, when the request begins
        // before the file does.
        val lead = (-startFrame).coerceIn(0, frames.toLong()).toInt()
        val from = startFrame + lead
        val available = (info.frameCount - from).coerceIn(0, (frames - lead).toLong()).toInt()
        if (available <= 0) return AudioBuffer.silence(channelCount, frames, sampleRate)

        val byteCount = available * bytesPerFrame
        if (scratch.size < byteCount) scratch = ByteArray(byteCount)

        handle.seek(info.dataOffset + from * bytesPerFrame)
        handle.readFully(scratch, 0, byteCount)

        val decoded = PcmCodec.decode(scratch, 0, byteCount, info.format)
        if (available == frames) return decoded

        // Short read: pad, so the caller's arithmetic never special-cases the edges.
        val padded = AudioBuffer.silence(channelCount, frames, sampleRate)
        for (c in 0 until channelCount) {
            decoded.channels[c].copyInto(padded.channels[c], lead)
        }
        return padded
    }

    /**
     * Builds the waveform envelope for the whole file.
     *
     * Streamed in blocks rather than read whole: a ninety-minute lecture is far past the
     * in-memory ceiling, and the peaks are the one thing that must exist for the *entire*
     * recording regardless of its length.
     */
    public fun buildPeaks(
        framesPerBucket: Int = PeakBuilder.DEFAULT_BASE_BUCKET,
        blockFrames: Int = 1 shl 18,
        onProgress: (Double) -> Unit = {},
    ): PeakLevel {
        val builder = PeakBuilder(framesPerBucket)
        var position = 0L
        while (position < info.frameCount) {
            val frames = minOf(blockFrames.toLong(), info.frameCount - position).toInt()
            builder.append(read(position, frames))
            position += frames
            onProgress(position.toDouble() / info.frameCount)
        }
        return builder.finish()
    }

    /** The full zoom pyramid, ready for the canvas. */
    public fun buildPyramid(
        framesPerBucket: Int = PeakBuilder.DEFAULT_BASE_BUCKET,
        onProgress: (Double) -> Unit = {},
    ): WaveformPyramid =
        Waveform.pyramid(buildPeaks(framesPerBucket, onProgress = onProgress), sampleRate, info.frameCount)

    override fun close() {
        runCatching { handle.close() }
    }
}
