package com.sajjil.core.plugin

import com.sajjil.core.dsp.Compressor
import com.sajjil.core.dsp.DeEsser
import com.sajjil.core.dsp.Limiter
import com.sajjil.core.dsp.NoiseGate
import com.sajjil.core.dsp.ParametricEqualizer

/**
 * Wraps SAJJIL's own DSP units as plugins under the [AudioEffectPlugin]
 * contract — proof that the architecture is load-bearing today, not just a
 * paper design. [registerAll] is called once at app startup.
 */
object BuiltinPlugins {

    val noiseGate = object : AudioEffectPlugin {
        override val id = "sajjil.builtin.noise_gate"
        override val displayName = "Noise Gate"
        override val description = "Tajweed-safe envelope gate with hold/hysteresis."
        override val category = PluginCategory.ENHANCEMENT
        override fun createProcessor(sampleRate: Int): AudioEffectProcessor {
            val gate = NoiseGate(sampleRate)
            return object : AudioEffectProcessor {
                override fun process(sample: Float) = gate.process(sample)
                override fun reset() = gate.reset()
            }
        }
    }

    val compressor = object : AudioEffectPlugin {
        override val id = "sajjil.builtin.compressor"
        override val displayName = "Vocal Compressor"
        override val description = "RMS feed-forward compressor with soft knee and auto makeup gain."
        override val category = PluginCategory.MASTERING
        override fun createProcessor(sampleRate: Int): AudioEffectProcessor {
            val compressor = Compressor(sampleRate).apply { makeupGainDb = autoMakeupGain() }
            return object : AudioEffectProcessor {
                override fun process(sample: Float) = compressor.process(sample)
                override fun reset() = compressor.reset()
            }
        }
    }

    val limiter = object : AudioEffectPlugin {
        override val id = "sajjil.builtin.limiter"
        override val displayName = "Loudness Maximizer"
        override val description = "Lookahead brickwall peak limiter for broadcast-safe loudness."
        override val category = PluginCategory.MASTERING
        override fun createProcessor(sampleRate: Int): AudioEffectProcessor {
            val limiter = Limiter(sampleRate)
            return object : AudioEffectProcessor {
                override fun process(sample: Float) = limiter.process(sample)
                override fun reset() = limiter.reset()
            }
        }
    }

    val deEsser = object : AudioEffectPlugin {
        override val id = "sajjil.builtin.de_esser"
        override val displayName = "De-Esser"
        override val description = "Dynamic sibilance control in the 4-9kHz band."
        override val category = PluginCategory.ENHANCEMENT
        override fun createProcessor(sampleRate: Int): AudioEffectProcessor {
            val deEsser = DeEsser(sampleRate)
            return object : AudioEffectProcessor {
                override fun process(sample: Float) = deEsser.process(sample)
                override fun reset() = deEsser.reset()
            }
        }
    }

    val basicEqualizer = object : AudioEffectPlugin {
        override val id = "sajjil.builtin.basic_eq"
        override val displayName = "Basic Equalizer"
        override val description = "4-band bass/mid/presence/treble tone control."
        override val category = PluginCategory.MASTERING
        override fun createProcessor(sampleRate: Int): AudioEffectProcessor {
            val eq = ParametricEqualizer.basic(sampleRate)
            return object : AudioEffectProcessor {
                override fun process(sample: Float) = eq.process(sample)
                override fun reset() = eq.reset()
            }
        }
    }

    fun registerAll() {
        listOf(noiseGate, compressor, limiter, deEsser, basicEqualizer).forEach(PluginRegistry::register)
    }
}
