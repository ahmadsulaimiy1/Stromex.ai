package com.sajjil.core.dsp

import com.sajjil.core.analysis.LoudnessAnalyzer
import com.sajjil.core.modes.VoiceProfile
import kotlin.math.abs
import kotlin.math.log10
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sqrt

enum class ContentType { RECITATION, LECTURE, NASHEED, SPEECH }

data class ContentFeatures(
    /** Fraction of frames sitting near the noise floor — pause structure. */
    val pauseRatio: Double,
    /** Fraction of *voiced* pause segments longer than ~400ms — long, deliberate pauses vs. quick breaths. */
    val longPauseFraction: Double,
    /** Standard deviation of the detected pitch track, in semitones, across voiced frames — melodic movement. */
    val pitchVariabilitySemitones: Double,
    /** Fraction of frames with a detectable, stable pitch — sung/chanted tone vs. noise-like unvoiced speech. */
    val voicedFraction: Double,
    val dynamicRangeDb: Double,
    /** High-band (>2kHz) energy as a fraction of total energy — brightness. */
    val spectralTilt: Double,
)

data class ContentClassification(val type: ContentType, val confidence: Double, val features: ContentFeatures)

/**
 * SAJJIL Adaptive Mastering: instead of asking the user to pick a
 * mastering profile, measure the take and build the chain automatically.
 *
 * This is a coarse acoustic-feature heuristic — pause structure, pitch
 * movement (classic time-domain autocorrelation pitch tracking, not a
 * trained model), dynamic range, and spectral tilt — mapped to the
 * *closest* flagship [VoiceProfile] and then nudged by the measured
 * features. It is not a language-aware or content-aware classifier: it
 * cannot tell Qur'an recitation from any other rhythmically-paused speech
 * in a language it doesn't parse. Treat the classification as a helpful
 * starting point ("looks most like recitation") that a user can always
 * override by picking a profile directly in Master, not an infallible
 * verdict.
 */
object AdaptiveMasteringEngine {

    fun recommend(samples: FloatArray, sampleRate: Int): ProcessingChainConfig {
        val classification = classify(samples, sampleRate)
        return adjust(baseProfile(classification.type).config, classification.features)
    }

    fun classify(samples: FloatArray, sampleRate: Int): ContentClassification {
        val features = analyzeContent(samples, sampleRate)

        // Score each content type against the measured features; highest wins.
        val scores = mapOf(
            ContentType.NASHEED to (features.pitchVariabilitySemitones / 6.0).coerceIn(0.0, 1.0) * 0.6 +
                features.voicedFraction * 0.4,
            ContentType.RECITATION to (1.0 - abs(features.pauseRatio - 0.25) / 0.25).coerceIn(0.0, 1.0) * 0.5 +
                (1.0 - features.longPauseFraction).coerceIn(0.0, 1.0) * 0.3 +
                features.voicedFraction * 0.2,
            ContentType.LECTURE to features.longPauseFraction * 0.6 +
                (features.dynamicRangeDb / 24.0).coerceIn(0.0, 1.0) * 0.4,
            ContentType.SPEECH to (1.0 - features.pitchVariabilitySemitones / 6.0).coerceIn(0.0, 1.0) * 0.5 +
                (1.0 - features.longPauseFraction) * 0.5,
        )
        val best = scores.maxBy { it.value }
        val totalScore = scores.values.sum().coerceAtLeast(1e-9)
        return ContentClassification(best.key, best.value / totalScore, features)
    }

