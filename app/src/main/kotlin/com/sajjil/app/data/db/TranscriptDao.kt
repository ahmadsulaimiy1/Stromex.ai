package com.sajjil.app.data.db

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

@Dao
interface TranscriptDao {
    @Query("SELECT * FROM transcript_segments WHERE recordingId = :recordingId ORDER BY startMs ASC")
    fun observeForRecording(recordingId: Long): Flow<List<TranscriptSegmentEntity>>

    @Query("SELECT * FROM transcript_segments ORDER BY recordingId ASC, startMs ASC")
    fun observeAll(): Flow<List<TranscriptSegmentEntity>>

    @Query("SELECT DISTINCT recordingId FROM transcript_segments")
    fun observeTranscribedRecordingIds(): Flow<List<Long>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(segments: List<TranscriptSegmentEntity>)

    @Query("DELETE FROM transcript_segments WHERE recordingId = :recordingId")
    suspend fun deleteForRecording(recordingId: Long)
}
