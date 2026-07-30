package com.sajjil.app.ui.screens.assistant

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.sajjil.app.data.db.RecordingEntity
import com.sajjil.app.di.asSajjilApplication
import com.sajjil.app.speech.AndroidNativeSpeechRecognizer
import com.sajjil.app.speech.RecognitionEvent
import com.sajjil.app.speech.SpeechRecognitionEngine
import com.sajjil.app.speech.TTSManager
import com.sajjil.core.assistant.AssistantIntent
import com.sajjil.core.assistant.AssistantIntentParser
import com.sajjil.core.assistant.QualityComparison
import com.sajjil.core.quran.QuranMetadata
import com.sajjil.core.speech.Transcript
import com.sajjil.core.speech.TranscriptLanguage
import com.sajjil.core.speech.TranscriptSearchEngine
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class AssistantResultItem(val recordingId: Long, val title: String, val subtitle: String)

data class AssistantUiState(
    val inputText: String = "",
    val language: TranscriptLanguage = TranscriptLanguage.ENGLISH,
    val isListening: Boolean = false,
    val results: List<AssistantResultItem> = emptyList(),
    val responseMessage: String? = null,
    val selectedRecordingId: Long? = null,
)

private val EXAMPLE_COMMANDS = listOf(
    "\"Show me Surah Al-Kahf recordings\"",
    "\"Find where I discussed zakat\"",
    "\"Read this transcript\"",
    "\"Which recordings have poor quality?\"",
)

/**
 * SAJJIL Assistant: a fixed, small set of requests
 * ([com.sajjil.core.assistant.AssistantIntentParser]) executed against
 * real library/transcript data. This is deliberately **not** a
 * conversational AI — there is no language model behind it, on-device or
 * otherwise, to bundle or verify in this environment. It understands the
 * phrasings its patterns cover and says so plainly when a request doesn't
 * match one, rather than guessing at meaning it can't actually derive.
 * See docs/REALTIME_ASSISTANT.md for the reasoning.
 */
class AssistantViewModel(application: Application) : AndroidViewModel(application) {
    private val app = application.asSajjilApplication()
    private val ttsManager = TTSManager(application)

    private val _uiState = MutableStateFlow(AssistantUiState())
    val uiState: StateFlow<AssistantUiState> = _uiState.asStateFlow()

    private var library: List<RecordingEntity> = emptyList()
    private var transcripts: List<Transcript> = emptyList()
    private var recognizer: SpeechRecognitionEngine? = null

    init {
        viewModelScope.launch { ttsManager.initialize() }
        viewModelScope.launch { app.recordingRepository.observeAll().collect { library = it } }
        viewModelScope.launch { app.transcriptRepository.observeAllAsTranscripts().collect { transcripts = it } }
    }

    fun updateInput(text: String) {
        _uiState.value = _uiState.value.copy(inputText = text)
    }

    fun selectLanguage(language: TranscriptLanguage) {
        if (_uiState.value.isListening) return
        _uiState.value = _uiState.value.copy(language = language)
    }

    fun selectResult(item: AssistantResultItem) {
        _uiState.value = _uiState.value.copy(selectedRecordingId = item.recordingId)
    }

    fun submit() {
        val text = _uiState.value.inputText.trim()
        if (text.isBlank()) return
        handle(text)
    }

    /** One-shot voice input for the request itself — not a continuous session like Voice Studio. */
    fun listenForCommand() {
        if (_uiState.value.isListening) return
        _uiState.value = _uiState.value.copy(isListening = true, responseMessage = null)
        viewModelScope.launch {
            val engine = AndroidNativeSpeechRecognizer(getApplication(), _uiState.value.language)
            recognizer = engine
            engine.start().collect { event ->
                when (event) {
                    is RecognitionEvent.FinalSegment -> {
                        _uiState.value = _uiState.value.copy(inputText = event.segment.text)
                        handle(event.segment.text)
                    }
                    is RecognitionEvent.Error ->
                        _uiState.value = _uiState.value.copy(responseMessage = event.message)
                    else -> Unit
                }
            }
            recognizer = null
            _uiState.value = _uiState.value.copy(isListening = false)
        }
    }

    fun stopListening() {
        recognizer?.stop()
    }

    private fun handle(text: String) {
        when (val intent = AssistantIntentParser.parse(text)) {
            is AssistantIntent.FindBySurah -> handleFindBySurah(intent)
            is AssistantIntent.FindByKeyword -> handleFindByKeyword(intent)
            AssistantIntent.ReadCurrentTranscript -> handleReadCurrentTranscript()
            is AssistantIntent.FilterByQuality -> handleFilterByQuality(intent)
            is AssistantIntent.Unrecognized -> handleUnrecognized()
        }
    }

