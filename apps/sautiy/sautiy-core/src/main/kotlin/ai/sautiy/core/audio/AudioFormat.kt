package ai.sautiy.core.audio

/**
 * How samples are laid out in bytes on the wire or on disk.
 *
 * SAUTIY works internally in 32-bit float. These encodings exist only at the boundaries —
 * reading a file, writing a file, or handing buffers to and from the platform audio device.
 */
public enum class SampleEncoding(public val bytesPerSample: Int, public val isFloat: Boolean) {
    PCM_8_UNSIGNED(1, false),
    PCM_16_LE(2, false),
    PCM_24_LE(3, false),
    PCM_32_LE(4, false),
    FLOAT_32_LE(4, true),
    FLOAT_64_LE(8, true),
}

/**
 * A complete description of an audio stream's shape.
 *
 * @param sampleRate frames per second
 * @param channelCount 1 for mono, 2 for stereo. SAUTIY supports both throughout; nothing in
 *   the engine assumes mono.
 */
public data class AudioFormat(
    val sampleRate: Int,
    val channelCount: Int,
    val encoding: SampleEncoding = SampleEncoding.FLOAT_32_LE,
) {
    init {
        require(sampleRate in 4_000..768_000) { "Unsupported sample rate: $sampleRate" }
        require(channelCount in 1..2) { "SAUTIY captures and edits mono or stereo, not $channelCount channels" }
    }

    val bytesPerFrame: Int get() = encoding.bytesPerSample * channelCount

    val isMono: Boolean get() = channelCount == 1

    /** Duration of [frames] at this rate, in milliseconds. */
    public fun framesToMillis(frames: Long): Long = frames * 1_000L / sampleRate

    /** Frames spanned by [millis] at this rate, rounded down. */
    public fun millisToFrames(millis: Long): Long = millis * sampleRate / 1_000L

    public fun framesToSeconds(frames: Long): Double = frames.toDouble() / sampleRate

    /** Bytes on disk for [frames] frames in this encoding. */
    public fun framesToBytes(frames: Long): Long = frames * bytesPerFrame

    public companion object {
        /**
         * SAUTIY's working rate. 48 kHz rather than 44.1 kHz because it is the native rate of
         * essentially every Android audio HAL shipped in the last decade, so choosing it means
         * the platform performs no resampling on the capture path — the single largest source
         * of avoidable latency and quality loss on mobile.
         */
        public const val STUDIO_SAMPLE_RATE: Int = 48_000

        /** The CD rate, still required by some publishing targets. */
        public const val CD_SAMPLE_RATE: Int = 44_100

        /** Speech-optimised rate for long-form lectures where storage matters more than air. */
        public const val VOICE_SAMPLE_RATE: Int = 24_000

        public val StudioMono: AudioFormat = AudioFormat(STUDIO_SAMPLE_RATE, 1)
        public val StudioStereo: AudioFormat = AudioFormat(STUDIO_SAMPLE_RATE, 2)
        public val CdStereo: AudioFormat = AudioFormat(CD_SAMPLE_RATE, 2)
    }
}

/**
 * The capture quality the user chooses, expressed in the terms the Bible uses on screen —
 * never as a raw sample rate, because "48 kHz / 24-bit" is not a decision most people can make
 * and every person can *hear*.
 */
public enum class CaptureQuality(
    public val displayName: String,
    public val format: AudioFormat,
    public val storageEncoding: SampleEncoding,
    public val summary: String,
) {
    VOICE(
        displayName = "Voice",
        format = AudioFormat(AudioFormat.VOICE_SAMPLE_RATE, 1),
        storageEncoding = SampleEncoding.PCM_16_LE,
        summary = "Smallest files. Right for long lectures and interviews.",
    ),
    STUDIO(
        displayName = "Studio",
        format = AudioFormat(AudioFormat.STUDIO_SAMPLE_RATE, 1),
        storageEncoding = SampleEncoding.PCM_16_LE,
        summary = "The default. Full-band mono at the device's native rate.",
    ),
    MASTER(
        displayName = "Master",
        format = AudioFormat(AudioFormat.STUDIO_SAMPLE_RATE, 1),
        storageEncoding = SampleEncoding.PCM_24_LE,
        summary = "24-bit headroom for material that will be processed heavily.",
    ),
    STEREO(
        displayName = "Stereo",
        format = AudioFormat(AudioFormat.STUDIO_SAMPLE_RATE, 2),
        storageEncoding = SampleEncoding.PCM_24_LE,
        summary = "Two channels at 24-bit, for rooms and performances.",
    ),
    ;

    /** Bytes per second of recording, used to state remaining time honestly (chapter 3.2.5). */
    public val bytesPerSecond: Long
        get() = format.sampleRate.toLong() * format.channelCount * storageEncoding.bytesPerSample

    /** Recordable seconds in [freeBytes], leaving a safety margin for the file system. */
    public fun secondsAvailable(freeBytes: Long): Long {
        val usable = (freeBytes - SAFETY_MARGIN_BYTES).coerceAtLeast(0)
        return usable / bytesPerSecond
    }

    public companion object {
        /** Never promise the last 8 MiB of a volume. */
        public const val SAFETY_MARGIN_BYTES: Long = 8L * 1024 * 1024
    }
}
