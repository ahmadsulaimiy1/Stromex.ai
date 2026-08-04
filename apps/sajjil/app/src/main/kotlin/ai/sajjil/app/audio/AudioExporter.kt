package ai.sajjil.app.audio

import ai.sajjil.audio.AudioBuffer
import ai.sajjil.audio.codec.FlacEncoder
import ai.sajjil.audio.codec.WavBitDepth
import ai.sajjil.audio.codec.WavWriter
import android.media.MediaCodec
import android.media.MediaCodecInfo
import android.media.MediaFormat
import android.media.MediaMuxer
import java.io.File
import java.io.IOException
import java.io.OutputStream
import java.nio.ByteBuffer

/** Where an export ended up, and what it is. */
data class ExportResult(
    val file: File,
    val format: ExportFormat,
    val sizeBytes: Long,
)

/** An export that could not be completed, phrased for the user rather than for a log. */
class ExportException(val userMessage: String, cause: Throwable? = null) : Exception(userMessage, cause)

/**
 * Writes an [AudioBuffer] out in a chosen format.
 *
 * Lossless formats are encoded in Kotlin by `core-audio`, so they behave identically on every
 * device. Lossy formats go through MediaCodec, because a hand-written psychoacoustic encoder
 * would be both enormous and worse than the hardware one sitting in the phone.
 */
class AudioExporter {

    /**
     * @param onProgress 0..1. Called often enough to animate a progress bar smoothly.
     * @throws ExportException with a message that can be shown as-is.
     */
    fun export(
        buffer: AudioBuffer,
        target: File,
        format: ExportFormat,
        quality: ExportQuality = ExportQuality.DEFAULT,
        onProgress: ((Double) -> Unit)? = null,
    ): ExportResult {
        target.parentFile?.mkdirs()
        try {
            when (format) {
                ExportFormat.WAV -> exportWav(buffer, target, onProgress)
                ExportFormat.FLAC -> exportFlac(buffer, target, onProgress)
                ExportFormat.M4A -> exportWithCodec(buffer, target, quality, muxed = true, onProgress)
                ExportFormat.AAC -> exportWithCodec(buffer, target, quality, muxed = false, onProgress)
                ExportFormat.MP3 -> exportMp3(buffer, target, quality, onProgress)
            }
        } catch (error: ExportException) {
            target.delete()
            throw error
        } catch (error: IOException) {
            target.delete()
            throw ExportException(
                "SAJJIL ran out of room while saving this export. Free up some space and try again.",
                error,
            )
        } catch (error: Exception) {
            target.delete()
            throw ExportException(
                "This recording could not be exported as ${format.displayName}. " +
                    "Exporting as WAV will always work.",
                error,
            )
        }
        onProgress?.invoke(1.0)
        return ExportResult(target, format, target.length())
    }

    private fun exportWav(buffer: AudioBuffer, target: File, onProgress: ((Double) -> Unit)?) {
        target.outputStream().buffered().use { out ->
            // 24-bit for exports: the working files are 16-bit, but anything that has been
            // through the enhancement chain has more resolution than 16 bits can hold, and this
            // is the format people take into another editor.
            WavWriter.write(buffer, out, WavBitDepth.PCM_24)
        }
        onProgress?.invoke(1.0)
    }

    private fun exportFlac(buffer: AudioBuffer, target: File, onProgress: ((Double) -> Unit)?) {
        target.outputStream().buffered().use { out ->
            FlacEncoder(buffer.sampleRate, buffer.channelCount, bitsPerSample = 24)
                .encode(buffer, out, onProgress)
        }
    }

    private fun exportMp3(
        buffer: AudioBuffer,
        target: File,
        quality: ExportQuality,
        onProgress: ((Double) -> Unit)?,
    ) {
        if (!ExportFormat.MP3.hasPlatformEncoder()) {
            throw ExportException(
                "This device has no MP3 encoder, so SAJJIL cannot write MP3 files on it. " +
                    "M4A is the same size and plays everywhere MP3 does."
            )
        }
        // MP3 is self-framing, so the encoder's output is a complete file with no container.
        encodeElementaryStream(
            buffer = buffer,
            mimeType = MediaFormat.MIMETYPE_AUDIO_MPEG,
            bitrate = quality.bitrate,
            target = target,
            addAdtsHeaders = false,
            onProgress = onProgress,
        )
    }

