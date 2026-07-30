package com.sajjil.app.ui.screens.voicestudio

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.sajjil.app.analysis.RecordingAutoAnalyzer
import com.sajjil.app.data.db.RecordingEntity
import com.sajjil.app.di.asSajjilApplication
import com.sajjil.app.speech.AndroidSpeechBridge
import com.sajjil.app.speech.OfflineArabicRecognizer
import com.sajjil.app.speech.OfflineEnglishRecognizer
import com.sajjil.app.speech.RecognitionEvent
import com.sajjil.app.speech.SpeechCapabilityReport
import com.sajjil.app.speech.SpeechRecognitionEngine
import com.sajjil.app.speech.TTSManager
import com.sajjil.core.modes.RecordingMode
import com.sajjil.core.speech.Transcript
import com.sajjil.core.speech.TranscriptLanguage
import com.sajjil.core.speech.TranscriptSearchEngine
import com.sajjil.core.speech.TranscriptSearchResult
import com.sajjil.core.speech.TranscriptSegment
import com.sajjil.core.speech.TranscriptStabilizer
import java.io.File
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class VoiceStudioUiState(
    val capability: SpeechCapabilityReport? = null,
    val selectedLanguage: TranscriptLanguage = TranscriptLanguage.ENGLISH,
    val isListening: Boolean = false,
    /** The part of the in-progress hypothesis that has held steady across recent updates — safe to render without flicker. */
    val stablePartialText: String = "",
    /** The trailing part still being revised by the recognizer — expect this to keep changing while listening. */
    val draftPartialText: String = "",
    val segments: List<TranscriptSegment> = emptyList(),
    val statusMessage: String? = null,
    val searchQuery: String = "",
    val searchResults: List<TranscriptSearchResult> = emptyList(),
    val isSpeaking: Boolean = false,
    val lastSavedTitle: String? = null,
) {
    val fullTranscriptText: String get() = segments.joinToString(" ") { it.text }
}

/**
 * SAJJIL Voice Studio: record, offline-transcribe, search, and read back
 * transcripts — one workflow, without leaving the screen. This does not
 * claim automatic accuracy for Qur'anic recitation; transcripts carry
 * whatever confidence the recognizer reports, unlabeled where it doesn't.
 *
 * `SpeechRecognizer` only ever returns one final result per session, so a
 * longer dictation is built by automatically starting a new session each
 * time the previous one finalizes, until the user presses Stop — segment
 * timestamps are offset to stay continuous across those restarts. Because
 * each restart opens a fresh capture file (reusing one across sessions
 * would silently corrupt it — `WavStreamWriter` rewrites the file header
 * from byte zero on open), only the most recent sub-session's raw audio
 * is kept as a reference clip when a session is saved; the transcript
 * itself is always the full, continuous session.
 */
class VoiceStudioViewModel(application: Application) : AndroidViewModel(application) {
    private val app = application.asSajjilApplication()
    private val bridge = AndroidSpeechBridge(application)
    private val ttsManager = TTSManager(application)

    private val _uiState = MutableStateFlow(VoiceStudioUiState())
    val uiState: StateFlow<VoiceStudioUiState> = _uiState.asStateFlow()

    private var recognizer: SpeechRecognitionEngine? = null
    private var listeningJob: Job? = null
    private var captureFile: File? = null
    private var cumulativeOffsetMs = 0L
    private var userRequestedStop = false
    private var allTranscripts: List<Transcript> = emptyList()

    init {
        refreshCapability()
        viewModelScope.launch { ttsManager.initialize() }
        viewModelScope.launch {
            app.transcriptRepository.observeAllAsTranscripts().collect { transcripts ->
                allTranscripts = transcripts
                if (_uiState.value.searchQuery.isNotBlank()) runSearch(_uiState.value.searchQuery)
            }
        }
    }

