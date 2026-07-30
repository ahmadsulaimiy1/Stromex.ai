package com.sajjil.app.data.repository

import com.sajjil.app.data.db.RecordingDao
import com.sajjil.app.data.db.RecordingEntity
import kotlinx.coroutines.flow.Flow

class RecordingRepository(private val dao: RecordingDao) {
    fun observeAll(): Flow<List<RecordingEntity>> = dao.observeAll()
    fun observeQuranLibrary(): Flow<List<RecordingEntity>> = dao.observeQuranLibrary()
    fun observeForSurah(surahNumber: Int): Flow<List<RecordingEntity>> = dao.observeForSurah(surahNumber)
    fun observeSurahsWithRecordings(): Flow<List<Int>> = dao.observeSurahsWithRecordings()
    fun search(query: String): Flow<List<RecordingEntity>> = dao.search(query)

    suspend fun getById(id: Long): RecordingEntity? = dao.getById(id)
    suspend fun save(recording: RecordingEntity): Long = dao.upsert(recording)
    suspend fun update(recording: RecordingEntity) = dao.update(recording)
    suspend fun delete(recording: RecordingEntity) = dao.delete(recording)
}