    /** AAC, either muxed into an MP4 container (`.m4a`) or as a raw ADTS stream (`.aac`). */
    private fun exportWithCodec(
        buffer: AudioBuffer,
        target: File,
        quality: ExportQuality,
        muxed: Boolean,
        onProgress: ((Double) -> Unit)?,
    ) {
        if (muxed) {
            encodeToMp4(buffer, target, quality, onProgress)
        } else {
            encodeElementaryStream(
                buffer = buffer,
                mimeType = MediaFormat.MIMETYPE_AUDIO_AAC,
                bitrate = quality.bitrate,
                target = target,
                addAdtsHeaders = true,
                onProgress = onProgress,
            )
        }
    }

    private fun encodeToMp4(
        buffer: AudioBuffer,
        target: File,
        quality: ExportQuality,
        onProgress: ((Double) -> Unit)?,
    ) {
        val format = aacFormat(buffer, quality)
        val codec = MediaCodec.createEncoderByType(MediaFormat.MIMETYPE_AUDIO_AAC)
        val muxer = MediaMuxer(target.absolutePath, MediaMuxer.OutputFormat.MUXER_OUTPUT_MPEG_4)
        var trackIndex = -1
        var muxerStarted = false

        try {
            codec.configure(format, null, null, MediaCodec.CONFIGURE_FLAG_ENCODE)
            codec.start()
            drive(codec, buffer, onProgress) { encoded, info ->
                if (!muxerStarted) {
                    trackIndex = muxer.addTrack(codec.outputFormat)
                    muxer.start()
                    muxerStarted = true
                }
                muxer.writeSampleData(trackIndex, encoded, info)
            }
        } finally {
            runCatching { codec.stop() }
            codec.release()
            if (muxerStarted) runCatching { muxer.stop() }
            runCatching { muxer.release() }
        }
    }

    private fun encodeElementaryStream(
        buffer: AudioBuffer,
        mimeType: String,
        bitrate: Int,
        target: File,
        addAdtsHeaders: Boolean,
        onProgress: ((Double) -> Unit)?,
    ) {
        val format = MediaFormat.createAudioFormat(mimeType, buffer.sampleRate, buffer.channelCount).apply {
            setInteger(MediaFormat.KEY_BIT_RATE, bitrate)
            if (mimeType == MediaFormat.MIMETYPE_AUDIO_AAC) {
                setInteger(MediaFormat.KEY_AAC_PROFILE, MediaCodecInfo.CodecProfileLevel.AACObjectLC)
            }
            setInteger(MediaFormat.KEY_MAX_INPUT_SIZE, MAX_INPUT_BYTES)
        }

        val codec = MediaCodec.createEncoderByType(mimeType)
        target.outputStream().buffered().use { out ->
            try {
                codec.configure(format, null, null, MediaCodec.CONFIGURE_FLAG_ENCODE)
                codec.start()
                drive(codec, buffer, onProgress) { encoded, info ->
                    val payload = ByteArray(info.size)
                    encoded.get(payload)
                    if (addAdtsHeaders) {
                        out.write(adtsHeader(payload.size, buffer.sampleRate, buffer.channelCount))
                    }
                    out.write(payload)
                }
            } finally {
                runCatching { codec.stop() }
                codec.release()
            }
        }
    }

    private fun aacFormat(buffer: AudioBuffer, quality: ExportQuality): MediaFormat =
        MediaFormat.createAudioFormat(
            MediaFormat.MIMETYPE_AUDIO_AAC,
            buffer.sampleRate,
            buffer.channelCount,
        ).apply {
            setInteger(MediaFormat.KEY_BIT_RATE, quality.bitrate)
            setInteger(MediaFormat.KEY_AAC_PROFILE, MediaCodecInfo.CodecProfileLevel.AACObjectLC)
            setInteger(MediaFormat.KEY_MAX_INPUT_SIZE, MAX_INPUT_BYTES)
        }

