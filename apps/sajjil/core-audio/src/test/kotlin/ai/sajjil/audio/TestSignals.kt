package ai.sajjil.audio

import kotlin.math.PI
import kotlin.math.sin
import kotlin.random.Random

/** Deterministic signal generators shared by the tests. */
object TestSignals {

    fun sine(
        frequencyHz: Double,
        seconds: Double,
        sampleRate: Int = 48000,
        amplitude: Double = 0.5,
        channels: Int = 1,
    ): AudioBuffer {
        val frames = (seconds * sampleRate).toInt()
        val data = FloatArray(frames) {
            (amplitude * sin(2.0 * PI * frequencyHz * it / sampleRate)).toFloat()
        }
        return AudioBuffer(sampleRate, Array(channels) { data.copyOf() })
    }

    /** Sine at a given dBFS level, which is how the loudness tests are specified. */
    fun sineAtDbfs(
        frequencyHz: Double,
        dbfs: Double,
        seconds: Double,
        sampleRate: Int = 48000,
        channels: Int = 1,
    ): AudioBuffer = sine(frequencyHz, seconds, sampleRate, dbToLinear(dbfs), channels)

    /** Reproducible white noise. Seeded so a failure is always reproducible. */
    fun noise(
        seconds: Double,
        sampleRate: Int = 48000,
        amplitude: Double = 0.1,
        channels: Int = 1,
        seed: Int = 42,
    ): AudioBuffer {
        val random = Random(seed)
        val frames = (seconds * sampleRate).toInt()
        return AudioBuffer(
            sampleRate,
            Array(channels) {
                FloatArray(frames) { ((random.nextDouble() * 2 - 1) * amplitude).toFloat() }
            },
        )
    }

    /** A sine plus noise, the shape of a real noisy voice recording. */
    fun sineWithNoise(
        frequencyHz: Double,
        seconds: Double,
        sampleRate: Int = 48000,
        signalAmplitude: Double = 0.4,
        noiseAmplitude: Double = 0.02,
        seed: Int = 7,
    ): AudioBuffer {
        val signal = sine(frequencyHz, seconds, sampleRate, signalAmplitude)
        val noise = noise(seconds, sampleRate, noiseAmplitude, seed = seed)
        val out = signal[0]
        for (i in out.indices) out[i] += noise[0][i]
        return signal
    }

    /** Alternating loud speech-like bursts and silence, for gate and silence tests. */
    fun burstsAndSilence(
        burstSeconds: Double,
        silenceSeconds: Double,
        repeats: Int,
        sampleRate: Int = 48000,
        amplitude: Double = 0.5,
    ): AudioBuffer {
        val parts = ArrayList<AudioBuffer>()
        repeat(repeats) {
            parts += sine(440.0, burstSeconds, sampleRate, amplitude)
            parts += AudioBuffer.silence(sampleRate, 1, (silenceSeconds * sampleRate).toInt())
        }
        return AudioBuffer.concat(parts)
    }

    /** Peak difference between two buffers, for round-trip assertions. */
    fun maxAbsoluteDifference(a: AudioBuffer, b: AudioBuffer): Double {
        require(a.channelCount == b.channelCount && a.frameCount == b.frameCount) {
            "buffers differ in shape: ${a.channelCount}x${a.frameCount} vs ${b.channelCount}x${b.frameCount}"
        }
        var worst = 0.0
        for (c in 0 until a.channelCount) {
            for (i in 0 until a.frameCount) {
                val d = kotlin.math.abs(a.channels[c][i] - b.channels[c][i]).toDouble()
                if (d > worst) worst = d
            }
        }
        return worst
    }
}
