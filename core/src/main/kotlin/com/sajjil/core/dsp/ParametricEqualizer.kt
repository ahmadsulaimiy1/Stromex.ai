package com.sajjil.core.dsp

/** ISO 1/3-octave center frequencies, 20 Hz - 20 kHz (31 bands). */
val GRAPHIC_EQ_31_BAND_FREQUENCIES: DoubleArray = doubleArrayOf(
    20.0, 25.0, 31.5, 40.0, 50.0, 63.0, 80.0, 100.0, 125.0, 160.0,
    200.0, 250.0, 315.0, 400.0, 500.0, 630.0, 800.0, 1000.0, 1250.0, 1600.0,
    2000.0, 2500.0, 3150.0, 4000.0, 5000.0, 6300.0, 8000.0, 10000.0, 12500.0, 16000.0, 20000.0,
)

/**
 * A cascade of biquad stages forming a parametric/graphic equalizer.
 * Each stage is a peaking or shelving filter; gains are in dB.
 */
class ParametricEqualizer(private val stages: List<BiquadFilter>) {

    fun reset() = stages.forEach { it.reset() }

    fun process(sample: Float): Float {
        var s = sample
        for (stage in stages) s = stage.process(s)
        return s
    }

    fun processBlock(samples: FloatArray) {
        for (i in samples.indices) samples[i] = process(samples[i])
    }

    companion object {
        /**
         * RBJ cookbook biquad formulas assume a center frequency well below
         * Nyquist; pushed close to or past it, the resulting pole can land
         * outside the unit circle and the filter blows up to NaN within a
         * few hundred samples. Every factory below clamps against this
         * before building a stage, so a fixed-frequency band (e.g. a
         * 9kHz treble shelf) stays stable even at a low capture sample
         * rate (e.g. 16kHz, where 9kHz would otherwise exceed Nyquist).
         */
        private fun safeFreq(freqHz: Double, sampleRate: Int): Double = freqHz.coerceAtMost(sampleRate * 0.45)

        /** Simple 4-band tone control: bass/mid/treble shelves + presence bell. */
        fun basic(
            sampleRate: Int,
            bassDb: Double = 0.0,
            midDb: Double = 0.0,
            trebleDb: Double = 0.0,
            presenceDb: Double = 0.0,
        ): ParametricEqualizer = ParametricEqualizer(
            listOf(
                BiquadFilter.lowShelf(safeFreq(120.0, sampleRate), sampleRate.toDouble(), bassDb),
                BiquadFilter.peaking(safeFreq(1000.0, sampleRate), sampleRate.toDouble(), 0.9, midDb),
                BiquadFilter.peaking(safeFreq(6500.0, sampleRate), sampleRate.toDouble(), 1.1, presenceDb),
                BiquadFilter.highShelf(safeFreq(9000.0, sampleRate), sampleRate.toDouble(), trebleDb),
            )
        )

        /** Full 31-band ISO graphic EQ. gainsDb.size must equal 31. */
        fun graphic31Band(sampleRate: Int, gainsDb: DoubleArray): ParametricEqualizer {
            require(gainsDb.size == GRAPHIC_EQ_31_BAND_FREQUENCIES.size) {
                "Expected ${GRAPHIC_EQ_31_BAND_FREQUENCIES.size} gain values, got ${gainsDb.size}"
            }
            val nyquist = sampleRate / 2.0
            val stages = GRAPHIC_EQ_31_BAND_FREQUENCIES.indices
                .filter { GRAPHIC_EQ_31_BAND_FREQUENCIES[it] < nyquist * 0.98 }
                .map { i -> BiquadFilter.peaking(GRAPHIC_EQ_31_BAND_FREQUENCIES[i], sampleRate.toDouble(), 4.32, gainsDb[i]) }
            return ParametricEqualizer(stages)
        }

        /** Arbitrary parametric band list: (freqHz, Q, gainDb) triples. */
        fun parametric(sampleRate: Int, bands: List<Triple<Double, Double, Double>>): ParametricEqualizer =
            ParametricEqualizer(bands.map { (freq, q, gain) -> BiquadFilter.peaking(safeFreq(freq, sampleRate), sampleRate.toDouble(), q, gain) })
    }
}
