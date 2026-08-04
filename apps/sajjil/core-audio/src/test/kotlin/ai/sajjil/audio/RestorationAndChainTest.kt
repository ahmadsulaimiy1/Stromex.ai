package ai.sajjil.audio

import ai.sajjil.audio.analysis.QualityAnalyzer
import ai.sajjil.audio.analysis.QualityFinding
import ai.sajjil.audio.chain.AmbienceProfiles
import ai.sajjil.audio.chain.EnhancementChain
import ai.sajjil.audio.chain.EnhancementSettings
import ai.sajjil.audio.chain.StudioPresets
import ai.sajjil.audio.chain.VoiceStyles
import ai.sajjil.audio.dsp.DeClicker
import ai.sajjil.audio.dsp.DeClipper
import ai.sajjil.audio.dsp.HumRemover
import ai.sajjil.audio.dsp.NoiseReductionSettings
import ai.sajjil.audio.dsp.Reverb
import ai.sajjil.audio.dsp.ReverbSettings
import ai.sajjil.audio.dsp.SpectralNoiseReducer
import ai.sajjil.audio.loudness.LoudnessMeter
import ai.sajjil.audio.waveform.LiveWaveform
import ai.sajjil.audio.waveform.WaveformPeaks
import kotlin.math.abs
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertTrue

class NoiseReductionTest {

    private val sampleRate = 48000

    /**
     * Speech with pauses over a continuous noise floor — the signal this stage is designed for.
     * The pauses are what let the noise be estimated at all; without them there is no moment in
     * the recording where noise can be observed on its own.
     */
    private fun noisySpeech(): AudioBuffer {
        val signal = TestSignals.burstsAndSilence(
            burstSeconds = 0.6, silenceSeconds = 0.6, repeats = 4,
            sampleRate = sampleRate, amplitude = 0.4,
        )
        val noise = TestSignals.noise(signal.durationSeconds, sampleRate, amplitude = 0.03)
        for (i in 0 until signal.frameCount) signal[0][i] += noise[0][i]
        return signal
    }

    @Test
    fun `noise between speech is reduced while the speech survives`() {
        val signal = noisySpeech()
        val toneBefore = burstEnergy(signal, 440.0)

        val cleaned = SpectralNoiseReducer(NoiseReductionSettings(strength = 0.7)).process(signal)

        val toneAfter = burstEnergy(cleaned, 440.0)
        assertTrue(toneAfter > toneBefore * 0.5, "the speech itself was damaged: $toneBefore -> $toneAfter")

        // Noise in a band the speech does not occupy should be well down.
        val noiseBefore = burstEnergy(signal, 9000.0)
        val noiseAfter = burstEnergy(cleaned, 9000.0)
        assertTrue(
            noiseAfter < noiseBefore * 0.7,
            "noise away from the speech was not reduced: $noiseBefore -> $noiseAfter",
        )
    }

    @Test
    fun `the noise floor in the pauses drops`() {
        val signal = noisySpeech()
        // Measure inside the first gap, which runs from 0.6 s to 1.2 s.
        val gap = { b: AudioBuffer ->
            b.slice((0.75 * sampleRate).toInt(), (1.05 * sampleRate).toInt()).rms()
        }
        val before = gap(signal)
        val after = gap(SpectralNoiseReducer(NoiseReductionSettings(strength = 0.7)).process(signal))
        assertTrue(after < before * 0.5, "the pauses were not cleaned up: $before -> $after")
    }

    @Test
    fun `zero strength is an exact bypass`() {
        val signal = TestSignals.sineWithNoise(440.0, 1.0, sampleRate)
        val result = SpectralNoiseReducer(NoiseReductionSettings(strength = 0.0)).process(signal)
        assertEquals(0.0, TestSignals.maxAbsoluteDifference(signal, result))
    }

    @Test
    fun `length is preserved exactly`() {
        // Overlap-add is easy to get subtly wrong at the tail; a shortened recording would be
        // immediately obvious to a user and is worth pinning down.
        for (frames in listOf(4096, 5000, 48000, 50123)) {
            val signal = AudioBuffer(sampleRate, arrayOf(FloatArray(frames) { 0.1f }))
            val result = SpectralNoiseReducer(NoiseReductionSettings(strength = 0.5)).process(signal)
            assertEquals(frames, result.frameCount, "length changed for a $frames-frame input")
        }
    }

