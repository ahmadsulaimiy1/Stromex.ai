package com.sajjil.app.ui.screens.speechsettings

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.sajjil.app.speech.AndroidSpeechBridge
import com.sajjil.app.speech.SpeechCapabilityReport
import com.sajjil.app.speech.TTSManager
import com.sajjil.app.speech.VoiceInfo
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class SpeechCapabilityUiState(
    val report: SpeechCapabilityReport? = null,
    val voices: List<VoiceInfo> = emptyList(),
    val isRefreshing: Boolean = false,
)

/** Drives the "Speech & Language Packs" settings section: what's on this device right now, queried fresh each time. */
class SpeechCapabilityViewModel(application: Application) : AndroidViewModel(application) {
    private val bridge = AndroidSpeechBridge(application)

    private val _uiState = MutableStateFlow(SpeechCapabilityUiState())
    val uiState: StateFlow<SpeechCapabilityUiState> = _uiState.asStateFlow()

    init {
        refresh()
    }

    fun refresh() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isRefreshing = true)
            val report = bridge.detect()
            val ttsManager = TTSManager(getApplication())
            val ready = ttsManager.initialize()
            val voices = if (ready) ttsManager.voiceCatalog() else emptyList()
            ttsManager.shutdown()
            _uiState.value = _uiState.value.copy(report = report, voices = voices, isRefreshing = false)
        }
    }
}
