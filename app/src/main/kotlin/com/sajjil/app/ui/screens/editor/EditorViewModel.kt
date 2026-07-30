package com.sajjil.app.ui.screens.editor

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.sajjil.app.analysis.RecordingAutoAnalyzer
import com.sajjil.app.data.db.RecordingEntity
import com.sajjil.app.di.asSajjilApplication
import com.sajjil.core.analysis.WaveformPeaks
import com.sajjil.core.audio.BitDepth
import com.sajjil.core.audio.WavIO
import com.sajjil.core.dsp.AudioEditor
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File

data class EditorUiState(
    val recording: RecordingEntity? = null,
    val isLoading: Boolean = true,
    val waveformPeaks: FloatArray? = null,
    val selectionStart: Float = 0f,
    val selectionEnd: Float = 1f,
    val fadeInEnabled: Boolean = false,
    val fadeOutEnabled: Boolean = false,
    val isProcessing: Boolean = false,
    val savedToLibrary: Boolean = false,
)

/**
 * Trim ("keep only the selection") and Cut ("remove the selection, keep the rest"), plus
 * optional fade in/out, saved as a new alternate-version take -- the original recording is
 * never modified in place, matching the pattern Enhance/Master already use for "Save to Library".
 *
 * Selection is driven by sliders (see EditorScreen), not a drag gesture directly on the
 * waveform -- the waveform here is a visual reference only.
 */
class EditorViewModel(application: Application) : AndroidViewModel(application) {
    private val app = application.asSajjilApplication()

    private var sourceSamples: FloatArray = FloatArray(0)
    private var sampleRate: Int = 48000
    private var channels: Int = 1

    private val _uiState = MutableStateFlow(EditorUiState())
    val uiState: StateFlow<EditorUiState> = _uiState.asStateFlow()

    fun load(recordingId: Long) {
        viewModelScope.launch {
            val recording = app.recordingRepository.getById(recordingId) ?: return@launch
            _uiState.value = EditorUiState(recording = recording, isLoading = true)
            val (samples, sr, ch, peaks) = withContext(Dispatchers.Default) {
                val decoded = WavIO.read(File(recording.filePath).readBytes())
                val computedPeaks = WaveformPeaks.compute(decoded.samples, WAVEFORM_BUCKET_COUNT)
                DecodedAudio(decoded.samples, decoded.sampleRate, decoded.channels, computedPeaks)
            }
            sourceSamples = samples
            sampleRate = sr
            channels = ch
            _uiState.value = _uiState.value.copy(isLoading = false, waveformPeaks = peaks)
        }
    }

    fun setSelection(start: Float, end: Float) {
        val clampedStart = start.coerceIn(0f, 1f)
        val clampedEnd = end.coerceIn(clampedStart, 1f)
        _uiState.value = _uiState.value.copy(selectionStart = clampedStart, selectionEnd = clampedEnd)
    }

    fun toggleFadeIn() {
        _uiState.value = _uiState.value.copy(fadeInEnabled = !_uiState.value.fadeInEnabled)
    }

    fun toggleFadeOut() {
        _uiState.value = _uiState.value.copy(fadeOutEnabled = !_uiState.value.fadeOutEnabled)
    }

    /** Keeps only the selected region, discards everything outside it. */
    fun applyTrim() = applyEdit { samples, startIndex, endIndex -> AudioEditor.trim(samples, startIndex, endIndex) }

    /** Removes the selected region, keeps everything before and after it. */
    fun applyCut() = applyEdit { samples, startIndex, endIndex -> AudioEditor.deleteRange(samples, startIndex, endIndex) }

    private fun applyEdit(edit: (samples: FloatArray, startIndex: Int, endIndex: Int) -> FloatArray) {
        val source = _uiState.value.recording ?: return
        if (sourceSamples.isEmpty()) return
        _uiState.value = _uiState.value.copy(isProcessing = true)
        viewModelScope.launch {
            val state = _uiState.value
            val outputFile = withContext(Dispatchers.Default) {
                val startIndex = (state.selectionStart * sourceSamples.size).toInt()
                val endIndex = (state.selectionEnd * sourceSamples.size).toInt()
                var edited = edit(sourceSamples, startIndex, endIndex)
                val fadeSamples = (sampleRate * FADE_SECONDS).toInt()
                if (state.fadeInEnabled) edited = AudioEditor.fadeIn(edited, fadeSamples)
                if (state.fadeOutEnabled) edited = AudioEditor.fadeOut(edited, fadeSamples)

                val outputDir = File(getApplication<Application>().filesDir, "edited").apply { mkdirs() }
                val file = File(outputDir, "edited_${source.id}_${System.currentTimeMillis()}.wav")
                file.outputStream().use { WavIO.write(it, edited, sampleRate, channels, BitDepth.PCM_16) }
                EditedResult(file, (edited.size.toLong() * 1000L) / sampleRate)
            }
            val recordingId = app.recordingRepository.save(
                source.copy(
                    id = 0,
                    title = "${source.title} (Edited)",
                    filePath = outputFile.file.absolutePath,
                    createdAtEpochMs = System.currentTimeMillis(),
                    durationMs = outputFile.durationMs,
                    fileSizeBytes = outputFile.file.length(),
                    exportFormat = "wav",
                    studioReadinessScore = null,
                    broadcastReadinessScore = null,
                    archiveReadinessScore = null,
                    isFavorite = false,
                    isPrimaryVersion = false,
                    notes = "Edited from \"${source.title}\".",
                ),
            )
            _uiState.value = _uiState.value.copy(isProcessing = false, savedToLibrary = true)
            launch { RecordingAutoAnalyzer.analyzeAndPersist(app.recordingRepository, recordingId, outputFile.file) }
        }
    }

    private data class DecodedAudio(val samples: FloatArray, val sampleRate: Int, val channels: Int, val peaks: FloatArray)
    private data class EditedResult(val file: File, val durationMs: Long)

    private companion object {
        const val WAVEFORM_BUCKET_COUNT = 150
        const val FADE_SECONDS = 0.3
    }
}
