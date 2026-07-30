package com.sajjil.app.ui.screens.record

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.sajjil.app.audio.AudioRecordEngine
import com.sajjil.app.audio.RecordingLevel
import com.sajjil.app.data.db.RecordingEntity
import com.sajjil.app.di.asSajjilApplication
import com.sajjil.core.modes.RecordingMode
import com.sajjil.core.modes.RecordingQuality
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.io.File

data class RecordUiState(
    val mode: RecordingMode = RecordingMode.QURAN_STUDIO,
    val quality: RecordingQuality = RecordingQuality.PROFESSIONAL,
    val isRecording: Boolean = false,
    val elapsedMs: Long = 0L,
    val level: RecordingLevel = RecordingLevel(-100f, -100f, 0f),
    val lastSavedFile: File? = null,
)

class RecordViewModel(application: Application) : AndroidViewModel(application) {
    private val app = application.asSajjilApplication()

    private val _uiState = MutableStateFlow(RecordUiState())
    val uiState: StateFlow<RecordUiState> = _uiState.asStateFlow()

    private var engine: AudioRecordEngine? = null
    private var startedAtMs: Long = 0L

    fun selectMode(mode: RecordingMode) {
        if (_uiState.value.isRecording) return
        _uiState.value = _uiState.value.copy(mode = mode)
    }

    fun selectQuality(quality: RecordingQuality) {
        if (_uiState.value.isRecording) return
        _uiState.value = _uiState.value.copy(quality = quality)
    }

    fun startRecording() {
        if (_uiState.value.isRecording) return
        val state = _uiState.value
        val outputDir = File(getApplication<Application>().filesDir, "recordings").apply { mkdirs() }
        val file = File(outputDir, "sajjil_${System.currentTimeMillis()}.wav")

        val newEngine = AudioRecordEngine(
            outputFile = file,
            requestedSampleRate = state.quality.sampleRate,
            outputBitDepth = state.quality.bitDepth,
            chainConfig = state.mode.config,
        )
        engine = newEngine
        startedAtMs = System.currentTimeMillis()
        newEngine.start(viewModelScope)
        _uiState.value = state.copy(isRecording = true, elapsedMs = 0L)

        viewModelScope.launch {
            newEngine.level.collect { level ->
                _uiState.value = _uiState.value.copy(
                    level = level,
                    elapsedMs = System.currentTimeMillis() - startedAtMs,
                )
            }
        }
    }

    fun stopRecording() {
        val current = engine ?: return
        viewModelScope.launch {
            val file = current.stop()
            engine = null
            app.recordingRepository.save(
                RecordingEntity(
                    title = file.nameWithoutExtension,
                    filePath = file.absolutePath,
                    createdAtEpochMs = System.currentTimeMillis(),
                    durationMs = _uiState.value.elapsedMs,
                    sampleRate = current.sampleRate,
                    channels = 1,
                    bitDepth = _uiState.value.quality.bitDepth.bits,
                    recordingMode = _uiState.value.mode.name,
                    fileSizeBytes = file.length(),
                    exportFormat = "wav",
                ),
            )
            _uiState.value = _uiState.value.copy(isRecording = false, lastSavedFile = file)
        }
    }

    override fun onCleared() {
        super.onCleared()
        engine = null
    }
}
