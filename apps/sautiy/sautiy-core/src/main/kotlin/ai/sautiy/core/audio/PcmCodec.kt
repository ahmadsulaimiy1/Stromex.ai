package ai.sautiy.core.audio

/**
 * Conversion between raw little-endian PCM bytes and SAUTIY's float working format.
 *
 * Both directions use the **same** scale — 2^(n−1), so 32768 for 16-bit — because that is the
 * true magnitude of the most negative representable sample. Scaling by 2^(n−1)−1 on the way out
 * instead, as a lot of conversion code does, introduces a systematic gain error of one part in
 * 32768: small, but it compounds to more than a full quantisation step at high levels, which is
 * exactly where a recording can least afford it.
 *
 * Using the symmetric scale means +1.0 maps to 32768, which does not fit. So the result is
 * **clamped**, not truncated to fit the bit pattern. That distinction is the whole game: a
 * wrapped +1.0 becomes −32768, turning the loudest instant of a recording into a maximally
 * negative sample — a single-sample click at every single peak, which is the classic and
 * thoroughly audible conversion bug this codec is written to avoid.
 */
public object PcmCodec {

    // One scale per depth, used in both directions. Clamping — not wrapping — handles the
    // single value (+1.0) that the symmetric scale cannot represent.
    private const val INT8_SCALE = 128.0f
    private const val INT16_SCALE = 32768.0f
    private const val INT24_SCALE = 8388608.0f
    private const val INT32_SCALE = 2147483648.0

    /** Decodes interleaved bytes into a planar [AudioBuffer]. */
    public fun decode(bytes: ByteArray, offset: Int, length: Int, format: AudioFormat): AudioBuffer {
        val bytesPerFrame = format.bytesPerFrame
        require(bytesPerFrame > 0)
        val frames = length / bytesPerFrame
        val channelCount = format.channelCount
        val channels = Array(channelCount) { FloatArray(frames) }
        val bytesPerSample = format.encoding.bytesPerSample

        var position = offset
        for (frame in 0 until frames) {
            for (c in 0 until channelCount) {
                channels[c][frame] = decodeSample(bytes, position, format.encoding)
                position += bytesPerSample
            }
        }
        return AudioBuffer(channels, format.sampleRate)
    }

    public fun decode(bytes: ByteArray, format: AudioFormat): AudioBuffer =
        decode(bytes, 0, bytes.size, format)

    private fun decodeSample(b: ByteArray, at: Int, encoding: SampleEncoding): Float = when (encoding) {
        SampleEncoding.PCM_8_UNSIGNED -> ((b[at].toInt() and 0xFF) - 128) / INT8_SCALE

        SampleEncoding.PCM_16_LE -> {
            val value = (b[at].toInt() and 0xFF) or (b[at + 1].toInt() shl 8)
            value.toShort() / INT16_SCALE
        }

        SampleEncoding.PCM_24_LE -> {
            // Sign-extend 24 bits into 32 by shifting the top byte up and back down
            // arithmetically — cheaper and less error-prone than masking and branching.
            val value = ((b[at].toInt() and 0xFF) shl 8) or
                ((b[at + 1].toInt() and 0xFF) shl 16) or
                (b[at + 2].toInt() shl 24)
            (value shr 8) / INT24_SCALE
        }

        SampleEncoding.PCM_32_LE -> {
            val value = (b[at].toInt() and 0xFF) or
                ((b[at + 1].toInt() and 0xFF) shl 8) or
                ((b[at + 2].toInt() and 0xFF) shl 16) or
                (b[at + 3].toInt() shl 24)
            (value / INT32_SCALE).toFloat()
        }

        SampleEncoding.FLOAT_32_LE -> {
            val bits = (b[at].toInt() and 0xFF) or
                ((b[at + 1].toInt() and 0xFF) shl 8) or
                ((b[at + 2].toInt() and 0xFF) shl 16) or
                (b[at + 3].toInt() shl 24)
            Float.fromBits(bits)
        }

        SampleEncoding.FLOAT_64_LE -> {
            var bits = 0L
            for (i in 7 downTo 0) bits = (bits shl 8) or (b[at + i].toLong() and 0xFF)
            Double.fromBits(bits).toFloat()
        }
    }

