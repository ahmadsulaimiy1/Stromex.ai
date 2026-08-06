package ai.sautiy.core

import ai.sautiy.core.audio.AudioBuffer
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.sqrt

/**
 * Signal generators and measurements shared by the DSP tests.
 *
 * These exist so that assertions can be made about *audio*, in decibels, rather than about
 * array contents. "The 19 kHz tone is 74 dB down after conversion to 16 kHz" is a claim about
 * whether the resampler works; "the array has 16000 entries" is not.
 */
object TestSignals {

    fun sine(
        frequencyHz: Double,
        seconds: Double,
        sampleRate: Int,
        amplitude: Double = 0.5,
        channels: Int = 1,
        phase: Double = 0.0,
    ): AudioBuffer {
        val frames = (seconds * sampleRate).toInt()
        val data = Array(channels) { FloatArray(frames) }
        val step = 2.0 * PI * frequencyHz / sampleRate
        for (i in 0 until frames) {
            val v = (amplitude * sin(step * i + phase)).toFloat()
            for (c in 0 until channels) data[c][i] = v
        }
        return AudioBuffer(data, sampleRate)
    }

    /** Deterministic pseudo-random noise. Seeded so failures reproduce exactly. */
    fun noise(seconds: Double, sampleRate: Int, amplitude: Double = 0.2, seed: Long = 1_618_033L, channels: Int = 1): AudioBuffer {
        val frames = (seconds * sampleRate).toInt()
        val random = java.util.Random(seed)
        val data = Array(channels) { FloatArray(frames) }
        for (c in 0 until channels) {
            for (i in 0 until frames) {
                data[c][i] = (random.nextGaussian() * amplitude).toFloat().coerceIn(-1f, 1f)
            }
        }
        return AudioBuffer(data, sampleRate)
    }

    fun silence(seconds: Double, sampleRate: Int, channels: Int = 1): AudioBuffer =
        AudioBuffer.silence(channels, (seconds * sampleRate).toInt(), sampleRate)

    /** A linear sweep, for checking a filter's response across the band in one pass. */
    fun sweep(fromHz: Double, toHz: Double, seconds: Double, sampleRate: Int, amplitude: Double = 0.5): AudioBuffer {
        val frames = (seconds * sampleRate).toInt()
        val out = FloatArray(frames)
        var phase = 0.0
        for (i in 0 until frames) {
            val t = i.toDouble() / frames
            val f = fromHz + (toHz - fromHz) * t
            phase += 2.0 * PI * f / sampleRate
            out[i] = (amplitude * sin(phase)).toFloat()
        }
        return AudioBuffer.mono(out, sampleRate)
    }

    /**
     * Amplitude at exactly one frequency, by Goertzel evaluation of the windowed DTFT.
     *
     * The **Hann window is not optional here**, and getting this wrong once already cost a
     * false accusation against the resampler. Measuring an unwindowed block gives rectangular
     * leakage that falls off only as 1/Δf: a −6 dBFS tone 800 Hz away still contributes about
     * −55 dBFS at the measurement point, so any assertion of the form "there is nothing at this
     * frequency" is really measuring the probe rather than the signal. Hann's sidelobes decay
     * at 18 dB per octave and put that same neighbour below −100 dBFS.
     *
     * Goertzel is evaluated at arbitrary, non-integer k, so this reads the DTFT at the exact
     * frequency asked for and suffers none of the scalloping loss an FFT bin would. Normalising
     * by the window's coherent sum keeps a pure tone reading as its own amplitude.
     */
    fun magnitudeAt(buffer: AudioBuffer, frequencyHz: Double, channel: Int = 0): Double {
        val x = buffer.channels[channel]
        val n = x.size
        if (n < 4) return 0.0

        val omega = 2.0 * PI * frequencyHz / buffer.sampleRate
        val coefficient = 2.0 * cos(omega)
        var s1 = 0.0
        var s2 = 0.0
        var windowSum = 0.0

        for (i in 0 until n) {
            val w = 0.5 - 0.5 * cos(2.0 * PI * i / (n - 1))
            windowSum += w
            val s0 = x[i] * w + coefficient * s1 - s2
            s2 = s1
            s1 = s0
        }
        val real = s1 - s2 * cos(omega)
        val imaginary = s2 * sin(omega)
        return 2.0 * sqrt(real * real + imaginary * imaginary) / windowSum
    }

    fun magnitudeDbAt(buffer: AudioBuffer, frequencyHz: Double, channel: Int = 0): Double =
        ai.sautiy.core.audio.Decibels.fromLinear(magnitudeAt(buffer, frequencyHz, channel))

    /**
     * Signal-to-noise ratio in dB between a reference and a processed version of it, after
     * trimming both to a common length.
     */
    fun snrDb(reference: AudioBuffer, measured: AudioBuffer, channel: Int = 0): Double {
        val a = reference.channels[channel]
        val b = measured.channels[channel]
        val n = minOf(a.size, b.size)
        var signal = 0.0
        var error = 0.0
        for (i in 0 until n) {
            signal += a[i].toDouble() * a[i]
            val difference = a[i].toDouble() - b[i]
            error += difference * difference
        }
        if (error == 0.0) return Double.POSITIVE_INFINITY
        return 10.0 * kotlin.math.log10(signal / error)
    }

    /** Peak absolute sample, as a plain double. */
    fun peak(buffer: AudioBuffer, channel: Int = 0): Double =
        buffer.channels[channel].maxOf { kotlin.math.abs(it) }.toDouble()

    /** Trims [skipFrames] from both ends, to exclude filter start-up and tail-off from a measurement. */
    fun trimEdges(buffer: AudioBuffer, skipFrames: Int): AudioBuffer =
        buffer.slice(skipFrames, (buffer.frameCount - skipFrames).coerceAtLeast(skipFrames))
}
