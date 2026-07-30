package com.sajjil.app.data.db

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase

@Database(entities = [RecordingEntity::class], version = 1, exportSchema = true)
abstract class SajjilDatabase : RoomDatabase() {
    abstract fun recordingDao(): RecordingDao

    companion object {
        @Volatile private var instance: SajjilDatabase? = null

        fun getInstance(context: Context): SajjilDatabase =
            instance ?: synchronized(this) {
                instance ?: Room.databaseBuilder(
                    context.applicationContext,
                    SajjilDatabase::class.java,
                    "sajjil.db",
                ).build().also { instance = it }
            }
    }
}
