package com.sajjil.core.modes

import com.sajjil.core.audio.BitDepth

/** Recording quality tiers, from casual voice notes up to archival mastering source. */
enum class RecordingQuality(val displayName: String, val sampleRate: Int, val bitDepth: BitDepth) {
    STANDARD("Standard", 44100, BitDepth.PCM_16),
    HIGH("High", 48000, BitDepth.PCM_16),
    PROFESSIONAL("Professional", 48000, BitDepth.PCM_24),
    STUDIO("Studio", 96000, BitDepth.PCM_24),
    ULTRA_STUDIO("Ultra Studio", 96000, BitDepth.FLOAT_32),
    REFERENCE_MASTER("Reference Master", 192000, BitDepth.FLOAT_32),
}