    @Test
    fun `audio shorter than one analysis window is passed through untouched`() {
        val tiny = AudioBuffer(sampleRate, arrayOf(FloatArray(500) { 0.2f }))
        val result = SpectralNoiseReducer(NoiseReductionSettings(strength = 0.8)).process(tiny)
        assertEquals(500, result.frameCount)
    }

    /** Band energy measured inside a burst, clear of the surrounding pauses. */
    private fun burstEnergy(buffer: AudioBuffer, frequency: Double): Double {
        val filtered = buffer.copy()
        ai.sajjil.audio.dsp.Biquad(
            ai.sajjil.audio.dsp.BiquadDesign.bandPass(frequency, sampleRate, q = 6.0)
        ).process(filtered[0])
        return filtered.slice((0.15 * sampleRate).toInt(), (0.5 * sampleRate).toInt()).rms()
    }
}

class HumRemoverTest {

    private val sampleRate = 48000

    @Test
    fun `hum at the fundamental and its harmonics is removed`() {
        val voice = TestSignals.sine(500.0, 2.0, sampleRate, amplitude = 0.4)
        val hum = TestSignals.sine(50.0, 2.0, sampleRate, amplitude = 0.15)
        val hum150 = TestSignals.sine(150.0, 2.0, sampleRate, amplitude = 0.08)
        for (i in 0 until voice.frameCount) {
            voice[0][i] += hum[0][i] + hum150[0][i]
        }

        val before50 = energyAt(voice, 50.0)
        val before500 = energyAt(voice, 500.0)

        HumRemover(sampleRate, fundamentalHz = 50.0).process(voice)

        assertTrue(energyAt(voice, 50.0) < before50 * 0.1, "the 50 Hz fundamental was not removed")
        assertTrue(energyAt(voice, 150.0) < 0.02, "the third harmonic was not removed")
        assertTrue(
            energyAt(voice, 500.0) > before500 * 0.85,
            "the voice was attenuated along with the hum",
        )
    }

    @Test
    fun `detection tells 50 Hz from 60 Hz`() {
        val with50 = withHum(50.0)
        val with60 = withHum(60.0)
        assertEquals(50.0, HumRemover.detectFundamental(with50))
        assertEquals(60.0, HumRemover.detectFundamental(with60))
    }

    @Test
    fun `detection declines to guess when there is no hum`() {
        // Notching a frequency the recording needs is worse than leaving hum removal off.
        val clean = TestSignals.sine(500.0, 2.0, sampleRate, amplitude = 0.4)
        assertNull(HumRemover.detectFundamental(clean))
    }

    private fun withHum(frequency: Double): AudioBuffer {
        val voice = TestSignals.sine(500.0, 2.0, sampleRate, amplitude = 0.3)
        val hum = TestSignals.sine(frequency, 2.0, sampleRate, amplitude = 0.2)
        for (i in 0 until voice.frameCount) voice[0][i] += hum[0][i]
        return voice
    }

    private fun energyAt(buffer: AudioBuffer, frequency: Double): Double {
        val filtered = buffer.copy()
        ai.sajjil.audio.dsp.Biquad(
            ai.sajjil.audio.dsp.BiquadDesign.bandPass(frequency, sampleRate, q = 8.0)
        ).process(filtered[0])
        return filtered.slice(sampleRate / 2, filtered.frameCount).rms()
    }
}

class DeClickerTest {

    @Test
    fun `clicks are found and repaired`() {
        val sampleRate = 48000
        val signal = TestSignals.sine(300.0, 1.0, sampleRate, amplitude = 0.4)
        val clean = signal.copy()

        // Inject impulsive clicks.
        val positions = listOf(5000, 12000, 30000)
        for (position in positions) {
            signal[0][position] = 0.95f
            signal[0][position + 1] = -0.9f
        }

        val repaired = DeClicker().process(signal)
        assertTrue(repaired > 0, "no clicks were detected")

        for (position in positions) {
            val error = abs(signal[0][position] - clean[0][position])
            assertTrue(error < 0.2f, "the click at $position was not repaired (error $error)")
        }
    }

