package ai.sajjil.app.data

import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Transaction
import androidx.room.Update
import kotlinx.coroutines.flow.Flow

/** How the Library is ordered. Exposed in the sort menu. */
enum class LibrarySort { NEWEST, OLDEST, LONGEST, SHORTEST, TITLE, QUALITY }

@Dao
interface RecordingDao {

    @Insert
    suspend fun insert(recording: RecordingEntity): Long

    @Update
    suspend fun update(recording: RecordingEntity)

    @Delete
    suspend fun delete(recording: RecordingEntity)

    @Query("SELECT * FROM recordings WHERE id = :id")
    suspend fun byId(id: Long): RecordingEntity?

    @Query("SELECT * FROM recordings WHERE id = :id")
    fun observeById(id: Long): Flow<RecordingEntity?>

    // Sorting is done in SQL rather than in Kotlin so the Library stays responsive with thousands
    // of recordings — the alternative loads every row into memory to sort it.
    @Query("SELECT * FROM recordings WHERE isIncomplete = 0 ORDER BY createdAt DESC")
    fun observeNewest(): Flow<List<RecordingEntity>>

    @Query("SELECT * FROM recordings WHERE isIncomplete = 0 ORDER BY createdAt ASC")
    fun observeOldest(): Flow<List<RecordingEntity>>

    @Query("SELECT * FROM recordings WHERE isIncomplete = 0 ORDER BY durationMs DESC")
    fun observeLongest(): Flow<List<RecordingEntity>>

    @Query("SELECT * FROM recordings WHERE isIncomplete = 0 ORDER BY durationMs ASC")
    fun observeShortest(): Flow<List<RecordingEntity>>

    @Query("SELECT * FROM recordings WHERE isIncomplete = 0 ORDER BY title COLLATE NOCASE ASC")
    fun observeByTitle(): Flow<List<RecordingEntity>>

    @Query("SELECT * FROM recordings WHERE isIncomplete = 0 ORDER BY qualityScore DESC, createdAt DESC")
    fun observeByQuality(): Flow<List<RecordingEntity>>

    @Query("SELECT * FROM recordings WHERE isIncomplete = 0 AND isFavourite = 1 ORDER BY createdAt DESC")
    fun observeFavourites(): Flow<List<RecordingEntity>>

    @Query("SELECT * FROM recordings WHERE isIncomplete = 0 AND folderId = :folderId ORDER BY createdAt DESC")
    fun observeInFolder(folderId: Long): Flow<List<RecordingEntity>>

    /**
     * Search across title, tags, notes and transcript text.
     *
     * The transcript join is what makes this useful: finding a lecture by a phrase said inside it
     * is the reason people transcribe at all.
     */
    @Query(
        """
        SELECT DISTINCT r.* FROM recordings r
        LEFT JOIN transcripts t ON t.recordingId = r.id
        WHERE r.isIncomplete = 0 AND (
            r.title LIKE '%' || :query || '%' COLLATE NOCASE
            OR r.tags LIKE '%' || :query || '%' COLLATE NOCASE
            OR r.notes LIKE '%' || :query || '%' COLLATE NOCASE
            OR t.text LIKE '%' || :query || '%' COLLATE NOCASE
        )
        ORDER BY r.createdAt DESC
        """
    )
    fun search(query: String): Flow<List<RecordingEntity>>

    /** Rows left behind by a crash mid-recording. Recovered at startup. */
    @Query("SELECT * FROM recordings WHERE isIncomplete = 1")
    suspend fun incomplete(): List<RecordingEntity>

    @Query("SELECT COUNT(*) FROM recordings WHERE isIncomplete = 0")
    fun observeCount(): Flow<Int>

    @Query("SELECT COALESCE(SUM(sizeBytes), 0) FROM recordings WHERE isIncomplete = 0")
    fun observeTotalBytes(): Flow<Long>

