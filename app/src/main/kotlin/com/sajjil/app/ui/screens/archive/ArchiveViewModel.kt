package com.sajjil.app.ui.screens.archive

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.sajjil.app.audio.AudioPlaybackEngine
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

    /** One shared player for the whole Library: at most one recording plays at a time, matched by file path. */
    val playback = AudioPlaybackEngine()
    val isPlaying: StateFlow<Boolean> = playback.isPlaying
    val positionMs: StateFlow<Long> = playback.positionMs
    val durationMs: StateFlow<Long> = playback.durationMs
    val playingFile: StateFlow<File?> = playback.playingFile

    private val query = MutableStateFlow("")
    val searchQuery: StateFlow<String> = query

    val recordings: StateFlow<List<RecordingEntity>> = query
        .flatMapLatest { q -> if (q.isBlank()) app.recordingRepository.observeAll() else app.recordingRepository.search(q) }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    fun onQueryChange(newQuery: String) {
        query.value = newQuery
    }

    /** Tap-to-play, tap-again-to-pause, on the same card that was already loaded. */
    fun togglePlay(recording: RecordingEntity) {
        val file = File(recording.filePath)
        if (playingFile.value == file) {
            if (isPlaying.value) playback.pause() else playback.resume(viewModelScope)
        } else {
            playback.play(file, viewModelScope)
        }
    }

    fun seekTo(ms: Long) {
        playback.seekTo(ms)
    }

    fun toggleFavorite(recording: RecordingEntity) {
        viewModelScope.launch { app.recordingRepository.update(recording.copy(isFavorite = !recording.isFavorite)) }
    }

    fun delete(recording: RecordingEntity) {
        if (playingFile.value == File(recording.filePath)) playback.stop()
        viewModelScope.launch {
            app.recordingRepository.delete(recording)
            runCatching { File(recording.filePath).delete() }
        }
    }

    override fun onCleared() {
        super.onCleared()
        playback.stop()
    }
}
