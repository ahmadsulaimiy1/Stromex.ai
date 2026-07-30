package com.sajjil.app.ui.screens.quranproject

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.sajjil.app.data.db.RecordingEntity
import com.sajjil.app.di.asSajjilApplication
import com.sajjil.core.quran.AyahRange
import com.sajjil.core.quran.QuranMetadata
import com.sajjil.core.quran.RecordedTake
import com.sajjil.core.quran.SurahInfo
import com.sajjil.core.quran.SurahProgress
import com.sajjil.core.quran.SurahProgressCalculator
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class QuranProjectUiState(
    val surah: SurahInfo? = null,
    val progress: SurahProgress? = null,
    /** All takes for this Surah, keyed by the exact ayah range they cover — includes alternate (non-primary) versions. */
    val versionGroups: List<Pair<AyahRange, List<RecordingEntity>>> = emptyList(),
)

/** SAJJIL Qur'an Production Suite: per-Surah progress, missing ayahs, and take-version management. */
class QuranProjectViewModel(application: Application) : AndroidViewModel(application) {
    private val app = application.asSajjilApplication()

    private val _uiState = MutableStateFlow(QuranProjectUiState())
    val uiState: StateFlow<QuranProjectUiState> = _uiState.asStateFlow()

    fun load(surahNumber: Int) {
        val surah = QuranMetadata.surahByNumber(surahNumber)
        viewModelScope.launch {
            app.recordingRepository.observeForSurah(surahNumber).collect { recordings ->
                val tagged = recordings.filter { it.ayahStart != null && it.ayahEnd != null }
                val primaryTakes = tagged.filter { it.isPrimaryVersion }
                    .map { RecordedTake(AyahRange(it.ayahStart!!, it.ayahEnd!!), it.studioReadinessScore) }
                val progress = SurahProgressCalculator.compute(surah, primaryTakes)

                val groups = tagged
                    .groupBy { AyahRange(it.ayahStart!!, it.ayahEnd!!) }
                    .toList()
                    .sortedBy { it.first.start }

                _uiState.value = QuranProjectUiState(surah, progress, groups)
            }
        }
    }

    fun setPrimaryVersion(range: AyahRange, chosen: RecordingEntity) {
        val group = _uiState.value.versionGroups.firstOrNull { it.first == range }?.second ?: return
        viewModelScope.launch {
            for (recording in group) {
                val shouldBePrimary = recording.id == chosen.id
                if (recording.isPrimaryVersion != shouldBePrimary) {
                    app.recordingRepository.update(recording.copy(isPrimaryVersion = shouldBePrimary))
                }
            }
        }
    }

    fun updateNotes(recording: RecordingEntity, notes: String) {
        viewModelScope.launch { app.recordingRepository.update(recording.copy(notes = notes.ifBlank { null })) }
    }
}
