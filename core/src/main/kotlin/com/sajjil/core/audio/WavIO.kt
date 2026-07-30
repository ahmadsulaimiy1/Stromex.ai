package com.sajjil.core.audio

import java.io.ByteArrayOutputStream
import java.io.OutputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder

enum class BitDepth(val bits: Int) { PCM_16(16), PCM_24(24), FLOAT_32(32) }

data class WavAudio(
    val samples: FloatArray,
    val sampleRate: Int,
    val channels: Int,
) {
    override fun equals(other: Any?): Boolean =
        other is WavAudio && sampleRate == other.sampleRate && channels == other.channels && samples.contentEquals(other.samples)

    override fun hashCode(): Int = 31 * (31 * samples.contentHashCode() + sampleRate) + channels
}

/** Reads and writes canonical PCM WAV (RIFF) files, supporting 16-bit / 24-bit int and 32-bit float. */
object WavIO {

    fun write(
        samples: FloatArray,
        sampleRate: Int,
        channels: Int = 1,
        bitDepth: BitDepth = BitDepth.PCM_16,
    ): ByteArray {
        val out = ByteArrayOutputStream()
        write(out, samples, sampleRate, channels, bitDepth)
        return out.toByteArray()
    }

    fun write(
        out: OutputStream,
        samples: FloatArray,
        sampleRate: Int,
        channels: Int,
        bitDepth: BitDepth,
    ) {
        val bytesPerSample = bitDepth.bits / 8
        val dataSize = samples.size * bytesPerSample
        out.write(buildHeader(dataSize, sampleRate, channels, bitDepth))

        val body = ByteBuffer.allocate(dataSize).order(ByteOrder.LITTLE_ENDIAN)
        for (s in samples) encodeSample(body, s, bitDepth)
        out.write(body.array())
    }

    internal fun encodeSample(buffer: ByteBuffer, sample: Float, bitDepth: BitDepth) {
        val clamped = sample.coerceIn(-1f, 1f)
        when (bitDepth) {
            BitDepth.PCM_16 -> buffer.putShort((clamped * Short.MAX_VALUE).toInt().toShort())
            BitDepth.PCM_24 -> {
                val v = (clamped * 8388607f).toInt()
                buffer.put((v and 0xFF).toByte())
                buffer.put(((v shr 8) and 0xFF).toByte())
                buffer.put(((v shr 16) and 0xFF).toByte())
            }
            BitDepth.FLOAT_32 -> buffer.putFloat(clamped)
        }
    }

    internal fun buildHeader(dataSize: Int, sampleRate: Int, channels: Int, bitDepth: BitDepth): ByteArray {
        val bytesPerSample = bitDepth.bits / 8
        val byteRate = sampleRate * channels * bytesPerSample
        val blockAlign = channels * bytesPerSample
        val audioFormat = if (bitDepth == BitDepth.FLOAT_32) 3 else 1

        val header = ByteBuffer.allocate(44).order(ByteOrder.LITTLE_ENDIAN)
        header.put("RIFF".toByteArray())
        header.putInt(36 + dataSize)
        header.put("WAVE".toByteArray())
        header.put("fmt ".toByteArray())
        header.putInt(16)
        header.putShort(audioFormat.toShort())
        header.putShort(channels.toShort())
        header.putInt(sampleRate)
        header.putInt(byteRate)
        header.putShort(blockAlign.toShort())
        header.putShort(bitDepth.bits.toShort())
        header.put("data".toByteArray())
        header.putInt(dataSize)
        return header.array()
    }

    fun read(bytes: ByteArray): WavAudio {
        val buf = ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN)
        require(buf.int == riffTag) { "Not a RIFF file" }
        buf.int // chunk size
        require(buf.int == waveTag) { "Not a WAVE file" }

        var channels = 1
        var sampleRate = 44100
        var bitsPerSample = 16
        var audioFormat = 1
        var samples = FloatArray(0)

        while (buf.remaining() >= 8) {
            val chunkId = buf.int
            val chunkSize = buf.int
            when (chunkId) {
                fmtTag -> {
                    val chunkStart = buf.position()
                    audioFormat = buf.short.toInt()
                    channels = buf.short.toInt()
                    sampleRate = buf.int
                    buf.int // byte rate
                    buf.short // block align
                    bitsPerSample = buf.short.toInt()
                    buf.position(chunkStart + chunkSize)
                }
                dataTag -> {
                    val bytesPerSample = bitsPerSample / 8
                    val count = chunkSize / bytesPerSample
                    samples = FloatArray(count)
                    for (i in 0 until count) {
                        samples[i] = when {
                            audioFormat == 3 && bitsPerSample == 32 -> buf.float
                            bitsPerSample == 16 -> buf.short / Short.MAX_VALUE.toFloat()
                            bitsPerSample == 24 -> {
                                val b0 = buf.get().toInt() and 0xFF
                                val b1 = buf.get().toInt() and 0xFF
                                val b2 = buf.get().toInt()
                                val v = (b2 shl 16) or (b1 shl 8) or b0
                                v / 8388608f
                            }
                            else -> error("Unsupported bit depth: $bitsPerSample")
                        }
                    }
                }
                else -> buf.position((buf.position() + chunkSize).coerceAtMost(buf.limit()))
            }
            if (chunkSize % 2 == 1 && buf.remaining() > 0) buf.get()
        }
        return WavAudio(samples, sampleRate, channels)
    }

    private const val riffTag = 0x46464952 // "RIFF" little-endian
    private const val waveTag = 0x45564157 // "WAVE"
    private const val fmtTag = 0x20746d66 // "fmt "
    private const val dataTag = 0x61746164 // "data"
}
