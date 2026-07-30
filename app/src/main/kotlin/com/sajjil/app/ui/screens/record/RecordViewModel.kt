package com.sajjil.app.ui.screens.record

import android.app.Application
import android.media.AudioDeviceInfo
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.sajjil.app.audio.AcousticProbeRecorder
import com.sajjil.app.audio.AudioInputDevices
import com.sajjil.app.audio.AudioRecordEngine
import com.sajjil.app.audio.LivePreviewMonitor
import com.sajjil.app.audio.RecordingLevel
import com.sajjil.app.data.db.RecordingEntity
import com.sajjil.app.di.asSajjilApplication
import com.sajjil.core.analysis.AcousticAnalyzer
import com.sajjil.core.analysis.AcousticProfile
import com.sajjil.core.analysis.DirectorGuidance
import com.sajjil.core.modes.MicrophoneProfile
import com.sajjil.core.modes.RecordingMode
import com.sajjil.core.modes.RecordingQuality
import com.sajjil.core.quran.QuranMetadata
import com.sajjil.core.quran.SurahInfo
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.io.File

data class RecordUiState(
    val mode: RecordingMode = RecordingMode.QURAN_STUDIO,
    val quality: RecordingQuality = RecordingQuality.PROFESSIONAL,
    val microphoneProfile: MicrophoneProfile = MicrophoneProfile.default,
    val isRecording: Boolean = false,
    val elapsedMs: Long = 0L,
    val level: RecordingLevel = RecordingLevel(-100f, -100f, 0f),
    val lastSavedFile: File? = null,
    val isCheckingRoom: Boolean = false,
    val roomProfile: AcousticProfile? = null,
    val availableInputDevices: List<AudioDeviceInfo> = emptyList(),
    val selectedInputDevice: AudioDeviceInfo? = null,
    val liveGuidance: DirectorGuidance? = null,
    // Qur'an Production Suite: set a target Surah/Ayah range before recording so the take is
    // tagged automatically on save — no separate trip to Qur'an Studio to tag it afterward.
    val targetSurah: SurahInfo? = null,
    val targetAyahStart: Int = 1,
    val targetAyahEnd: Int = 1,
)

class RecordViewModel(application: Application) : AndroidViewModel(application) {
    private val app = application.asSajjilApplication()

    private val _uiState = MutableStateFlow(RecordUiState())
    val uiState: StateFlow<RecordUiState> = _uiState.asStateFlow()

    private var engine: AudioRecordEngine? = null
    private var startedAtMs: Long = 0L
    private val liveMonitor = LivePreviewMonitor()

    init {
        refreshInputDevices()
        startLiveMonitoring()
    }

    /** SAJJIL USB Professional Microphone Support: re-scan when a mic is plugged in / unplugged. */
    fun refreshInputDevices() {
        val devices = AudioInputDevices.list(getApplication())
        _uiState.value = _uiState.value.copy(availableInputDevices = devices)
    }

    fun selectInputDevice(device: AudioDeviceInfo?) {
        if (_uiState.value.isRecording) return
        _uiState.value = _uiState.value.copy(selectedInputDevice = device)
    }

    fun selectMode(mode: RecordingMode) {
        if (_uiState.value.isRecording) return
        _uiState.value = _uiState.value.copy(mode = mode)
    }

    fun selectQuality(quality: RecordingQuality) {
        if (_uiState.value.isRecording) return
        _uiState.value = _uiState.value.copy(quality = quality)
    }

    fun selectMicrophoneProfile(profile: MicrophoneProfile) {
        if (_uiState.value.isRecording) return
        _uiState.value = _uiState.value.copy(microphoneProfile = profile)
    }

    /** Intelligent Recording Director: continuous gain/echo/clipping guidance while the mic is live but not yet recording. */
    private fun startLiveMonitoring() {
        liveMonitor.start(viewModelScope)
        viewModelScope.launch {
            liveMonitor.guidance.collect { guidance ->
                if (!_uiState.value.isRecording) {
                    _uiState.value = _uiState.value.copy(liveGuidance = guidance)
                }
            }
        }
    }

