package ai.sajjil.audio.codec

import java.io.ByteArrayOutputStream

/**
 * Most-significant-bit-first bit writer.
 *
 * FLAC's bitstream is defined MSB-first and is not byte-aligned inside a frame, so the encoder
 * needs this rather than a byte-oriented stream.
 */
class BitWriter(initialCapacity: Int = 8192) {

    private val bytes = ByteArrayOutputStream(initialCapacity)
    private var accumulator = 0L
    private var bitsHeld = 0

    /** Total bits written, including those still in the accumulator. */
    var bitCount: Long = 0
        private set

    val isByteAligned: Boolean get() = bitsHeld == 0

    /** Writes the low [count] bits of [value], most significant first. */
    fun writeBits(value: Long, count: Int) {
        require(count in 0..64) { "cannot write $count bits at once" }
        if (count == 0) return
        var remaining = count
        while (remaining > 0) {
            val take = minOf(remaining, 32)
            val chunk = (value ushr (remaining - take)) and maskOf(take)
            accumulator = (accumulator shl take) or chunk
            bitsHeld += take
            bitCount += take
            remaining -= take
            flushWholeBytes()
        }
    }

    fun writeBits(value: Int, count: Int) = writeBits(value.toLong() and 0xFFFFFFFFL, count)

    fun writeBit(bit: Int) = writeBits(bit.toLong() and 1L, 1)

    /** Writes [count] zero bits. Used for Rice unary quotients, which can be long. */
    fun writeZeroes(count: Int) {
        var remaining = count
        while (remaining > 0) {
            val take = minOf(remaining, 32)
            writeBits(0L, take)
            remaining -= take
        }
    }

    /** Writes a whole byte array, which must be byte-aligned. */
    fun writeBytes(source: ByteArray) {
        check(isByteAligned) { "writeBytes needs a byte-aligned position" }
        bytes.write(source)
        bitCount += source.size.toLong() * 8
    }

    /** Pads with zero bits to the next byte boundary. Returns the number of bits added. */
    fun alignToByte(): Int {
        if (bitsHeld == 0) return 0
        val padding = 8 - bitsHeld
        writeBits(0L, padding)
        return padding
    }

    fun toByteArray(): ByteArray {
        check(isByteAligned) { "the bitstream must be byte-aligned before it can be read out" }
        return bytes.toByteArray()
    }

    val byteSize: Int get() = bytes.size()

    private fun flushWholeBytes() {
        while (bitsHeld >= 8) {
            val shift = bitsHeld - 8
            bytes.write(((accumulator ushr shift) and 0xFF).toInt())
            bitsHeld -= 8
            accumulator = accumulator and maskOf(bitsHeld)
        }
    }

    private fun maskOf(bits: Int): Long =
        if (bits >= 64) -1L else (1L shl bits) - 1L
}
