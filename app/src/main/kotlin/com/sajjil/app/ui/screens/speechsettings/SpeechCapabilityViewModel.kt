package com.sajjil.app.ui.screens.speechsettings

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.sajjil.app.speech.AndroidSpeechBridge
import com.sajjil.app.speech.SpeechCapabilityReport
import com.sajjil.app.speech.TTSManager
import com.sajjil.app.speech.VoiceInfo
import com.sajjil.core.speechpack.SpeechPackCatalog
import com.sajjil.core.speechpack.SpeechPackDescriptor
import com.sajjil.core.speechpack.SpeechPackEvent
import com.sajjil.core.speechpack.SpeechPackStateMachine
import com.sajjil.core.speechpack.SpeechPackStatus
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class SpeechCapabilityUiState(
    val report: SpeechCapabilityReport? = null,
    val voices: List<VoiceInfo> = emptyList(),
    val isRefreshing: Boolean = false,
    val packs: List<Pair<SpeechPackDescriptor, SpeechPackStatus>> = emptyList(),
)

/** Drives the "Speech & Language Packs" settings section: what's on this device right now, queried fresh each time. */
class SpeechCapabilityViewModel(application: Application) : AndroidViewModel(application) {
    private val bridge = AndroidSpeechBridge(application)

    private val _uiState = MutableStateFlow(
        SpeechCapabilityUiState(
            // No real model source exists to download from in this build (see
            // docs/SPEECH_INTELLIGENCE.md) — every pack is driven straight to UNAVAILABLE
            // through the same state machine a real download implementation would use, rather
            // than showing a "Download" button that would silently do nothing.
            packs = SpeechPackCatalog.packs.map {
                it to SpeechPackStateMachine.reduce(SpeechPackStatus.initial, SpeechPackEvent.MarkedUnavailable)
            },
        ),
    )
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
