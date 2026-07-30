package com.sajjil.app.ui.screens.enhance

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.sajjil.app.analysis.RecordingAutoAnalyzer
import com.sajjil.app.audio.AudioPlaybackEngine
import com.sajjil.app.data.db.RecordingEntity
import com.sajjil.app.di.asSajjilApplication
import com.sajjil.core.audio.WavIO
import com.sajjil.core.dsp.NoiseReductionStrength
import com.sajjil.core.dsp.SpectralNoiseReducer
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File

data class EnhanceUiState(
    val recordings: List<RecordingEntity> = emptyList(),
    val selected: RecordingEntity? = null,
    val strength: NoiseReductionStrength = NoiseReductionStrength.MODERATE,
    val isProcessing: Boolean = false,
    val enhancedFile: File? = null,
    val savedToLibrary: Boolean = false,
)

class EnhanceViewModel(application: Application) : AndroidViewModel(application) {
    private val app = application.asSajjilApplication()
    val playback = AudioPlaybackEngine()

    private val _uiState = MutableStateFlow(EnhanceUiState())
    val uiState: StateFlow<EnhanceUiState> = _uiState.asStateFlow()

    init {
        viewModelScope.launch {
            app.recordingRepository.observeAll().collect { list ->
                _uiState.value = _uiState.value.copy(recordings = list)
            }
        }
    }

    fun select(recording: RecordingEntity) {
        _uiState.value = _uiState.value.copy(selected = recording, enhancedFile = null, savedToLibrary = false)
    }

    fun setStrength(strength: NoiseReductionStrength) {
        _uiState.value = _uiState.value.copy(strength = strength)
    }

    fun playOriginal() {
        val file = _uiState.value.selected?.let { File(it.filePath) } ?: return
        playback.play(file, viewModelScope)
    }

    fun playEnhanced() {
        val file = _uiState.value.enhancedFile ?: return
        playback.play(file, viewModelScope)
    }

    fun enhance() {
        val selected = _uiState.value.selected ?: return
        _uiState.value = _uiState.value.copy(isProcessing = true)
        viewModelScope.launch {
            val outputFile = withContext(Dispatchers.Default) {
                val audio = WavIO.read(File(selected.filePath).readBytes())
                val reducer = SpectralNoiseReducer(audio.sampleRate)
                val cleaned = reducer.process(audio.samples, _uiState.value.strength)
                val output = File(
                    File(getApplication<Application>().filesDir, "enhanced").apply { mkdirs() },
                    "enhanced_${selected.id}_${System.currentTimeMillis()}.wav",
                )
                output.outputStream().use { out ->
                    WavIO.write(out, cleaned, audio.sampleRate, audio.channels, com.sajjil.core.audio.BitDepth.PCM_16)
                }
                output
            }
            _uiState.value = _uiState.value.copy(isProcessing = false, enhancedFile = outputFile)
        }
    }

    /** Files onto the same Surah/Ayah tag as the source, so the enhanced take shows up as an alternate version to choose from. */
    fun saveToLibrary() {
        val source = _uiState.value.selected ?: return
        val file = _uiState.value.enhancedFile ?: return
        viewModelScope.launch {
            val recordingId = app.recordingRepository.save(
                source.copy(
                    id = 0,
                    title = "${source.title} (Enhanced)",
                    filePath = file.absolutePath,
                    createdAtEpochMs = System.currentTimeMillis(),
                    fileSizeBytes = file.length(),
                    studioReadinessScore = null,
                    broadcastReadinessScore = null,
                    archiveReadinessScore = null,
                    isFavorite = false,
                    isPrimaryVersion = false,
                    notes = "Enhanced from \"${source.title}\" (${_uiState.value.strength.name.lowercase()} noise reduction).",
                ),
            )
            _uiState.value = _uiState.value.copy(savedToLibrary = true)
            // Background Intelligence: fill the score in shortly after, rather than making the
            // save wait on it or leaving it null until Dashboard is opened.
            launch { RecordingAutoAnalyzer.analyzeAndPersist(app.recordingRepository, recordingId, file) }
        }
    }

    override fun onCleared() {
        super.onCleared()
        playback.stop()
    }
}
