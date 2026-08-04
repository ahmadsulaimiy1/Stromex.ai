package ai.sajjil.audio.chain

import ai.sajjil.audio.AudioBuffer
import ai.sajjil.audio.dsp.BiquadChain
import ai.sajjil.audio.dsp.BiquadCoefficients
import ai.sajjil.audio.dsp.BiquadDesign
import ai.sajjil.audio.dsp.Compressor
import ai.sajjil.audio.dsp.DeClicker
import ai.sajjil.audio.dsp.DeClipper
import ai.sajjil.audio.dsp.DeEsser
import ai.sajjil.audio.dsp.HumRemover
import ai.sajjil.audio.dsp.Limiter
import ai.sajjil.audio.dsp.NoiseGate
import ai.sajjil.audio.dsp.Reverb
import ai.sajjil.audio.dsp.SpectralNoiseReducer
import ai.sajjil.audio.dsp.StereoWidener
import ai.sajjil.audio.dsp.WindReducer
import ai.sajjil.audio.loudness.LoudnessNormalizer

/** What the chain did, so the UI can say something specific instead of "Done". */
data class EnhancementReport(
    val clicksRepaired: Int = 0,
    val clippedSamplesRepaired: Int = 0,
    val humFundamentalHz: Double? = null,
    val loudnessBeforeLufs: Double? = null,
    val loudnessAfterLufs: Double? = null,
    val appliedGainDb: Double = 0.0,
    val limiterEngaged: Boolean = false,
    /** True when the recording was too quiet to reach the preset's loudness target. */
    val loudnessTargetOutOfReach: Boolean = false,
)

/**
 * Runs the enhancement graph over a whole recording.
 *
 * Stage order is not arbitrary and is the main thing that separates this from a pile of effects:
 *
 *  1. **Repair first** — clicks and clipping are errors in the samples themselves. Every later
 *     stage would otherwise treat them as signal; a compressor in particular will duck the whole
 *     voice around a click it should never have seen.
 *  2. **Then subtract what should not be there** — hum, wind, broadband noise, and the gate.
 *     These all estimate a noise floor, which only means something once the repairs are done.
 *  3. **Then shape** — high-pass, EQ, de-esser. Shaping before noise reduction would change the
 *     spectrum the noise estimator is measuring.
 *  4. **Then control dynamics** — the compressor, operating on a signal that is already clean.
 *  5. **Then add space** — reverb goes after compression, never before, or the compressor pumps
 *     on the tail rather than on the voice.
 *  6. **Loudness and the limiter last** — the final level has to be measured on the finished
 *     signal, and nothing may follow the limiter or its ceiling is not a ceiling.
 */
class EnhancementChain(private val sampleRate: Int) {

    /**
     * Applies [settings] to a copy of [buffer].
     *
     * @param onProgress 0..1, called between stages so a long enhancement can show real progress.
     */
    fun apply(
        buffer: AudioBuffer,
        settings: EnhancementSettings,
        onProgress: ((Double) -> Unit)? = null,
    ): Pair<AudioBuffer, EnhancementReport> {
        var working = buffer.copy()
        var report = EnhancementReport()
        val stages = countStages(settings)
        var completed = 0
        val step = {
            completed++
            onProgress?.invoke(completed.toDouble() / stages.coerceAtLeast(1))
            Unit
        }

        // 1. Repair
        if (settings.repairClipping) {
            report = report.copy(clippedSamplesRepaired = DeClipper().process(working))
            step()
        }
        if (settings.repairClicks) {
            report = report.copy(clicksRepaired = DeClicker().process(working))
            step()
        }

        // 2. Subtract
        if (settings.removeHum) {
            val fundamental = settings.humFundamentalHz ?: HumRemover.detectFundamental(working)
            if (fundamental != null) {
                HumRemover(sampleRate, fundamentalHz = fundamental).process(working)
                report = report.copy(humFundamentalHz = fundamental)
            }
            step()
        }
        if (settings.windReduction > 0.0) {
            WindReducer(sampleRate, settings.windReduction).process(working)
            step()
        }
        settings.noiseReduction?.let {
            working = SpectralNoiseReducer(it).process(working)
            step()
        }
        settings.gate?.let {
            NoiseGate(sampleRate, it).process(working)
            step()
        }

        // 3. Shape
        val filters = buildFilterChain(settings)
        if (filters.isNotEmpty()) {
            for (channel in working.channels) BiquadChain(filters).process(channel)
            step()
        }
        settings.deEsser?.let {
            DeEsser(sampleRate, it).process(working)
            step()
        }

        // 4. Dynamics
        settings.compressor?.let {
            Compressor(sampleRate, it).process(working)
            step()
        }

        // 5. Space
        settings.reverb?.let {
            if (it.amount > 0.0) Reverb(sampleRate, it).process(working)
            step()
        }
        if (settings.stereoWidth != 1.0) {
            StereoWidener.process(working, settings.stereoWidth)
            step()
        }

        // 6. Level
        settings.targetLoudnessLufs?.let { target ->
            val ceiling = settings.limiter?.ceilingDb ?: -1.0
            val result = LoudnessNormalizer(sampleRate).normalize(working, target, ceiling)
            report = report.copy(
                loudnessBeforeLufs = result.measuredBeforeLufs,
                loudnessAfterLufs = result.measuredAfterLufs,
                appliedGainDb = result.appliedGainDb,
                limiterEngaged = result.limiterEngaged,
                loudnessTargetOutOfReach = result.gainLimited,
            )
            step()
        }
        // A limiter with no loudness target still guarantees the ceiling on export.
        if (settings.targetLoudnessLufs == null) {
            settings.limiter?.let {
                Limiter(sampleRate, it).process(working)
                report = report.copy(limiterEngaged = true)
                step()
            }
        }

        onProgress?.invoke(1.0)
        return working to report
    }

    private fun buildFilterChain(settings: EnhancementSettings): List<BiquadCoefficients> {
        val sections = ArrayList<BiquadCoefficients>()
        settings.highPassHz?.let {
            sections += BiquadDesign.highPass(it, sampleRate, q = 0.7071)
        }
        for (band in settings.equaliser) {
            sections += when (band.type) {
                EqBandType.PEAKING -> BiquadDesign.peaking(band.frequencyHz, sampleRate, band.gainDb, band.q)
                EqBandType.LOW_SHELF -> BiquadDesign.lowShelf(band.frequencyHz, sampleRate, band.gainDb)
                EqBandType.HIGH_SHELF -> BiquadDesign.highShelf(band.frequencyHz, sampleRate, band.gainDb)
                EqBandType.HIGH_PASS -> BiquadDesign.highPass(band.frequencyHz, sampleRate, band.q)
                EqBandType.LOW_PASS -> BiquadDesign.lowPass(band.frequencyHz, sampleRate, band.q)
            }
        }
        return sections
    }

    private fun countStages(settings: EnhancementSettings): Int {
        var n = 0
        if (settings.repairClipping) n++
        if (settings.repairClicks) n++
        if (settings.removeHum) n++
        if (settings.windReduction > 0.0) n++
        if (settings.noiseReduction != null) n++
        if (settings.gate != null) n++
        if (settings.highPassHz != null || settings.equaliser.isNotEmpty()) n++
        if (settings.deEsser != null) n++
        if (settings.compressor != null) n++
        if (settings.reverb != null) n++
        if (settings.stereoWidth != 1.0) n++
        if (settings.targetLoudnessLufs != null || settings.limiter != null) n++
        return n
    }
}
