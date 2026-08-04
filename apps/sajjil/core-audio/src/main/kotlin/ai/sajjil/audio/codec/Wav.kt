package ai.sajjil.audio.codec

import ai.sajjil.audio.AudioBuffer
import java.io.EOFException
import java.io.InputStream
import java.io.OutputStream
import kotlin.math.roundToLong

/** Bit depths this codec reads and writes. */
enum class WavBitDepth(val bits: Int, val isFloat: Boolean) {
    PCM_16(16, false),
    PCM_24(24, false),
    PCM_32(32, false),
    FLOAT_32(32, true);

    companion object {
        fun of(bits: Int, isFloat: Boolean): WavBitDepth = entries.firstOrNull {
            it.bits == bits && it.isFloat == isFloat
        } ?: throw UnsupportedAudioException(
            "SAJJIL can read 16, 24 and 32-bit WAV files. This one is $bits-bit" +
                if (isFloat) " floating point." else "."
        )
    }
}

/** Raised when a file is readable but in a form the app does not handle. */
class UnsupportedAudioException(message: String) : Exception(message)

/** Raised when a file is not the format it claims to be, or is truncated. */
class MalformedAudioException(message: String) : Exception(message)

/**
 * RIFF/WAVE reader and writer.
 *
 * WAV is the app's working format: recording writes it directly, and every edit and export reads
 * from it. It is uncompressed and header-simple, so a recording that is interrupted by a crash is
 * still a valid file once the header is repaired — which is exactly what
 * [WavWriter.repairTruncated] does.
 */
object WavWriter {

    /** Writes [buffer] as a complete RIFF/WAVE file. */
    fun write(buffer: AudioBuffer, out: OutputStream, depth: WavBitDepth = WavBitDepth.PCM_16) {
        val bytesPerSample = depth.bits / 8
        val dataBytes = buffer.frameCount.toLong() * buffer.channelCount * bytesPerSample
        writeHeader(out, buffer.sampleRate, buffer.channelCount, depth, dataBytes)
        writeSamples(buffer, out, depth)
        out.flush()
    }

    fun writeHeader(
        out: OutputStream,
        sampleRate: Int,
        channelCount: Int,
        depth: WavBitDepth,
        dataBytes: Long,
    ) {
        val bytesPerSample = depth.bits / 8
        val byteRate = sampleRate.toLong() * channelCount * bytesPerSample
        val blockAlign = channelCount * bytesPerSample
        // 36 is the size of everything after the RIFF size field up to the data payload.
        val riffSize = 36L + dataBytes

        out.write("RIFF".toByteArray(Charsets.US_ASCII))
        writeLittleEndian32(out, riffSize.toInt())
        out.write("WAVE".toByteArray(Charsets.US_ASCII))

        out.write("fmt ".toByteArray(Charsets.US_ASCII))
        writeLittleEndian32(out, 16)
        // 1 = integer PCM, 3 = IEEE float.
        writeLittleEndian16(out, if (depth.isFloat) 3 else 1)
        writeLittleEndian16(out, channelCount)
        writeLittleEndian32(out, sampleRate)
        writeLittleEndian32(out, byteRate.toInt())
        writeLittleEndian16(out, blockAlign)
        writeLittleEndian16(out, depth.bits)

        out.write("data".toByteArray(Charsets.US_ASCII))
        writeLittleEndian32(out, dataBytes.toInt())
    }

    /** Byte offset of the `data` chunk payload in a header written by [writeHeader]. */
    const val HEADER_BYTES = 44

    fun writeSamples(buffer: AudioBuffer, out: OutputStream, depth: WavBitDepth) {
        val bytesPerSample = depth.bits / 8
        val block = ByteArray(buffer.channelCount * bytesPerSample * WRITE_BLOCK_FRAMES)
        var frame = 0
        while (frame < buffer.frameCount) {
            val frames = minOf(WRITE_BLOCK_FRAMES, buffer.frameCount - frame)
            var offset = 0
            for (i in 0 until frames) {
                for (channel in buffer.channels) {
                    offset = encodeSample(channel[frame + i], block, offset, depth)
                }
            }
            out.write(block, 0, offset)
            frame += frames
        }
    }

