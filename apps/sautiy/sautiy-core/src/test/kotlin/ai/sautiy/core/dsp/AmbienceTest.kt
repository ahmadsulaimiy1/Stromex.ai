package ai.sautiy.core.dsp

import ai.sautiy.core.TestSignals
import ai.sautiy.core.audio.AudioBuffer
import kotlin.math.abs
import kotlin.math.log10
import kotlin.math.sqrt
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * The ambience engine, measured rather than described.
 *
 * The claims this file has to defend are the ones the panel makes to the user: that a decay
 * stated in seconds is the decay you get, that pre-delay is a real gap, that width is real
 * stereo, and — the one that decides whether live preview is possible at all — that the engine
 * gives the same audio whatever block size it is fed in.
 */
class AmbienceTest {

    private val rate = 48_000

    /** Pure wet, so the tail can be measured without the dry signal on top of it. */
    private fun wetOnly(settings: AmbienceSettings) = settings.copy(amount = 1.0, wetDryMix = 1.0)

    private fun impulseResponse(settings: AmbienceSettings, seconds: Double, channels: Int = 1): AudioBuffer {
        val frames = (seconds * rate).toInt()
        val buffer = AudioBuffer.silence(channels, frames, rate)
        for (c in 0 until channels) buffer.channels[c][0] = 1f
        Ambience(settings, rate, channels).process(buffer)
        return buffer
    }

    /**
     * T30, the standard reverberation measurement: fit the decay between −5 dB and −35 dB and
     * extrapolate to −60. Measuring to −60 directly would measure the noise floor of the tail
     * rather than the tail.
     */
    private fun measuredRt60(response: FloatArray, sampleRate: Int): Double {
        // Schroeder backward integration turns one noisy impulse response into a smooth curve.
        val energy = DoubleArray(response.size)
        var running = 0.0
        for (i in response.indices.reversed()) {
            running += response[i].toDouble() * response[i]
            energy[i] = running
        }
        val total = energy[0]
        if (total <= 0.0) return 0.0
        val curveDb = DoubleArray(energy.size) { 10.0 * log10((energy[it] / total).coerceAtLeast(1e-18)) }

        val from = curveDb.indexOfFirst { it <= -5.0 }
        val to = curveDb.indexOfFirst { it <= -35.0 }
        if (from < 0 || to <= from) return 0.0
        val slopeDbPerFrame = (curveDb[to] - curveDb[from]) / (to - from).toDouble()
        return -60.0 / slopeDbPerFrame / sampleRate
    }

    private fun rms(samples: FloatArray): Double {
        var energy = 0.0
        for (s in samples) energy += s.toDouble() * s
        return sqrt(energy / samples.size.coerceAtLeast(1))
    }

    @Test
    fun `block size does not change a single sample`() {
        // This is the property live preview stands on. An engine that rebuilds its delay lines
        // per block restarts the tail at every boundary — a click twenty-five times a second.
        val settings = AmbienceSettings(
            roomSize = 0.7, decaySeconds = 1.5, preDelayMs = 25.0,
            earlyReflections = 0.6, width = 0.9, wetDryMix = 0.4,
        )
        val source = TestSignals.noise(1.0, rate, amplitude = 0.5, channels = 2)

        val oneShot = source.copy()
        Ambience(settings, rate, 2).process(oneShot)

        val streamed = source.copy()
        val engine = Ambience(settings, rate, 2)
        var position = 0
        // Deliberately not a power of two, and not a divisor of the length, so buckets and
        // blocks fall out of step exactly as they do under a real audio callback.
        val block = 137
        while (position < streamed.frameCount) {
            val frames = minOf(block, streamed.frameCount - position)
            val slice = streamed.slice(position, position + frames)
            engine.process(slice)
            for (c in 0 until 2) slice.channels[c].copyInto(streamed.channels[c], position)
            position += frames
        }

        for (c in 0 until 2) {
            for (i in 0 until oneShot.frameCount) {
                assertEquals("channel $c frame $i", oneShot.channels[c][i], streamed.channels[c][i], 0f)
            }
        }
    }

