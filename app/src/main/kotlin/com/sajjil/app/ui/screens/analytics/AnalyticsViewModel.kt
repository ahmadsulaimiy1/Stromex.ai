package com.sajjil.app.ui.screens.analytics

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.sajjil.app.di.asSajjilApplication
import com.sajjil.core.analysis.AnalyticsCalculator
import com.sajjil.core.analysis.ExecutiveAnalytics
import com.sajjil.core.analysis.RecordingSummary
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/** SAJJIL Executive Analytics: the library reduced to the numbers a production lead actually wants to see. */
class AnalyticsViewModel(application: Application) : AndroidViewModel(application) {
    private val app = application.asSajjilApplication()

    private val _analytics = MutableStateFlow<ExecutiveAnalytics?>(null)
    val analytics: StateFlow<ExecutiveAnalytics?> = _analytics.asStateFlow()

    init {
        viewModelScope.launch {
            app.recordingRepository.observeAll().collect { recordings ->
                val summaries = recordings.map { recording ->
                    RecordingSummary(
                        durationMs = recording.durationMs,
                        createdAtEpochMs = recording.createdAtEpochMs,
                        surahNumber = recording.surahNumber,
                        ayahStart = recording.ayahStart,
                        ayahEnd = recording.ayahEnd,
                        studioReadinessScore = recording.studioReadinessScore,
                        fileSizeBytes = recording.fileSizeBytes,
                    )
                }
                _analytics.value = AnalyticsCalculator.compute(summaries)
            }
        }
    }
}