    @Test
    fun `clean audio is left alone`() {
        val signal = TestSignals.sine(300.0, 1.0, 48000, amplitude = 0.4)
        val original = signal.copy()
        DeClicker().process(signal)
        assertTrue(
            TestSignals.maxAbsoluteDifference(original, signal) < 0.02,
            "the de-clicker damaged clean audio",
        )
    }
}

class DeClipperTest {

    @Test
    fun `flat tops are detected and reconstructed`() {
        val sampleRate = 48000
        val signal = TestSignals.sine(200.0, 0.5, sampleRate, amplitude = 1.4)
        // Simulate clipping by hard-limiting into the buffer.
        for (i in 0 until signal.frameCount) {
            signal[0][i] = signal[0][i].coerceIn(-1f, 1f)
        }

        val flatBefore = countFlatSamples(signal)
        assertTrue(flatBefore > 0, "the test signal should be clipped to begin with")

        val repaired = DeClipper().process(signal)
        assertTrue(repaired > 0, "no clipping was detected")
        assertTrue(
            countFlatSamples(signal) < flatBefore / 4,
            "the flat tops are still there after repair",
        )
    }

    @Test
    fun `unclipped audio is untouched`() {
        val signal = TestSignals.sine(200.0, 0.5, 48000, amplitude = 0.5)
        val original = signal.copy()
        assertEquals(0, DeClipper().process(signal))
        assertEquals(0.0, TestSignals.maxAbsoluteDifference(original, signal))
    }

    private fun countFlatSamples(buffer: AudioBuffer): Int {
        var count = 0
        for (i in 1 until buffer.frameCount) {
            if (abs(buffer[0][i]) > 0.98f && buffer[0][i] == buffer[0][i - 1]) count++
        }
        return count
    }
}

class ReverbTest {

    private val sampleRate = 48000

    @Test
    fun `an impulse produces a decaying tail`() {
        val frames = sampleRate * 3
        val data = FloatArray(frames)
        data[100] = 1f
        val signal = AudioBuffer(sampleRate, arrayOf(data))

        Reverb(sampleRate, ReverbSettings(amount = 1.0, decaySeconds = 1.5, size = 0.6))
            .process(signal)

        val early = signal.slice(sampleRate / 10, sampleRate / 2).rms()
        val late = signal.slice(sampleRate * 2, frames).rms()

        assertTrue(early > 1e-5, "the reverb produced no tail at all")
        assertTrue(late < early * 0.5, "the tail did not decay: $early -> $late")
    }

    @Test
    fun `a longer decay setting produces a longer tail`() {
        val short = impulseTailEnergy(ReverbSettings(amount = 1.0, decaySeconds = 0.4))
        val long = impulseTailEnergy(ReverbSettings(amount = 1.0, decaySeconds = 3.0))
        assertTrue(long > short * 2, "decay time had little effect: $short vs $long")
    }

    @Test
    fun `zero amount is an exact bypass`() {
        val signal = TestSignals.sine(440.0, 0.5, sampleRate)
        val original = signal.copy()
        Reverb(sampleRate, ReverbSettings(amount = 0.0)).process(signal)
        assertEquals(0.0, TestSignals.maxAbsoluteDifference(original, signal))
    }

    @Test
    fun `the tail stays bounded rather than running away`() {
        // A feedback network with too much gain oscillates. Sustained input is the worst case.
        val signal = TestSignals.sine(440.0, 8.0, sampleRate, amplitude = 0.5)
        Reverb(sampleRate, ReverbSettings(amount = 0.9, decaySeconds = 6.0, size = 1.0))
            .process(signal)
        assertTrue(signal.peak().isFinite(), "the reverb produced non-finite samples")
        assertTrue(signal.peak() < 4f, "the reverb ran away to ${signal.peak()}")
    }

