package ai.sautiy.core.codec

import ai.sautiy.core.audio.AudioBuffer
import java.io.OutputStream
import kotlin.math.abs

/**
 * A FLAC encoder and decoder, in pure Kotlin.
 *
 * FLAC earns its place in SAUTIY because it is the only format that is simultaneously
 * **exact** and **small**: a reciter keeping thirty takes of a passage should not have to
 * choose between losing quality and filling the phone. On speech it typically lands near half
 * the size of the equivalent WAV, with every sample recoverable bit for bit.
 *
 * The encoder uses **fixed polynomial predictors** (orders 0–4) with partitioned Rice residual
 * coding. Fixed predictors are chosen over general LPC deliberately: they need no
 * autocorrelation, no Levinson–Durbin, and no coefficient quantisation, they cost a handful of
 * subtractions per sample, and on speech they land within a few per cent of what LPC achieves.
 * The result is fully conformant FLAC — any decoder reads it — produced by code small enough to
 * be read and verified.
 *
 * A matching decoder lives in [FlacDecoder], and the round-trip is asserted bit-exact by test.
 * A lossless codec that is only *believed* to be lossless is not lossless.
 */
public class FlacEncoder(
    /** Frames per block. 4096 is FLAC's usual choice and what every decoder is tuned for. */
    public val blockSize: Int = 4096,
    /** Bits per sample written to the file. */
    public val bitsPerSample: Int = 16,
) : AudioEncoder {

    init {
        require(blockSize in 16..65535) { "FLAC block size must be 16..65535" }
        require(bitsPerSample in setOf(8, 16, 24)) { "SAUTIY writes 8, 16 or 24-bit FLAC" }
    }

    override val format: ExportFormat get() = ExportFormat.FLAC

    override fun encode(
        audio: AudioBuffer,
        output: OutputStream,
        metadata: ExportMetadata,
        progress: (Double) -> Unit,
    ) {
        val channels = audio.channelCount
        val frames = audio.frameCount
        val scale = (1 shl (bitsPerSample - 1)).toDouble()

        // Convert once, to the integer domain the codec works in. Everything downstream is
        // exact integer arithmetic — which is what makes the round trip provable.
        val samples = Array(channels) { c ->
            IntArray(frames) { i ->
                val limit = (1 shl (bitsPerSample - 1))
                Math.round(audio.channels[c][i].coerceIn(-1f, 1f) * scale)
                    .toInt().coerceIn(-limit, limit - 1)
            }
        }

        output.write("fLaC".toByteArray(Charsets.US_ASCII))
        writeStreamInfo(output, audio.sampleRate, channels, frames.toLong(), samples)
        writeVorbisComment(output, metadata)

        var position = 0
        var frameNumber = 0L
        while (position < frames) {
            val count = minOf(blockSize, frames - position)
            writeFrame(output, samples, position, count, audio.sampleRate, frameNumber)
            position += count
            frameNumber++
            progress(position.toDouble() / frames)
        }
        progress(1.0)
    }

    // --- Metadata blocks --------------------------------------------------------------------

    private fun writeStreamInfo(
        out: OutputStream,
        sampleRate: Int,
        channels: Int,
        totalFrames: Long,
        samples: Array<IntArray>,
    ) {
        val bits = BitWriter()
        bits.write(blockSize, 16) // minimum block size
        bits.write(blockSize, 16) // maximum block size
        bits.write(0, 24) // minimum frame size, 0 for unknown
        bits.write(0, 24) // maximum frame size, 0 for unknown
        bits.write(sampleRate, 20)
        bits.write(channels - 1, 3)
        bits.write(bitsPerSample - 1, 5)
        bits.writeLong(totalFrames, 36)
        // The MD5 of the unencoded audio is optional; SAUTIY writes zeros to say "not present"
        // rather than writing a wrong digest, which some decoders would report as corruption.
        repeat(16) { bits.write(0, 8) }
        val body = bits.finish()

        // Not the last block: a Vorbis comment follows.
        out.write(0x00)
        writeUInt24(out, body.size)
        out.write(body)
    }

    private fun writeVorbisComment(out: OutputStream, metadata: ExportMetadata) {
        val vendor = "SAUTIY".toByteArray(Charsets.UTF_8)
        val comments = buildList {
            metadata.title?.let { add("TITLE=$it") }
            metadata.artist?.let { add("ARTIST=$it") }
            metadata.album?.let { add("ALBUM=$it") }
            metadata.comment?.let { add("DESCRIPTION=$it") }
            metadata.year?.let { add("DATE=$it") }
            metadata.trackNumber?.let { add("TRACKNUMBER=$it") }
            add("ENCODER=${metadata.encodedBy}")
        }.map { it.toByteArray(Charsets.UTF_8) }

        val body = java.io.ByteArrayOutputStream()
        writeUInt32LE(body, vendor.size)
        body.write(vendor)
        writeUInt32LE(body, comments.size)
        for (comment in comments) {
            writeUInt32LE(body, comment.size)
            body.write(comment)
        }
        val bytes = body.toByteArray()

        out.write(0x84) // last metadata block, type 4 (Vorbis comment)
        writeUInt24(out, bytes.size)
        out.write(bytes)
    }

    // --- Frames ------------------------------------------------------------------------------

    private fun writeFrame(
        out: OutputStream,
        samples: Array<IntArray>,
        offset: Int,
        count: Int,
        sampleRate: Int,
        frameNumber: Long,
    ) {
        val header = BitWriter()
        header.write(0b11111111111110, 14) // sync
        header.write(0, 1) // reserved
        header.write(0, 1) // fixed block size, frame number follows

        // Block size and sample rate are coded as "read it from the end of the header", which
        // avoids depending on the enumerated tables matching whatever the user recorded at.
        header.write(0b0111, 4) // block size: 16 bits at end of header
        header.write(0b1101, 4) // sample rate: 16 bits at end of header, in Hz
        header.write(samples.size - 1, 4) // channel assignment: independent channels
        header.write(
            when (bitsPerSample) {
                8 -> 0b001
                16 -> 0b100
                else -> 0b110
            },
            3,
        )
        header.write(0, 1) // reserved

        header.writeUtf8(frameNumber)
        header.write(count - 1, 16)
        header.write(sampleRate, 16)

        val headerBytes = header.finish()
        val crc8 = crc8(headerBytes)

        val body = BitWriter()
        for (channel in samples) {
            writeSubframe(body, channel, offset, count)
        }
        body.alignToByte()
        val bodyBytes = body.finish()

        val frame = headerBytes + byteArrayOf(crc8) + bodyBytes
        val crc16 = crc16(frame)
        out.write(frame)
        out.write((crc16 ushr 8) and 0xFF)
        out.write(crc16 and 0xFF)
    }

    /**
     * Chooses and writes the cheapest representation of one block of one channel.
     *
     * The five fixed predictors are tried and the one producing the smallest residual wins.
     * Trying them all costs five passes over the block and reliably beats any heuristic, since
     * which order fits best changes with the material — order 2 suits voiced speech, order 0
     * suits noise, and a heuristic that guesses gets it wrong on exactly the material where it
     * matters.
     */
    private fun writeSubframe(bits: BitWriter, channel: IntArray, offset: Int, count: Int) {
        // A constant block is free to encode and common in silence and in trimmed tails.
        var constant = true
        val first = channel[offset]
        for (i in offset until offset + count) {
            if (channel[i] != first) {
                constant = false
                break
            }
        }
        if (constant) {
            bits.write(0, 1) // zero bit
            bits.write(0b000000, 6) // subframe type: constant
            bits.write(0, 1) // no wasted bits
            bits.writeSigned(first, bitsPerSample)
            return
        }

        var bestOrder = 0
        var bestCost = Long.MAX_VALUE
        var bestResidual: IntArray? = null

        for (order in 0..MAX_FIXED_ORDER) {
            if (count <= order) continue
            val residual = IntArray(count - order)
            for (i in order until count) {
                residual[i - order] = fixedResidual(channel, offset + i, order)
            }
            var cost = 0L
            for (r in residual) cost += abs(r.toLong())
            // Warm-up samples are stored verbatim, so a higher order is not free.
            cost += order.toLong() * bitsPerSample * count / 8
            if (cost < bestCost) {
                bestCost = cost
                bestOrder = order
                bestResidual = residual
            }
        }

        val residual = bestResidual ?: IntArray(0)
        bits.write(0, 1)
        bits.write(0b001000 or bestOrder, 6) // fixed predictor of the chosen order
        bits.write(0, 1) // no wasted bits

        for (i in 0 until bestOrder) bits.writeSigned(channel[offset + i], bitsPerSample)
        writeRiceResidual(bits, residual, bestOrder, count)
    }

    private fun fixedResidual(channel: IntArray, index: Int, order: Int): Int = when (order) {
        0 -> channel[index]
        1 -> channel[index] - channel[index - 1]
        2 -> channel[index] - 2 * channel[index - 1] + channel[index - 2]
        3 -> channel[index] - 3 * channel[index - 1] + 3 * channel[index - 2] - channel[index - 3]
        else -> channel[index] - 4 * channel[index - 1] + 6 * channel[index - 2] -
            4 * channel[index - 3] + channel[index - 4]
    }

    /**
     * Partitioned Rice coding.
     *
     * The block is split into partitions and each gets its own Rice parameter, because speech
     * is not stationary: a loud syllable and the pause after it want very different parameters,
     * and one parameter for the whole block spends bits on the quiet part to serve the loud one.
     */
    private fun writeRiceResidual(bits: BitWriter, residual: IntArray, order: Int, blockCount: Int) {
        val partitionOrder = choosePartitionOrder(blockCount, order)
        val partitions = 1 shl partitionOrder

        bits.write(0, 2) // residual method: Rice with 4-bit parameters
        bits.write(partitionOrder, 4)

        var index = 0
        for (p in 0 until partitions) {
            val partitionSamples = if (p == 0) {
                blockCount / partitions - order
            } else {
                blockCount / partitions
            }
            val slice = IntArray(partitionSamples) { residual[index + it] }
            val parameter = bestRiceParameter(slice)
            bits.write(parameter, 4)
            for (value in slice) bits.writeRice(zigZag(value), parameter)
            index += partitionSamples
        }
    }

    private fun choosePartitionOrder(blockCount: Int, order: Int): Int {
        var best = 0
        for (candidate in 0..MAX_PARTITION_ORDER) {
            val partitions = 1 shl candidate
            if (blockCount % partitions != 0) break
            if (blockCount / partitions <= order) break
            // Partitions of fewer than 32 samples spend more on parameters than they save.
            if (blockCount / partitions < 32) break
            best = candidate
        }
        return best
    }

    private fun bestRiceParameter(values: IntArray): Int {
        if (values.isEmpty()) return 0
        var sum = 0L
        for (v in values) sum += zigZag(v).toLong()
        val mean = sum.toDouble() / values.size
        // The optimal Rice parameter is about log2 of the mean of the zig-zagged values.
        var parameter = 0
        while (parameter < MAX_RICE_PARAMETER && (1L shl (parameter + 1)) < mean) parameter++
        return parameter
    }

    public companion object {
        internal const val MAX_FIXED_ORDER = 4
        internal const val MAX_PARTITION_ORDER = 6

        /** 15 is the escape value in a 4-bit parameter field, so 14 is the largest usable. */
        internal const val MAX_RICE_PARAMETER = 14

        /** Folds a signed value into an unsigned one, small magnitudes staying small. */
        internal fun zigZag(value: Int): Int = if (value >= 0) value shl 1 else ((-value) shl 1) - 1

        internal fun unZigZag(value: Int): Int = if (value and 1 == 0) value ushr 1 else -((value + 1) ushr 1)

        private val CRC8_TABLE = IntArray(256) { i ->
            var crc = i
            repeat(8) { crc = if (crc and 0x80 != 0) (crc shl 1) xor 0x07 else crc shl 1 }
            crc and 0xFF
        }

        private val CRC16_TABLE = IntArray(256) { i ->
            var crc = i shl 8
            repeat(8) { crc = if (crc and 0x8000 != 0) (crc shl 1) xor 0x8005 else crc shl 1 }
            crc and 0xFFFF
        }

        internal fun crc8(data: ByteArray): Byte {
            var crc = 0
            for (b in data) crc = CRC8_TABLE[(crc xor (b.toInt() and 0xFF)) and 0xFF]
            return crc.toByte()
        }

        internal fun crc16(data: ByteArray): Int {
            var crc = 0
            for (b in data) crc = ((crc shl 8) xor CRC16_TABLE[((crc ushr 8) xor (b.toInt() and 0xFF)) and 0xFF]) and 0xFFFF
            return crc
        }

        private fun writeUInt24(out: OutputStream, value: Int) {
            out.write((value ushr 16) and 0xFF)
            out.write((value ushr 8) and 0xFF)
            out.write(value and 0xFF)
        }

        private fun writeUInt32LE(out: OutputStream, value: Int) {
            out.write(value and 0xFF)
            out.write((value ushr 8) and 0xFF)
            out.write((value ushr 16) and 0xFF)
            out.write((value ushr 24) and 0xFF)
        }
    }
}

