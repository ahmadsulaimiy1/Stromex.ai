package com.sajjil.app.data.db

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "transcript_segments")
data class TranscriptSegmentEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val recordingId: Long,
    /** BCP-47 tag, e.g. "ar-SA" / "en-US" — matches `TranscriptLanguage.bcp47`. */
    val language: String,
    val startMs: Long,
    val endMs: Long,
    val text: String,
    val confidence: Float? = null,
    /** Which recognizer produced this — e.g. "android-native", for future engines to tell their output apart. */
    val engineId: String,
)