    private fun handleFindBySurah(intent: AssistantIntent.FindBySurah) {
        val surah = QuranMetadata.surahs.firstOrNull { it.transliteratedName.equals(intent.surahQuery, ignoreCase = true) }
            ?: QuranMetadata.surahs.firstOrNull { it.transliteratedName.contains(intent.surahQuery, ignoreCase = true) }

        if (surah == null) {
            respond(emptyList(), "I couldn't match \"${intent.surahQuery}\" to a Surah name. Try the transliterated name, e.g. \"Al-Kahf\".")
            return
        }

        val matches = library.filter { it.surahNumber == surah.number && it.isPrimaryVersion }
            .sortedBy { it.ayahStart }
            .map { AssistantResultItem(it.id, it.title, "Ayah ${it.ayahStart}-${it.ayahEnd} · ${qualityLabel(it.studioReadinessScore)}") }

        val message = if (matches.isEmpty()) {
            "No recordings yet for Surah ${surah.transliteratedName}."
        } else {
            "Found ${matches.size} recording(s) for Surah ${surah.transliteratedName}."
        }
        respond(matches, message)
    }

    private fun handleFindByKeyword(intent: AssistantIntent.FindByKeyword) {
        val keyword = intent.keyword
        val titleMatches = library.filter {
            it.title.contains(keyword, ignoreCase = true) || it.notes?.contains(keyword, ignoreCase = true) == true
        }
        val transcriptMatches = TranscriptSearchEngine.search(transcripts, keyword)
            .mapNotNull { result -> library.firstOrNull { it.id == result.recordingId } }

        val combined = (titleMatches + transcriptMatches).distinctBy { it.id }
            .map { AssistantResultItem(it.id, it.title, "Recorded ${formatDate(it.createdAtEpochMs)}") }

        val message = if (combined.isEmpty()) {
            "Nothing in your library mentions \"$keyword\" — checked titles, notes, and saved transcripts."
        } else {
            "Found ${combined.size} recording(s) mentioning \"$keyword\"."
        }
        respond(combined, message)
    }

    private fun handleReadCurrentTranscript() {
        val state = _uiState.value
        val targetId = state.selectedRecordingId
            ?: state.results.firstOrNull()?.recordingId
            ?: transcripts.maxByOrNull { it.segments.lastOrNull()?.endMs ?: 0L }?.recordingId

        if (targetId == null) {
            respond(state.results, "No transcript is selected to read. Search for a recording first, then try again.")
            return
        }

        val transcript = transcripts.firstOrNull { it.recordingId == targetId }
        val recording = library.firstOrNull { it.id == targetId }
        if (transcript == null || transcript.fullText.isBlank()) {
            respond(state.results, "\"${recording?.title ?: "That recording"}\" has no saved transcript yet.")
            return
        }

        val started = ttsManager.speak(transcript.fullText, transcript.language)
        val message = if (started) {
            "Reading the transcript for \"${recording?.title ?: "recording #$targetId"}\"."
        } else {
            "No offline voice is available for ${transcript.language.displayName} — check Speech & Language Packs in Settings."
        }
        respond(state.results, message, selectedRecordingId = targetId)
    }

    private fun handleFilterByQuality(intent: AssistantIntent.FilterByQuality) {
        val scored = library.filter { it.studioReadinessScore != null }
        val filtered = when (intent.comparison) {
            QualityComparison.BELOW -> scored.filter { it.studioReadinessScore!! < intent.threshold }.sortedBy { it.studioReadinessScore }
            QualityComparison.ABOVE -> scored.filter { it.studioReadinessScore!! >= intent.threshold }.sortedByDescending { it.studioReadinessScore }
        }
        val matches = filtered.map { AssistantResultItem(it.id, it.title, qualityLabel(it.studioReadinessScore)) }

        val comparisonWord = if (intent.comparison == QualityComparison.BELOW) "below" else "at or above"
        val message = if (matches.isEmpty()) {
            "Nothing scored $comparisonWord ${intent.threshold}/100 yet."
        } else {
            "${matches.size} recording(s) scored $comparisonWord ${intent.threshold}/100."
        }
        respond(matches, message)
    }

    private fun handleUnrecognized() {
        respond(
            emptyList(),
            "That doesn't match a request I understand yet. Try things like: ${EXAMPLE_COMMANDS.joinToString(", ")}.",
        )
    }

    private fun respond(results: List<AssistantResultItem>, message: String, selectedRecordingId: Long? = _uiState.value.selectedRecordingId) {
        _uiState.value = _uiState.value.copy(results = results, responseMessage = message, selectedRecordingId = selectedRecordingId)
    }

    private fun qualityLabel(score: Int?): String = score?.let { "Quality: $it/100" } ?: "Not yet scored"

    private fun formatDate(epochMs: Long): String {
        val date = java.text.SimpleDateFormat("MMM d, yyyy", java.util.Locale.getDefault())
        return date.format(java.util.Date(epochMs))
    }

    override fun onCleared() {
        super.onCleared()
        recognizer?.stop()
        ttsManager.shutdown()
    }
}