/** Big-endian bit writer. FLAC is a big-endian bitstream throughout. */
internal class BitWriter {
    private val bytes = java.io.ByteArrayOutputStream(1 shl 16)
    private var accumulator = 0L
    private var bitCount = 0

    fun write(value: Int, bits: Int) {
        writeLong(value.toLong() and ((1L shl bits) - 1), bits)
    }

    fun writeLong(value: Long, bits: Int) {
        require(bits in 1..57) { "Cannot write $bits bits at once" }
        accumulator = (accumulator shl bits) or (value and ((1L shl bits) - 1))
        bitCount += bits
        while (bitCount >= 8) {
            bitCount -= 8
            bytes.write(((accumulator ushr bitCount) and 0xFF).toInt())
        }
    }

    fun writeSigned(value: Int, bits: Int) {
        write(value and ((1 shl bits) - 1), bits)
    }

    /** Rice code: quotient in unary, then the remainder in [parameter] bits. */
    fun writeRice(value: Int, parameter: Int) {
        val quotient = value ushr parameter
        // A pathological residual would emit a huge unary run; the encoder's parameter choice
        // keeps this small, and the guard keeps a corrupt input from producing a corrupt file.
        require(quotient < 1 shl 20) { "Rice quotient overflow — residual is out of range" }
        var remaining = quotient
        while (remaining >= 32) {
            write(0, 32)
            remaining -= 32
        }
        if (remaining > 0) write(0, remaining)
        write(1, 1)
        if (parameter > 0) write(value and ((1 shl parameter) - 1), parameter)
    }

