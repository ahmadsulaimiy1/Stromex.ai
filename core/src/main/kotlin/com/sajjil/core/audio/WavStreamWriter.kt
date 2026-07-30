package com.sajjil.core.audio

import java.io.File
import java.io.RandomAccessFile
import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * Writes a WAV file incrementally as samples arrive from the live recording
 * chain, instead of buffering an entire session (a full Qur'an sitting can
 * run well past an hour) in memory. A placeholder header is written first
 * and patched with the true RIFF/data sizes in [close].
 */
class WavStreamWriter(
    file: File,
    private val sampleRate: Int,
    private val channels: Int,
    private val bitDepth: BitDepth,
) {
    private val raf = RandomAccessFile(file, "rw")
    private var bytesWritten = 0L

    init {
        raf.write(WavIO.buildHeader(0, sampleRate, channels, bitDepth))
    }

    fun write(samples: FloatArray, count: Int = samples.size) {
        val bytesPerSample = bitDepth.bits / 8
        val buffer = ByteBuffer.allocate(count * bytesPerSample).order(ByteOrder.LITTLE_ENDIAN)
        for (i in 0 until count) WavIO.encodeSample(buffer, samples[i], bitDepth)
        raf.write(buffer.array())
        bytesWritten += buffer.array().size
    }

    val durationMs: Long
        get() {
            val bytesPerSample = bitDepth.bits / 8
            val totalSamples = bytesWritten / bytesPerSample / channels
            return (totalSamples * 1000L) / sampleRate
        }

    fun close() {
        raf.seek(0)
        raf.write(WavIO.buildHeader(bytesWritten.toInt(), sampleRate, channels, bitDepth))
        raf.close()
    }
}
