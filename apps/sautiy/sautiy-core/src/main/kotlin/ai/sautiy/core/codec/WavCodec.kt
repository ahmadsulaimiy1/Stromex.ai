package ai.sautiy.core.codec

import ai.sautiy.core.audio.AudioBuffer
import ai.sautiy.core.audio.AudioFormat
import ai.sautiy.core.audio.PcmCodec
import ai.sautiy.core.audio.SampleEncoding
import java.io.BufferedOutputStream
import java.io.File
import java.io.OutputStream
import java.io.RandomAccessFile

/**
 * RIFF/WAVE reader and writer.
 *
 * WAV is SAUTIY's capture format because it is the only common container that can be written
 * *incrementally and safely*: audio bytes are appended as they arrive, and the two length
 * fields in the header are patched at the end. If the process dies mid-recording the file on
 * disk is still a complete, playable WAV of everything captured up to the last flush — which
 * is precisely what chapter 1.3.5 requires and what a compressed container cannot offer.
 *
 * Reading handles the formats that real files use: PCM (8/16/24/32-bit), IEEE float
 * (32/64-bit), and WAVE_FORMAT_EXTENSIBLE, with unknown chunks skipped rather than rejected.
 */
public object WavCodec {

    private const val FORMAT_PCM = 1
    private const val FORMAT_IEEE_FLOAT = 3
    private const val FORMAT_EXTENSIBLE = 0xFFFE

    private const val HEADER_BYTES = 44
    private const val RIFF_SIZE_OFFSET = 4
    private const val DATA_SIZE_OFFSET = 40

    /** WAV's 32-bit size fields cap a file at 4 GiB; SAUTIY stops short of the ambiguity. */
    public const val MAX_DATA_BYTES: Long = 0xFFFFFFFFL - HEADER_BYTES - 8

    public class WavFormatException(message: String) : IllegalArgumentException(message)

    public data class WavInfo(
        val format: AudioFormat,
        val frameCount: Long,
        val dataOffset: Long,
        val dataBytes: Long,
    ) {
        val durationSeconds: Double get() = frameCount.toDouble() / format.sampleRate
    }

    // --- Reading ---------------------------------------------------------------------------

    /** Parses the header only. Fast enough to run on every file in a library listing. */
    public fun probe(file: File): WavInfo {
        RandomAccessFile(file, "r").use { raf ->
            val header = ByteArray(12)
            if (raf.read(header) < 12) throw WavFormatException("File is too short to be a WAV")
            if (!header.matchesAscii(0, "RIFF")) throw WavFormatException("Not a RIFF file")
            if (!header.matchesAscii(8, "WAVE")) throw WavFormatException("RIFF file is not WAVE")

            var encoding: SampleEncoding? = null
            var sampleRate = 0
            var channelCount = 0
            var dataOffset = -1L
            var dataBytes = 0L

            val chunkHeader = ByteArray(8)
            while (raf.filePointer + 8 <= raf.length()) {
                if (raf.read(chunkHeader) < 8) break
                val id = String(chunkHeader, 0, 4, Charsets.US_ASCII)
                val size = chunkHeader.readUInt32LE(4)
                val bodyStart = raf.filePointer

                when (id) {
                    "fmt " -> {
                        val body = ByteArray(minOf(size, 40L).toInt())
                        raf.readFully(body)
                        var formatTag = body.readUInt16LE(0)
                        channelCount = body.readUInt16LE(2)
                        sampleRate = body.readUInt32LE(4).toInt()
                        val bitsPerSample = body.readUInt16LE(14)

                        if (formatTag == FORMAT_EXTENSIBLE && body.size >= 26) {
                            // The real format lives in the first two bytes of the SubFormat GUID.
                            formatTag = body.readUInt16LE(24)
                        }

                        encoding = when (formatTag) {
                            FORMAT_PCM -> when (bitsPerSample) {
                                8 -> SampleEncoding.PCM_8_UNSIGNED
                                16 -> SampleEncoding.PCM_16_LE
                                24 -> SampleEncoding.PCM_24_LE
                                32 -> SampleEncoding.PCM_32_LE
                                else -> throw WavFormatException("Unsupported PCM depth: $bitsPerSample-bit")
                            }

                            FORMAT_IEEE_FLOAT -> when (bitsPerSample) {
                                32 -> SampleEncoding.FLOAT_32_LE
                                64 -> SampleEncoding.FLOAT_64_LE
                                else -> throw WavFormatException("Unsupported float depth: $bitsPerSample-bit")
                            }

                            else -> throw WavFormatException(
                                "Unsupported WAV encoding (format tag $formatTag). " +
                                    "SAUTIY reads PCM and IEEE float.",
                            )
                        }
                    }

                    "data" -> {
                        dataOffset = bodyStart
                        // A streaming writer that died before patching leaves 0 or 0xFFFFFFFF
                        // here. Trusting the field would report an empty recording; measuring
                        // what is actually on disk recovers every captured sample.
                        val declared = size
                        val actual = raf.length() - bodyStart
                        dataBytes = if (declared == 0L || declared > actual) actual else declared
                    }
                }

                // Chunks are word-aligned: an odd size is followed by a pad byte.
                val advance = size + (size and 1L)
                raf.seek(bodyStart + advance)
            }

            val resolvedEncoding = encoding ?: throw WavFormatException("WAV file has no fmt chunk")
            if (dataOffset < 0) throw WavFormatException("WAV file has no data chunk")
            if (channelCount !in 1..2) {
                throw WavFormatException("SAUTIY reads mono and stereo; this file has $channelCount channels")
            }

            val audioFormat = AudioFormat(sampleRate, channelCount, resolvedEncoding)
            return WavInfo(
                format = audioFormat,
                frameCount = dataBytes / audioFormat.bytesPerFrame,
                dataOffset = dataOffset,
                dataBytes = dataBytes,
            )
        }
    }

