package ai.sajjil.audio.codec

import ai.sajjil.audio.AudioBuffer
import java.io.OutputStream
import java.security.MessageDigest
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min

/**
 * FLAC encoder — the "subset" profile, using constant, verbatim and fixed predictors with
 * partitioned Rice-coded residuals.
 *
 * Written in Kotlin rather than delegated to a platform codec on purpose. Android's FLAC encoder
 * availability varies by device and API level, and `MediaMuxer` cannot write a native FLAC
 * container at all, so relying on it would mean FLAC export silently working on some phones and
 * not others. This produces a real, spec-compliant `.flac` on every device.
 *
 * It does not implement LPC prediction, so files are typically 3–8% larger than reference libFLAC
 * at its default setting. They are bit-exact lossless either way, which is the property that
 * matters; the size difference is not worth the risk of a hand-written LPC quantiser.
 */
class FlacEncoder(
    private val sampleRate: Int,
    private val channelCount: Int,
    private val bitsPerSample: Int = 16,
    private val blockSize: Int = 4096,
) {
    init {
        require(sampleRate in 1..1_048_575) { "FLAC supports sample rates up to 1048575 Hz" }
        require(channelCount in 1..8) { "FLAC supports 1 to 8 channels" }
        // Whole bytes only: the STREAMINFO MD5 is defined over little-endian samples packed into
        // bitsPerSample/8 bytes, which is not well defined for depths like 12 or 20.
        require(bitsPerSample in 8..32 && bitsPerSample % 8 == 0) {
            "SAJJIL writes FLAC at 8, 16, 24 or 32 bits per sample, not $bitsPerSample"
        }
        require(blockSize in 16..65535) { "block size must be between 16 and 65535" }
    }

    /**
     * Encodes [buffer] to a complete `.flac` file.
     *
     * @param onProgress called with a 0..1 fraction; export runs off the main thread and drives
     *   the progress bar from here.
     */
    fun encode(
        buffer: AudioBuffer,
        out: OutputStream,
        onProgress: ((Double) -> Unit)? = null,
    ) {
        require(buffer.channelCount == channelCount) {
            "encoder was built for $channelCount channels but got ${buffer.channelCount}"
        }
        val samples = quantise(buffer)
        val totalFrames = buffer.frameCount

        // Two passes: encode the audio first so STREAMINFO can declare real min/max frame sizes
        // and the MD5 of the audio, both of which decoders use to verify the stream.
        val md5 = MessageDigest.getInstance("MD5")
        val frames = ArrayList<ByteArray>(totalFrames / blockSize + 1)
        var minFrameSize = Int.MAX_VALUE
        var maxFrameSize = 0

        var offset = 0
        var frameNumber = 0L
        while (offset < totalFrames) {
            val count = min(blockSize, totalFrames - offset)
            md5.update(md5Bytes(samples, offset, count))
            val encoded = encodeFrame(samples, offset, count, frameNumber)
            frames += encoded
            minFrameSize = min(minFrameSize, encoded.size)
            maxFrameSize = max(maxFrameSize, encoded.size)
            offset += count
            frameNumber++
            onProgress?.invoke(offset.toDouble() / totalFrames)
        }
        if (frames.isEmpty()) {
            minFrameSize = 0
            maxFrameSize = 0
        }

        out.write(MAGIC)
        out.write(streamInfo(totalFrames.toLong(), minFrameSize, maxFrameSize, md5.digest()))
        for (frame in frames) out.write(frame)
        out.flush()
        onProgress?.invoke(1.0)
    }

    // ---- sample preparation --------------------------------------------------------------

    /** Float PCM to signed integers at [bitsPerSample], one array per channel. */
    private fun quantise(buffer: AudioBuffer): Array<IntArray> {
        val fullScale = (1L shl (bitsPerSample - 1)).toDouble()
        val maximum = (fullScale - 1).toInt()
        val minimum = (-fullScale).toInt()
        return Array(channelCount) { c ->
            val source = buffer.channels[c]
            IntArray(source.size) { i ->
                val scaled = Math.round(source[i].coerceIn(-1f, 1f).toDouble() * (fullScale - 1))
                scaled.toInt().coerceIn(minimum, maximum)
            }
        }
    }

    /** Interleaved little-endian bytes at the coded depth, which is what the MD5 covers. */
    private fun md5Bytes(samples: Array<IntArray>, offset: Int, count: Int): ByteArray {
        val bytesPerSample = bitsPerSample / 8
        val out = ByteArray(count * channelCount * bytesPerSample)
        var at = 0
        for (i in 0 until count) {
            for (c in 0 until channelCount) {
                val v = samples[c][offset + i]
                for (b in 0 until bytesPerSample) {
                    out[at++] = ((v shr (8 * b)) and 0xFF).toByte()
                }
            }
        }
        return out
    }

    // ---- metadata ------------------------------------------------------------------------

    private fun streamInfo(
        totalSamples: Long,
        minFrameSize: Int,
        maxFrameSize: Int,
        md5: ByteArray,
    ): ByteArray {
        val writer = BitWriter(64)
        // Metadata block header: last-block flag, 7-bit type (0 = STREAMINFO), 24-bit length.
        writer.writeBit(1)
        writer.writeBits(0L, 7)
        writer.writeBits(34L, 24)

        writer.writeBits(blockSize.toLong(), 16) // minimum block size
        writer.writeBits(blockSize.toLong(), 16) // maximum block size
        writer.writeBits(if (minFrameSize == Int.MAX_VALUE) 0L else minFrameSize.toLong(), 24)
        writer.writeBits(maxFrameSize.toLong(), 24)
        writer.writeBits(sampleRate.toLong(), 20)
        writer.writeBits((channelCount - 1).toLong(), 3)
        writer.writeBits((bitsPerSample - 1).toLong(), 5)
        writer.writeBits(totalSamples, 36)
        writer.alignToByte()
        val header = writer.toByteArray()
        return header + md5
    }

    // ---- frames --------------------------------------------------------------------------

    private fun encodeFrame(
        samples: Array<IntArray>,
        offset: Int,
        count: Int,
        frameNumber: Long,
    ): ByteArray {
        val header = BitWriter(16)
        header.writeBits(0b11111111111110L, 14) // sync code
        header.writeBit(0) // reserved
        header.writeBit(0) // fixed block size strategy

        val blockSizeCode = blockSizeCodeFor(count)
        header.writeBits(blockSizeCode.code.toLong(), 4)
        // 0 means "read the sample rate from STREAMINFO", which is always valid and avoids the
        // lookup table's gaps (it cannot express 22050 or 11025 directly, for instance).
        header.writeBits(0L, 4)
        header.writeBits((channelCount - 1).toLong(), 4) // independent channels
        header.writeBits(0L, 3) // sample size from STREAMINFO
        header.writeBit(0) // reserved

        writeUtf8(header, frameNumber)
        when (blockSizeCode.explicitBits) {
            8 -> header.writeBits((count - 1).toLong(), 8)
            16 -> header.writeBits((count - 1).toLong(), 16)
        }

        check(header.isByteAligned) { "frame header must be byte-aligned before its CRC" }
        val headerBytes = header.toByteArray()
        val crc8 = Crc.crc8(headerBytes)

        val body = BitWriter(count * channelCount * 2)
        body.writeBytes(headerBytes)
        body.writeBits(crc8.toLong(), 8)

        for (c in 0 until channelCount) {
            writeSubframe(body, samples[c], offset, count)
        }
        body.alignToByte()

        val withoutCrc = body.toByteArray()
        val crc16 = Crc.crc16(withoutCrc)
        return withoutCrc + byteArrayOf(((crc16 shr 8) and 0xFF).toByte(), (crc16 and 0xFF).toByte())
    }

    private data class BlockSizeCode(val code: Int, val explicitBits: Int)

    private fun blockSizeCodeFor(count: Int): BlockSizeCode = when (count) {
        192 -> BlockSizeCode(0b0001, 0)
        576 -> BlockSizeCode(0b0010, 0)
        1152 -> BlockSizeCode(0b0011, 0)
        2304 -> BlockSizeCode(0b0100, 0)
        4608 -> BlockSizeCode(0b0101, 0)
        256 -> BlockSizeCode(0b1000, 0)
        512 -> BlockSizeCode(0b1001, 0)
        1024 -> BlockSizeCode(0b1010, 0)
        2048 -> BlockSizeCode(0b1011, 0)
        4096 -> BlockSizeCode(0b1100, 0)
        8192 -> BlockSizeCode(0b1101, 0)
        16384 -> BlockSizeCode(0b1110, 0)
        32768 -> BlockSizeCode(0b1111, 0)
        // The final block of a file is almost never a table size, so it carries its length
        // explicitly. 8 bits where it fits, 16 otherwise.
        in 1..256 -> BlockSizeCode(0b0110, 8)
        else -> BlockSizeCode(0b0111, 16)
    }

    /** FLAC's UTF-8-like coding for the frame number. */
    private fun writeUtf8(writer: BitWriter, value: Long) {
        when {
            value < 0x80 -> writer.writeBits(value, 8)
            value < 0x800 -> {
                writer.writeBits(0xC0L or (value shr 6), 8)
                writer.writeBits(0x80L or (value and 0x3F), 8)
            }
            value < 0x10000 -> {
                writer.writeBits(0xE0L or (value shr 12), 8)
                writer.writeBits(0x80L or ((value shr 6) and 0x3F), 8)
                writer.writeBits(0x80L or (value and 0x3F), 8)
            }
            value < 0x200000 -> {
                writer.writeBits(0xF0L or (value shr 18), 8)
                writer.writeBits(0x80L or ((value shr 12) and 0x3F), 8)
                writer.writeBits(0x80L or ((value shr 6) and 0x3F), 8)
                writer.writeBits(0x80L or (value and 0x3F), 8)
            }
            value < 0x4000000 -> {
                writer.writeBits(0xF8L or (value shr 24), 8)
                writer.writeBits(0x80L or ((value shr 18) and 0x3F), 8)
                writer.writeBits(0x80L or ((value shr 12) and 0x3F), 8)
                writer.writeBits(0x80L or ((value shr 6) and 0x3F), 8)
                writer.writeBits(0x80L or (value and 0x3F), 8)
            }
            else -> {
                writer.writeBits(0xFCL or (value shr 30), 8)
                writer.writeBits(0x80L or ((value shr 24) and 0x3F), 8)
                writer.writeBits(0x80L or ((value shr 18) and 0x3F), 8)
                writer.writeBits(0x80L or ((value shr 12) and 0x3F), 8)
                writer.writeBits(0x80L or ((value shr 6) and 0x3F), 8)
                writer.writeBits(0x80L or (value and 0x3F), 8)
            }
        }
    }

    // ---- subframes -----------------------------------------------------------------------

    private fun writeSubframe(writer: BitWriter, channel: IntArray, offset: Int, count: Int) {
        // Constant: the whole block is one value. Costs a handful of bits, and digital silence
        // between takes is extremely common in voice recordings.
        val first = channel[offset]
        var constant = true
        for (i in 1 until count) {
            if (channel[offset + i] != first) {
                constant = false
                break
            }
        }
        if (constant) {
            writer.writeBit(0)
            writer.writeBits(0b000000L, 6) // CONSTANT
            writer.writeBit(0) // no wasted bits
            writer.writeBits(first.toLong(), bitsPerSample)
            return
        }

        val order = bestFixedOrder(channel, offset, count)
        val residual = fixedResidual(channel, offset, count, order)
        val partitionOrder = bestPartitionOrder(residual, count, order)
        val estimatedBits = riceBitCost(residual, count, order, partitionOrder)
        val verbatimBits = count * bitsPerSample

        if (estimatedBits >= verbatimBits) {
            // Rare, but real for near-random content: raw samples are smaller than any prediction.
            writer.writeBit(0)
            writer.writeBits(0b000001L, 6) // VERBATIM
            writer.writeBit(0)
            for (i in 0 until count) writer.writeBits(channel[offset + i].toLong(), bitsPerSample)
            return
        }

        writer.writeBit(0)
        writer.writeBits((0b001000 or order).toLong(), 6) // FIXED, order in the low three bits
        writer.writeBit(0)
        for (i in 0 until order) writer.writeBits(channel[offset + i].toLong(), bitsPerSample)
        writeResidual(writer, residual, count, order, partitionOrder)
    }

    /** Picks the fixed predictor order whose residuals have the smallest absolute sum. */
    private fun bestFixedOrder(channel: IntArray, offset: Int, count: Int): Int {
        var bestOrder = 0
        var bestCost = Long.MAX_VALUE
        val maxOrder = min(MAX_FIXED_ORDER, count - 1)
        for (order in 0..maxOrder) {
            var cost = 0L
            for (i in order until count) {
                cost += abs(fixedPredictionError(channel, offset, i, order).toLong())
            }
            if (cost < bestCost) {
                bestCost = cost
                bestOrder = order
            }
        }
        return bestOrder
    }

    private fun fixedResidual(channel: IntArray, offset: Int, count: Int, order: Int): IntArray {
        val residual = IntArray(count - order)
        for (i in order until count) {
            residual[i - order] = fixedPredictionError(channel, offset, i, order)
        }
        return residual
    }

    /**
     * Residual of FLAC's fixed polynomial predictors, which are successive differences:
     * order 1 is x[n]-x[n-1], order 2 the second difference, and so on to order 4.
     */
    private fun fixedPredictionError(channel: IntArray, offset: Int, i: Int, order: Int): Int {
        val x = { k: Int -> channel[offset + i - k] }
        return when (order) {
            0 -> x(0)
            1 -> x(0) - x(1)
            2 -> x(0) - 2 * x(1) + x(2)
            3 -> x(0) - 3 * x(1) + 3 * x(2) - x(3)
            else -> x(0) - 4 * x(1) + 6 * x(2) - 4 * x(3) + x(4)
        }
    }

    // ---- Rice-coded residual ---------------------------------------------------------------

    private fun bestPartitionOrder(residual: IntArray, blockSamples: Int, predictorOrder: Int): Int {
        var best = 0
        var bestBits = Long.MAX_VALUE
        for (order in 0..MAX_PARTITION_ORDER) {
            val partitions = 1 shl order
            if (blockSamples % partitions != 0) continue
            val perPartition = blockSamples / partitions
            // The first partition also has to hold the warm-up samples' worth of headroom.
            if (perPartition <= predictorOrder) continue
            val bits = riceBitCost(residual, blockSamples, predictorOrder, order)
            if (bits < bestBits) {
                bestBits = bits
                best = order
            }
        }
        return best
    }

    private fun riceBitCost(
        residual: IntArray,
        blockSamples: Int,
        predictorOrder: Int,
        partitionOrder: Int,
    ): Long {
        var total = 0L
        forEachPartition(blockSamples, predictorOrder, partitionOrder) { from, until ->
            val parameter = bestRiceParameter(residual, from, until)
            total += 4 + partitionBits(residual, from, until, parameter)
        }
        return total
    }

    private fun writeResidual(
        writer: BitWriter,
        residual: IntArray,
        blockSamples: Int,
        predictorOrder: Int,
        partitionOrder: Int,
    ) {
        // Coding method 0: 4-bit Rice parameters. Method 1 (5-bit) is only needed for
        // parameters above 14, which this encoder never selects.
        writer.writeBits(0L, 2)
        writer.writeBits(partitionOrder.toLong(), 4)
        forEachPartition(blockSamples, predictorOrder, partitionOrder) { from, until ->
            val parameter = bestRiceParameter(residual, from, until)
            writer.writeBits(parameter.toLong(), 4)
            for (i in from until until) {
                writeRice(writer, residual[i], parameter)
            }
        }
    }

    /**
     * Walks the residual index ranges of each partition.
     *
     * The first partition is short by [predictorOrder] because those samples were written as
     * warm-up values in the subframe header and have no residual — an off-by-one here produces a
     * stream that decodes to noise, so it lives in one place.
     */
    private inline fun forEachPartition(
        blockSamples: Int,
        predictorOrder: Int,
        partitionOrder: Int,
        action: (from: Int, until: Int) -> Unit,
    ) {
        val partitions = 1 shl partitionOrder
        val perPartition = blockSamples shr partitionOrder
        var from = 0
        for (p in 0 until partitions) {
            val length = if (p == 0) perPartition - predictorOrder else perPartition
            action(from, from + length)
            from += length
        }
    }

    private fun bestRiceParameter(residual: IntArray, from: Int, until: Int): Int {
        val n = until - from
        if (n <= 0) return 0
        var sum = 0L
        for (i in from until until) sum += zigzag(residual[i]).toLong()
        // Optimal k for a geometric distribution is about log2(mean); search the neighbourhood
        // exactly rather than trusting the estimate, since it is cheap and the estimate is only
        // asymptotically right.
        val mean = sum.toDouble() / n
        val estimate = if (mean <= 0.0) 0 else (Math.log(mean) / Math.log(2.0)).toInt()
        var best = 0
        var bestBits = Long.MAX_VALUE
        for (k in max(0, estimate - 2)..min(MAX_RICE_PARAMETER, estimate + 2)) {
            val bits = partitionBits(residual, from, until, k)
            if (bits < bestBits) {
                bestBits = bits
                best = k
            }
        }
        return best
    }

    private fun partitionBits(residual: IntArray, from: Int, until: Int, parameter: Int): Long {
        var bits = 0L
        for (i in from until until) {
            // quotient in unary + a stop bit + the parameter remainder bits
            bits += (zigzag(residual[i]) ushr parameter) + 1L + parameter
        }
        return bits
    }

    private fun writeRice(writer: BitWriter, value: Int, parameter: Int) {
        val folded = zigzag(value)
        val quotient = folded ushr parameter
        writer.writeZeroes(quotient)
        writer.writeBit(1)
        if (parameter > 0) {
            writer.writeBits((folded and ((1 shl parameter) - 1)).toLong(), parameter)
        }
    }

    /** Folds a signed value into an unsigned one: 0,-1,1,-2,2 becomes 0,1,2,3,4. */
    private fun zigzag(value: Int): Int = (value shl 1) xor (value shr 31)

    private companion object {
        val MAGIC = "fLaC".toByteArray(Charsets.US_ASCII)
        const val MAX_FIXED_ORDER = 4
        const val MAX_PARTITION_ORDER = 6
        const val MAX_RICE_PARAMETER = 14
    }
}

