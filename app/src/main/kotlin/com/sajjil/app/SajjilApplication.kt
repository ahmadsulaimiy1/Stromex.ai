package com.sajjil.app

import android.app.Application
import com.sajjil.app.audio.AudioPlaybackEngine
import com.sajjil.app.data.db.SajjilDatabase
import com.sajjil.app.data.repository.RecordingRepository
import com.sajjil.app.data.repository.SettingsRepository
import com.sajjil.app.data.repository.TranscriptRepository
import com.sajjil.core.plugin.BuiltinPlugins
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob

class SajjilApplication : Application() {
    lateinit var recordingRepository: RecordingRepository
        private set
    lateinit var settingsRepository: SettingsRepository
        private set
    lateinit var transcriptRepository: TranscriptRepository
        private set

    /**
     * Process-lifetime scope for playback that must survive navigating away from whichever
     * screen started it (a mini-player that stops the moment you leave the Library isn't a
     * mini-player). Deliberately NOT a ViewModel's viewModelScope, which is cancelled on
     * screen exit.
     */
    private val appScope = CoroutineScope(SupervisorJob() + Dispatchers.Main)

    /** Single shared player so "what's playing" is one truth, visible from any screen's mini-player. */
    lateinit var playbackEngine: AudioPlaybackEngine
        private set

    override fun onCreate() {
        super.onCreate()
        val database = SajjilDatabase.getInstance(this)
        recordingRepository = RecordingRepository(database.recordingDao())
        settingsRepository = SettingsRepository(this)
        transcriptRepository = TranscriptRepository(database.transcriptDao())
        playbackEngine = AudioPlaybackEngine()
        BuiltinPlugins.registerAll()
    }

    fun playbackScope(): CoroutineScope = appScope
}
