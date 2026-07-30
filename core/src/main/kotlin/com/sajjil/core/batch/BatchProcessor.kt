package com.sajjil.core.batch

import com.sajjil.core.analysis.AudioAnalysisReport
import com.sajjil.core.analysis.AudioQualityScorer
import com.sajjil.core.analysis.LoudnessAnalyzer
import com.sajjil.core.audio.BitDepth
import com.sajjil.core.audio.WavIO
import com.sajjil.core.dsp.AudioProcessingChain
import com.sajjil.core.dsp.ProcessingChainConfig
import java.io.File

data class BatchJobItem(val label: String, val inputFile: File, val outputFile: File)

data class BatchItemResult(
    val item: BatchJobItem,
    val success: Boolean,
    val report: AudioAnalysisReport? = null,
    val error: String? = null,
)

data class BatchResult(val results: List<BatchItemResult>) {
    val successCount: Int get() = results.count { it.success }
    val failureCount: Int get() = results.size - successCount
}

/**
 * SAJJIL Batch Qur'an Production: applies one mastering chain across many
 * files in a single pass — an entire Surah, a Juz, or a full recitation
 * archive — instead of mastering each recording by hand. Export beyond WAV
 * (AAC/M4A) needs `android.media.MediaCodec`, which lives in the `app`
 * module; this stays a pure-JVM WAV-in/WAV-out pipeline so it's testable
 * here, with the app layer able to re-encode each output afterward.
 */
object BatchProcessor {

    fun run(
        items: List<BatchJobItem>,
        config: ProcessingChainConfig,
        outputBitDepth: BitDepth = BitDepth.PCM_24,
        onItemComplete: (BatchItemResult) -> Unit = {},
    ): BatchResult {
        val results = items.map { item ->
            val result = runCatching {
                val audio = WavIO.read(item.inputFile.readBytes())
                val chain = AudioProcessingChain(audio.sampleRate, config)
                val processed = FloatArray(audio.samples.size)
                for (i in audio.samples.indices) processed[i] = chain.process(audio.samples[i])

                item.outputFile.parentFile?.mkdirs()
                item.outputFile.outputStream().use { out ->
                    WavIO.write(out, processed, audio.sampleRate, audio.channels, outputBitDepth)
                }

                val metrics = LoudnessAnalyzer.analyze(processed, audio.sampleRate)
                AudioQualityScorer.score(metrics)
            }.fold(
                onSuccess = { report -> BatchItemResult(item, success = true, report = report) },
                onFailure = { error -> BatchItemResult(item, success = false, error = error.message ?: error.toString()) },
            )
            onItemComplete(result)
            result
        }
        return BatchResult(results)
    }
}
