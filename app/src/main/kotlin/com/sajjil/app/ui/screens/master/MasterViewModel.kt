package com.sajjil.app.ui.screens.master

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.sajjil.app.audio.AudioPlaybackEngine
import com.sajjil.app.data.db.RecordingEntity
import com.sajjil.app.di.asSajjilApplication
import com.sajjil.app.export.AudioExporter
import com.sajjil.app.export.ExportFormat
import com.sajjil.core.analysis.AudioAnalysisReport
import com.sajjil.core.analysis.AudioQualityScorer
import com.sajjil.core.analysis.LoudnessAnalyzer
import com.sajjil.core.audio.BitDepth
import com.sajjil.core.audio.WavIO
import com.sajjil.core.dsp.AudioProcessingChain
import com.sajjil.core.modes.VoiceProfile
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File

data class MasterUiState(
    val recordings: List<RecordingEntity> = emptyList(),
    val selected: RecordingEntity? = null,
    val profile: VoiceProfile = VoiceProfile.STUDIO_QARI,
    val isProcessing: Boolean = false,
    val masteredFile: File? = null,
    val report: AudioAnalysisReport? = null,
    val exportFormat: ExportFormat = ExportFormat.WAV,
)

class MasterViewModel(application: Application) : AndroidViewModel(application) {
    private val app = application.asSajjilApplication()
    private val exporter = AudioExporter()
    val playback = AudioPlaybackEngine()

    private val _uiState = MutableStateFlow(MasterUiState())
    val uiState: StateFlow<MasterUiState> = _uiState.asStateFlow()

    init {
        viewModelScope.launch {
            app.recordingRepository.observeAll().collect { list ->
                _uiState.value = _uiState.value.copy(recordings = list)
            }
        }
    }

    fun select(recording: RecordingEntity) {
        _uiState.value = _uiState.value.copy(selected = recording, masteredFile = null, report = null)
    }

    fun selectProfile(profile: VoiceProfile) {
        _uiState.value = _uiState.value.copy(profile = profile)
    }

    fun selectExportFormat(format: ExportFormat) {
        _uiState.value = _uiState.value.copy(exportFormat = format)
    }

    fun master() {
        val selected = _uiState.value.selected ?: return
        _uiState.value = _uiState.value.copy(isProcessing = true)
        viewModelScope.launch {
            val (outputFile, report) = withContext(Dispatchers.Default) {
                val audio = WavIO.read(File(selected.filePath).readBytes())
                val chain = AudioProcessingChain(audio.sampleRate, _uiState.value.profile.config)
                val mastered = FloatArray(audio.samples.size)
                for (i in audio.samples.indices) mastered[i] = chain.process(audio.samples[i])

                val masterDir = File(getApplication<Application>().filesDir, "mastered").apply { mkdirs() }
                val wavFile = File(masterDir, "master_${selected.id}_${System.currentTimeMillis()}.wav")
                wavFile.outputStream().use { WavIO.write(it, mastered, audio.sampleRate, audio.channels, BitDepth.PCM_24) }

                val finalFile = when (_uiState.value.exportFormat) {
                    ExportFormat.WAV -> wavFile
                    ExportFormat.M4A_AAC -> {
                        val aacFile = File(masterDir, "master_${selected.id}_${System.currentTimeMillis()}.m4a")
                        exporter.exportAac(wavFile, aacFile)
                        aacFile
                    }
                }

                val metrics = LoudnessAnalyzer.analyze(mastered, audio.sampleRate)
                finalFile to AudioQualityScorer.score(metrics)
            }
            _uiState.value = _uiState.value.copy(isProcessing = false, masteredFile = outputFile, report = report)
        }
    }

    fun playMastered() {
        val file = _uiState.value.masteredFile ?: return
        if (file.extension == "wav") playback.play(file, viewModelScope)
    }

    override fun onCleared() {
        super.onCleared()
        playback.stop()
    }
}