    fun refreshCapability() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(capability = bridge.detect())
        }
    }

    fun selectLanguage(language: TranscriptLanguage) {
        if (_uiState.value.isListening) return
        _uiState.value = _uiState.value.copy(selectedLanguage = language)
    }

    fun startListening() {
        if (_uiState.value.isListening) return
        cumulativeOffsetMs = 0L
        userRequestedStop = false
        _uiState.value = _uiState.value.copy(
            isListening = true,
            stablePartialText = "",
            draftPartialText = "",
            segments = emptyList(),
            statusMessage = null,
            lastSavedTitle = null,
        )
        listeningJob = viewModelScope.launch { listenLoop() }
    }

    private suspend fun listenLoop() {
        val language = _uiState.value.selectedLanguage
        while (!userRequestedStop) {
            val dir = File(getApplication<Application>().filesDir, "voice_studio").apply { mkdirs() }
            val file = File(dir, "voice_studio_${System.currentTimeMillis()}.wav")
            captureFile = file

            val engine: SpeechRecognitionEngine = when (language) {
                TranscriptLanguage.ARABIC -> OfflineArabicRecognizer(getApplication(), file)
                TranscriptLanguage.ENGLISH -> OfflineEnglishRecognizer(getApplication(), file)
            }
            recognizer = engine
            // Fresh per sub-session: a restarted SpeechRecognizer session starts a brand new
            // hypothesis stream, unrelated to the previous one, so stability history must not
            // carry across the boundary.
            val stabilizer = TranscriptStabilizer()

            var shouldContinue = false
            engine.start().collect { event ->
                when (event) {
                    RecognitionEvent.ReadyForSpeech ->
                        _uiState.value = _uiState.value.copy(statusMessage = "Listening…")
                    is RecognitionEvent.PartialResult -> {
                        val split = stabilizer.update(event.text)
                        _uiState.value = _uiState.value.copy(
                            stablePartialText = split.stableText,
                            draftPartialText = split.draftText,
                        )
                    }
                    is RecognitionEvent.FinalSegment -> {
                        stabilizer.commitFinal(event.segment.text)
                        val adjusted = event.segment.copy(
                            startMs = cumulativeOffsetMs + event.segment.startMs,
                            endMs = cumulativeOffsetMs + event.segment.endMs,
                        )
                        cumulativeOffsetMs = adjusted.endMs
                        _uiState.value = _uiState.value.copy(
                            segments = _uiState.value.segments + adjusted,
                            stablePartialText = "",
                            draftPartialText = "",
                        )
                        shouldContinue = true
                    }
                    is RecognitionEvent.Error -> {
                        stabilizer.reset()
                        _uiState.value = _uiState.value.copy(
                            statusMessage = event.message,
                            stablePartialText = "",
                            draftPartialText = "",
                        )
                        shouldContinue = event.recoverable
                    }
                    RecognitionEvent.EndOfSession -> Unit
                }
            }
            recognizer = null
            if (!shouldContinue) break
        }
        _uiState.value = _uiState.value.copy(
            isListening = false,
            statusMessage = _uiState.value.statusMessage ?: "Stopped.",
        )
    }

    fun stopListening() {
        userRequestedStop = true
        recognizer?.stop()
    }

    fun search(query: String) {
        _uiState.value = _uiState.value.copy(searchQuery = query)
        runSearch(query)
    }

    private fun runSearch(query: String) {
        val results = if (query.isBlank()) emptyList() else TranscriptSearchEngine.search(allTranscripts, query)
        _uiState.value = _uiState.value.copy(searchResults = results)
    }

    fun speak(text: String) {
        val language = _uiState.value.selectedLanguage
        val started = ttsManager.speak(text, language)
        _uiState.value = _uiState.value.copy(
            isSpeaking = started,
            statusMessage = if (!started) "No offline voice available for ${language.displayName}." else _uiState.value.statusMessage,
        )
    }

    fun stopSpeaking() {
        ttsManager.stop()
        _uiState.value = _uiState.value.copy(isSpeaking = false)
    }

    fun saveSession(title: String) {
        val state = _uiState.value
        if (state.isListening || state.segments.isEmpty()) return
        val file = captureFile
        val language = state.selectedLanguage

        viewModelScope.launch {
            val recordingId = if (file != null && file.exists() && file.length() > 44) {
                app.recordingRepository.save(
                    RecordingEntity(
                        title = title.ifBlank { "Voice Studio Session" },
                        filePath = file.absolutePath,
                        createdAtEpochMs = System.currentTimeMillis(),
                        durationMs = state.segments.last().endMs,
                        sampleRate = 16_000,
                        channels = 1,
                        bitDepth = 16,
                        recordingMode = RecordingMode.LECTURE.name,
                        fileSizeBytes = file.length(),
                        exportFormat = "wav",
                        notes = "Captured via SAJJIL Voice Studio live transcription. Reference audio only — " +
                            "the most recent segment of a multi-part session, not the full session.",
                    ),
                )
            } else {
                null
            }

            if (recordingId != null) {
                // Background Intelligence: score the reference clip too, same as any other save path.
                launch { RecordingAutoAnalyzer.analyzeAndPersist(app.recordingRepository, recordingId, file!!) }
                app.transcriptRepository.replaceForRecording(
                    recordingId,
                    Transcript(recordingId = recordingId, language = language, segments = state.segments, engineId = "android-native"),
                )
                _uiState.value = _uiState.value.copy(
                    lastSavedTitle = title.ifBlank { "Voice Studio Session" },
                    segments = emptyList(),
                    searchQuery = "",
                    searchResults = emptyList(),
                )
            } else {
                _uiState.value = _uiState.value.copy(statusMessage = "No reference audio was captured — nothing to save.")
            }
        }
    }

    override fun onCleared() {
        super.onCleared()
        recognizer?.stop()
        ttsManager.shutdown()
    }
}
