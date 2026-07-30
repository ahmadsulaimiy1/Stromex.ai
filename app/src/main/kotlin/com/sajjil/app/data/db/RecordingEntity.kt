package com.sajjil.app.data.db

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "recordings")
data class RecordingEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val title: String,
    val filePath: String,
    val createdAtEpochMs: Long,
    val durationMs: Long,
    val sampleRate: Int,
    val channels: Int,
    val bitDepth: Int,
    val recordingMode: String,
    val fileSizeBytes: Long,
    val exportFormat: String,
    // Qur'an Creator Suite organisation — null for non-recitation content.
    val surahNumber: Int? = null,
    val ayahStart: Int? = null,
    val ayahEnd: Int? = null,
    val juz: Int? = null,
    // Executive Dashboard scores captured at the time of the last analysis pass.
    val studioReadinessScore: Int? = null,
    val broadcastReadinessScore: Int? = null,
    val archiveReadinessScore: Int? = null,
    val isFavorite: Boolean = false,
)
