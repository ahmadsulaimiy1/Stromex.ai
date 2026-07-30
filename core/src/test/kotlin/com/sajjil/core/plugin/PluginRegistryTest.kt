package com.sajjil.core.plugin

import kotlin.test.AfterTest
import kotlin.test.BeforeTest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class PluginRegistryTest {

    @BeforeTest
    fun setUp() {
        BuiltinPlugins.registerAll()
    }

    @AfterTest
    fun tearDown() {
        PluginRegistry.all().forEach { PluginRegistry.unregister(it.id) }
    }

    @Test
    fun `registers all builtin plugins with unique ids`() {
        val ids = PluginRegistry.all().map { it.id }
        assertEquals(ids.toSet().size, ids.size, "plugin ids must be unique")
        assertTrue(PluginRegistry.get("sajjil.builtin.compressor") != null)
    }

    @Test
    fun `plugins are filterable by category`() {
        val mastering = PluginRegistry.byCategory(PluginCategory.MASTERING)
        assertTrue(mastering.any { it.id == "sajjil.builtin.compressor" })
        assertTrue(mastering.none { it.id == "sajjil.builtin.noise_gate" })
    }

    @Test
    fun `a plugin's processor actually processes audio`() {
        val plugin = PluginRegistry.get("sajjil.builtin.limiter")!!
        val processor = plugin.createProcessor(48000)
        val loud = FloatArray(2000) { 0.99f }
        processor.processBlock(loud)
        assertTrue(loud.all { kotlin.math.abs(it) <= 1f })
    }

    @Test
    fun `unregister removes a plugin`() {
        PluginRegistry.unregister("sajjil.builtin.de_esser")
        assertTrue(PluginRegistry.get("sajjil.builtin.de_esser") == null)
    }
}
