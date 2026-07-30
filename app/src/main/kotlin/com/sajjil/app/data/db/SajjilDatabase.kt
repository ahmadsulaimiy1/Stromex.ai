package com.sajjil.app.data.db

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase

@Database(entities = [RecordingEntity::class, TranscriptSegmentEntity::class], version = 3, exportSchema = true)
abstract class SajjilDatabase : RoomDatabase() {
    abstract fun recordingDao(): RecordingDao
    abstract fun transcriptDao(): TranscriptDao

    companion object {
        @Volatile private var instance: SajjilDatabase? = null

        fun getInstance(context: Context): SajjilDatabase =
            instance ?: synchronized(this) {
                instance ?: Room.databaseBuilder(
                    context.applicationContext,
                    SajjilDatabase::class.java,
                    "sajjil.db",
                )
                    // Pre-release schema: no shipped installs to preserve yet, so a destructive
                    // fallback is the right tradeoff over hand-written migrations for now.
                    .fallbackToDestructiveMigration()
                    .build()
                    .also { instance = it }
            }
    }
}
