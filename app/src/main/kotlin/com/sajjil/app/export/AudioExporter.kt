package com.sajjil.app.export

import android.media.MediaCodec
import android.media.MediaCodecInfo
import android.media.MediaFormat
import android.media.MediaMuxer
import com.sajjil.core.audio.BitDepth
import com.sajjil.core.audio.WavIO
import java.io.File
import java.nio.ByteBuffer
import java.nio.ByteOrder

enum class ExportFormat(val displayName: String, val extension: String) {
    WAV("WAV", "wav"),
    M4A_AAC("AAC (M4A)", "m4a"),
}

/**
 * Renders a captured/mastered WAV take to the requested delivery format.
 * WAV re-encoding (bit-depth conversion) and AAC/M4A are implemented
 * natively via [WavIO] and Android's [MediaCodec]/[MediaMuxer] — no
 * third-party codec libraries. FLAC/MP3/OGG/OPUS/ALAC/AIFF require
 * licensed or NDK-cross-compiled codecs and are tracked on the roadmap
 * rather than faked here.
 */
class AudioExporter {

    fun exportWav(sourceWav: File, destination: File, bitDepth: BitDepth) {
        val audio = WavIO.read(sourceWav.readBytes())
        destination.outputStream().use { out ->
            WavIO.write(out, audio.samples, audio.sampleRate, audio.channels, bitDepth)
        }
    }

    /** Encodes to AAC-LC in an M4A container at the given bitrate. */
    fun exportAac(sourceWav: File, destination: File, bitrateBps: Int = 192_000) {
        val audio = WavIO.read(sourceWav.readBytes())
        val mimeType = MediaFormat.MIMETYPE_AUDIO_AAC

        val format = MediaFormat.createAudioFormat(mimeType, audio.sampleRate, audio.channels).apply {
            setInteger(MediaFormat.KEY_AAC_PROFILE, MediaCodecInfo.CodecProfileLevel.AACObjectLC)
            setInteger(MediaFormat.KEY_BIT_RATE, bitrateBps)
        }

        val codec = MediaCodec.createEncoderByType(mimeType)
        codec.configure(format, null, null, MediaCodec.CONFIGURE_FLAG_ENCODE)
        codec.start()

        val muxer = MediaMuxer(destination.absolutePath, MediaMuxer.OutputFormat.MUXER_OUTPUT_MPEG_4)
        var muxerTrackIndex = -1
        var muxerStarted = false
        val bufferInfo = MediaCodec.BufferInfo()

        val pcm = floatsToPcm16(audio.samples)
        var pcmOffset = 0
        var presentationTimeUs = 0L
        val bytesPerFramePerChannel = 2
        val bytesPerSampleFrame = bytesPerFramePerChannel * audio.channels
        var inputDone = false

        try {
            while (true) {
                if (!inputDone) {
                    val inputIndex = codec.dequeueInputBuffer(10_000)
                    if (inputIndex >= 0) {
                        val inputBuffer = codec.getInputBuffer(inputIndex)!!
                        inputBuffer.clear()
                        val remaining = pcm.size - pcmOffset
                        val chunk = minOf(inputBuffer.capacity(), remaining)
                        if (chunk <= 0) {
                            codec.queueInputBuffer(inputIndex, 0, 0, presentationTimeUs, MediaCodec.BUFFER_FLAG_END_OF_STREAM)
                            inputDone = true
                        } else {
                            inputBuffer.put(pcm, pcmOffset, chunk)
                            codec.queueInputBuffer(inputIndex, 0, chunk, presentationTimeUs, 0)
                            val frames = chunk / bytesPerSampleFrame
                            presentationTimeUs += frames * 1_000_000L / audio.sampleRate
                            pcmOffset += chunk
                        }
                    }
                }

                val outputIndex = codec.dequeueOutputBuffer(bufferInfo, 10_000)
                when {
                    outputIndex == MediaCodec.INFO_OUTPUT_FORMAT_CHANGED -> {
                        muxerTrackIndex = muxer.addTrack(codec.outputFormat)
                        muxer.start()
                        muxerStarted = true
                    }
                    outputIndex >= 0 -> {
                        val outputBuffer = codec.getOutputBuffer(outputIndex)!!
                        if (bufferInfo.size > 0 && muxerStarted) {
                            outputBuffer.position(bufferInfo.offset)
                            outputBuffer.limit(bufferInfo.offset + bufferInfo.size)
                            muxer.writeSampleData(muxerTrackIndex, outputBuffer, bufferInfo)
                        }
                        codec.releaseOutputBuffer(outputIndex, false)
                        if (bufferInfo.flags and MediaCodec.BUFFER_FLAG_END_OF_STREAM != 0) break
                    }
                }
            }
        } finally {
            codec.stop()
            codec.release()
            if (muxerStarted) muxer.stop()
            muxer.release()
        }
    }

    private fun floatsToPcm16(samples: FloatArray): ByteArray {
        val buffer = ByteBuffer.allocate(samples.size * 2).order(ByteOrder.LITTLE_ENDIAN)
        for (s in samples) buffer.putShort((s.coerceIn(-1f, 1f) * Short.MAX_VALUE).toInt().toShort())
        return buffer.array()
    }
}