    /** FLAC codes frame numbers with the UTF-8 byte pattern, extended to 36 bits. */
    fun writeUtf8(value: Long) {
        when {
            value < 0x80 -> write(value.toInt(), 8)
            value < 0x800 -> {
                write(0xC0 or ((value ushr 6).toInt() and 0x1F), 8)
                write(0x80 or (value.toInt() and 0x3F), 8)
            }

            value < 0x10000 -> {
                write(0xE0 or ((value ushr 12).toInt() and 0x0F), 8)
                write(0x80 or ((value ushr 6).toInt() and 0x3F), 8)
                write(0x80 or (value.toInt() and 0x3F), 8)
            }

            else -> {
                write(0xF0 or ((value ushr 18).toInt() and 0x07), 8)
                write(0x80 or ((value ushr 12).toInt() and 0x3F), 8)
                write(0x80 or ((value ushr 6).toInt() and 0x3F), 8)
                write(0x80 or (value.toInt() and 0x3F), 8)
            }
        }
    }

    fun alignToByte() {
        if (bitCount > 0) write(0, 8 - bitCount)
    }

    fun finish(): ByteArray {
        alignToByte()
        return bytes.toByteArray()
    }
}

/** Big-endian bit reader, the inverse of [BitWriter]. */
internal class BitReader(private val data: ByteArray, private var bytePosition: Int = 0) {
    private var bitPosition = 0