    @Test
    fun `every ambience profile is stable`() {
        for (profile in AmbienceProfiles.ALL) {
            val signal = TestSignals.sine(440.0, 2.0, sampleRate, amplitude = 0.5)
            Reverb(sampleRate, profile.reverb).process(signal)
            assertTrue(signal.peak().isFinite(), "${profile.name} produced non-finite samples")
            assertTrue(signal.peak() < 3f, "${profile.name} ran away to ${signal.peak()}")
        }
    }

    private fun impulseTailEnergy(settings: ReverbSettings): Double {
        val frames = sampleRate * 4
        val data = FloatArray(frames)
        data[100] = 1f
        val signal = AudioBuffer(sampleRate, arrayOf(data))
        Reverb(sampleRate, settings).process(signal)
        return signal.slice(sampleRate, frames).rms()
    }
}

class EnhancementChainTest {

    private val sampleRate = 48000

    /**
     * A noisy, quiet, hum-contaminated recording with pauses in it — the state most real
     * recordings arrive in, and the shape every stage of the chain is designed around.
     */
    private fun problematicRecording(): AudioBuffer {
        val voice = TestSignals.burstsAndSilence(
            burstSeconds = 0.7, silenceSeconds = 0.5, repeats = 5,
            sampleRate = sampleRate, amplitude = 0.08,
        )
        val noise = TestSignals.noise(voice.durationSeconds, sampleRate, amplitude = 0.006)
        val hum = TestSignals.sine(50.0, voice.durationSeconds, sampleRate, amplitude = 0.01)
        for (i in 0 until voice.frameCount) {
            voice[0][i] += noise[0][i] + hum[0][i]
        }
        return voice
    }

    @Test
    fun `every studio preset produces valid audio and hits its loudness target`() {
        for (preset in StudioPresets.ALL) {
            val (result, report) = EnhancementChain(sampleRate)
                .apply(problematicRecording(), preset.settings)

            assertTrue(result.peak().isFinite(), "${preset.name} produced non-finite samples")
            assertTrue(result.peak() <= 1.0f, "${preset.name} exceeded full scale at ${result.peak()}")
            assertEquals(
                problematicRecording().frameCount, result.frameCount,
                "${preset.name} changed the recording's length",
            )

            val target = preset.settings.targetLoudnessLufs
            if (target != null) {
                val measured = report.loudnessAfterLufs
                assertNotNull(measured, "${preset.name} reported no loudness")
                // Either the target was met, or the chain said plainly that it could not be.
                assertTrue(
                    abs(measured - target) < 2.0 || report.loudnessTargetOutOfReach,
                    "${preset.name} targeted $target LUFS, reached $measured, " +
                        "and did not report the target as out of reach",
                )
            }
        }
    }

    @Test
    fun `enhancement improves the signal to noise ratio`() {
        val original = problematicRecording()
        val before = QualityAnalyzer(sampleRate).analyse(original).signalToNoiseDb

        val (enhanced, _) = EnhancementChain(sampleRate)
            .apply(original, StudioPresets.STUDIO_VOICE.settings)
        val after = QualityAnalyzer(sampleRate).analyse(enhanced).signalToNoiseDb

        assertTrue(after > before, "enhancement made the signal-to-noise ratio worse: $before -> $after")
    }

    @Test
    fun `the source buffer is never modified`() {
        // The Studio previews presets live; mutating the source would corrupt the recording.
        val original = problematicRecording()
        val snapshot = original.copy()
        EnhancementChain(sampleRate).apply(original, StudioPresets.PODCAST.settings)
        assertEquals(
            0.0,
            TestSignals.maxAbsoluteDifference(snapshot, original),
            "the chain modified its input",
        )
    }

    @Test
    fun `an empty settings object leaves the audio alone`() {
        val original = problematicRecording()
        val (result, _) = EnhancementChain(sampleRate).apply(original, EnhancementSettings.NONE)
        assertEquals(0.0, TestSignals.maxAbsoluteDifference(original, result))
    }