    @Test
    fun `a bypassed space returns the audio untouched, bit for bit`() {
        val source = TestSignals.noise(0.2, rate, amplitude = 0.6)
        val processed = source.copy()
        Ambience(AmbienceSettings.NONE, rate, 1).process(processed)

        assertTrue(AmbienceSettings.NONE.isBypassed)
        for (i in 0 until source.frameCount) {
            assertEquals(source.channels[0][i], processed.channels[0][i], 0f)
        }
    }

    @Test
    fun `the measured decay is the decay the panel prints`() {
        // The whole reason the feedback is derived from RT60 rather than from a size dial: a
        // number shown to a user has to be true.
        for (requested in listOf(0.5, 1.0, 2.0, 3.0)) {
            val settings = wetOnly(
                AmbienceSettings(
                    roomSize = 0.6, decaySeconds = requested, preDelayMs = 0.0,
                    earlyReflections = 0.0, warmth = 0.0, wetDryMix = 1.0,
                ),
            )
            val response = impulseResponse(settings, requested * 2.5 + 0.5)
            val measured = measuredRt60(response.channels[0], rate)

            assertTrue(
                "Asked for $requested s, measured $measured s",
                abs(measured - requested) <= requested * 0.25,
            )
        }
    }

    @Test
    fun `a longer decay always outlasts a shorter one`() {
        val short = impulseResponse(
            wetOnly(AmbienceSettings(decaySeconds = 0.4, earlyReflections = 0.0, preDelayMs = 0.0)),
            4.0,
        )
        val long = impulseResponse(
            wetOnly(AmbienceSettings(decaySeconds = 3.0, earlyReflections = 0.0, preDelayMs = 0.0)),
            4.0,
        )
        // Two seconds in, the short room is over and the long one is not.
        val late = 2 * rate
        val shortTail = rms(short.channels[0].copyOfRange(late, late + rate / 2))
        val longTail = rms(long.channels[0].copyOfRange(late, late + rate / 2))

        assertTrue("Short room tail $shortTail, long room tail $longTail", longTail > shortTail * 10)
    }

    @Test
    fun `damping shortens the high frequencies without shortening the low ones`() {
        // What a warm room means physically: soft surfaces absorb treble first.
        fun tailAt(frequency: Double, damping: Double): Double {
            val settings = wetOnly(
                AmbienceSettings(
                    decaySeconds = 2.0, roomSize = 0.7, preDelayMs = 0.0,
                    earlyReflections = 0.0, damping = damping, warmth = 0.5, brightness = 0.5,
                    presence = 0.0, speechPriority = 0.0, wetDryMix = 1.0,
                ),
            )
            val source = TestSignals.sine(frequency, 0.5, rate, amplitude = 0.7)
            val frames = rate * 2
            val padded = AudioBuffer.silence(1, frames, rate)
            source.channels[0].copyInto(padded.channels[0], 0)
            Ambience(settings, rate, 1).process(padded)
            // A second after the tone stops, how much is left?
            return rms(padded.channels[0].copyOfRange((1.4 * rate).toInt(), frames))
        }

        val liveLow = tailAt(200.0, damping = 0.0)
        val dampedLow = tailAt(200.0, damping = 1.0)
        val liveHigh = tailAt(8_000.0, damping = 0.0)
        val dampedHigh = tailAt(8_000.0, damping = 1.0)

        assertTrue("Damping must cut the high tail: $liveHigh → $dampedHigh", dampedHigh < liveHigh * 0.5)
        assertTrue("Damping must leave the low tail alone: $liveLow → $dampedLow", dampedLow > liveLow * 0.5)
    }

    @Test
    fun `pre-delay is a real gap before the room answers`() {
        val preDelayMs = 50.0
        val settings = wetOnly(
            AmbienceSettings(
                roomSize = 0.5, decaySeconds = 1.5, preDelayMs = preDelayMs,
                earlyReflections = 1.0, wetDryMix = 1.0,
            ),
        )
        val response = impulseResponse(settings, 1.0)
        val expected = (preDelayMs * rate / 1000.0).toInt()

        val firstSound = response.channels[0].indexOfFirst { abs(it) > 1e-6f }
        assertTrue("Nothing at all came out", firstSound >= 0)
        assertTrue(
            "The room answered at frame $firstSound, before the $expected-frame pre-delay",
            firstSound >= expected,
        )
    }