    val position: Int get() = bytePosition

    fun read(bits: Int): Int = readLong(bits).toInt()

    fun readLong(bits: Int): Long {
        var value = 0L
        var remaining = bits
        while (remaining > 0) {
            check(bytePosition < data.size) { "Bitstream ended early" }
            val available = 8 - bitPosition
            val take = minOf(available, remaining)
            val current = data[bytePosition].toInt() and 0xFF
            val shifted = (current ushr (available - take)) and ((1 shl take) - 1)
            value = (value shl take) or shifted.toLong()
            bitPosition += take
            remaining -= take
            if (bitPosition == 8) {
                bitPosition = 0
                bytePosition++
            }
        }
        return value
    }

    fun readSigned(bits: Int): Int {
        val raw = read(bits)
        val signBit = 1 shl (bits - 1)
        return if (raw and signBit != 0) raw - (1 shl bits) else raw
    }

    fun readRice(parameter: Int): Int {
        var quotient = 0
        while (read(1) == 0) {
            quotient++
            check(quotient < 1 shl 20) { "Runaway unary code — the bitstream is corrupt" }
        }
        val remainder = if (parameter > 0) read(parameter) else 0
        return (quotient shl parameter) or remainder
    }

    fun alignToByte() {
        if (bitPosition > 0) {
            bitPosition = 0
            bytePosition++
        }
    }