    @Query("SELECT COALESCE(SUM(durationMs), 0) FROM recordings WHERE isIncomplete = 0")
    fun observeTotalDurationMs(): Flow<Long>
}

@Dao
interface FolderDao {

    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insert(folder: FolderEntity): Long

    @Delete
    suspend fun delete(folder: FolderEntity)

    @Query("SELECT * FROM folders ORDER BY name COLLATE NOCASE ASC")
    fun observeAll(): Flow<List<FolderEntity>>

    /** Recordings in a deleted folder move back to the root rather than disappearing with it. */
    @Query("UPDATE recordings SET folderId = NULL WHERE folderId = :folderId")
    suspend fun detachRecordings(folderId: Long)

    @Transaction
    suspend fun deleteAndDetach(folder: FolderEntity) {
        detachRecordings(folder.id)
        delete(folder)
    }
}

@Dao
interface TranscriptDao {

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(transcript: TranscriptEntity)

    @Query("SELECT * FROM transcripts WHERE recordingId = :recordingId")
    suspend fun forRecording(recordingId: Long): TranscriptEntity?

    @Query("SELECT * FROM transcripts WHERE recordingId = :recordingId")
    fun observeForRecording(recordingId: Long): Flow<TranscriptEntity?>

    @Query("SELECT recordingId FROM transcripts")
    fun observeTranscribedIds(): Flow<List<Long>>

    @Query("DELETE FROM transcripts WHERE recordingId = :recordingId")
    suspend fun deleteForRecording(recordingId: Long)
}

@Dao
interface QuranDao {

    @Insert
    suspend fun insertProject(project: QuranProjectEntity): Long

    @Update
    suspend fun updateProject(project: QuranProjectEntity)

    @Delete
    suspend fun deleteProject(project: QuranProjectEntity)

    @Query("SELECT * FROM quran_projects ORDER BY updatedAt DESC")
    fun observeProjects(): Flow<List<QuranProjectEntity>>

    @Query("SELECT * FROM quran_projects WHERE id = :id")
    fun observeProject(id: Long): Flow<QuranProjectEntity?>

    @Query("SELECT * FROM quran_projects WHERE id = :id")
    suspend fun project(id: Long): QuranProjectEntity?

    @Insert
    suspend fun insertTake(take: QuranTakeEntity): Long

    @Update
    suspend fun updateTake(take: QuranTakeEntity)

    @Delete
    suspend fun deleteTake(take: QuranTakeEntity)

    @Query("SELECT * FROM quran_takes WHERE projectId = :projectId ORDER BY ayahFrom ASC, takeNumber ASC")
    fun observeTakes(projectId: Long): Flow<List<QuranTakeEntity>>

    @Query("SELECT * FROM quran_takes WHERE projectId = :projectId AND ayahFrom = :ayahFrom AND ayahTo = :ayahTo ORDER BY takeNumber ASC")
    suspend fun takesForRange(projectId: Long, ayahFrom: Int, ayahTo: Int): List<QuranTakeEntity>

    /** Number of distinct ayat covered by a selected take. Drives the progress ring. */
    @Query(
        """
        SELECT COALESCE(SUM(ayahTo - ayahFrom + 1), 0) FROM quran_takes
        WHERE projectId = :projectId AND isSelected = 1
        """
    )
    fun observeCompletedAyah(projectId: Long): Flow<Int>

    @Query("UPDATE quran_takes SET isSelected = 0 WHERE projectId = :projectId AND ayahFrom = :ayahFrom AND ayahTo = :ayahTo")
    suspend fun clearSelectionForRange(projectId: Long, ayahFrom: Int, ayahTo: Int)

    /** Exactly one take per range is the keeper; selecting a new one deselects the old. */
    @Transaction
    suspend fun selectTake(take: QuranTakeEntity) {
        clearSelectionForRange(take.projectId, take.ayahFrom, take.ayahTo)
        updateTake(take.copy(isSelected = true))
    }
}