    @Test
    fun `pre-delay never delays the voice itself`() {
        // Delaying the dry path would put a speaker out of time with everything else. The
        // pre-delay feeds the room only.
        val settings = AmbienceSettings(
            roomSize = 0.5, decaySeconds = 1.0, preDelayMs = 120.0,
            earlyReflections = 0.5, amount = 1.0, wetDryMix = 0.3,
        )
        val frames = rate / 2
        val buffer = AudioBuffer.silence(1, frames, rate)
        buffer.channels[0][0] = 1f
        Ambience(settings, rate, 1).process(buffer)

        // The dry impulse is still at frame 0, scaled by the dry proportion.
        assertEquals(0.7f, buffer.channels[0][0], 1e-4f)
    }

    @Test
    fun `width is the difference between the two ears`() {
        val narrow = wetOnly(
            AmbienceSettings(roomSize = 0.6, decaySeconds = 1.2, width = 0.0, wetDryMix = 1.0),
        )
        val wide = narrow.copy(width = 1.0)

        val narrowResponse = impulseResponse(narrow, 1.0, channels = 2)
        val wideResponse = impulseResponse(wide, 1.0, channels = 2)

        var narrowDifference = 0.0
        var wideDifference = 0.0
        for (i in 0 until narrowResponse.frameCount) {
            narrowDifference += abs(narrowResponse.channels[0][i] - narrowResponse.channels[1][i]).toDouble()
            wideDifference += abs(wideResponse.channels[0][i] - wideResponse.channels[1][i]).toDouble()
        }

        assertEquals("At width 0 both ears hear one room", 0.0, narrowDifference, 1e-9)
        assertTrue("At width 1 the ears must differ, was $wideDifference", wideDifference > 0.1)
    }

    @Test
    fun `a larger room answers later`() {
        fun firstReflection(roomSize: Double): Int {
            val settings = wetOnly(
                AmbienceSettings(
                    roomSize = roomSize, decaySeconds = 1.5, preDelayMs = 0.0,
                    earlyReflections = 1.0, wetDryMix = 1.0,
                ),
            )
            return impulseResponse(settings, 0.5).channels[0].indexOfFirst { abs(it) > 1e-6f }
        }

        val small = firstReflection(0.0)
        val large = firstReflection(1.0)
        assertTrue("Small room first reflection at $small, large at $large", large > small)
    }

    @Test
    fun `early reflections can be turned off and on and it is audible`() {
        val base = wetOnly(
            AmbienceSettings(roomSize = 0.5, decaySeconds = 1.0, preDelayMs = 5.0, wetDryMix = 1.0),
        )
        val without = impulseResponse(base.copy(earlyReflections = 0.0), 0.5)
        val with = impulseResponse(base.copy(earlyReflections = 1.0), 0.5)

        // The first reflection lands around 13 ms (5 ms pre-delay plus an 8 ms tap) and the comb
        // bank's shortest loop does not return until about 30 ms. The window between them
        // contains early reflections and nothing else, which is the only place this can be
        // measured cleanly.
        val window = (0.024 * rate).toInt()
        val withoutEarly = rms(without.channels[0].copyOfRange(0, window))
        val withEarly = rms(with.channels[0].copyOfRange(0, window))
        assertTrue(
            "Early reflections must add energy up front: $withoutEarly → $withEarly",
            withEarly > withoutEarly * 2,
        )
    }

    @Test
    fun `amount and mix both scale the room, and either at zero is silence from it`() {
        val settings = AmbienceSettings(roomSize = 0.6, decaySeconds = 1.2, wetDryMix = 0.4)
        val source = TestSignals.noise(0.3, rate, amplitude = 0.4)

        fun wetEnergy(amount: Double): Double {
            val processed = source.copy()
            Ambience(settings.copy(amount = amount), rate, 1).process(processed)
            var difference = 0.0
            for (i in 0 until source.frameCount) {
                val d = (processed.channels[0][i] - source.channels[0][i]).toDouble()
                difference += d * d
            }
            return sqrt(difference / source.frameCount)
        }

        assertEquals("Amount 0 must be a complete bypass", 0.0, wetEnergy(0.0), 0.0)
        assertTrue(wetEnergy(1.0) > wetEnergy(0.5))
        assertTrue(wetEnergy(0.5) > 0.0)
    }