    /** Encodes one sample into [target] at [offset], returning the next offset. */
    fun encodeSample(sample: Float, target: ByteArray, offset: Int, depth: WavBitDepth): Int {
        var at = offset
        when (depth) {
            WavBitDepth.PCM_16 -> {
                val v = scaleToInt(sample, 32767.0).toInt()
                target[at++] = (v and 0xFF).toByte()
                target[at++] = ((v shr 8) and 0xFF).toByte()
            }
            WavBitDepth.PCM_24 -> {
                val v = scaleToInt(sample, 8388607.0).toInt()
                target[at++] = (v and 0xFF).toByte()
                target[at++] = ((v shr 8) and 0xFF).toByte()
                target[at++] = ((v shr 16) and 0xFF).toByte()
            }
            WavBitDepth.PCM_32 -> {
                val v = scaleToInt(sample, 2147483647.0)
                target[at++] = (v and 0xFF).toByte()
                target[at++] = ((v shr 8) and 0xFF).toByte()
                target[at++] = ((v shr 16) and 0xFF).toByte()
                target[at++] = ((v shr 24) and 0xFF).toByte()
            }
            WavBitDepth.FLOAT_32 -> {
                val bits = java.lang.Float.floatToIntBits(sample)
                target[at++] = (bits and 0xFF).toByte()
                target[at++] = ((bits shr 8) and 0xFF).toByte()
                target[at++] = ((bits shr 16) and 0xFF).toByte()
                target[at++] = ((bits shr 24) and 0xFF).toByte()
            }
        }
        return at
    }

    /**
     * Rewrites the two size fields of a WAV whose header says one thing and whose payload says
     * another — the state a file is left in when recording is killed by the system.
     *
     * @return the number of audio bytes the repaired file contains.
     */
    fun repairTruncated(header: ByteArray, actualFileBytes: Long): Long {
        require(header.size >= HEADER_BYTES) { "not enough header bytes to repair" }
        val dataBytes = actualFileBytes - HEADER_BYTES
        require(dataBytes >= 0) { "file is shorter than a WAV header" }
        putLittleEndian32(header, 4, (36L + dataBytes).toInt())
        putLittleEndian32(header, 40, dataBytes.toInt())
        return dataBytes
    }

    private const val WRITE_BLOCK_FRAMES = 4096

    private fun scaleToInt(sample: Float, fullScale: Double): Int {
        val clamped = sample.coerceIn(-1f, 1f).toDouble()
        return (clamped * fullScale).roundToLong().toInt()
    }

    private fun writeLittleEndian16(out: OutputStream, value: Int) {
        out.write(value and 0xFF)
        out.write((value shr 8) and 0xFF)
    }

    private fun writeLittleEndian32(out: OutputStream, value: Int) {
        out.write(value and 0xFF)
        out.write((value shr 8) and 0xFF)
        out.write((value shr 16) and 0xFF)
        out.write((value shr 24) and 0xFF)
    }

    private fun putLittleEndian32(target: ByteArray, offset: Int, value: Int) {
        target[offset] = (value and 0xFF).toByte()
        target[offset + 1] = ((value shr 8) and 0xFF).toByte()
        target[offset + 2] = ((value shr 16) and 0xFF).toByte()
        target[offset + 3] = ((value shr 24) and 0xFF).toByte()
    }
}

/** What a WAV's headers declare, without reading the audio. */
data class WavInfo(
    val sampleRate: Int,
    val channelCount: Int,
    val depth: WavBitDepth,
    val frameCount: Int,
)

object WavReader {

