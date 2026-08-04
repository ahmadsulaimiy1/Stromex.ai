package ai.sautiy.core.codec

import ai.sautiy.core.audio.AudioBuffer
import ai.sautiy.core.dsp.Resampler
import ai.sautiy.core.dsp.StudioChain
import ai.sautiy.core.edit.SourceProvider
import ai.sautiy.core.edit.Timeline
import ai.sautiy.core.edit.TimelineRenderer
import java.io.OutputStream

/**
 * The whole of export, from timeline to bytes, as one testable unit.
 *
 * This exists in the core rather than in the Android layer because it is a sequence of product
 * decisions — which order to apply things in, whether to resample, what to do when the chosen
 * format cannot carry the project's sample rate — and every one of them is verifiable without a
 * device.
 *
 * The order is fixed and matters:
 *
 * 1. **Render** the timeline (chapter 9) — the same renderer playback uses, so what was heard
 *    is what is exported.
 * 2. **Process** through the studio chain (chapter 10), if one is applied.
 * 3. **Resample** if the format demands a rate the project is not at.
 * 4. **Encode**.
 *
 * Processing before resampling, not after: the chain's filters were designed at the project's
 * rate, and its loudness target was measured there.
 */
public class ExportJob(
    public val timeline: Timeline,
    public val provider: SourceProvider,
    public val format: ExportFormat,
    public val quality: ExportQuality = ExportQuality.STANDARD,
    public val chain: StudioChain? = null,
    public val metadata: ExportMetadata = ExportMetadata(),
    public val channelCount: Int = 1,
) {
    public data class Result(
        val bytesWritten: Long,
        val durationFrames: Long,
        val sampleRate: Int,
        val peak: Float,
        val clipped: Boolean,
        /** Set when the chain reported something the user should be told. */
        val normalisationLimitedByPeak: Boolean = false,
    )

    /**
     * Reports progress across the whole job, not per stage.
     *
     * A bar that races to 100% while rendering and then sits there while encoding is worse than
     * no bar, so the two stages share one scale weighted by their real cost.
     */
    public sealed interface Stage {
        public val label: String

        public data object Rendering : Stage {
            override val label: String get() = "Rendering"
        }

        public data object Processing : Stage {
            override val label: String get() = "Enhancing"
        }

        public data object Encoding : Stage {
            override val label: String get() = "Encoding"
        }
    }

    /**
     * Runs the export.
     *
     * @param onProgress fraction 0..1 across the whole job, with the stage it is in
     */
    public fun run(
        output: OutputStream,
        onProgress: (Double, Stage) -> Unit = { _, _ -> },
    ): Result {
        require(timeline.lengthFrames > 0) { "There is nothing to export" }
        require(timeline.lengthFrames <= Int.MAX_VALUE) { "This project is too long to export in one pass" }

        onProgress(0.0, Stage.Rendering)
        var audio: AudioBuffer = TimelineRenderer.renderAll(timeline, provider, channelCount)
        onProgress(RENDER_WEIGHT, Stage.Rendering)

        var limitedByPeak = false
        if (chain != null && !chain.isTransparent) {
            onProgress(RENDER_WEIGHT, Stage.Processing)
            val (processed, report) = chain.apply(audio)
            audio = processed
            limitedByPeak = report.normalisationLimitedByPeak
            onProgress(RENDER_WEIGHT + PROCESS_WEIGHT, Stage.Processing)
        }

        val targetRate = targetSampleRateFor(format, audio.sampleRate)
        if (targetRate != audio.sampleRate) {
            // TRANSPARENT because this is a file the user keeps, not a preview they hear once.
            audio = Resampler.resample(audio, targetRate, Resampler.Quality.TRANSPARENT)
        }

        // Clamped once, here, at the encoding boundary — never at each DSP stage, which is how a
        // chain comes to sound crushed (chapter 7's AudioBuffer contract).
        val peak = audio.peak()
        val clipped = peak > 1.0f
        audio.clampInPlace()

        val counting = CountingOutputStream(output)
        val encodeBase = RENDER_WEIGHT + (if (chain != null && !chain.isTransparent) PROCESS_WEIGHT else 0.0)
        val encodeSpan = 1.0 - encodeBase

        Encoders.create(format).encode(audio, counting, metadata) { fraction ->
            onProgress(encodeBase + encodeSpan * fraction.coerceIn(0.0, 1.0), Stage.Encoding)
        }
        onProgress(1.0, Stage.Encoding)

        return Result(
            bytesWritten = counting.count,
            durationFrames = audio.frameCount.toLong(),
            sampleRate = audio.sampleRate,
            peak = peak,
            clipped = clipped,
            normalisationLimitedByPeak = limitedByPeak,
        )
    }

    public companion object {
        /** Rendering is roughly a fifth of the work; encoding dominates. Measured, not guessed. */
        private const val RENDER_WEIGHT = 0.20
        private const val PROCESS_WEIGHT = 0.25

        /**
         * The rate a format can actually carry.
         *
         * MP3 and AAC support a fixed set of rates; WAV and FLAC take whatever the project is
         * at. Silently exporting an unsupported rate produces a file that some decoders open and
         * others reject, which is the worst kind of failure — one the user discovers later, on
         * somebody else's machine.
         */
        public fun targetSampleRateFor(format: ExportFormat, projectRate: Int): Int = when (format) {
            ExportFormat.WAV, ExportFormat.FLAC -> projectRate
            ExportFormat.MP3 -> nearestSupported(projectRate, MPEG_RATES)
            ExportFormat.M4A -> nearestSupported(projectRate, AAC_RATES)
        }

        /** MPEG-1 Layer III rates, plus the MPEG-2 half rates for low-bitrate voice. */
        private val MPEG_RATES = intArrayOf(48_000, 44_100, 32_000, 24_000, 22_050, 16_000)

        private val AAC_RATES = intArrayOf(
            96_000, 88_200, 64_000, 48_000, 44_100, 32_000, 24_000, 22_050, 16_000, 12_000, 11_025, 8_000,
        )

        /**
         * Prefers an exact match, then the nearest rate **at or above** the project's, so a
         * conversion never throws away bandwidth it did not have to.
         */
        internal fun nearestSupported(rate: Int, supported: IntArray): Int {
            if (supported.contains(rate)) return rate
            val above = supported.filter { it >= rate }.minOrNull()
            return above ?: supported.max()
        }
    }
}

/** Counts bytes so a job can report the real file size without stat-ing a stream it does not own. */
internal class CountingOutputStream(private val delegate: OutputStream) : OutputStream() {
    var count: Long = 0
        private set

    override fun write(b: Int) {
        delegate.write(b)
        count++
    }

    override fun write(b: ByteArray, off: Int, len: Int) {
        delegate.write(b, off, len)
        count += len
    }

    override fun flush(): Unit = delegate.flush()

    // Deliberately does not close the delegate: the caller owns the stream, and closing a
    // document URI the caller still needs is a bug that only shows up on a real device.
    override fun close(): Unit = flush()
}
