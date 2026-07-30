package com.sajjil.app.ui.screens.archive

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.sajjil.app.data.db.RecordingEntity
import com.sajjil.app.di.asSajjilApplication
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import java.io.File

@OptIn(ExperimentalCoroutinesApi::class)
class ArchiveViewModel(application: Application) : AndroidViewModel(application) {
    private val app = application.asSajjilApplication()

    private val query = MutableStateFlow("")
    val searchQuery: StateFlow<String> = query

    val recordings: StateFlow<List<RecordingEntity>> = query
        .flatMapLatest { q -> if (q.isBlank()) app.recordingRepository.observeAll() else app.recordingRepository.search(q) }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    fun onQueryChange(newQuery: String) {
        query.value = newQuery
    }

    fun toggleFavorite(recording: RecordingEntity) {
        viewModelScope.launch { app.recordingRepository.update(recording.copy(isFavorite = !recording.isFavorite)) }
    }

    fun delete(recording: RecordingEntity) {
        viewModelScope.launch {
            app.recordingRepository.delete(recording)
            runCatching { File(recording.filePath).delete() }
        }
    }
}
