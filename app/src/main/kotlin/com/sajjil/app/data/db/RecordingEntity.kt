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
    // Qur'an Production Suite: recording notes and take-version tracking. When several
    // recordings share the same surah/ayah range, `isPrimaryVersion` marks the one that
    // counts toward Surah/Juz progress and shows first — the rest are alternate takes kept
    // for comparison rather than deleted.
    val notes: String? = null,
    val isPrimaryVersion: Boolean = true,
)
