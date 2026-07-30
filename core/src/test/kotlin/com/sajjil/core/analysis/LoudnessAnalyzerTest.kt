package com.sajjil.core.analysis

import kotlin.math.PI
import kotlin.math.sin
import kotlin.test.Test
import kotlin.test.assertTrue

class LoudnessAnalyzerTest {
    private val sampleRate = 48000

    @Test
    fun `quieter signal yields lower peak and rms than louder signal`() {
        val loud = FloatArray(sampleRate) { (0.9 * sin(2.0 * PI * 440 * it / sampleRate)).toFloat() }
        val quiet = FloatArray(sampleRate) { (0.05 * sin(2.0 * PI * 440 * it / sampleRate)).toFloat() }

        val loudMetrics = LoudnessAnalyzer.analyze(loud, sampleRate)
        val quietMetrics = LoudnessAnalyzer.analyze(quiet, sampleRate)

        assertTrue(loudMetrics.peakDb > quietMetrics.peakDb)
        assertTrue(loudMetrics.rmsDb > quietMetrics.rmsDb)
        assertTrue(loudMetrics.integratedLoudnessLufs > quietMetrics.integratedLoudnessLufs)
    }

    @Test
    fun `constant tone has near-zero dynamic range`() {
        val tone = FloatArray(sampleRate * 2) { (0.5 * sin(2.0 * PI * 440 * it / sampleRate)).toFloat() }
        val metrics = LoudnessAnalyzer.analyze(tone, sampleRate)
        assertTrue(metrics.dynamicRangeDb < 2.0, "expected low dynamic range for constant tone, got ${metrics.dynamicRangeDb}")
    }

    @Test
    fun `scorer produces values within 0 to 100`() {
        val tone = FloatArray(sampleRate) { (0.3 * sin(2.0 * PI * 440 * it / sampleRate)).toFloat() }
        val metrics = LoudnessAnalyzer.analyze(tone, sampleRate)
        val report = AudioQualityScorer.score(metrics)
        for (score in listOf(
            report.clarityScore, report.noiseScore, report.loudnessScore, report.dynamicsScore,
            report.studioReadinessScore, report.broadcastReadinessScore, report.archiveReadinessScore,
        )) {
            assertTrue(score in 0..100, "score out of range: $score")
        }
    }

    @Test
    fun `echoScore is null without an RT60 measurement and present with one`() {
        val tone = FloatArray(sampleRate) { (0.3 * sin(2.0 * PI * 440 * it / sampleRate)).toFloat() }
        val metrics = LoudnessAnalyzer.analyze(tone, sampleRate)

        val withoutRt60 = AudioQualityScorer.score(metrics)
        assertTrue(withoutRt60.echoScore == null)

        val dryReport = AudioQualityScorer.score(metrics, rt60Seconds = 0.2)
        val reverberantReport = AudioQualityScorer.score(metrics, rt60Seconds = 1.5)
        assertTrue(dryReport.echoScore != null && reverberantReport.echoScore != null)
        assertTrue(dryReport.echoScore!! > reverberantReport.echoScore!!, "a drier room should score higher than a reverberant one")
    }
}
