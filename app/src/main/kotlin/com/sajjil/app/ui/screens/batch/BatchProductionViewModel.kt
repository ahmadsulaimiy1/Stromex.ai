package com.sajjil.app.ui.screens.batch

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.sajjil.app.data.db.RecordingEntity
import com.sajjil.app.di.asSajjilApplication
import com.sajjil.core.batch.BatchItemResult
import com.sajjil.core.batch.BatchJobItem
import com.sajjil.core.batch.BatchProcessor
import com.sajjil.core.modes.VoiceProfile
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File

data class BatchProductionUiState(
    val library: List<RecordingEntity> = emptyList(),
    val selectedIds: Set<Long> = emptySet(),
    val profile: VoiceProfile = VoiceProfile.HARAMAIN_BROADCAST,
    val isRunning: Boolean = false,
    val completed: Int = 0,
    val total: Int = 0,
    val results: List<BatchItemResult> = emptyList(),
)

/** SAJJIL Batch Qur'an Production: master an entire Surah/Juz/library selection in one pass. */
class BatchProductionViewModel(application: Application) : AndroidViewModel(application) {
    private val app = application.asSajjilApplication()

    private val _uiState = MutableStateFlow(BatchProductionUiState())
    val uiState: StateFlow<BatchProductionUiState> = _uiState.asStateFlow()

    init {
        viewModelScope.launch {
            app.recordingRepository.observeQuranLibrary().collect { list ->
                _uiState.value = _uiState.value.copy(library = list.sortedWith(compareBy({ it.surahNumber }, { it.ayahStart })))
            }
        }
    }

    fun toggleSelected(id: Long) {
        val current = _uiState.value.selectedIds
        _uiState.value = _uiState.value.copy(selectedIds = if (id in current) current - id else current + id)
    }

    fun selectAll() {
        _uiState.value = _uiState.value.copy(selectedIds = _uiState.value.library.map { it.id }.toSet())
    }

    fun clearSelection() {
        _uiState.value = _uiState.value.copy(selectedIds = emptySet())
    }

    fun selectProfile(profile: VoiceProfile) {
        _uiState.value = _uiState.value.copy(profile = profile)
    }

    fun runBatch() {
        val state = _uiState.value
        val selected = state.library.filter { it.id in state.selectedIds }
        if (selected.isEmpty() || state.isRunning) return

        _uiState.value = state.copy(isRunning = true, completed = 0, total = selected.size, results = emptyList())
        viewModelScope.launch {
            val outDir = File(getApplication<Application>().filesDir, "batch").apply { mkdirs() }
            val items = selected.map { recording ->
                BatchJobItem(
                    label = recording.title,
                    inputFile = File(recording.filePath),
                    outputFile = File(outDir, "batch_${recording.id}_${System.currentTimeMillis()}.wav"),
                )
            }
            val result = withContext(Dispatchers.Default) {
                BatchProcessor.run(items, state.profile.config) { itemResult ->
                    _uiState.value = _uiState.value.copy(
                        completed = _uiState.value.completed + 1,
                        results = _uiState.value.results + itemResult,
                    )
                }
            }
            _uiState.value = _uiState.value.copy(isRunning = false, results = result.results)
        }
    }
}
