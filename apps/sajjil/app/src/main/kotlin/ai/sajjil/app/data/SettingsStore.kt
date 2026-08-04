package ai.sajjil.app.data

import ai.sajjil.app.audio.ExportFormat
import ai.sajjil.app.audio.ExportQuality
import android.content.Context
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.intPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.dataStore by preferencesDataStore(name = "sajjil_settings")

/** Everything the app remembers between launches, other than the recordings themselves. */
data class SajjilSettings(
    val sampleRate: Int = 48000,
    val channelCount: Int = 1,
    /** Whether to let the platform's own noise suppression and AGC run during capture. */
    val usePlatformProcessing: Boolean = false,
    val defaultExportFormatId: String = ExportFormat.M4A.id,
    val defaultExportQuality: String = ExportQuality.DEFAULT.name,
    val librarySort: String = LibrarySort.NEWEST.name,
    /**
     * Whether the Studio's advanced controls are open.
     *
     * Remembered because progressive disclosure only works if it is not re-imposed on someone
     * who has already asked for the detail once.
     */
    val studioAdvancedOpen: Boolean = false,
    val keepScreenOnWhileRecording: Boolean = true,
) {
    val exportFormat: ExportFormat
        get() = ExportFormat.byId(defaultExportFormatId) ?: ExportFormat.M4A

    val exportQuality: ExportQuality
        get() = runCatching { ExportQuality.valueOf(defaultExportQuality) }
            .getOrDefault(ExportQuality.DEFAULT)

    val sort: LibrarySort
        get() = runCatching { LibrarySort.valueOf(librarySort) }.getOrDefault(LibrarySort.NEWEST)
}

class SettingsStore(private val context: Context) {

    val settings: Flow<SajjilSettings> = context.dataStore.data.map { preferences ->
        SajjilSettings(
            sampleRate = preferences[Keys.SAMPLE_RATE] ?: 48000,
            channelCount = preferences[Keys.CHANNEL_COUNT] ?: 1,
            usePlatformProcessing = preferences[Keys.PLATFORM_PROCESSING] ?: false,
            defaultExportFormatId = preferences[Keys.EXPORT_FORMAT] ?: ExportFormat.M4A.id,
            defaultExportQuality = preferences[Keys.EXPORT_QUALITY] ?: ExportQuality.DEFAULT.name,
            librarySort = preferences[Keys.LIBRARY_SORT] ?: LibrarySort.NEWEST.name,
            studioAdvancedOpen = preferences[Keys.STUDIO_ADVANCED] ?: false,
            keepScreenOnWhileRecording = preferences[Keys.KEEP_SCREEN_ON] ?: true,
        )
    }

    suspend fun setSampleRate(value: Int) = put(Keys.SAMPLE_RATE, value)
    suspend fun setChannelCount(value: Int) = put(Keys.CHANNEL_COUNT, value)
    suspend fun setPlatformProcessing(value: Boolean) = put(Keys.PLATFORM_PROCESSING, value)
    suspend fun setExportFormat(value: String) = put(Keys.EXPORT_FORMAT, value)
    suspend fun setExportQuality(value: String) = put(Keys.EXPORT_QUALITY, value)
    suspend fun setLibrarySort(value: String) = put(Keys.LIBRARY_SORT, value)
    suspend fun setStudioAdvancedOpen(value: Boolean) = put(Keys.STUDIO_ADVANCED, value)
    suspend fun setKeepScreenOn(value: Boolean) = put(Keys.KEEP_SCREEN_ON, value)

    private suspend fun <T> put(key: Preferences.Key<T>, value: T) {
        context.dataStore.edit { it[key] = value }
    }

    private object Keys {
        val SAMPLE_RATE = intPreferencesKey("sample_rate")
        val CHANNEL_COUNT = intPreferencesKey("channel_count")
        val PLATFORM_PROCESSING = booleanPreferencesKey("platform_processing")
        val EXPORT_FORMAT = stringPreferencesKey("export_format")
        val EXPORT_QUALITY = stringPreferencesKey("export_quality")
        val LIBRARY_SORT = stringPreferencesKey("library_sort")
        val STUDIO_ADVANCED = booleanPreferencesKey("studio_advanced")
        val KEEP_SCREEN_ON = booleanPreferencesKey("keep_screen_on")
    }
}