/** The two CRCs FLAC frames carry. */
object Crc {

    private val TABLE8 = IntArray(256) { i ->
        var crc = i
        repeat(8) {
            crc = if (crc and 0x80 != 0) ((crc shl 1) xor 0x07) and 0xFF else (crc shl 1) and 0xFF
        }
        crc
    }

    private val TABLE16 = IntArray(256) { i ->
        var crc = i shl 8
        repeat(8) {
            crc = if (crc and 0x8000 != 0) ((crc shl 1) xor 0x8005) and 0xFFFF else (crc shl 1) and 0xFFFF
        }
        crc
    }

    /** CRC-8, polynomial x^8 + x^2 + x + 1, initial value 0. Covers the frame header. */
    fun crc8(data: ByteArray): Int {
        var crc = 0
        for (byte in data) crc = TABLE8[(crc xor (byte.toInt() and 0xFF)) and 0xFF]
        return crc
    }

    /** CRC-16, polynomial x^16 + x^15 + x^2 + 1, initial value 0. Covers the whole frame. */
    fun crc16(data: ByteArray): Int {
        var crc = 0
        for (byte in data) {
            crc = ((crc shl 8) xor TABLE16[((crc shr 8) xor (byte.toInt() and 0xFF)) and 0xFF]) and 0xFFFF
        }
        return crc
    }
}