    @Test
    fun `every space stays finite and inside the rails`() {
        val source = TestSignals.noise(0.6, rate, amplitude = 0.85, channels = 2)
        for (preset in VoiceSpacePreset.entries) {
            val settings = preset.settings.effectiveAmbience
            if (settings.isBypassed) continue
            val processed = source.copy()
            Ambience(settings, rate, 2).process(processed)

            for (c in 0 until 2) {
                for (sample in processed.channels[c]) {
                    assertTrue("${preset.displayName} produced $sample", sample.isFinite())
                    assertTrue("${preset.displayName} ran away to $sample", abs(sample) < 4f)
                }
            }
        }
    }

    @Test
    fun `no space is so loud or so quiet that presets cannot be compared by ear`() {
        // Decay time must not double as a volume control. Without the comb-bank normalisation a
        // three-second hall is many times louder than a booth at the same mix, and no two
        // presets can be judged against each other — which is the whole point of having a list.
        val dryOnly = TestSignals.noise(1.0, rate, amplitude = 0.5)
        var dryEnergy = 0.0
        for (sample in dryOnly.channels[0]) dryEnergy += sample.toDouble() * sample

        val levels = LinkedHashMap<String, Double>()
        for (preset in VoiceSpacePreset.entries) {
            val settings = preset.settings.effectiveAmbience
            if (settings.isBypassed) continue

            // The window has to contain the tail, and the comparison has to be of energy rather
            // than RMS. A room redistributes energy in time; comparing RMS across windows of
            // different lengths just measures how long the tail is and reads every large space
            // as too quiet.
            val frames = ((1.0 + settings.decaySeconds) * rate).toInt()
            val padded = AudioBuffer.silence(1, frames, rate)
            dryOnly.channels[0].copyInto(padded.channels[0], 0)
            Ambience(wetOnly(settings), rate, 1).process(padded)

            var wetEnergy = 0.0
            for (sample in padded.channels[0]) wetEnergy += sample.toDouble() * sample
            levels[preset.displayName] = 10.0 * log10((wetEnergy / dryEnergy).coerceAtLeast(1e-12))
        }

        // Comparability is a statement about the *spread*, not about any one preset: what breaks
        // an audition is one space arriving twice as loud as the last, not the whole set sitting
        // a few decibels down.
        val quietest = levels.minBy { it.value }
        val loudest = levels.maxBy { it.value }
        assertTrue(
            "The spaces span ${loudest.value - quietest.value} dB, from ${quietest.key} at " +
                "${quietest.value} dB to ${loudest.key} at ${loudest.value} dB — too wide to " +
                "compare by ear",
            loudest.value - quietest.value <= 12.0,
        )
        for ((name, level) in levels) {
            assertTrue(
                "$name returns $level dB of the energy put into it",
                level in -14.0..8.0,
            )
        }
    }

    @Test
    fun `reset clears the tail so a seek does not drag the old room with it`() {
        val settings = wetOnly(AmbienceSettings(roomSize = 0.8, decaySeconds = 2.5, wetDryMix = 1.0))
        val engine = Ambience(settings, rate, 1)

        val loud = TestSignals.noise(0.5, rate, amplitude = 0.9)
        engine.process(loud)

        val silenceAfterReset = AudioBuffer.silence(1, rate / 4, rate)
        engine.reset()
        engine.process(silenceAfterReset)
        assertEquals("A reset room must be silent", 0f, silenceAfterReset.peak(), 0f)

        // And without the reset it would not be — otherwise the test proves nothing.
        val ringing = AudioBuffer.silence(1, rate / 4, rate)
        val stillRinging = Ambience(settings, rate, 1)
        stillRinging.process(TestSignals.noise(0.5, rate, amplitude = 0.9))
        stillRinging.process(ringing)
        assertNotEquals(0f, ringing.peak())
    }