    fun analyzeContent(samples: FloatArray, sampleRate: Int): ContentFeatures {
        if (samples.size < sampleRate / 10) {
            return ContentFeatures(0.0, 0.0, 0.0, 0.0, 0.0, 0.5)
        }

        val frameMs = 30.0
        val frameSize = max(1, (sampleRate * frameMs / 1000.0).toInt())
        val frames = mutableListOf<FloatArray>()
        var start = 0
        while (start + frameSize <= samples.size) {
            frames.add(samples.copyOfRange(start, start + frameSize))
            start += frameSize
        }
        if (frames.isEmpty()) return ContentFeatures(0.0, 0.0, 0.0, 0.0, 0.0, 0.5)

        val frameDb = frames.map { frameRmsDb(it) }
        // Anchored to the *typical* (median) frame level rather than a low percentile: a
        // percentile-based floor degenerates on a signal with little level variation (e.g. a
        // sustained tone with no real silence) — nearly every frame sits close to that floor,
        // so a floor+10dB threshold ends up misclassifying the entire signal as "pause."
        val typicalLevelDb = frameDb.sorted().let { it[it.size / 2] }
        val speechThreshold = typicalLevelDb - 20.0

        val pauseFlags = frameDb.map { it < speechThreshold }
        val pauseRatio = pauseFlags.count { it }.toDouble() / pauseFlags.size

        val minLongPauseFrames = (400.0 / frameMs).toInt().coerceAtLeast(1)
        var longPauseFrames = 0
        var runLength = 0
        for (isPause in pauseFlags) {
            if (isPause) {
                runLength++
            } else {
                if (runLength >= minLongPauseFrames) longPauseFrames += runLength
                runLength = 0
            }
        }
        if (runLength >= minLongPauseFrames) longPauseFrames += runLength
        val longPauseFraction = if (pauseFlags.any { it }) longPauseFrames.toDouble() / pauseFlags.count { it } else 0.0

        val pitches = frames.mapIndexed { i, frame -> if (pauseFlags[i]) null else estimatePitchHz(frame, sampleRate) }
        val voiced = pitches.filterNotNull()
        val voicedFraction = voiced.size.toDouble() / frames.size
        val pitchVariability = if (voiced.size >= 2) {
            val semitones = voiced.map { 12.0 * kotlin.math.ln(it / voiced.first()) / kotlin.math.ln(2.0) }
            val mean = semitones.average()
            sqrt(semitones.sumOf { (it - mean) * (it - mean) } / semitones.size)
        } else 0.0

        val loudness = LoudnessAnalyzer.analyze(samples, sampleRate)
        val tilt = spectralTilt(samples, sampleRate)

        return ContentFeatures(
            pauseRatio = pauseRatio,
            longPauseFraction = longPauseFraction,
            pitchVariabilitySemitones = pitchVariability,
            voicedFraction = voicedFraction,
            dynamicRangeDb = loudness.dynamicRangeDb,
            spectralTilt = tilt,
        )
    }

    /** Nudges the chosen base profile toward what was actually measured, rather than applying it blindly. */
    private fun adjust(base: ProcessingChainConfig, features: ContentFeatures): ProcessingChainConfig {
        val ratioAdjustment = ((features.dynamicRangeDb - 14.0) / 20.0).coerceIn(-0.6, 0.8)
        val deEsserAdjustment = ((features.spectralTilt - 0.25) * 12.0).coerceIn(-4.0, 4.0)

        return base.copy(
            compressorRatio = (base.compressorRatio + ratioAdjustment).coerceIn(1.5, 6.0),
            deEsserThresholdDb = (base.deEsserThresholdDb - deEsserAdjustment).coerceIn(-30.0, -14.0),
        )
    }

    private fun baseProfile(type: ContentType): VoiceProfile = when (type) {
        ContentType.RECITATION -> VoiceProfile.QARI_PRESTIGE
        ContentType.NASHEED -> VoiceProfile.MAKKAH_STUDIO
        ContentType.LECTURE -> VoiceProfile.LECTURE_AUTHORITY
        ContentType.SPEECH -> VoiceProfile.ROYAL_PODCAST
    }

    private fun frameRmsDb(frame: FloatArray): Double {
        var sum = 0.0
        for (s in frame) sum += s.toDouble() * s
        return 20.0 * log10(max(sqrt(sum / frame.size), 1e-9))
    }

    /** Classic time-domain autocorrelation pitch estimate over a single frame; null when no clear periodicity. */
    private fun estimatePitchHz(frame: FloatArray, sampleRate: Int, minHz: Double = 80.0, maxHz: Double = 500.0): Double? {
        val minLag = (sampleRate / maxHz).toInt().coerceAtLeast(1)
        val maxLag = (sampleRate / minHz).toInt().coerceAtMost(frame.size - 1)
        if (minLag >= maxLag) return null

        var energy = 0.0
        for (s in frame) energy += s.toDouble() * s
        if (energy < 1e-6) return null

        var bestLag = -1
        var bestCorrelation = 0.0
        for (lag in minLag..maxLag) {
            var sum = 0.0
            for (i in 0 until frame.size - lag) sum += frame[i] * frame[i + lag]
            val normalized = sum / energy
            if (normalized > bestCorrelation) {
                bestCorrelation = normalized
                bestLag = lag
            }
        }
        return if (bestLag > 0 && bestCorrelation > 0.35) sampleRate.toDouble() / bestLag else null
    }

    private fun spectralTilt(samples: FloatArray, sampleRate: Int): Double {
        val low = BiquadFilter.lowPass(2000.0, sampleRate.toDouble())
        val high = BiquadFilter.highPass(2000.0, sampleRate.toDouble())
        var lowEnergy = 0.0
        var highEnergy = 0.0
        for (s in samples) {
            val l = low.process(s)
            val h = high.process(s)
            lowEnergy += l.toDouble() * l
            highEnergy += h.toDouble() * h
        }
        val total = lowEnergy + highEnergy
        return if (total < 1e-9) 0.5 else min(1.0, highEnergy / total)
    }
}