    /**
     * Reads a whole WAV file.
     *
     * Chunks other than `fmt ` and `data` (LIST, INFO, and anything a phone's recorder decided to
     * add) are skipped rather than rejected, because refusing to open a file over a metadata
     * chunk is exactly the kind of failure users cannot act on.
     */
    fun read(input: InputStream): AudioBuffer {
        val stream = input.buffered()
        expectAscii(stream, "RIFF")
        readLittleEndian32(stream) // RIFF size; unreliable in truncated files, so ignored.
        expectAscii(stream, "WAVE")

        var sampleRate = 0
        var channelCount = 0
        var depth: WavBitDepth? = null

        while (true) {
            val chunkId = readAscii(stream, 4) ?: throw MalformedAudioException(
                "This file ends before its audio does. It may have been cut short while saving."
            )
            val chunkSize = readLittleEndian32(stream)
            if (chunkSize < 0) throw MalformedAudioException("This WAV file declares an impossible chunk size.")

            when (chunkId) {
                "fmt " -> {
                    val format = readLittleEndian16(stream)
                    channelCount = readLittleEndian16(stream)
                    sampleRate = readLittleEndian32(stream)
                    readLittleEndian32(stream) // byte rate, derivable
                    readLittleEndian16(stream) // block align, derivable
                    val bits = readLittleEndian16(stream)
                    // 0xFFFE is WAVE_FORMAT_EXTENSIBLE; the real format sits in its extension,
                    // but for PCM and float the bit depth alone is enough to decode correctly.
                    val isFloat = format == 3 || (format == 0xFFFE && bits == 32)
                    if (format != 1 && format != 3 && format != 0xFFFE) {
                        throw UnsupportedAudioException(
                            "This WAV file is compressed in a form SAJJIL cannot open. " +
                                "Convert it to PCM and try again."
                        )
                    }
                    depth = WavBitDepth.of(bits, isFloat)
                    skipFully(stream, (chunkSize - 16).toLong().coerceAtLeast(0))
                }
                "data" -> {
                    val format = depth ?: throw MalformedAudioException(
                        "This WAV file describes its audio after the audio itself, which SAJJIL cannot read."
                    )
                    return readData(stream, sampleRate, channelCount, format, chunkSize)
                }
                else -> skipFully(stream, chunkSize.toLong())
            }
            // Chunks are word-aligned; an odd size is followed by one pad byte.
            if (chunkSize % 2 == 1) skipFully(stream, 1)
        }
    }

    private fun readData(
        stream: InputStream,
        sampleRate: Int,
        channelCount: Int,
        depth: WavBitDepth,
        declaredBytes: Int,
    ): AudioBuffer {
        require(channelCount > 0) { "WAV declares $channelCount channels" }
        val bytesPerSample = depth.bits / 8
        val bytesPerFrame = bytesPerSample * channelCount

        val payload = stream.readBytes()
        // Trust the payload over the header: a file killed mid-write has a stale declared size,
        // and the audio that did land is still perfectly good.
        val usableBytes = if (declaredBytes in 1..payload.size) declaredBytes else payload.size
        val frameCount = usableBytes / bytesPerFrame

        val channels = Array(channelCount) { FloatArray(frameCount) }
        var offset = 0
        for (frame in 0 until frameCount) {
            for (c in 0 until channelCount) {
                channels[c][frame] = decodeSample(payload, offset, depth)
                offset += bytesPerSample
            }
        }
        return AudioBuffer(sampleRate, channels)
    }