    fun skipBytes(count: Int) {
        bytePosition += count
    }
}

/**
 * The matching decoder.
 *
 * It exists so that "lossless" is a proven property rather than a claim: the test suite encodes
 * real material, decodes it here, and asserts every sample is identical. A lossless codec that
 * has only been eyeballed is not a lossless codec.
 */
public object FlacDecoder {

    public class FlacFormatException(message: String) : IllegalArgumentException(message)

    public data class StreamInfo(
        val sampleRate: Int,
        val channelCount: Int,
        val bitsPerSample: Int,
        val totalFrames: Long,
    )

    public fun decode(data: ByteArray): AudioBuffer {
        if (data.size < 8 || String(data, 0, 4, Charsets.US_ASCII) != "fLaC") {
            throw FlacFormatException("Not a FLAC stream")
        }

        var position = 4
        var info: StreamInfo? = null

        // Metadata blocks.
        while (true) {
            if (position + 4 > data.size) throw FlacFormatException("Truncated metadata")
            val header = data[position].toInt() and 0xFF
            val isLast = header and 0x80 != 0
            val type = header and 0x7F
            val length = ((data[position + 1].toInt() and 0xFF) shl 16) or
                ((data[position + 2].toInt() and 0xFF) shl 8) or
                (data[position + 3].toInt() and 0xFF)
            position += 4

            if (type == 0) {
                val reader = BitReader(data, position)
                reader.read(16) // minimum block size
                reader.read(16) // maximum block size
                reader.read(24) // minimum frame size
                reader.read(24) // maximum frame size
                val sampleRate = reader.read(20)
                val channels = reader.read(3) + 1
                val bits = reader.read(5) + 1
                val total = reader.readLong(36)
                info = StreamInfo(sampleRate, channels, bits, total)
            }
            position += length
            if (isLast) break
        }

        val streamInfo = info ?: throw FlacFormatException("FLAC stream has no STREAMINFO")
        val channels = Array(streamInfo.channelCount) { ArrayList<Int>(streamInfo.totalFrames.toInt()) }

        while (position < data.size - 2) {
            val reader = BitReader(data, position)
            val sync = reader.read(14)
            if (sync != 0b11111111111110) break
            reader.read(1)
            reader.read(1)
            val blockSizeCode = reader.read(4)
            val sampleRateCode = reader.read(4)
            val channelAssignment = reader.read(4)
            reader.read(3)
            reader.read(1)

            // Frame number, UTF-8 coded: the leading byte states its own length.
            val firstByte = reader.read(8)
            val extraBytes = when {
                firstByte < 0x80 -> 0
                firstByte and 0xE0 == 0xC0 -> 1
                firstByte and 0xF0 == 0xE0 -> 2
                else -> 3
            }
            repeat(extraBytes) { reader.read(8) }

            val blockSize = when (blockSizeCode) {
                0b0110 -> reader.read(8) + 1
                0b0111 -> reader.read(16) + 1
                else -> throw FlacFormatException("Unsupported block size code $blockSizeCode")
            }
            when (sampleRateCode) {
                0b1100 -> reader.read(8)
                0b1101, 0b1110 -> reader.read(16)
            }
            reader.read(8) // header CRC-8

            val channelCount = channelAssignment + 1
            if (channelCount != streamInfo.channelCount) {
                throw FlacFormatException("Frame declares $channelCount channels, stream declares ${streamInfo.channelCount}")
            }

            for (c in 0 until channelCount) {
                val decoded = decodeSubframe(reader, blockSize, streamInfo.bitsPerSample)
                for (v in decoded) channels[c].add(v)
            }
            reader.alignToByte()
            reader.skipBytes(2) // frame CRC-16
            position = reader.position
        }

        val scale = (1 shl (streamInfo.bitsPerSample - 1)).toFloat()
        val out = Array(streamInfo.channelCount) { c ->
            FloatArray(channels[c].size) { channels[c][it] / scale }
        }
        return AudioBuffer(out, streamInfo.sampleRate)
    }