    /**
     * Spectral crest: the peakiest bin against the average.
     *
     * A ringing tail concentrates its energy in a few resonant bins and reads high; a smeared one
     * spreads across many and reads low. This is what "metallic" is, measured.
     */
    private fun spectralCrest(samples: FloatArray, from: Int, count: Int): Double {
        val n = Integer.highestOneBit(count)
        val real = DoubleArray(n)
        for (i in 0 until n) {
            // Hann, so the measurement is of the tail and not of the window's own edges.
            val w = 0.5 - 0.5 * kotlin.math.cos(2.0 * Math.PI * i / (n - 1))
            real[i] = samples[from + i].toDouble() * w
        }
        val imaginary = DoubleArray(n)
        Fft(n).forward(real, imaginary)
        val spectrum = DoubleArray(n / 2) { sqrt(real[it] * real[it] + imaginary[it] * imaginary[it]) }
        // Measured inside narrow sub-bands and averaged. Crest across one wide band confuses
        // ringing with tone: a tail that is simply darker has a lower mean and therefore a
        // higher crest, without ringing at all. A 500 Hz band is locally flat, so what is left
        // is the peakiness itself.
        var total = 0.0
        var bands = 0
        var edge = 500.0
        while (edge < 4_000.0) {
            val lo = (edge * n / rate).toInt()
            val hi = ((edge + 500.0) * n / rate).toInt().coerceAtMost(spectrum.size - 1)
            if (hi > lo) {
                var peak = 0.0
                var sum = 0.0
                for (i in lo..hi) {
                    if (spectrum[i] > peak) peak = spectrum[i]
                    sum += spectrum[i]
                }
                val mean = sum / (hi - lo + 1)
                if (mean > 0.0) {
                    total += peak / mean
                    bands++
                }
            }
            edge += 500.0
        }
        return if (bands == 0) 0.0 else total / bands
    }

    @Test
    fun `keeping the tail moving removes the metallic ring`() {
        // The single biggest difference between a tail that sounds like a room and one that
        // sounds like an effect. Static combs resonate at fixed frequencies; a wandering read
        // position smears those resonances into a continuous response.
        val base = wetOnly(
            AmbienceSettings(
                roomSize = 0.7, decaySeconds = 2.0, preDelayMs = 0.0, earlyReflections = 0.0,
                damping = 0.3, diffusion = 0.6, presence = 0.0, speechPriority = 0.0,
                wetDryMix = 1.0,
            ),
        )
        val still = impulseResponse(base.copy(tailSmoothness = 0.0), 2.0)
        val moving = impulseResponse(base.copy(tailSmoothness = 1.0), 2.0)

        // Measured well into the tail, where the ringing is all that is left.
        val at = (0.5 * rate).toInt()
        val window = 16_384
        val ringing = spectralCrest(still.channels[0], at, window)
        val smeared = spectralCrest(moving.channels[0], at, window)

        assertTrue(
            "A still tail should ring more than a moving one: still $ringing, moving $smeared",
            smeared < ringing,
        )
    }

    @Test
    fun `diffusion multiplies the reflections instead of leaving them countable`() {
        // Low diffusion is heard as separate ticks; high diffusion as texture. Counting sign
        // changes in the tail is a fair proxy for how many distinct events are arriving.
        fun density(diffusion: Double): Int {
            val settings = wetOnly(
                AmbienceSettings(
                    roomSize = 0.8, decaySeconds = 2.0, preDelayMs = 0.0, earlyReflections = 0.0,
                    diffusion = diffusion, tailSmoothness = 0.0, presence = 0.0,
                    speechPriority = 0.0, wetDryMix = 1.0,
                ),
            )
            val response = impulseResponse(settings, 1.0).channels[0]
            var crossings = 0
            for (i in (rate / 10) until (rate / 2)) {
                if (response[i - 1] <= 0f && response[i] > 0f) crossings++
            }
            return crossings
        }

        val sparse = density(0.0)
        val dense = density(1.0)
        assertTrue("Diffusion did not thicken the tail: $sparse then $dense", dense > sparse)
    }

    @Test
    fun `the reverb send loses the bottom so a large room does not turn to mud`() {
        // Voice energy below about 200 Hz carries no intelligibility and a great deal of power.
        // Putting it into a long tail is exactly what makes a big space unusable for speech.
        fun wetAt(frequency: Double): Double {
            val settings = wetOnly(
                AmbienceSettings(
                    roomSize = 0.8, decaySeconds = 2.0, preDelayMs = 0.0, earlyReflections = 0.5,
                    presence = 0.0, speechPriority = 0.0, wetDryMix = 1.0,
                ),
            )
            val source = TestSignals.sine(frequency, 1.0, rate, amplitude = 0.5)
            Ambience(settings, rate, 1).process(source)
            return rms(source.channels[0].copyOfRange(rate / 2, rate))
        }

        val low = wetAt(70.0)
        val speech = wetAt(1_000.0)
        assertTrue(
            "70 Hz reached the room at $low against $speech at 1 kHz — the send is not filtered",
            low < speech * 0.5,
        )
    }

