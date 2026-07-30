package com.sajjil.app.data.repository

import com.sajjil.app.data.db.TranscriptDao
import com.sajjil.app.data.db.TranscriptSegmentEntity
import com.sajjil.core.speech.Transcript
import com.sajjil.core.speech.TranscriptLanguage
import com.sajjil.core.speech.TranscriptSegment
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

class TranscriptRepository(private val dao: TranscriptDao) {

    fun observeForRecording(recordingId: Long): Flow<List<TranscriptSegmentEntity>> = dao.observeForRecording(recordingId)

    fun observeTranscribedRecordingIds(): Flow<List<Long>> = dao.observeTranscribedRecordingIds()

    /** All transcripts grouped by recording, in the shape `TranscriptSearchEngine` expects. */
    fun observeAllAsTranscripts(): Flow<List<Transcript>> = dao.observeAll().map { rows ->
        rows.groupBy { it.recordingId to it.language }.map { (key, segments) ->
            val (recordingId, languageTag) = key
            Transcript(
                recordingId = recordingId,
                language = languageFromTag(languageTag),
                segments = segments.map { it.toDomain() },
                engineId = segments.firstOrNull()?.engineId.orEmpty(),
            )
        }
    }

    suspend fun replaceForRecording(recordingId: Long, transcript: Transcript) {
        dao.deleteForRecording(recordingId)
        dao.insertAll(
            transcript.segments.map { segment ->
                TranscriptSegmentEntity(
                    recordingId = recordingId,
                    language = transcript.language.bcp47,
                    startMs = segment.startMs,
                    endMs = segment.endMs,
                    text = segment.text,
                    confidence = segment.confidence,
                    engineId = transcript.engineId,
                )
            },
        )
    }

    suspend fun appendSegment(recordingId: Long, language: TranscriptLanguage, engineId: String, segment: TranscriptSegment) {
        dao.insertAll(
            listOf(
                TranscriptSegmentEntity(
                    recordingId = recordingId,
                    language = language.bcp47,
                    startMs = segment.startMs,
                    endMs = segment.endMs,
                    text = segment.text,
                    confidence = segment.confidence,
                    engineId = engineId,
                ),
            ),
        )
    }

    suspend fun deleteForRecording(recordingId: Long) = dao.deleteForRecording(recordingId)

    private fun TranscriptSegmentEntity.toDomain() = TranscriptSegment(startMs, endMs, text, confidence)

    private fun languageFromTag(tag: String): TranscriptLanguage =
        TranscriptLanguage.entries.firstOrNull { it.bcp47 == tag } ?: TranscriptLanguage.ENGLISH
}
