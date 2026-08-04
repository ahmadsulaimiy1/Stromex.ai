package ai.sajjil.app.ui.library

import ai.sajjil.app.Services
import ai.sajjil.app.data.LibrarySort
import ai.sajjil.app.data.RecordingEntity
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.FlowPreview
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.debounce
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

data class LibraryUiState(
    val recordings: List<RecordingEntity> = emptyList(),
    val transcribedIds: Set<Long> = emptySet(),
    val query: String = "",
    val sort: LibrarySort = LibrarySort.NEWEST,
    val totalCount: Int = 0,
    val totalBytes: Long = 0,
    val totalDurationMs: Long = 0,
    val isLoading: Boolean = true,
)

@OptIn(ExperimentalCoroutinesApi::class, FlowPreview::class)
class LibraryViewModel(private val services: Services) : ViewModel() {

    private val repository = services.repository

    private val query = MutableStateFlow("")
    private val sort = MutableStateFlow(LibrarySort.NEWEST)

    private val listings = combine(query.debounce(200), sort) { text, order -> text to order }
        .flatMapLatest { (text, order) ->
            if (text.isBlank()) repository.observe(order) else repository.search(text.trim())
        }

    val state: StateFlow<LibraryUiState> = combine(
        listings,
        repository.observeTranscribedIds(),
        repository.observeCount(),
        repository.observeTotalBytes(),
        repository.observeTotalDurationMs(),
    ) { recordings, transcribed, count, bytes, duration ->
        LibraryUiState(
            recordings = recordings,
            transcribedIds = transcribed.toSet(),
            query = query.value,
            sort = sort.value,
            totalCount = count,
            totalBytes = bytes,
            totalDurationMs = duration,
            isLoading = false,
        )
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), LibraryUiState())

    init {
        viewModelScope.launch {
            sort.value = services.settings.settings.first().sort
        }
    }

    fun setQuery(text: String) {
        query.value = text
    }

    fun setSort(order: LibrarySort) {
        sort.value = order
        viewModelScope.launch { services.settings.setLibrarySort(order.name) }
    }

    fun toggleFavourite(recording: RecordingEntity) {
        viewModelScope.launch { repository.setFavourite(recording, !recording.isFavourite) }
    }

    fun rename(recording: RecordingEntity, title: String) {
        viewModelScope.launch { repository.rename(recording, title) }
    }

    fun delete(recording: RecordingEntity) {
        viewModelScope.launch { repository.delete(recording) }
    }

    /** Play from the card, without opening the recording first. */
    fun togglePlayback(recording: RecordingEntity) {
        val playback = services.playback
        if (playback.state.value.recordingId == recording.id) {
            playback.togglePlayPause()
        } else {
            playback.play(
                recordingId = recording.id,
                file = repository.fileFor(recording),
                title = recording.title,
            )
        }
    }

    class Factory(private val services: Services) : ViewModelProvider.Factory {
        @Suppress("UNCHECKED_CAST")
        override fun <T : ViewModel> create(modelClass: Class<T>): T =
            LibraryViewModel(services) as T
    }
}