    fun selectTargetSurah(surah: SurahInfo?) {
        _uiState.value = _uiState.value.copy(targetSurah = surah, targetAyahStart = 1, targetAyahEnd = surah?.ayahCount ?: 1)
    }

    fun setTargetAyahRange(start: Int, end: Int) {
        val surah = _uiState.value.targetSurah ?: return
        _uiState.value = _uiState.value.copy(
            targetAyahStart = start.coerceIn(1, surah.ayahCount),
            targetAyahEnd = end.coerceIn(start, surah.ayahCount),
        )
    }

    /** SAJJIL AI Acoustic Intelligence: a short probe capture, analysed for noise/echo/clipping before the take. */
    fun runRoomCheck() {
        if (_uiState.value.isRecording || _uiState.value.isCheckingRoom) return
        _uiState.value = _uiState.value.copy(isCheckingRoom = true, roomProfile = null)
        viewModelScope.launch {
            val sampleRate = 48000
            val probe = AcousticProbeRecorder.capture(durationSeconds = 3.0, sampleRate = sampleRate)
            val profile = AcousticAnalyzer.analyze(probe, sampleRate)
            _uiState.value = _uiState.value.copy(isCheckingRoom = false, roomProfile = profile)
        }
    }

    fun dismissRoomCheck() {
        _uiState.value = _uiState.value.copy(roomProfile = null)
    }

    fun applyRecommendedMode() {
        val recommended = _uiState.value.roomProfile?.recommendedModeName ?: return
        val mode = RecordingMode.entries.firstOrNull { it.name == recommended } ?: return
        selectMode(mode)
    }

    fun startRecording() {
        if (_uiState.value.isRecording) return
        liveMonitor.stop()
        val state = _uiState.value
        val outputDir = File(getApplication<Application>().filesDir, "recordings").apply { mkdirs() }
        val file = File(outputDir, "sajjil_${System.currentTimeMillis()}.wav")

        val newEngine = AudioRecordEngine(
            outputFile = file,
            requestedSampleRate = state.quality.sampleRate,
            outputBitDepth = state.quality.bitDepth,
            chainConfig = state.mode.config,
            microphoneProfile = state.microphoneProfile,
            preferredInputDevice = state.selectedInputDevice,
        )
        engine = newEngine
        startedAtMs = System.currentTimeMillis()
        newEngine.start(viewModelScope)
        _uiState.value = state.copy(isRecording = true, elapsedMs = 0L, liveGuidance = null)

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
            val state = _uiState.value
            val target = state.targetSurah
            app.recordingRepository.save(
                RecordingEntity(
                    title = target?.let { "${it.transliteratedName} ${state.targetAyahStart}-${state.targetAyahEnd}" }
                        ?: file.nameWithoutExtension,
                    filePath = file.absolutePath,
                    createdAtEpochMs = System.currentTimeMillis(),
                    durationMs = state.elapsedMs,
                    sampleRate = current.sampleRate,
                    channels = 1,
                    bitDepth = state.quality.bitDepth.bits,
                    recordingMode = state.mode.name,
                    fileSizeBytes = file.length(),
                    exportFormat = "wav",
                    surahNumber = target?.number,
                    ayahStart = target?.let { state.targetAyahStart },
                    ayahEnd = target?.let { state.targetAyahEnd },
                    juz = target?.let { QuranMetadata.juzForSurahAyah(it.number, state.targetAyahStart) },
                ),
            )
            _uiState.value = state.copy(isRecording = false, lastSavedFile = file)
            startLiveMonitoring()
        }
    }

    override fun onCleared() {
        super.onCleared()
        engine = null
        liveMonitor.stop()
    }
}
