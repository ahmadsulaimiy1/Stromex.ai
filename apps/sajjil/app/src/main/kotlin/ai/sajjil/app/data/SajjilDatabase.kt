package ai.sajjil.app.data

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase

@Database(
    entities = [
        RecordingEntity::class,
        FolderEntity::class,
        TranscriptEntity::class,
        QuranProjectEntity::class,
        QuranTakeEntity::class,
    ],
    version = 1,
    exportSchema = true,
)
abstract class SajjilDatabase : RoomDatabase() {

    abstract fun recordings(): RecordingDao
    abstract fun folders(): FolderDao
    abstract fun transcripts(): TranscriptDao
    abstract fun quran(): QuranDao

    companion object {

        @Volatile
        private var instance: SajjilDatabase? = null

        fun get(context: Context): SajjilDatabase =
            instance ?: synchronized(this) {
                instance ?: build(context.applicationContext).also { instance = it }
            }

        private fun build(context: Context): SajjilDatabase =
            Room.databaseBuilder(context, SajjilDatabase::class.java, "sajjil.db")
                // No fallbackToDestructiveMigration. Losing a user's recording index because a
                // schema changed is not an acceptable failure mode; every future version ships a
                // real migration or does not ship.
                .build()
    }
}