    /** Encodes a planar buffer to interleaved little-endian bytes. */
    public fun encode(buffer: AudioBuffer, encoding: SampleEncoding): ByteArray {
        val bytesPerSample = encoding.bytesPerSample
        val out = ByteArray(buffer.frameCount * buffer.channelCount * bytesPerSample)
        var position = 0
        for (frame in 0 until buffer.frameCount) {
            for (c in 0 until buffer.channelCount) {
                encodeSample(buffer.channels[c][frame], out, position, encoding)
                position += bytesPerSample
            }
        }
        return out
    }

    private fun encodeSample(sample: Float, out: ByteArray, at: Int, encoding: SampleEncoding) {
        when (encoding) {
            SampleEncoding.PCM_8_UNSIGNED -> {
                // Rounded, not truncated: truncation biases every sample toward zero and adds
                // a half-step of avoidable noise on a format that has very little to spare.
                val v = Math.round(sample.coerceIn(-1f, 1f) * INT8_SCALE) + 128
                out[at] = v.coerceIn(0, 255).toByte()
            }

            SampleEncoding.PCM_16_LE -> {
                val v = Math.round(sample.coerceIn(-1f, 1f) * INT16_SCALE).coerceIn(-32768, 32767)
                out[at] = (v and 0xFF).toByte()
                out[at + 1] = ((v shr 8) and 0xFF).toByte()
            }

            SampleEncoding.PCM_24_LE -> {
                val v = Math.round(sample.coerceIn(-1f, 1f) * INT24_SCALE).coerceIn(-8388608, 8388607)
                out[at] = (v and 0xFF).toByte()
                out[at + 1] = ((v shr 8) and 0xFF).toByte()
                out[at + 2] = ((v shr 16) and 0xFF).toByte()
            }

            SampleEncoding.PCM_32_LE -> {
                val v = Math.round(sample.coerceIn(-1f, 1f).toDouble() * INT32_SCALE)
                    .coerceIn(Int.MIN_VALUE.toLong(), Int.MAX_VALUE.toLong()).toInt()
                out[at] = (v and 0xFF).toByte()
                out[at + 1] = ((v shr 8) and 0xFF).toByte()
                out[at + 2] = ((v shr 16) and 0xFF).toByte()
                out[at + 3] = ((v shr 24) and 0xFF).toByte()
            }

            SampleEncoding.FLOAT_32_LE -> {
                val bits = sample.toRawBits()
                out[at] = (bits and 0xFF).toByte()
                out[at + 1] = ((bits shr 8) and 0xFF).toByte()
                out[at + 2] = ((bits shr 16) and 0xFF).toByte()
                out[at + 3] = ((bits shr 24) and 0xFF).toByte()
            }

            SampleEncoding.FLOAT_64_LE -> {
                var bits = sample.toDouble().toRawBits()
                for (i in 0 until 8) {
                    out[at + i] = (bits and 0xFF).toByte()
                    bits = bits ushr 8
                }
            }
        }
    }

    /**
     * Decodes 16-bit interleaved shorts straight from the capture device into planar floats,
     * without an intermediate byte array. This is the hot path during recording, called once
     * per capture buffer, and it allocates exactly one array per channel.
     */
    public fun decodeInt16(interleaved: ShortArray, validSamples: Int, channelCount: Int, sampleRate: Int): AudioBuffer {
        val frames = validSamples / channelCount
        val channels = Array(channelCount) { FloatArray(frames) }
        var r = 0
        for (frame in 0 until frames) {
            for (c in 0 until channelCount) {
                channels[c][frame] = interleaved[r++] / INT16_SCALE
            }
        }
        return AudioBuffer(channels, sampleRate)
    }
}
