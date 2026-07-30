package com.sajjil.core.plugin

enum class PluginCategory { ENHANCEMENT, MASTERING, RESTORATION, STUDIO_PACK, VOICE_PACK }

/** A single, real-time-safe audio effect stage a plugin contributes to a processing chain. */
interface AudioEffectProcessor {
    fun process(sample: Float): Float
    fun processBlock(samples: FloatArray) {
        for (i in samples.indices) samples[i] = process(samples[i])
    }
    fun reset()
}

/**
 * SAJJIL's plugin contract. Deliberately narrow: a plugin describes itself
 * and produces a per-session [AudioEffectProcessor] — it does not reach
 * into UI, storage, or export, which keeps third-party "Enhancement
 * plugins / Mastering plugins / Studio packs / Voice packs" (per the
 * product roadmap) sandboxed to signal processing.
 *
 * This is the architecture requested ahead of a full marketplace: it is
 * live and in use today (see [BuiltinPlugins]) via in-process registration,
 * not dynamic/downloadable loading — that remains a roadmap item, since it
 * needs a sandboxing and signing story before it can accept third-party
 * code safely.
 */
interface AudioEffectPlugin {
    val id: String
    val displayName: String
    val description: String
    val category: PluginCategory
    fun createProcessor(sampleRate: Int): AudioEffectProcessor
}

/** In-process registry of available plugins, built-in today, third-party-loadable in a future phase. */
object PluginRegistry {
    private val plugins = linkedMapOf<String, AudioEffectPlugin>()

    fun register(plugin: AudioEffectPlugin) {
        plugins[plugin.id] = plugin
    }

    fun unregister(id: String) {
        plugins.remove(id)
    }

    fun get(id: String): AudioEffectPlugin? = plugins[id]

    fun all(): List<AudioEffectPlugin> = plugins.values.toList()

    fun byCategory(category: PluginCategory): List<AudioEffectPlugin> = plugins.values.filter { it.category == category }
}
