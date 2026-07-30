package com.sajjil.app.data.db

import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import kotlinx.coroutines.flow.Flow

@Dao
interface RecordingDao {
    @Query("SELECT * FROM recordings ORDER BY createdAtEpochMs DESC")
    fun observeAll(): Flow<List<RecordingEntity>>

    @Query("SELECT * FROM recordings WHERE surahNumber IS NOT NULL ORDER BY surahNumber ASC, ayahStart ASC")
    fun observeQuranLibrary(): Flow<List<RecordingEntity>>

    @Query("SELECT * FROM recordings WHERE surahNumber = :surahNumber ORDER BY ayahStart ASC, createdAtEpochMs ASC")
    fun observeForSurah(surahNumber: Int): Flow<List<RecordingEntity>>

    @Query("SELECT DISTINCT surahNumber FROM recordings WHERE surahNumber IS NOT NULL ORDER BY surahNumber ASC")
    fun observeSurahsWithRecordings(): Flow<List<Int>>

    @Query("SELECT * FROM recordings WHERE id = :id")
    suspend fun getById(id: Long): RecordingEntity?

    @Query("SELECT * FROM recordings WHERE title LIKE '%' || :query || '%' OR notes LIKE '%' || :query || '%' ORDER BY createdAtEpochMs DESC")
    fun search(query: String): Flow<List<RecordingEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(recording: RecordingEntity): Long

    @Update
    suspend fun update(recording: RecordingEntity)

    @Delete
    suspend fun delete(recording: RecordingEntity)
}
