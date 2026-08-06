package ai.sautiy.core.codec

import ai.sautiy.core.audio.AudioBuffer
import ai.sautiy.core.audio.SampleEncoding
import java.io.File
import java.io.OutputStream

/**
 * Editorial Bible chapter 14 — the export contract.
 *
 * Every format SAUTIY can write implements this, so the export panel is a list of encoders
 * rather than a switch statement that grows a new arm each time a format is added, and so the
 * Android layer can add a platform-backed encoder without the core knowing anything about it.
 */
public interface AudioEncoder {

    public val format: ExportFormat

    /**
     * Writes [audio] to [output].
     *
     * @param progress called with 0.0..1.0 as the encode proceeds, so the export panel shows
     *   real progress rather than an indeterminate spinner.
     */
    public fun encode(
        audio: AudioBuffer,
        output: OutputStream,
        metadata: ExportMetadata = ExportMetadata(),
        progress: (Double) -> Unit = {},
    )

    public fun encode(
        audio: AudioBuffer,
        file: File,
        metadata: ExportMetadata = ExportMetadata(),
        progress: (Double) -> Unit = {},
    ) {
        file.parentFile?.mkdirs()
        java.io.BufferedOutputStream(file.outputStream(), 1 shl 16).use { out ->
            encode(audio, out, metadata, progress)
        }
    }
}

/**
 * The formats SAUTIY offers, in the order the export panel lists them.
 *
 * Each entry states plainly what it is for. Chapter 3.2.2 allows the user exactly one decision
 * at export — the format — so that decision has to be answerable without knowing what a codec
 * is.
 */
public enum class ExportFormat(
    public val displayName: String,
    public val extension: String,
    public val mimeType: String,
    public val summary: String,
    public val lossless: Boolean,
) {
    MP3(
        "MP3", "mp3", "audio/mpeg",
        "Plays everywhere. The right choice for sharing and publishing.",
        lossless = false,
    ),
    M4A(
        "M4A", "m4a", "audio/mp4",
        "Smaller than MP3 at the same quality. Best for Apple devices and modern players.",
        lossless = false,
    ),
    WAV(
        "WAV", "wav", "audio/wav",
        "Uncompressed and exact. For sending to an editor or an archive.",
        lossless = true,
    ),
    FLAC(
        "FLAC", "flac", "audio/flac",
        "Exact like WAV, at about half the size. For keeping.",
        lossless = true,
    ),
    ;

    public companion object {
        /** Default. MP3 first because it is the answer for most people most of the time. */
        public val panelOrder: List<ExportFormat> = listOf(MP3, M4A, WAV, FLAC)
    }
}

/** Quality choice for the lossy formats, expressed as what it is for rather than as a bitrate. */
public enum class ExportQuality(
    public val displayName: String,
    public val bitrateKbps: Int,
    public val summary: String,
) {
    VOICE("Voice", 96, "Speech only. Smallest files."),
    STANDARD("Standard", 160, "The default. Right for almost everything."),
    HIGH("High", 224, "For music, or for material that will be edited again."),
    MAXIMUM("Maximum", 320, "The most a lossy format can carry."),
}

/** Tags written into the exported file where the format supports them. */
public data class ExportMetadata(
    val title: String? = null,
    val artist: String? = null,
    val album: String? = null,
    val comment: String? = null,
    val year: Int? = null,
    val trackNumber: Int? = null,
    /** Always written, so a file can be traced back to what made it. */
    val encodedBy: String = "SAUTIY",
)

/** WAV, via the codec of chapter 7. */
public class WavEncoder(
    private val encoding: SampleEncoding = SampleEncoding.PCM_24_LE,
) : AudioEncoder {
    override val format: ExportFormat get() = ExportFormat.WAV

    override fun encode(
        audio: AudioBuffer,
        output: OutputStream,
        metadata: ExportMetadata,
        progress: (Double) -> Unit,
    ) {
        val bytes = ai.sautiy.core.audio.PcmCodec.encode(audio, encoding)
        WavCodec.writeHeader(
            out = output,
            format = ai.sautiy.core.audio.AudioFormat(audio.sampleRate, audio.channelCount, encoding),
            dataBytes = bytes.size.toLong(),
        )
        // Written in blocks so progress is real rather than a jump from zero to one.
        val block = 1 shl 18
        var written = 0
        while (written < bytes.size) {
            val count = minOf(block, bytes.size - written)
            output.write(bytes, written, count)
            written += count
            progress(written.toDouble() / bytes.size)
        }
        progress(1.0)
    }
}

/**
 * The registry the export panel reads.
 *
 * Encoders that need a platform — AAC through Android's MediaCodec, for instance — register
 * themselves at startup. The core neither knows nor cares which are present; the panel simply
 * offers what has been registered, so a format is never listed and then found not to work.
 */
public object Encoders {

    private val registry = LinkedHashMap<ExportFormat, () -> AudioEncoder>()

    init {
        register(ExportFormat.WAV) { WavEncoder() }
        register(ExportFormat.FLAC) { FlacEncoder() }
    }

    public fun register(format: ExportFormat, factory: () -> AudioEncoder) {
        registry[format] = factory
    }

    public fun isAvailable(format: ExportFormat): Boolean = registry.containsKey(format)

    public fun create(format: ExportFormat): AudioEncoder =
        registry[format]?.invoke()
            ?: error(
                "No encoder is registered for ${format.displayName}. " +
                    "The export panel must not offer a format that cannot be written.",
            )

    /** Formats actually writable right now, in panel order. */
    public fun available(): List<ExportFormat> = ExportFormat.panelOrder.filter { isAvailable(it) }
}