    @Test
    fun `progress runs from zero to one without going backwards`() {
        val seen = ArrayList<Double>()
        EnhancementChain(sampleRate)
            .apply(problematicRecording(), StudioPresets.STUDIO_VOICE.settings) { seen += it }

        assertTrue(seen.isNotEmpty())
        assertEquals(1.0, seen.last())
        assertTrue(seen.zipWithNext().all { (a, b) -> b >= a - 1e-9 }, "progress went backwards")
        assertTrue(seen.all { it in 0.0..1.0 }, "progress left the 0..1 range")
    }

    @Test
    fun `every voice style layered on every preset stays valid`() {
        // 35 combinations, and the UI lets the user reach all of them.
        for (preset in StudioPresets.ALL) {
            for (style in VoiceStyles.ALL) {
                val settings = VoiceStyles.apply(preset.settings, style)
                val (result, _) = EnhancementChain(sampleRate).apply(problematicRecording(), settings)
                assertTrue(
                    result.peak().isFinite() && result.peak() <= 1.0f,
                    "${preset.name} + ${style.name} produced ${result.peak()}",
                )
            }
        }
    }

    @Test
    fun `the limiter guarantees the ceiling even with no loudness target`() {
        val hot = TestSignals.sine(440.0, 2.0, sampleRate, amplitude = 0.99)
        val (result, report) = EnhancementChain(sampleRate).apply(
            hot,
            EnhancementSettings(limiter = ai.sajjil.audio.dsp.LimiterSettings(ceilingDb = -3.0)),
        )
        assertTrue(report.limiterEngaged)
        assertTrue(
            linearToDb(result.peak().toDouble()) <= -3.0 + 0.05,
            "the ceiling was not honoured: ${linearToDb(result.peak().toDouble())} dB",
        )
    }

    @Test
    fun `stereo recordings stay stereo`() {
        val stereo = TestSignals.sine(300.0, 4.0, sampleRate, amplitude = 0.2, channels = 2)
        val (result, _) = EnhancementChain(sampleRate).apply(stereo, StudioPresets.PODCAST.settings)
        assertEquals(2, result.channelCount)
    }
}

class QualityAnalyzerTest {

    private val sampleRate = 48000

    /** Speech-shaped material: bursts with pauses, over a noise floor of the given amplitude. */
    private fun recording(speechAmplitude: Double, noiseAmplitude: Double): AudioBuffer {
        val signal = TestSignals.burstsAndSilence(
            burstSeconds = 0.8, silenceSeconds = 0.5, repeats = 6,
            sampleRate = sampleRate, amplitude = speechAmplitude,
        )
        if (noiseAmplitude > 0) {
            val noise = TestSignals.noise(signal.durationSeconds, sampleRate, amplitude = noiseAmplitude)
            for (i in 0 until signal.frameCount) signal[0][i] += noise[0][i]
        }
        return signal
    }

    @Test
    fun `a clean well-levelled recording scores highly`() {
        val clean = recording(speechAmplitude = 0.3, noiseAmplitude = 0.0005)
        val report = QualityAnalyzer(sampleRate).analyse(clean)
        assertTrue(report.score >= 70, "a clean recording scored only ${report.score}: ${report.findings.map { it.message }}")
    }

    @Test
    fun `continuous material is not mistaken for a wall of noise`() {
        // A sustained tone has no pauses, so its noise floor is unmeasurable. Reporting that is
        // right; scoring it as the noisiest possible recording is not.
        val sustained = TestSignals.sineAtDbfs(440.0, -18.0, 8.0, sampleRate)
        val report = QualityAnalyzer(sampleRate).analyse(sustained)
        assertTrue(report.score >= 70, "continuous audio scored ${report.score}")
        assertTrue(
            report.findings.any { it.message.contains("no pauses", ignoreCase = true) },
            "the report should say why noise could not be measured",
        )
    }

    @Test
    fun `a noisy recording scores lower and says why`() {
        val noisy = recording(speechAmplitude = 0.1, noiseAmplitude = 0.03)
        val report = QualityAnalyzer(sampleRate).analyse(noisy)

        assertTrue(report.score < 80, "a noisy recording scored ${report.score}")
        assertTrue(
            report.findings.any { it.message.contains("noise", ignoreCase = true) },
            "the report did not mention noise: ${report.findings.map { it.message }}",
        )
        assertTrue(
            report.findings.any { it.suggestedPresetId != null },
            "a problem was found but no preset was suggested to fix it",
        )
    }

