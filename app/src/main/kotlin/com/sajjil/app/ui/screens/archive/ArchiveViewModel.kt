package com.sajjil.app.ui.screens.archive

import android.app.Application
import android.net.Uri
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.sajjil.app.data.db.RecordingEntity
import com.sajjil.app.di.asSajjilApplication
import com.sajjil.core.analysis.WaveformPeaks
import com.sajjil.core.audio.WavIO
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import java.io.File

@OptIn(ExperimentalCoroutinesApi::class)
class ArchiveViewModel(application: Application) : AndroidViewModel(application) {
    private val app = application.asSajjilApplication()

    /**
     * Uses the app-wide shared player (not a private instance) and the app-wide playback
     * scope (not viewModelScope) so tapping Play here and then navigating to another screen
     * keeps the recording playing -- the whole point of a mini-player. A ViewModel-scoped
     * player would have its position-tracking coroutine cancelled the moment this screen is
     * left, silently breaking the mini-player elsewhere in the app.
     */
    private val playback = app.playbackEngine
    private val playbackScope = app.playbackScope()
    val isPlaying: StateFlow<Boolean> = playback.isPlaying
    val positionMs: StateFlow<Long> = playback.positionMs
    val durationMs: StateFlow<Long> = playback.durationMs
    val playingFile: StateFlow<File?> = playback.playingFile

    /** Peak-amplitude bars for whichever recording is currently loaded; null while still decoding, or when nothing is loaded. */
    private val _waveformPeaks = MutableStateFlow<FloatArray?>(null)
    val waveformPeaks: StateFlow<FloatArray?> = _waveformPeaks.asStateFlow()
    private var waveformJob: Job? = null

    /** One-shot feedback for the "Save to device" action; the screen clears it after showing a toast. */
    private val _exportMessage = MutableStateFlow<String?>(null)
    val exportMessage: StateFlow<String?> = _exportMessage.asStateFlow()

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
            if (isPlaying.value) playback.pause() else playback.resume(playbackScope)
        } else {
            playback.play(file, playbackScope, label = recording.title)
            loadWaveform(file)
        }
    }

    fun seekTo(ms: Long) {
        playback.seekTo(ms)
    }

    /** Decodes the file once off the main thread and buckets it into peaks -- not something to redo on every recomposition. */
    private fun loadWaveform(file: File) {
        _waveformPeaks.value = null
        waveformJob?.cancel()
        waveformJob = viewModelScope.launch(Dispatchers.Default) {
            val peaks = runCatching {
                val audio = WavIO.read(file.readBytes())
                WaveformPeaks.compute(audio.samples, WAVEFORM_BUCKET_COUNT)
            }.getOrNull()
            _waveformPeaks.value = peaks
        }
    }

    fun toggleFavorite(recording: RecordingEntity) {
        viewModelScope.launch { app.recordingRepository.update(recording.copy(isFavorite = !recording.isFavorite)) }
    }

    /** Copies a recording's bytes to a Storage Access Framework destination the user picked -- internal storage, SD card, or any provider the system's document picker offers. */
    fun exportTo(destinationUri: Uri, recording: RecordingEntity) {
        viewModelScope.launch(Dispatchers.IO) {
            val success = runCatching {
                val context = getApplication<Application>()
                context.contentResolver.openOutputStream(destinationUri)?.use { out ->
                    File(recording.filePath).inputStream().use { input -> input.copyTo(out) }
                } ?: error("ContentResolver returned no output stream")
            }.isSuccess
            _exportMessage.value = if (success) {
                "Saved \"${recording.title}\""
            } else {
                "Couldn't save \"${recording.title}\" -- try again"
            }
        }
    }

    fun clearExportMessage() {
        _exportMessage.value = null
    }

    fun delete(recording: RecordingEntity) {
        if (playingFile.value == File(recording.filePath)) {
            playback.stop()
            waveformJob?.cancel()
            _waveformPeaks.value = null
        }
        viewModelScope.launch {
            app.recordingRepository.delete(recording)
            runCatching { File(recording.filePath).delete() }
        }
    }

    // No playback.stop() in onCleared(): the shared player is owned by the app, not this
    // screen, so leaving Library must not interrupt a recording that's still playing.

    private companion object {
        const val WAVEFORM_BUCKET_COUNT = 120
    }
}
