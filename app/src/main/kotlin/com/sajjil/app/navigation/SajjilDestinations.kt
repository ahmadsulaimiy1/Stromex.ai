package com.sajjil.app.navigation

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AutoFixHigh
import androidx.compose.material.icons.filled.Equalizer
import androidx.compose.material.icons.filled.LibraryMusic
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.MenuBook
import androidx.compose.ui.graphics.vector.ImageVector

sealed class SajjilDestination(val route: String, val label: String, val icon: ImageVector) {
    data object Record : SajjilDestination("record", "Record", Icons.Filled.Mic)
    data object Enhance : SajjilDestination("enhance", "Enhance", Icons.Filled.AutoFixHigh)
    data object Master : SajjilDestination("master", "Master", Icons.Filled.Equalizer)
    data object Archive : SajjilDestination("archive", "Archive", Icons.Filled.LibraryMusic)
    data object QuranStudio : SajjilDestination("quran_studio", "Qur'an Studio", Icons.Filled.MenuBook)

    companion object {
        val bottomNavItems = listOf(Record, Enhance, Master, Archive, QuranStudio)
    }
}

object SajjilRoutes {
    const val SETTINGS = "settings"
    const val BATCH_PRODUCTION = "batch_production"
    const val ANALYTICS = "analytics"
    const val COMPARISON_LAB = "comparison_lab"
    const val VOICE_STUDIO = "voice_studio"
    const val SPEECH_CAPABILITY = "speech_capability"
    const val PRODUCTION_READINESS = "production_readiness"
    const val DASHBOARD = "dashboard/{recordingId}"
    const val QURAN_PROJECT = "quran_project/{surahNumber}"
    fun dashboard(recordingId: Long) = "dashboard/$recordingId"
    fun quranProject(surahNumber: Int) = "quran_project/$surahNumber"
}