    @Test
    fun `clipping is detected and flagged as a problem`() {
        val clipped = TestSignals.sine(440.0, 4.0, sampleRate, amplitude = 1.6)
        for (i in 0 until clipped.frameCount) clipped[0][i] = clipped[0][i].coerceIn(-1f, 1f)

        val report = QualityAnalyzer(sampleRate).analyse(clipped)
        assertTrue(report.clippedSampleCount > 0, "clipping was not detected")
        assertTrue(
            report.findings.any { it.severity == QualityFinding.Severity.PROBLEM },
            "clipping should be reported as a problem",
        )
    }

    @Test
    fun `a very quiet recording is flagged`() {
        val quiet = recording(speechAmplitude = 0.004, noiseAmplitude = 0.00005)
        val report = QualityAnalyzer(sampleRate).analyse(quiet)
        assertTrue(
            report.findings.any { it.message.contains("quiet", ignoreCase = true) },
            "a -45 dBFS recording should be called quiet",
        )
    }

    @Test
    fun `an empty recording reports a problem instead of crashing`() {
        val empty = AudioBuffer.silence(sampleRate, 1, 0)
        val report = QualityAnalyzer(sampleRate).analyse(empty)
        assertEquals(0, report.score)
        assertTrue(report.findings.isNotEmpty())
    }

    @Test
    fun `the score always lands in range and carries a grade`() {
        val cases = listOf(
            TestSignals.sineAtDbfs(440.0, -18.0, 6.0, sampleRate),
            TestSignals.noise(6.0, sampleRate, amplitude = 0.5),
            AudioBuffer.silence(sampleRate, 1, sampleRate * 3),
            TestSignals.sineAtDbfs(440.0, -60.0, 6.0, sampleRate),
        )
        for (case in cases) {
            val report = QualityAnalyzer(sampleRate).analyse(case)
            assertTrue(report.score in 0..100, "score ${report.score} is out of range")
            assertTrue(report.grade.isNotEmpty())
        }
    }

    @Test
    fun `enhancement raises the score of a poor recording`() {
        val poor = recording(speechAmplitude = 0.06, noiseAmplitude = 0.02)
        val before = QualityAnalyzer(sampleRate).analyse(poor).score
        val (enhanced, _) = EnhancementChain(sampleRate)
            .apply(poor, StudioPresets.STUDIO_VOICE.settings)
        val after = QualityAnalyzer(sampleRate).analyse(enhanced).score

        assertTrue(after > before, "enhancement lowered the score from $before to $after")
    }
}

class WaveformPeaksTest {

    private val sampleRate = 48000

    @Test
    fun `peaks span the requested number of buckets`() {
        val signal = TestSignals.sine(440.0, 10.0, sampleRate)
        val peaks = WaveformPeaks.extract(signal, targetBuckets = 500)
        assertTrue(
            abs(peaks.bucketCount - 500) <= 1,
            "asked for 500 buckets, got ${peaks.bucketCount}",
        )
    }

    @Test
    fun `peaks bracket the signal and RMS sits inside them`() {
        val signal = TestSignals.sine(440.0, 2.0, sampleRate, amplitude = 0.7)
        val peaks = WaveformPeaks.extract(signal, 200)
        for (i in 0 until peaks.bucketCount) {
            assertTrue(peaks.maxima[i] >= peaks.minima[i], "bucket $i is inverted")
            assertTrue(
                peaks.rms[i] <= peaks.maxima[i] + 1e-6,
                "bucket $i has RMS above its peak, which cannot happen",
            )
        }
        assertTrue(peaks.maxima.max() > 0.65f && peaks.minima.min() < -0.65f)
    }

