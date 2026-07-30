package com.sajjil.app.analysis

import com.sajjil.app.data.repository.RecordingRepository
import com.sajjil.core.analysis.AcousticAnalyzer
import com.sajjil.core.analysis.AudioAnalysisReport
import com.sajjil.core.analysis.AudioQualityScorer
import com.sajjil.core.analysis.LoudnessAnalyzer
import com.sajjil.core.audio.WavIO
import java.io.File
import java.io.IOException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.withContext

/**
 * "Background Intelligence": the same RT60 + loudness/quality analysis
 * Dashboard already runs on demand, extracted so every save path
 * (Record, Enhance, Master save-to-library, Voice Studio) can trigger it
 * automatically the moment a take is saved — a recording no longer sits
 * at a permanent null score until someone happens to open its Dashboard.
 * RT60 estimation and loudness analysis are independent, so they run
 * concurrently here too, matching Dashboard's own pattern (Phase 5).
 *
 * Deliberately does not compute the spectrogram — that's a heavier pass
 * only Dashboard's on-demand view actually needs; running it for every
 * background save would cost more than the score it doesn't produce.
 */
object RecordingAutoAnalyzer {

    suspend fun analyze(file: File): AudioAnalysisReport = withContext(Dispatchers.Default) {
        val audio = WavIO.read(file.readBytes())
        coroutineScope {
            val rt60Deferred = async { AcousticAnalyzer.estimateRt60(audio.samples, audio.sampleRate) }
            val metricsDeferred = async { LoudnessAnalyzer.analyze(audio.samples, audio.sampleRate) }
            AudioQualityScorer.score(metricsDeferred.await(), rt60Deferred.await())
        }
    }

    /** Analyzes [file] and writes the resulting readiness scores back onto [recordingId]. Fails silently on I/O error — the recording is still saved, just without a score yet. */
    suspend fun analyzeAndPersist(repository: RecordingRepository, recordingId: Long, file: File) {
        val report = try {
            analyze(file)
        } catch (e: IOException) {
            return
        }
        val recording = repository.getById(recordingId) ?: return
        repository.update(
            recording.copy(
                studioReadinessScore = report.studioReadinessScore,
                broadcastReadinessScore = report.broadcastReadinessScore,
                archiveReadinessScore = report.archiveReadinessScore,
            ),
        )
    }
}
