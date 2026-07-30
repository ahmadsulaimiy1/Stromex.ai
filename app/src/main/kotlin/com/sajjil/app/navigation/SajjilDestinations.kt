package com.sajjil.app.navigation

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AutoFixHigh
import androidx.compose.material.icons.filled.LibraryMusic
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.MenuBook
import androidx.compose.ui.graphics.vector.ImageVector

sealed class SajjilDestination(val route: String, val label: String, val icon: ImageVector) {
    data object Record : SajjilDestination("record", "Record", Icons.Filled.Mic)

    // Formerly two separate destinations (Enhance, Master) with two disconnected "Select a
    // recording" flows -- merged into one Studio workspace with Enhance/Master as tabs that
    // share a single selection (see StudioScreen).
    data object Studio : SajjilDestination("studio", "Studio", Icons.Filled.AutoFixHigh)
    data object Archive : SajjilDestination("archive", "Library", Icons.Filled.LibraryMusic)
    data object QuranStudio : SajjilDestination("quran_studio", "Qur'an Studio", Icons.Filled.MenuBook)

    companion object {
        val bottomNavItems = listOf(Record, Studio, Archive, QuranStudio)
    }
}

object SajjilRoutes {
    const val SETTINGS = "settings"
    const val ABOUT = "about"
    const val BATCH_PRODUCTION = "batch_production"
    const val ANALYTICS = "analytics"
    const val COMPARISON_LAB = "comparison_lab"
    const val VOICE_STUDIO = "voice_studio"
    const val ASSISTANT = "assistant?recordingId={recordingId}&surahNumber={surahNumber}"
    const val SPEECH_CAPABILITY = "speech_capability"
    const val PRODUCTION_READINESS = "production_readiness"
    const val DASHBOARD = "dashboard/{recordingId}"
    const val QURAN_PROJECT = "quran_project/{surahNumber}"
    const val EDITOR = "editor/{recordingId}"
    fun dashboard(recordingId: Long) = "dashboard/$recordingId"
    fun quranProject(surahNumber: Int) = "quran_project/$surahNumber"
    fun editor(recordingId: Long) = "editor/$recordingId"

    /** Project-memory: opens the Assistant already aware of a recording and/or Surah, so "read this transcript" or a Surah-scoped question doesn't need re-stating context. */
    fun assistant(recordingId: Long? = null, surahNumber: Int? = null) =
        "assistant?recordingId=${recordingId ?: -1}&surahNumber=${surahNumber ?: -1}"
}