    /** Reads a whole file into memory. */
    public fun read(file: File): AudioBuffer = readRange(file, 0, Long.MAX_VALUE)

    /**
     * Reads frames `[startFrame, startFrame + maxFrames)`.
     *
     * Range reading is what lets the waveform, the editor and playback all work on a file far
     * larger than the heap ceiling of chapter 1's performance budget.
     */
    public fun readRange(file: File, startFrame: Long, maxFrames: Long): AudioBuffer {
        val info = probe(file)
        val frames = minOf(maxFrames, (info.frameCount - startFrame).coerceAtLeast(0))
        if (frames <= 0) {
            return AudioBuffer.silence(info.format.channelCount, 0, info.format.sampleRate)
        }
        require(frames <= Int.MAX_VALUE / info.format.bytesPerFrame) { "Requested range is too large for one buffer" }

        val byteCount = (frames * info.format.bytesPerFrame).toInt()
        val bytes = ByteArray(byteCount)
        RandomAccessFile(file, "r").use { raf ->
            raf.seek(info.dataOffset + startFrame * info.format.bytesPerFrame)
            raf.readFully(bytes)
        }
        return PcmCodec.decode(bytes, info.format)
    }

    // --- Writing ----------------------------------------------------------------------------

    /** Writes a complete buffer in one call. */
    public fun write(file: File, buffer: AudioBuffer, encoding: SampleEncoding = SampleEncoding.PCM_16_LE) {
        file.parentFile?.mkdirs()
        BufferedOutputStream(file.outputStream(), 64 * 1024).use { out ->
            val bytes = PcmCodec.encode(buffer, encoding)
            writeHeader(
                out = out,
                format = AudioFormat(buffer.sampleRate, buffer.channelCount, encoding),
                dataBytes = bytes.size.toLong(),
            )
            out.write(bytes)
        }
    }

    internal fun writeHeader(out: OutputStream, format: AudioFormat, dataBytes: Long) {
        val bitsPerSample = format.encoding.bytesPerSample * 8
        val formatTag = if (format.encoding.isFloat) FORMAT_IEEE_FLOAT else FORMAT_PCM
        val byteRate = format.sampleRate.toLong() * format.bytesPerFrame

        out.writeAscii("RIFF")
        out.writeUInt32LE(36 + dataBytes)
        out.writeAscii("WAVE")
        out.writeAscii("fmt ")
        out.writeUInt32LE(16)
        out.writeUInt16LE(formatTag)
        out.writeUInt16LE(format.channelCount)
        out.writeUInt32LE(format.sampleRate.toLong())
        out.writeUInt32LE(byteRate)
        out.writeUInt16LE(format.bytesPerFrame)
        out.writeUInt16LE(bitsPerSample)
        out.writeAscii("data")
        out.writeUInt32LE(dataBytes)
    }

