package ai.sautiy.export

import ai.sautiy.core.audio.AudioBuffer
import ai.sautiy.core.audio.PcmCodec
import ai.sautiy.core.audio.SampleEncoding
import ai.sautiy.core.codec.AudioEncoder
import ai.sautiy.core.codec.Encoders
import ai.sautiy.core.codec.ExportFormat
import ai.sautiy.core.codec.ExportMetadata
import ai.sautiy.core.codec.ExportQuality
import java.io.OutputStream

/**
 * MP3 export, through a native LAME encoder loaded at runtime.
 *
 * ## Why this is native
 *
 * Android has never shipped an MP3 *encoder*. `MediaCodec` decodes `audio/mpeg` and will not
 * encode it, on any API level, with any configuration. That is a platform fact, not a gap in
 * this code.
 *
 * That leaves two honest routes: a Layer III encoder written from scratch in Kotlin, or LAME
 * through the NDK. LAME is the right answer for a shipping product — it is the reference-quality
 * encoder, it is what every serious recorder on Android uses, and a hand-written Layer III
 * encoder would have to reproduce roughly 1,500 entries of Huffman table data exactly, where a
 * single wrong code produces files that some decoders open and others reject.
 *
 * ## How it fails safely
 *
 * The native library is loaded **optionally**. If `libsautiymp3.so` is not in the APK — which is
 * the case for any build made without the NDK step in
 * `apps/sautiy/app/src/main/cpp/README.md` — [isAvailable] is false, this encoder is never
 * registered, and MP3 simply does not appear in the export panel.
 *
 * That is deliberate and is chapter 14.2: **a format is never listed unless an encoder for it is
 * actually registered.** The alternative — offering MP3 and failing at the moment the user
 * presses Export, or quietly writing a WAV with an `.mp3` extension — is the exact silent
 * failure this product refuses to ship.
 */
public class Mp3Encoder(
    private val quality: ExportQuality = ExportQuality.STANDARD,
) : AudioEncoder {

    override val format: ExportFormat get() = ExportFormat.MP3

    override fun encode(
        audio: AudioBuffer,
        output: OutputStream,
        metadata: ExportMetadata,
        progress: (Double) -> Unit,
    ) {
        check(isAvailable) { "The MP3 encoder library is not present in this build" }

        // ID3v2 first, so a player knows the title before it has decoded a frame.
        output.write(id3v2(metadata))

        val handle = nativeInit(audio.sampleRate, audio.channelCount, quality.bitrateKbps)
        check(handle != 0L) { "LAME refused the requested configuration" }

        try {
            val pcm = PcmCodec.encode(audio.copy().clampInPlace(), SampleEncoding.PCM_16_LE)
            val bytesPerFrame = 2 * audio.channelCount
            val framesPerBlock = BLOCK_FRAMES
            // LAME's own guidance for the worst-case output size of a block.
            val out = ByteArray((1.25 * framesPerBlock).toInt() + 7_200)

            var frame = 0
            val totalFrames = audio.frameCount
            while (frame < totalFrames) {
                val count = minOf(framesPerBlock, totalFrames - frame)
                val written = nativeEncode(handle, pcm, frame * bytesPerFrame, count, out)
                if (written < 0) {
                    error(
                        when (written) {
                            -1 -> "The MP3 encoder was closed before the encode finished"
                            -2 -> "The MP3 encoder could not reach the audio buffer"
                            -3 -> "The MP3 encoder was asked for $count frames beyond the audio"
                            else -> "LAME reported an encoding failure ($written)"
                        },
                    )
                }
                if (written > 0) output.write(out, 0, written)
                frame += count
                progress(frame.toDouble() / totalFrames)
            }

            val tail = nativeFlush(handle, out)
            if (tail > 0) output.write(out, 0, tail)
        } finally {
            nativeClose(handle)
        }
        progress(1.0)
    }

    /**
     * A minimal ID3v2.3 tag.
     *
     * Written here rather than left to LAME because LAME's tag writer needs a seekable file, and
     * SAUTIY exports into a document URI that may not be seekable at all (chapter 14.3).
     */
    private fun id3v2(metadata: ExportMetadata): ByteArray {
        val frames = buildList {
            metadata.title?.let { add(textFrame("TIT2", it)) }
            metadata.artist?.let { add(textFrame("TPE1", it)) }
            metadata.album?.let { add(textFrame("TALB", it)) }
            metadata.year?.let { add(textFrame("TYER", it.toString())) }
            metadata.trackNumber?.let { add(textFrame("TRCK", it.toString())) }
            metadata.comment?.let { add(textFrame("COMM", it)) }
            add(textFrame("TSSE", metadata.encodedBy))
        }
        val body = frames.reduceOrNull { a, b -> a + b } ?: ByteArray(0)

        val header = ByteArray(10)
        header[0] = 'I'.code.toByte()
        header[1] = 'D'.code.toByte()
        header[2] = '3'.code.toByte()
        header[3] = 3 // version 2.3
        header[4] = 0
        header[5] = 0 // no flags
        // The size is a synchsafe integer: seven bits per byte, so the tag can never contain a
        // byte sequence a decoder would mistake for a frame sync.
        var size = body.size
        for (i in 9 downTo 6) {
            header[i] = (size and 0x7F).toByte()
            size = size shr 7
        }
        return header + body
    }

    private fun textFrame(id: String, value: String): ByteArray {
        // UTF-16 with a byte-order mark, so Arabic titles survive.
        val text = value.toByteArray(Charsets.UTF_16)
        val size = text.size + 1
        val frame = ByteArray(10 + size)
        for (i in 0 until 4) frame[i] = id[i].code.toByte()
        frame[4] = ((size shr 24) and 0xFF).toByte()
        frame[5] = ((size shr 16) and 0xFF).toByte()
        frame[6] = ((size shr 8) and 0xFF).toByte()
        frame[7] = (size and 0xFF).toByte()
        frame[8] = 0
        frame[9] = 0
        frame[10] = 1 // encoding: UTF-16 with BOM
        text.copyInto(frame, 11)
        return frame
    }

    private external fun nativeInit(sampleRate: Int, channels: Int, bitrateKbps: Int): Long
    private external fun nativeEncode(handle: Long, pcm: ByteArray, offset: Int, frames: Int, out: ByteArray): Int
    private external fun nativeFlush(handle: Long, out: ByteArray): Int
    private external fun nativeClose(handle: Long)

    public companion object {
        private const val BLOCK_FRAMES = 8_192

        /**
         * True when the native encoder is present in this APK.
         *
         * Resolved once, at class-load, by attempting the load and treating failure as absence
         * rather than as an error — a build without the NDK step is a valid build, it simply has
         * no MP3.
         */
        private val loadOutcome: Result<Unit> = runCatching { System.loadLibrary("sautiymp3") }

        public val isAvailable: Boolean = loadOutcome.isSuccess

        /**
         * Why the library did not load, when it did not.
         *
         * The first version discarded this, and a build whose native library was missing looked
         * identical to a build where it failed to link — both simply had no MP3, with nothing
         * to act on. An absence a person cannot diagnose is worse than a crash.
         */
        public val unavailableReason: String?
            get() = loadOutcome.exceptionOrNull()?.let { "${it::class.java.simpleName}: ${it.message}" }

        /** Registers MP3 only if it can actually be written. */
        public fun registerIfAvailable() {
            if (isAvailable) {
                Encoders.register(ExportFormat.MP3) { Mp3Encoder() }
            }
        }
    }
}