    /**
     * Feeds PCM into [codec] and hands each encoded packet to [onEncoded].
     *
     * Synchronous MediaCodec rather than the async callback API: export runs on a background
     * thread already, and the straight-line version is far easier to reason about at the two
     * places this can stall — a full input queue and a drained output queue.
     */
    private fun drive(
        codec: MediaCodec,
        buffer: AudioBuffer,
        onProgress: ((Double) -> Unit)?,
        onEncoded: (ByteBuffer, MediaCodec.BufferInfo) -> Unit,
    ) {
        val info = MediaCodec.BufferInfo()
        val totalFrames = buffer.frameCount
        var framesSubmitted = 0
        var inputDone = false
        var outputDone = false
        var presentationTimeUs = 0L

        while (!outputDone) {
            if (!inputDone) {
                val inputIndex = codec.dequeueInputBuffer(TIMEOUT_US)
                if (inputIndex >= 0) {
                    val input = codec.getInputBuffer(inputIndex)!!
                    input.clear()

                    val capacityFrames = input.capacity() / (2 * buffer.channelCount)
                    val frames = minOf(capacityFrames, totalFrames - framesSubmitted)

                    if (frames <= 0) {
                        codec.queueInputBuffer(
                            inputIndex, 0, 0, presentationTimeUs,
                            MediaCodec.BUFFER_FLAG_END_OF_STREAM,
                        )
                        inputDone = true
                    } else {
                        for (i in 0 until frames) {
                            for (channel in buffer.channels) {
                                val sample = (channel[framesSubmitted + i].coerceIn(-1f, 1f) * 32767f)
                                    .toInt()
                                    .coerceIn(-32768, 32767)
                                input.put((sample and 0xFF).toByte())
                                input.put(((sample shr 8) and 0xFF).toByte())
                            }
                        }
                        val bytes = frames * 2 * buffer.channelCount
                        codec.queueInputBuffer(inputIndex, 0, bytes, presentationTimeUs, 0)
                        framesSubmitted += frames
                        presentationTimeUs = framesSubmitted * 1_000_000L / buffer.sampleRate
                        onProgress?.invoke(framesSubmitted.toDouble() / totalFrames)
                    }
                }
            }

            val outputIndex = codec.dequeueOutputBuffer(info, TIMEOUT_US)
            when {
                outputIndex >= 0 -> {
                    val output = codec.getOutputBuffer(outputIndex)!!
                    // Codec config packets describe the stream; the muxer reads them from
                    // outputFormat instead, and writing them as audio would corrupt the file.
                    if (info.flags and MediaCodec.BUFFER_FLAG_CODEC_CONFIG == 0 && info.size > 0) {
                        output.position(info.offset)
                        output.limit(info.offset + info.size)
                        onEncoded(output, info)
                    }
                    codec.releaseOutputBuffer(outputIndex, false)
                    if (info.flags and MediaCodec.BUFFER_FLAG_END_OF_STREAM != 0) outputDone = true
                }
                outputIndex == MediaCodec.INFO_TRY_AGAIN_LATER -> {
                    // Nothing ready yet. If the input is finished this simply spins until the
                    // encoder flushes its tail, which is bounded by the codec's own latency.
                    if (inputDone && framesSubmitted >= totalFrames) continue
                }
            }
        }
    }

    /**
     * A 7-byte ADTS header for a raw AAC frame.
     *
     * Without it, a `.aac` file is a bare stream that most players cannot open, because nothing
     * tells them the sample rate or channel count.
     */
    private fun adtsHeader(payloadLength: Int, sampleRate: Int, channelCount: Int): ByteArray {
        val frameLength = payloadLength + 7
        val profile = 2 // AAC LC
        val frequencyIndex = ADTS_SAMPLE_RATES.indexOf(sampleRate).let { if (it < 0) 4 else it }

        return byteArrayOf(
            0xFF.toByte(),
            0xF1.toByte(), // MPEG-4, layer 0, no CRC
            (((profile - 1) shl 6) or (frequencyIndex shl 2) or (channelCount shr 2)).toByte(),
            (((channelCount and 3) shl 6) or (frameLength shr 11)).toByte(),
            ((frameLength and 0x7FF) shr 3).toByte(),
            (((frameLength and 7) shl 5) or 0x1F).toByte(),
            0xFC.toByte(),
        )
    }

    private companion object {
        const val TIMEOUT_US = 10_000L
        const val MAX_INPUT_BYTES = 32 * 1024
        val ADTS_SAMPLE_RATES = intArrayOf(
            96000, 88200, 64000, 48000, 44100, 32000,
            24000, 22050, 16000, 12000, 11025, 8000, 7350,
        )
    }
}