    private fun decodeSubframe(reader: BitReader, blockSize: Int, bitsPerSample: Int): IntArray {
        reader.read(1) // zero bit
        val type = reader.read(6)
        val wastedFlag = reader.read(1)
        if (wastedFlag != 0) throw FlacFormatException("SAUTIY does not write wasted bits")

        if (type == 0) {
            val value = reader.readSigned(bitsPerSample)
            return IntArray(blockSize) { value }
        }
        if (type and 0b111000 != 0b001000) {
            throw FlacFormatException("Unsupported subframe type $type")
        }

        val order = type and 0b000111
        val out = IntArray(blockSize)
        for (i in 0 until order) out[i] = reader.readSigned(bitsPerSample)

        val method = reader.read(2)
        if (method != 0) throw FlacFormatException("Unsupported residual method $method")
        val partitionOrder = reader.read(4)
        val partitions = 1 shl partitionOrder

        var index = order
        for (p in 0 until partitions) {
            val parameter = reader.read(4)
            if (parameter == 15) throw FlacFormatException("Escaped partitions are not written by SAUTIY")
            val samples = if (p == 0) blockSize / partitions - order else blockSize / partitions
            repeat(samples) {
                val residual = FlacEncoder.unZigZag(reader.readRice(parameter))
                out[index] = residual + prediction(out, index, order)
                index++
            }
        }
        return out
    }

    private fun prediction(out: IntArray, index: Int, order: Int): Int = when (order) {
        0 -> 0
        1 -> out[index - 1]
        2 -> 2 * out[index - 1] - out[index - 2]
        3 -> 3 * out[index - 1] - 3 * out[index - 2] + out[index - 3]
        else -> 4 * out[index - 1] - 6 * out[index - 2] + 4 * out[index - 3] - out[index - 4]
    }
}