    @Test
    fun `speech priority makes the room stand back while a word is being spoken`() {
        // What keeps a cathedral intelligible, and what a mixing engineer does by hand.
        val settings = AmbienceSettings(
            roomSize = 0.85, decaySeconds = 2.5, preDelayMs = 30.0, earlyReflections = 0.4,
            wetDryMix = 0.4, amount = 1.0,
        )

        // A word, then a gap, then a word.
        val frames = rate * 3
        val source = AudioBuffer.silence(1, frames, rate)
        val step = 2.0 * Math.PI * 300.0 / rate
        for (i in 0 until rate) source.channels[0][i] = (0.6 * kotlin.math.sin(step * i)).toFloat()

        fun tailInTheGap(priority: Double): Double {
            val processed = source.copy()
            Ambience(
                settings.copy(speechPriority = priority, amount = 1.0, wetDryMix = 1.0),
                rate,
                1,
            ).process(processed)
            // 200 ms after the word stops: the room, with no voice on top of it.
            return rms(processed.channels[0].copyOfRange(rate + rate / 5, rate + rate / 2))
        }

        // Measured on the room alone. Measuring the mixture instead confuses "the room got
        // quieter" with "the whole output got quieter", which are not the same claim.
        fun roomDuringSpeech(priority: Double): Double {
            val processed = source.copy()
            Ambience(
                settings.copy(speechPriority = priority, amount = 1.0, wetDryMix = 1.0),
                rate,
                1,
            ).process(processed)
            return rms(processed.channels[0].copyOfRange(rate / 2, rate))
        }

        val off = roomDuringSpeech(0.0)
        val on = roomDuringSpeech(1.0)
        assertTrue("Speech priority did not duck the room: $off then $on", on < off)

        // And the room must still be there in the gap — ducking, not removing.
        assertTrue("The tail vanished entirely", tailInTheGap(1.0) > 1e-5)
    }

    @Test
    fun `every mode is the same room at a different strength`() {
        val space = VoiceSpacePreset.LECTURE_HALL.settings.ambience
        val natural = AmbienceMode.NATURAL.applyTo(space)
        val studio = AmbienceMode.STUDIO.applyTo(space)
        val immersive = AmbienceMode.IMMERSIVE.applyTo(space)

        assertTrue(natural.wetDryMix < studio.wetDryMix)
        assertTrue(studio.wetDryMix < immersive.wetDryMix)

        // The room itself is unchanged — only how much of it there is.
        assertEquals(space.decaySeconds, immersive.decaySeconds, 0.0)
        assertEquals(space.roomSize, immersive.roomSize, 0.0)
        assertEquals(space.preDelayMs, immersive.preDelayMs, 0.0)

        // More room means less speech, so the protection scales with the thing it protects
        // against: turning the room up cannot quietly cost intelligibility.
        assertTrue(natural.speechPriority >= space.speechPriority)
        assertTrue(immersive.speechPriority > 0.0)

        // A bypassed space stays bypassed rather than acquiring a room from a mode.
        assertTrue(AmbienceMode.IMMERSIVE.applyTo(AmbienceSettings.NONE).isBypassed)
    }

    @Test
    fun `settings refuse values they cannot honour`() {
        assertTrue(runCatching { AmbienceSettings(decaySeconds = 0.0) }.isFailure)
        assertTrue(runCatching { AmbienceSettings(decaySeconds = 60.0) }.isFailure)
        assertTrue(runCatching { AmbienceSettings(preDelayMs = -1.0) }.isFailure)
        assertTrue(runCatching { AmbienceSettings(roomSize = 1.5) }.isFailure)
        assertTrue(runCatching { AmbienceSettings(width = -0.1) }.isFailure)
        assertTrue(runCatching { Ambience(AmbienceSettings(), 48_000, 3) }.isFailure)
    }
}
