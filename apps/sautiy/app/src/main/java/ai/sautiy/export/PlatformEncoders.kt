package ai.sautiy.export

import ai.sautiy.core.audio.AudioBuffer
import ai.sautiy.core.audio.PcmCodec
import ai.sautiy.core.audio.SampleEncoding
import ai.sautiy.core.codec.AudioEncoder
import ai.sautiy.core.codec.Encoders
import ai.sautiy.core.codec.ExportFormat
import ai.sautiy.core.codec.ExportMetadata
import ai.sautiy.core.codec.ExportQuality
import android.media.MediaCodec
import android.media.MediaCodecInfo
import android.media.MediaFormat
import java.io.OutputStream
import java.nio.ByteBuffer

/**
 * Encoders that need the device — Editorial Bible chapter 14.
 *
 * The core's registry knows nothing about Android. This object is where a platform-backed
 * format becomes available, and the registration is conditional: if the device has no AAC
 * encoder, M4A is simply never offered, rather than being offered and then failing at the
 * moment the user presses Export.
 *
 * **MP3 needs the NDK.** Android's `MediaCodec` decodes MP3 but has never encoded it, and no
 * amount of configuration changes that. SAUTIY ships MP3 through LAME as an optional native
 * component; [Mp3Encoder.registerIfAvailable] adds it when `libsautiymp3.so` is in the APK and
 * does nothing when it is not. See `app/src/main/cpp/README.md`.
 */
object PlatformEncoders {

    fun registerAll() {
        if (hasEncoderFor(MediaFormat.MIMETYPE_AUDIO_AAC)) {
            Encoders.register(ExportFormat.M4A) { AacEncoder() }
        }
        // Present only in builds made with -PsautiyMp3=true, which bundle LAME. In every other
        // build MP3 is absent from the panel rather than present and broken.
        Mp3Encoder.registerIfAvailable()
    }

    private fun hasEncoderFor(mimeType: String): Boolean = runCatching {
        val codecs = android.media.MediaCodecList(android.media.MediaCodecList.REGULAR_CODECS)
        codecs.codecInfos.any { info -> info.isEncoder && info.supportedTypes.any { it.equals(mimeType, true) } }
    }.getOrDefault(false)
}

/**
 * AAC in an ADTS stream, through the platform encoder.
 *
 * ADTS rather than an MP4 container because ADTS frames carry their own headers, which means
 * the encode is a straight pipe to an [OutputStream] and never needs to seek — so an export can
 * be written directly into a document the user picked, over a content URI that may not be
 * seekable at all.
 */
private class AacEncoder(
    private val quality: ExportQuality = ExportQuality.STANDARD,
) : AudioEncoder {

    override val format: ExportFormat get() = ExportFormat.M4A

    override fun encode(
        audio: AudioBuffer,
        output: OutputStream,
        metadata: ExportMetadata,
        progress: (Double) -> Unit,
    ) {
        val mediaFormat = MediaFormat.createAudioFormat(
            MediaFormat.MIMETYPE_AUDIO_AAC,
            audio.sampleRate,
            audio.channelCount,
        ).apply {
            setInteger(MediaFormat.KEY_AAC_PROFILE, MediaCodecInfo.CodecProfileLevel.AACObjectLC)
            setInteger(MediaFormat.KEY_BIT_RATE, quality.bitrateKbps * 1_000)
            setInteger(MediaFormat.KEY_MAX_INPUT_SIZE, MAX_INPUT_BYTES)
        }

        val codec = MediaCodec.createEncoderByType(MediaFormat.MIMETYPE_AUDIO_AAC)
        codec.configure(mediaFormat, null, null, MediaCodec.CONFIGURE_FLAG_ENCODE)
        codec.start()

        val pcm = PcmCodec.encode(audio.copy().clampInPlace(), SampleEncoding.PCM_16_LE)
        val info = MediaCodec.BufferInfo()
        var inputOffset = 0
        var sawInputEnd = false
        var sawOutputEnd = false

        try {
            while (!sawOutputEnd) {
                if (!sawInputEnd) {
                    val index = codec.dequeueInputBuffer(TIMEOUT_US)
                    if (index >= 0) {
                        val buffer: ByteBuffer = codec.getInputBuffer(index) ?: continue
                        buffer.clear()
                        val count = minOf(buffer.capacity(), pcm.size - inputOffset)
                        if (count <= 0) {
                            codec.queueInputBuffer(
                                index, 0, 0, presentationTimeFor(inputOffset, audio),
                                MediaCodec.BUFFER_FLAG_END_OF_STREAM,
                            )
                            sawInputEnd = true
                        } else {
                            buffer.put(pcm, inputOffset, count)
                            codec.queueInputBuffer(index, 0, count, presentationTimeFor(inputOffset, audio), 0)
                            inputOffset += count
                            progress(inputOffset.toDouble() / pcm.size)
                        }
                    }
                }

                val outputIndex = codec.dequeueOutputBuffer(info, TIMEOUT_US)
                if (outputIndex >= 0) {
                    val buffer = codec.getOutputBuffer(outputIndex)
                    if (buffer != null && info.size > 0 &&
                        info.flags and MediaCodec.BUFFER_FLAG_CODEC_CONFIG == 0
                    ) {
                        val frame = ByteArray(info.size)
                        buffer.position(info.offset)
                        buffer.get(frame, 0, info.size)
                        output.write(adtsHeader(info.size, audio.sampleRate, audio.channelCount))
                        output.write(frame)
                    }
                    codec.releaseOutputBuffer(outputIndex, false)
                    if (info.flags and MediaCodec.BUFFER_FLAG_END_OF_STREAM != 0) sawOutputEnd = true
                }
            }
        } finally {
            runCatching { codec.stop() }
            codec.release()
        }
        progress(1.0)
    }

    private fun presentationTimeFor(byteOffset: Int, audio: AudioBuffer): Long {
        val frames = byteOffset / (2 * audio.channelCount)
        return frames * 1_000_000L / audio.sampleRate
    }

    /** A seven-byte ADTS header per frame, so the stream is self-describing. */
    private fun adtsHeader(payloadBytes: Int, sampleRate: Int, channelCount: Int): ByteArray {
        val total = payloadBytes + 7
        val samplingIndex = SAMPLING_FREQUENCIES.indexOf(sampleRate).takeIf { it >= 0 } ?: 4
        val header = ByteArray(7)

        header[0] = 0xFF.toByte()
        header[1] = 0xF1.toByte() // MPEG-4, layer 0, no CRC
        header[2] = (((PROFILE_AAC_LC - 1) shl 6) or (samplingIndex shl 2) or (channelCount shr 2)).toByte()
        header[3] = (((channelCount and 3) shl 6) or (total shr 11)).toByte()
        header[4] = ((total and 0x7FF) shr 3).toByte()
        header[5] = (((total and 7) shl 5) or 0x1F).toByte()
        header[6] = 0xFC.toByte()
        return header
    }

    private companion object {
        const val TIMEOUT_US = 10_000L
        const val MAX_INPUT_BYTES = 32 * 1024
        const val PROFILE_AAC_LC = 2
        val SAMPLING_FREQUENCIES = intArrayOf(
            96_000, 88_200, 64_000, 48_000, 44_100, 32_000,
            24_000, 22_050, 16_000, 12_000, 11_025, 8_000, 7_350,
        )
    }
}