    @Test
    fun `extracting a range only reads that range`() {
        // Silence at the front, tone at the back: a range over the front must read as silent.
        val silence = AudioBuffer.silence(sampleRate, 1, sampleRate)
        val tone = TestSignals.sine(440.0, 1.0, sampleRate, amplitude = 0.8)
        val signal = AudioBuffer.concat(listOf(silence, tone))

        val front = WaveformPeaks.extractRange(signal, 0, sampleRate, 100)
        assertEquals(0f, front.maxima.max(), "the silent range should be flat")

        val back = WaveformPeaks.extractRange(signal, sampleRate, signal.frameCount, 100)
        assertTrue(back.maxima.max() > 0.7f, "the tone range should show the tone")
    }

    @Test
    fun `an empty range yields no buckets rather than failing`() {
        val signal = TestSignals.sine(440.0, 1.0, sampleRate)
        val peaks = WaveformPeaks.extractRange(signal, 1000, 1000, 100)
        assertEquals(0, peaks.bucketCount)
    }
}

class LiveWaveformTest {

    @Test
    fun `values arrive oldest to newest and are right aligned`() {
        val live = LiveWaveform(capacity = 8)
        live.push(0.1f)
        live.push(0.2f)
        live.push(0.3f)

        val snapshot = live.snapshot()
        assertEquals(8, snapshot.size)
        // The leading gap is zero, so a new recording grows in from the right.
        assertEquals(0f, snapshot[0])
        assertEquals(0.1f, snapshot[5])
        assertEquals(0.2f, snapshot[6])
        assertEquals(0.3f, snapshot[7])
    }

    @Test
    fun `the oldest values fall off once it is full`() {
        val live = LiveWaveform(capacity = 4)
        for (i in 1..6) live.push(i / 10f)
        val snapshot = live.snapshot()
        assertEquals(floatArrayOf(0.3f, 0.4f, 0.5f, 0.6f).toList(), snapshot.toList())
    }

    @Test
    fun `levels are clamped into range`() {
        val live = LiveWaveform(capacity = 2)
        live.push(5f)
        live.push(-3f)
        assertEquals(listOf(1f, 0f), live.snapshot().toList())
    }

    @Test
    fun `clearing resets to silence`() {
        val live = LiveWaveform(capacity = 4)
        for (i in 1..4) live.push(0.5f)
        live.clear()
        assertTrue(live.snapshot().all { it == 0f })
    }
}

class LoudnessRegressionTest {

    @Test
    fun `presets do not leave recordings above the delivery ceiling`() {
        // A guard against a preset being edited later in a way that ships clipped exports.
        val sampleRate = 48000
        for (preset in StudioPresets.ALL) {
            val loud = TestSignals.sine(440.0, 5.0, sampleRate, amplitude = 0.95)
            val (result, _) = EnhancementChain(sampleRate).apply(loud, preset.settings)
            val ceiling = preset.settings.limiter?.ceilingDb ?: 0.0
            val peak = linearToDb(result.peak().toDouble())
            assertTrue(
                peak <= ceiling + 0.1,
                "${preset.name} left peaks at $peak dB against a $ceiling dB ceiling",
            )
        }
    }

    @Test
    fun `measurement is stable when a recording is processed twice`() {
        // Enhancing an already-enhanced recording should not drift the level much; users do this
        // by accident all the time.
        val sampleRate = 48000
        val chain = EnhancementChain(sampleRate)
        val original = TestSignals.burstsAndSilence(
            burstSeconds = 0.7, silenceSeconds = 0.5, repeats = 6,
            sampleRate = sampleRate, amplitude = 0.2,
        ).also { signal ->
            val noise = TestSignals.noise(signal.durationSeconds, sampleRate, amplitude = 0.01)
            for (i in 0 until signal.frameCount) signal[0][i] += noise[0][i]
        }

        val (once, _) = chain.apply(original, StudioPresets.PODCAST.settings)
        val (twice, _) = chain.apply(once, StudioPresets.PODCAST.settings)

        val meter = LoudnessMeter(sampleRate)
        val first = meter.measureIntegrated(once)!!
        val second = meter.measureIntegrated(twice)!!
        assertTrue(abs(first - second) < 1.5, "loudness drifted from $first to $second")
    }
}
