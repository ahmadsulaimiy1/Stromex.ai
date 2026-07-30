package com.sajjil.app

import android.app.Application
import com.sajjil.app.data.db.SajjilDatabase
import com.sajjil.app.data.repository.RecordingRepository
import com.sajjil.app.data.repository.SettingsRepository
import com.sajjil.core.plugin.BuiltinPlugins

class SajjilApplication : Application() {
    lateinit var recordingRepository: RecordingRepository
        private set
    lateinit var settingsRepository: SettingsRepository
        private set

    override fun onCreate() {
        super.onCreate()
        val database = SajjilDatabase.getInstance(this)
        recordingRepository = RecordingRepository(database.recordingDao())
        settingsRepository = SettingsRepository(this)
        BuiltinPlugins.registerAll()
    }
}
