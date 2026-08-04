package ai.sajjil.app.ui.assistant

import ai.sajjil.app.Services
import ai.sajjil.app.data.LibrarySort
import ai.sajjil.app.data.RecordingEntity
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn

data class Suggestion(val title: String, val body: String)

data class AssistantUiState(
    val recordingCount: Int = 0,
    val totalDurationMs: Long = 0,
    val totalBytes: Long = 0,
    val averageQuality: Int? = null,
    val averageGrade: String? = null,
    val suggestions: List<Suggestion> = emptyList(),
)

/**
 * Turns the library's measurements into advice.
 *
 * Every suggestion is derived from numbers the app has already measured — quality scores and
 * integrated loudness — so each one can be justified from the data rather than being generic
 * recording advice that happens to be printed on a screen.
 */
class AssistantViewModel(services: Services) : ViewModel() {

    private val repository = services.repository

    val state: StateFlow<AssistantUiState> = combine(
        repository.observe(LibrarySort.NEWEST),
        repository.observeTotalBytes(),
        repository.observeTotalDurationMs(),
    ) { recordings, bytes, duration ->
        val scored = recordings.mapNotNull { it.qualityScore }
        val average = if (scored.isEmpty()) null else scored.average().toInt()

        AssistantUiState(
            recordingCount = recordings.size,
            totalDurationMs = duration,
            totalBytes = bytes,
            averageQuality = average,
            averageGrade = average?.let(::gradeFor),
            suggestions = suggestionsFor(recordings, average),
        )
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), AssistantUiState())

    private fun gradeFor(score: Int): String = when {
        score >= 85 -> "Excellent"
        score >= 70 -> "Good"
        score >= 55 -> "Usable"
        else -> "Needs work"
    }

    private fun suggestionsFor(
        recordings: List<RecordingEntity>,
        averageQuality: Int?,
    ): List<Suggestion> {
        if (recordings.isEmpty()) return emptyList()
        val suggestions = mutableListOf<Suggestion>()

        val scored = recordings.mapNotNull { it.qualityScore }
        val poor = scored.count { it < 60 }
        if (poor > 0 && poor.toDouble() / scored.size > 0.3) {
            suggestions += Suggestion(
                "Several recordings are scoring low",
                "$poor of ${scored.size} scored below 60. Running Studio Voice over them will " +
                    "clean up most of what is dragging the score down.",
            )
        }

        val loudnessValues = recordings.mapNotNull { it.loudnessLufs }
        if (loudnessValues.size >= 3) {
            val averageLoudness = loudnessValues.average()
            if (averageLoudness < -28) {
                suggestions += Suggestion(
                    "Your recordings are consistently quiet",
                    "They average ${String.format(java.util.Locale.US, "%.1f", averageLoudness)} LUFS. " +
                        "Recording a little closer to the microphone leaves far more headroom than " +
                        "raising the level afterwards does.",
                )
            } else if (averageLoudness > -12) {
                suggestions += Suggestion(
                    "Your input level is running hot",
                    "They average ${String.format(java.util.Locale.US, "%.1f", averageLoudness)} LUFS, " +
                        "which leaves little room before distortion. Moving back slightly will help.",
                )
            }
        }

        val untitled = recordings.count { it.title.startsWith("Recording ") }
        if (untitled >= 10) {
            suggestions += Suggestion(
                "$untitled recordings still have their default names",
                "Renaming them makes search useful — SAJJIL searches titles, tags, notes and " +
                    "transcripts together.",
            )
        }

        if (averageQuality != null && averageQuality >= 85 && suggestions.isEmpty()) {
            suggestions += Suggestion(
                "Your recording setup is working well",
                "An average of $averageQuality across ${scored.size} recordings is a strong result. " +
                    "Whatever you are doing, keep doing it.",
            )
        }

        return suggestions
    }

    class Factory(private val services: Services) : ViewModelProvider.Factory {
        @Suppress("UNCHECKED_CAST")
        override fun <T : ViewModel> create(modelClass: Class<T>): T =
            AssistantViewModel(services) as T
    }
}
