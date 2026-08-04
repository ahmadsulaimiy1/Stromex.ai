package ai.sajjil.app.data

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.PrimaryKey

/**
 * A recording's metadata. The audio itself lives on disk under [fileName]; only what the Library
 * needs to sort, search and draw a card is in the database.
 *
 * Every column is a primitive or a String on purpose — no type converters. Converters are a
 * frequent source of migration surprises, and nothing here needs one.
 */
@Entity(
    tableName = "recordings",
    indices = [
        Index("createdAt"),
        Index("folderId"),
        Index("isFavourite"),
    ],
)
data class RecordingEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,

    val title: String,

    /** File name inside the app's recordings directory. Never a full path — paths change. */
    val fileName: String,

    val createdAt: Long,
    val updatedAt: Long,
    val durationMs: Long,
    val sampleRate: Int,
    val channelCount: Int,
    val sizeBytes: Long,

    /** 0-100 from the quality analyser, or null when it has not run yet. */
    val qualityScore: Int? = null,

    /** Integrated loudness in LUFS, or null when unmeasured. */
    val loudnessLufs: Double? = null,

    val isFavourite: Boolean = false,
    val folderId: Long? = null,

    /** Comma-separated. A join table would be correct but is not worth it at this scale. */
    val tags: String = "",

    val notes: String = "",

    /** Preset last applied in Studio, so reopening a recording restores where the user was. */
    val lastPresetId: String? = null,
    val lastVoiceStyleId: String? = null,
    val lastAmbienceId: String? = null,

    /**
     * True while a recording is still being written. A row in this state that is found at
     * startup was interrupted by a crash or by the system, and gets recovered.
     */
    val isIncomplete: Boolean = false,
)

@Entity(tableName = "folders", indices = [Index(value = ["name"], unique = true)])
data class FolderEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val name: String,
    val createdAt: Long,
)

/** A transcript. Separate from the recording so the (potentially large) text is loaded on demand. */
@Entity(
    tableName = "transcripts",
    foreignKeys = [
        ForeignKey(
            entity = RecordingEntity::class,
            parentColumns = ["id"],
            childColumns = ["recordingId"],
            onDelete = ForeignKey.CASCADE,
        ),
    ],
    indices = [Index(value = ["recordingId"], unique = true)],
)
data class TranscriptEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val recordingId: Long,
    /** BCP-47, e.g. "ar" or "en". */
    val language: String,
    val text: String,
    val createdAt: Long,
    /** Which engine produced it, so the UI can be honest about where the text came from. */
    val source: String,
)

/** A Qur'an recording project: one surah, one juz, or the whole Qur'an. */
@Entity(tableName = "quran_projects")
data class QuranProjectEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val name: String,
    /** SURAH, JUZ or FULL. Stored as a string so adding a kind needs no migration. */
    val kind: String,
    /** 1-114 for a surah project, null otherwise. */
    val surahNumber: Int? = null,
    /** 1-30 for a juz project, null otherwise. */
    val juzNumber: Int? = null,
    val createdAt: Long,
    val updatedAt: Long,
    /** How many ayat the project covers, for the progress ring. */
    val totalAyah: Int,
    val notes: String = "",
)

/**
 * One take of one ayah range.
 *
 * Multiple takes per range is the whole point — a reciter records a passage several times and
 * chooses afterwards, so [isSelected] marks the keeper rather than the others being deleted.
 */
@Entity(
    tableName = "quran_takes",
    foreignKeys = [
        ForeignKey(
            entity = QuranProjectEntity::class,
            parentColumns = ["id"],
            childColumns = ["projectId"],
            onDelete = ForeignKey.CASCADE,
        ),
        ForeignKey(
            entity = RecordingEntity::class,
            parentColumns = ["id"],
            childColumns = ["recordingId"],
            onDelete = ForeignKey.CASCADE,
        ),
    ],
    indices = [Index("projectId"), Index("recordingId")],
)
data class QuranTakeEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val projectId: Long,
    val recordingId: Long,
    val ayahFrom: Int,
    val ayahTo: Int,
    val takeNumber: Int,
    val isSelected: Boolean = false,
    val createdAt: Long,
    @ColumnInfo(defaultValue = "") val notes: String = "",
)