    /**
     * An append-only WAV writer for the capture path.
     *
     * The contract that matters: **after every [flush], the file on disk is a valid, complete,
     * playable WAV of everything written so far.** The header is rewritten on each flush, so a
     * process kill at any moment costs only the samples since the last one — the mechanism
     * behind chapter 1.3.5's promise that nothing is ever lost.
     */
    public class StreamingWriter(
        private val file: File,
        public val format: AudioFormat,
    ) : AutoCloseable {

        private val raf: RandomAccessFile
        private var dataBytes: Long = 0
        private var closed = false

        /** Frames committed to the file so far. */
        public val frameCount: Long get() = dataBytes / format.bytesPerFrame

        public val durationSeconds: Double get() = frameCount.toDouble() / format.sampleRate

        init {
            file.parentFile?.mkdirs()
            raf = RandomAccessFile(file, "rw")
            raf.setLength(0)
            val header = java.io.ByteArrayOutputStream(HEADER_BYTES)
            writeHeader(header, format, 0)
            raf.write(header.toByteArray())
        }

        /** Appends a captured block. Returns the frames written. */
        public fun append(buffer: AudioBuffer): Int {
            check(!closed) { "Writer is closed" }
            require(buffer.channelCount == format.channelCount) {
                "Buffer has ${buffer.channelCount} channels, file has ${format.channelCount}"
            }
            val bytes = PcmCodec.encode(buffer, format.encoding)
            if (dataBytes + bytes.size > MAX_DATA_BYTES) {
                throw WavFormatException("WAV cannot exceed 4 GiB — start a new take")
            }
            raf.write(bytes)
            dataBytes += bytes.size
            return buffer.frameCount
        }

        /** Appends raw interleaved device bytes without a float round trip. */
        public fun appendRaw(bytes: ByteArray, length: Int) {
            check(!closed) { "Writer is closed" }
            if (dataBytes + length > MAX_DATA_BYTES) {
                throw WavFormatException("WAV cannot exceed 4 GiB — start a new take")
            }
            raf.write(bytes, 0, length)
            dataBytes += length
        }

        /**
         * Patches the header and forces bytes to the platter, leaving a fully valid file
         * behind. Called on the cadence of `PerformanceBudget.CAPTURE_FLUSH_INTERVAL_MS`.
         */
        public fun flush() {
            check(!closed) { "Writer is closed" }
            val position = raf.filePointer
            raf.seek(RIFF_SIZE_OFFSET.toLong())
            raf.writeUInt32LE(36 + dataBytes)
            raf.seek(DATA_SIZE_OFFSET.toLong())
            raf.writeUInt32LE(dataBytes)
            raf.seek(position)
            raf.fd.sync()
        }

        override fun close() {
            if (closed) return
            flush()
            closed = true
            raf.close()
        }
    }
}

// --- Little-endian helpers ------------------------------------------------------------------

private fun ByteArray.matchesAscii(at: Int, text: String): Boolean {
    if (at + text.length > size) return false
    for (i in text.indices) if (this[at + i].toInt().toChar() != text[i]) return false
    return true
}

private fun ByteArray.readUInt16LE(at: Int): Int =
    (this[at].toInt() and 0xFF) or ((this[at + 1].toInt() and 0xFF) shl 8)

private fun ByteArray.readUInt32LE(at: Int): Long =
    (this[at].toLong() and 0xFF) or
        ((this[at + 1].toLong() and 0xFF) shl 8) or
        ((this[at + 2].toLong() and 0xFF) shl 16) or
        ((this[at + 3].toLong() and 0xFF) shl 24)

private fun OutputStream.writeAscii(text: String) {
    for (ch in text) write(ch.code)
}

private fun OutputStream.writeUInt16LE(value: Int) {
    write(value and 0xFF)
    write((value shr 8) and 0xFF)
}

private fun OutputStream.writeUInt32LE(value: Long) {
    write((value and 0xFF).toInt())
    write(((value shr 8) and 0xFF).toInt())
    write(((value shr 16) and 0xFF).toInt())
    write(((value shr 24) and 0xFF).toInt())
}

private fun RandomAccessFile.writeUInt32LE(value: Long) {
    write((value and 0xFF).toInt())
    write(((value shr 8) and 0xFF).toInt())
    write(((value shr 16) and 0xFF).toInt())
    write(((value shr 24) and 0xFF).toInt())
}