    /** Reads only the headers. Used by the library to show duration without loading audio. */
    fun readInfo(input: InputStream, totalBytes: Long): WavInfo {
        val stream = input.buffered()
        expectAscii(stream, "RIFF")
        readLittleEndian32(stream)
        expectAscii(stream, "WAVE")

        var sampleRate = 0
        var channelCount = 0
        var depth: WavBitDepth? = null
        var consumed = 12L

        while (true) {
            val chunkId = readAscii(stream, 4) ?: throw MalformedAudioException("Truncated WAV header.")
            val chunkSize = readLittleEndian32(stream)
            consumed += 8
            when (chunkId) {
                "fmt " -> {
                    val format = readLittleEndian16(stream)
                    channelCount = readLittleEndian16(stream)
                    sampleRate = readLittleEndian32(stream)
                    readLittleEndian32(stream)
                    readLittleEndian16(stream)
                    val bits = readLittleEndian16(stream)
                    depth = WavBitDepth.of(bits, format == 3 || (format == 0xFFFE && bits == 32))
                    skipFully(stream, (chunkSize - 16).toLong().coerceAtLeast(0))
                    consumed += chunkSize
                }
                "data" -> {
                    val format = depth ?: throw MalformedAudioException("WAV data precedes its format.")
                    val available = totalBytes - consumed
                    val bytes = if (chunkSize in 1..available) chunkSize.toLong() else available
                    val bytesPerFrame = (format.bits / 8) * channelCount
                    return WavInfo(
                        sampleRate = sampleRate,
                        channelCount = channelCount,
                        depth = format,
                        frameCount = if (bytesPerFrame > 0) (bytes / bytesPerFrame).toInt() else 0,
                    )
                }
                else -> {
                    skipFully(stream, chunkSize.toLong())
                    consumed += chunkSize
                }
            }
            if (chunkSize % 2 == 1) {
                skipFully(stream, 1)
                consumed += 1
            }
        }
    }

    fun decodeSample(source: ByteArray, offset: Int, depth: WavBitDepth): Float = when (depth) {
        WavBitDepth.PCM_16 -> {
            val v = (source[offset].toInt() and 0xFF) or (source[offset + 1].toInt() shl 8)
            v.toShort() / 32768f
        }
        WavBitDepth.PCM_24 -> {
            var v = (source[offset].toInt() and 0xFF) or
                ((source[offset + 1].toInt() and 0xFF) shl 8) or
                ((source[offset + 2].toInt() and 0xFF) shl 16)
            // Sign-extend from 24 to 32 bits.
            if (v and 0x800000 != 0) v = v or 0xFF000000.toInt()
            v / 8388608f
        }
        WavBitDepth.PCM_32 -> {
            val v = (source[offset].toInt() and 0xFF) or
                ((source[offset + 1].toInt() and 0xFF) shl 8) or
                ((source[offset + 2].toInt() and 0xFF) shl 16) or
                (source[offset + 3].toInt() shl 24)
            (v / 2147483648.0).toFloat()
        }
        WavBitDepth.FLOAT_32 -> {
            val bits = (source[offset].toInt() and 0xFF) or
                ((source[offset + 1].toInt() and 0xFF) shl 8) or
                ((source[offset + 2].toInt() and 0xFF) shl 16) or
                (source[offset + 3].toInt() shl 24)
            java.lang.Float.intBitsToFloat(bits)
        }
    }

    private fun expectAscii(stream: InputStream, expected: String) {
        val actual = readAscii(stream, expected.length)
        if (actual != expected) {
            throw MalformedAudioException(
                "This does not look like a WAV file. SAJJIL can open WAV, and can import M4A, AAC and FLAC."
            )
        }
    }

    private fun readAscii(stream: InputStream, length: Int): String? {
        val bytes = ByteArray(length)
        var read = 0
        while (read < length) {
            val n = stream.read(bytes, read, length - read)
            if (n < 0) return null
            read += n
        }
        return String(bytes, Charsets.US_ASCII)
    }

    private fun readLittleEndian16(stream: InputStream): Int {
        val a = stream.read()
        val b = stream.read()
        if (a < 0 || b < 0) throw EOFException("Unexpected end of WAV file")
        return a or (b shl 8)
    }

    private fun readLittleEndian32(stream: InputStream): Int {
        val a = stream.read()
        val b = stream.read()
        val c = stream.read()
        val d = stream.read()
        if (a < 0 || b < 0 || c < 0 || d < 0) throw EOFException("Unexpected end of WAV file")
        return a or (b shl 8) or (c shl 16) or (d shl 24)
    }

    private fun skipFully(stream: InputStream, count: Long) {
        var remaining = count
        while (remaining > 0) {
            val skipped = stream.skip(remaining)
            if (skipped <= 0) {
                if (stream.read() < 0) return
                remaining--
            } else {
                remaining -= skipped
            }
        }
    }
}
