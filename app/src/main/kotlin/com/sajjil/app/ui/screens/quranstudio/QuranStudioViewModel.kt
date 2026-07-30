package com.sajjil.app.ui.screens.quranstudio

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.sajjil.app.data.db.RecordingEntity
import com.sajjil.app.di.asSajjilApplication
import com.sajjil.core.quran.QuranMetadata
import com.sajjil.core.quran.SurahInfo
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class QuranStudioUiState(
    val untaggedRecordings: List<RecordingEntity> = emptyList(),
    val library: List<RecordingEntity> = emptyList(),
    val selectedRecording: RecordingEntity? = null,
    val selectedSurah: SurahInfo = QuranMetadata.surahs.first(),
    val ayahStart: Int = 1,
    val ayahEnd: Int = 1,
)

class QuranStudioViewModel(application: Application) : AndroidViewModel(application) {
    private val app = application.asSajjilApplication()

    private val _uiState = MutableStateFlow(QuranStudioUiState())
    val uiState: StateFlow<QuranStudioUiState> = _uiState.asStateFlow()

    init {
        viewModelScope.launch {
            app.recordingRepository.observeAll().collect { all ->
                _uiState.value = _uiState.value.copy(
                    untaggedRecordings = all.filter { it.surahNumber == null },
                    library = all.filter { it.surahNumber != null },
                )
            }
        }
    }

    fun selectRecording(recording: RecordingEntity) {
        _uiState.value = _uiState.value.copy(selectedRecording = recording)
    }

    fun selectSurah(surah: SurahInfo) {
        _uiState.value = _uiState.value.copy(selectedSurah = surah, ayahStart = 1, ayahEnd = 1)
    }

    fun setAyahRange(start: Int, end: Int) {
        val surah = _uiState.value.selectedSurah
        _uiState.value = _uiState.value.copy(
            ayahStart = start.coerceIn(1, surah.ayahCount),
            ayahEnd = end.coerceIn(start, surah.ayahCount),
        )
    }

    fun tagSelected() {
        val state = _uiState.value
        val recording = state.selectedRecording ?: return
        val juz = QuranMetadata.juzForSurahAyah(state.selectedSurah.number, state.ayahStart)
        viewModelScope.launch {
            app.recordingRepository.update(
                recording.copy(
                    surahNumber = state.selectedSurah.number,
                    ayahStart = state.ayahStart,
                    ayahEnd = state.ayahEnd,
                    juz = juz,
                ),
            )
            _uiState.value = state.copy(selectedRecording = null)
        }
    }
}
