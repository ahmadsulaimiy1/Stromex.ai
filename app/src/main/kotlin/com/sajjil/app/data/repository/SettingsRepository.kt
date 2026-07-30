package com.sajjil.app.data.repository

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.sajjil.app.ui.theme.SajjilTheme
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.settingsDataStore by preferencesDataStore(name = "sajjil_settings")

/** Persists lightweight app-wide preferences: theme, quality defaults, last used mode. */
class SettingsRepository(private val context: Context) {
    private object Keys {
        val theme = stringPreferencesKey("theme")
        val defaultRecordingMode = stringPreferencesKey("default_recording_mode")
        val defaultQualityLevel = stringPreferencesKey("default_quality_level")
    }

    val theme: Flow<SajjilTheme> = context.settingsDataStore.data.map { prefs ->
        prefs[Keys.theme]?.let { name -> runCatching { SajjilTheme.valueOf(name) }.getOrNull() }
            ?: SajjilTheme.ROYAL_GOLD
    }

    suspend fun setTheme(theme: SajjilTheme) {
        context.settingsDataStore.edit { it[Keys.theme] = theme.name }
    }

    val defaultRecordingMode: Flow<String?> = context.settingsDataStore.data.map { it[Keys.defaultRecordingMode] }

    suspend fun setDefaultRecordingMode(modeName: String) {
        context.settingsDataStore.edit { it[Keys.defaultRecordingMode] = modeName }
    }

    val defaultQualityLevel: Flow<String?> = context.settingsDataStore.data.map { it[Keys.defaultQualityLevel] }

    suspend fun setDefaultQualityLevel(level: String) {
        context.settingsDataStore.edit { it[Keys.defaultQualityLevel] = level }
    }
}
