package com.sajjil.app.ui.screens.master

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.sajjil.app.audio.AudioPlaybackEngine
import com.sajjil.app.data.db.RecordingEntity
import com.sajjil.app.di.asSajjilApplication
import com.sajjil.app.export.AudioExporter
import com.sajjil.app.export.ExportFormat
import com.sajjil.core.analysis.AcousticAnalyzer
import com.sajjil.core.analysis.AudioAnalysisReport
import com.sajjil.core.analysis.AudioQualityScorer
import com.sajjil.core.analysis.LoudnessAnalyzer
import com.sajjil.core.analysis.LoudnessSample
import com.sajjil.core.analysis.Spectrogram
import com.sajjil.core.analysis.SpectrogramAnalyzer
import com.sajjil.core.audio.BitDepth
import com.sajjil.core.audio.WavIO
import com.sajjil.core.dsp.AudioProcessingChain
import com.sajjil.core.dsp.AudioRestoration
import com.sajjil.core.dsp.Dereverberator
import com.sajjil.core.dsp.ReferenceMatcher
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
    val repairDamage: Boolean = false,
    val removeEcho: Boolean = false,
    val referenceRecording: RecordingEntity? = null,
    val spectrogram: Spectrogram? = null,
    val loudnessHistory: List<LoudnessSample> = emptyList(),
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
        _uiState.value = _uiState.value.copy(selected = recording, masteredFile = null, report = null, spectrogram = null, loudnessHistory = emptyList())
    }

    fun selectProfile(profile: VoiceProfile) {
        _uiState.value = _uiState.value.copy(profile = profile)
    }

    fun selectExportFormat(format: ExportFormat) {
        _uiState.value = _uiState.value.copy(exportFormat = format)
    }

    fun setRepairDamage(enabled: Boolean) {
        _uiState.value = _uiState.value.copy(repairDamage = enabled)
    }

    fun setRemoveEcho(enabled: Boolean) {
        _uiState.value = _uiState.value.copy(removeEcho = enabled)
    }

    fun selectReferenceRecording(recording: RecordingEntity?) {
        _uiState.value = _uiState.value.copy(referenceRecording = recording)
    }

    fun master() {
        val selected = _uiState.value.selected ?: return
        _uiState.value = _uiState.value.copy(isProcessing = true)
        viewModelScope.launch {
            val request = _uiState.value
            val (outputFile, report, spectrogram, loudnessHistory) = withContext(Dispatchers.Default) {
                val audio = WavIO.read(File(selected.filePath).readBytes())
                var working = audio.samples

                // Restoration Laboratory: declip + denoise + level-rescue, before tonal shaping.
                if (request.repairDamage) {
                    working = AudioRestoration.restore(working, audio.sampleRate)
                }

                // AI Echo Removal: dereverberate using a blind RT60 estimate off the take itself.
                var rt60: Double? = null
                if (request.removeEcho) {
                    rt60 = AcousticAnalyzer.estimateRt60(working, audio.sampleRate)
                    if (rt60 != null) {
                        working = Dereverberator(audio.sampleRate).process(working, rt60)
                    }
                }

                // Reference Mastering Engine: optional spectral match to another take before the profile's own EQ/dynamics.
                request.referenceRecording?.let { reference ->
                    val referenceAudio = WavIO.read(File(reference.filePath).readBytes())
                    working = ReferenceMatcher.matchToReference(audio.sampleRate, working, referenceAudio.samples)
                }

                val chain = AudioProcessingChain(audio.sampleRate, request.profile.config)
                val mastered = FloatArray(working.size)
                for (i in working.indices) mastered[i] = chain.process(working[i])

                val masterDir = File(getApplication<Application>().filesDir, "mastered").apply { mkdirs() }
                val wavFile = File(masterDir, "master_${selected.id}_${System.currentTimeMillis()}.wav")
                wavFile.outputStream().use { WavIO.write(it, mastered, audio.sampleRate, audio.channels, BitDepth.PCM_24) }

                val finalFile = when (request.exportFormat) {
                    ExportFormat.WAV -> wavFile
                    ExportFormat.M4A_AAC -> {
                        val aacFile = File(masterDir, "master_${selected.id}_${System.currentTimeMillis()}.m4a")
                        exporter.exportAac(wavFile, aacFile)
                        aacFile
                    }
                }

                val echoRt60 = rt60 ?: AcousticAnalyzer.estimateRt60(mastered, audio.sampleRate)
                val metrics = LoudnessAnalyzer.analyze(mastered, audio.sampleRate)
                val scoreReport = AudioQualityScorer.score(metrics, echoRt60)
                val spectrogramData = SpectrogramAnalyzer.compute(mastered, audio.sampleRate)
                val history = SpectrogramAnalyzer.loudnessHistory(mastered, audio.sampleRate)

                MasterResult(finalFile, scoreReport, spectrogramData, history)
            }
            _uiState.value = _uiState.value.copy(
                isProcessing = false,
                masteredFile = outputFile,
                report = report,
                spectrogram = spectrogram,
                loudnessHistory = loudnessHistory,
            )
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

    private data class MasterResult(
        val file: File,
        val report: AudioAnalysisReport,
        val spectrogram: Spectrogram,
        val loudnessHistory: List<LoudnessSample>,
    )
}
