package com.sajjil.app.ui.screens.comparison

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.sajjil.app.audio.ComparisonPlayer
import com.sajjil.app.data.db.RecordingEntity
import com.sajjil.app.di.asSajjilApplication
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.io.File

data class ComparisonLabUiState(
    val library: List<RecordingEntity> = emptyList(),
    /** Up to 3 slots — Original / Enhanced / Mastered by default, but any recording can fill any slot. */
    val slots: Map<String, RecordingEntity?> = linkedMapOf("A" to null, "B" to null, "C" to null),
)

/** SAJJIL Audio Comparison Laboratory: instant-switch A/B/C listening between takes. */
class ComparisonLabViewModel(application: Application) : AndroidViewModel(application) {
    private val app = application.asSajjilApplication()
    val player = ComparisonPlayer()

    private val _uiState = MutableStateFlow(ComparisonLabUiState())
    val uiState: StateFlow<ComparisonLabUiState> = _uiState.asStateFlow()

    init {
        viewModelScope.launch {
            app.recordingRepository.observeAll().collect { list ->
                _uiState.value = _uiState.value.copy(library = list)
            }
        }
    }

    fun assignSlot(slot: String, recording: RecordingEntity?) {
        _uiState.value = _uiState.value.copy(slots = _uiState.value.slots + (slot to recording))
    }

    fun play(slot: String) {
        val recording = _uiState.value.slots[slot] ?: return
        val file = File(recording.filePath)
        if (player.activeSlot.value == null) {
            player.playFromStart(slot, file, viewModelScope)
        } else {
            player.switchTo(slot, file, viewModelScope)
        }
    }

    fun stop() = player.stop()

    override fun onCleared() {
        super.onCleared()
        player.stop()
    }
}
