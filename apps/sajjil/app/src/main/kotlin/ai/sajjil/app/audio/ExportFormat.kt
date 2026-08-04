package ai.sajjil.app.audio

import android.media.MediaCodecList
import android.media.MediaFormat

/**
 * A format the user can export to.
 *
 * @property isAlwaysAvailable false for formats that depend on a codec the device may not ship.
 *   Formats that are not available are never shown, rather than shown and then failing.
 */
enum class ExportFormat(
    val id: String,
    val displayName: String,
    val extension: String,
    val mimeType: String,
    val summary: String,
    val isLossless: Boolean,
    val isAlwaysAvailable: Boolean,
) {
    M4A(
        id = "m4a",
        displayName = "M4A",
        extension = "m4a",
        mimeType = "audio/mp4",
        summary = "Small file, plays everywhere. Best for sharing.",
        isLossless = false,
        isAlwaysAvailable = true,
    ),

    AAC(
        id = "aac",
        displayName = "AAC",
        extension = "aac",
        mimeType = "audio/aac",
        summary = "The same audio as M4A without the wrapper, for broadcast workflows.",
        isLossless = false,
        isAlwaysAvailable = true,
    ),

    MP3(
        id = "mp3",
        displayName = "MP3",
        extension = "mp3",
        mimeType = "audio/mpeg",
        summary = "The most widely compatible format of all.",
        isLossless = false,
        // Android guarantees an MP3 *decoder* but not an encoder. Some devices ship one; most do
        // not. Availability is therefore checked on the device rather than assumed.
        isAlwaysAvailable = false,
    ),

    WAV(
        id = "wav",
        displayName = "WAV",
        extension = "wav",
        mimeType = "audio/wav",
        summary = "Uncompressed and exact. Large files, for editing elsewhere.",
        isLossless = true,
        isAlwaysAvailable = true,
    ),

    FLAC(
        id = "flac",
        displayName = "FLAC",
        extension = "flac",
        mimeType = "audio/flac",
        summary = "Exact like WAV, at roughly half the size. For archiving.",
        isLossless = true,
        isAlwaysAvailable = true,
    );

    companion object {

        /**
         * The formats this device can actually produce.
         *
         * WAV and FLAC are encoded by SAJJIL itself, so they are always here. M4A and AAC use the
         * platform AAC encoder, which every Android device is required to ship. MP3 appears only
         * where the device really has an MP3 encoder.
         */
        fun availableOn(): List<ExportFormat> =
            entries.filter { it.isAlwaysAvailable || it.hasPlatformEncoder() }

        fun byId(id: String): ExportFormat? = entries.firstOrNull { it.id == id }
    }
}

/** Whether the platform exposes an encoder for this format's codec. */
fun ExportFormat.hasPlatformEncoder(): Boolean {
    val codecMime = when (this) {
        ExportFormat.MP3 -> MediaFormat.MIMETYPE_AUDIO_MPEG
        ExportFormat.M4A, ExportFormat.AAC -> MediaFormat.MIMETYPE_AUDIO_AAC
        // Encoded in Kotlin, so no platform codec is involved.
        ExportFormat.WAV, ExportFormat.FLAC -> return true
    }
    return runCatching {
        MediaCodecList(MediaCodecList.REGULAR_CODECS).codecInfos.any { info ->
            info.isEncoder && info.supportedTypes.any { it.equals(codecMime, ignoreCase = true) }
        }
    }.getOrDefault(false)
}

/** Bitrate choices for the lossy formats. */
enum class ExportQuality(
    val displayName: String,
    val bitrate: Int,
    val summary: String,
) {
    VOICE("Voice", 96_000, "Smallest. Fine for speech."),
    STANDARD("Standard", 160_000, "The right choice for almost everything."),
    HIGH("High", 256_000, "For recitation and music."),
    MAXIMUM("Maximum", 320_000, "As close to the original as a compressed file gets.");

    companion object {
        val DEFAULT = STANDARD
    }
}
