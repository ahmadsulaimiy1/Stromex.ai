package ai.sajjil.app.data

import ai.sajjil.app.audio.AudioExporter
import ai.sajjil.app.audio.ExportFormat
import ai.sajjil.app.audio.ExportQuality
import ai.sajjil.app.audio.ExportResult
import ai.sajjil.audio.AudioBuffer
import ai.sajjil.audio.analysis.QualityAnalyzer
import ai.sajjil.audio.analysis.QualityReport
import ai.sajjil.audio.chain.EnhancementChain
import ai.sajjil.audio.chain.EnhancementReport
import ai.sajjil.audio.chain.EnhancementSettings
import ai.sajjil.audio.waveform.WaveformPeaks
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.withContext
import java.io.File

/**
 * Everything the UI does to a recording.
 *
 * All of it runs on [Dispatchers.IO] — decoding, enhancement and export are seconds of work on a
 * long recording, and none of them may touch the main thread. ViewModels call straight into here
 * and never see a file or a codec.
 */
class RecordingRepository(
    private val database: SajjilDatabase,
    private val fileStore: AudioFileStore,
    private val exporter: AudioExporter,
) {
    private val recordings = database.recordings()
    private val transcripts = database.transcripts()

    // ---- queries -------------------------------------------------------------------------

    fun observe(sort: LibrarySort): Flow<List<RecordingEntity>> = when (sort) {
        LibrarySort.NEWEST -> recordings.observeNewest()
        LibrarySort.OLDEST -> recordings.observeOldest()
        LibrarySort.LONGEST -> recordings.observeLongest()
        LibrarySort.SHORTEST -> recordings.observeShortest()
        LibrarySort.TITLE -> recordings.observeByTitle()
        LibrarySort.QUALITY -> recordings.observeByQuality()
    }

    fun observeFavourites(): Flow<List<RecordingEntity>> = recordings.observeFavourites()

    fun observeInFolder(folderId: Long): Flow<List<RecordingEntity>> =
        recordings.observeInFolder(folderId)

    fun search(query: String): Flow<List<RecordingEntity>> = recordings.search(query)

    fun observe(id: Long): Flow<RecordingEntity?> = recordings.observeById(id)

    fun observeCount(): Flow<Int> = recordings.observeCount()

    fun observeTotalBytes(): Flow<Long> = recordings.observeTotalBytes()

    fun observeTotalDurationMs(): Flow<Long> = recordings.observeTotalDurationMs()

    fun observeTranscribedIds(): Flow<List<Long>> = transcripts.observeTranscribedIds()

    fun observeFolders(): Flow<List<FolderEntity>> = database.folders().observeAll()

    suspend fun byId(id: Long): RecordingEntity? = withContext(Dispatchers.IO) { recordings.byId(id) }

    // ---- audio ---------------------------------------------------------------------------

    suspend fun loadAudio(recording: RecordingEntity): AudioBuffer = withContext(Dispatchers.IO) {
        fileStore.read(recording.fileName)
    }

    fun fileFor(recording: RecordingEntity): File = fileStore.fileFor(recording.fileName)

    /**
     * Waveform buckets for drawing.
     *
     * The whole file is read to produce these, which is why it is a suspend function on IO and
     * why playback never waits on it — the transport starts immediately and the waveform fills in.
     */
    suspend fun waveform(recording: RecordingEntity, buckets: Int): WaveformPeaks =
        withContext(Dispatchers.IO) {
            WaveformPeaks.extract(fileStore.read(recording.fileName), buckets)
        }

    suspend fun analyse(recording: RecordingEntity): QualityReport = withContext(Dispatchers.IO) {
        val audio = fileStore.read(recording.fileName)
        QualityAnalyzer(audio.sampleRate).analyse(audio)
    }

    /**
     * Applies an enhancement chain and writes the result back over the recording.
     *
     * Destructive on purpose, and safe because [AudioFileStore.write] stages through a temporary
     * file. An undo history that survived app restarts would mean keeping a second copy of every
     * recording on a device that is usually short of space; the Studio's in-session undo covers
     * the case that actually matters.
     */
    suspend fun enhanceInPlace(
        recording: RecordingEntity,
        settings: EnhancementSettings,
        onProgress: ((Double) -> Unit)? = null,
    ): EnhancementReport = withContext(Dispatchers.IO) {
        val audio = fileStore.read(recording.fileName)
        val (processed, report) = EnhancementChain(audio.sampleRate).apply(audio, settings, onProgress)
        fileStore.write(recording.fileName, processed)

        val quality = QualityAnalyzer(processed.sampleRate).analyse(processed)
        recordings.update(
            recording.copy(
                durationMs = processed.frameCount * 1000L / processed.sampleRate,
                sizeBytes = fileStore.sizeOf(recording.fileName),
                updatedAt = System.currentTimeMillis(),
                qualityScore = quality.score,
                loudnessLufs = quality.integratedLufs,
            )
        )
        report
    }

    /** Writes edited audio back, e.g. after a trim or a cut in the waveform editor. */
    suspend fun saveAudio(recording: RecordingEntity, audio: AudioBuffer) = withContext(Dispatchers.IO) {
        fileStore.write(recording.fileName, audio)
        val quality = QualityAnalyzer(audio.sampleRate).analyse(audio)
        recordings.update(
            recording.copy(
                durationMs = audio.frameCount * 1000L / audio.sampleRate,
                sizeBytes = fileStore.sizeOf(recording.fileName),
                updatedAt = System.currentTimeMillis(),
                qualityScore = quality.score,
                loudnessLufs = quality.integratedLufs,
            )
        )
    }

    // ---- export --------------------------------------------------------------------------

    suspend fun export(
        recording: RecordingEntity,
        format: ExportFormat,
        quality: ExportQuality,
        onProgress: ((Double) -> Unit)? = null,
    ): ExportResult = withContext(Dispatchers.IO) {
        val audio = fileStore.read(recording.fileName)
        val safeName = recording.title.replace(Regex("[^\\p{L}\\p{N} _-]"), "").trim()
            .ifEmpty { "recording" }
        val target = File(fileStore.exportsDirectory, "$safeName.${format.extension}")
        exporter.export(audio, target, format, quality, onProgress)
    }

    // ---- organisation --------------------------------------------------------------------

    suspend fun rename(recording: RecordingEntity, title: String) = withContext(Dispatchers.IO) {
        recordings.update(
            recording.copy(title = title.trim().ifEmpty { recording.title }, updatedAt = System.currentTimeMillis())
        )
    }

    suspend fun setFavourite(recording: RecordingEntity, favourite: Boolean) = withContext(Dispatchers.IO) {
        recordings.update(recording.copy(isFavourite = favourite))
    }

    suspend fun setNotes(recording: RecordingEntity, notes: String) = withContext(Dispatchers.IO) {
        recordings.update(recording.copy(notes = notes, updatedAt = System.currentTimeMillis()))
    }

    suspend fun setTags(recording: RecordingEntity, tags: List<String>) = withContext(Dispatchers.IO) {
        recordings.update(
            recording.copy(
                tags = tags.map { it.trim() }.filter { it.isNotEmpty() }.distinct().joinToString(","),
                updatedAt = System.currentTimeMillis(),
            )
        )
    }

    suspend fun moveToFolder(recording: RecordingEntity, folderId: Long?) = withContext(Dispatchers.IO) {
        recordings.update(recording.copy(folderId = folderId, updatedAt = System.currentTimeMillis()))
    }

    suspend fun rememberStudioChoices(
        recording: RecordingEntity,
        presetId: String?,
        voiceStyleId: String?,
        ambienceId: String?,
    ) = withContext(Dispatchers.IO) {
        recordings.update(
            recording.copy(
                lastPresetId = presetId,
                lastVoiceStyleId = voiceStyleId,
                lastAmbienceId = ambienceId,
            )
        )
    }

    /** Copies a recording, audio and all. Used before an experiment the user may want to undo. */
    suspend fun duplicate(recording: RecordingEntity): Long = withContext(Dispatchers.IO) {
        val now = System.currentTimeMillis()
        val fileName = fileStore.newRecordingFileName(now)
        fileStore.write(fileName, fileStore.read(recording.fileName))
        recordings.insert(
            recording.copy(
                id = 0,
                title = "${recording.title} (copy)",
                fileName = fileName,
                createdAt = now,
                updatedAt = now,
                sizeBytes = fileStore.sizeOf(fileName),
            )
        )
    }

    suspend fun delete(recording: RecordingEntity) = withContext(Dispatchers.IO) {
        fileStore.delete(recording.fileName)
        recordings.delete(recording)
    }

    suspend fun createFolder(name: String): Long = withContext(Dispatchers.IO) {
        database.folders().insert(FolderEntity(name = name.trim(), createdAt = System.currentTimeMillis()))
    }

    suspend fun deleteFolder(folder: FolderEntity) = withContext(Dispatchers.IO) {
        database.folders().deleteAndDetach(folder)
    }

    // ---- transcripts ---------------------------------------------------------------------

    fun observeTranscript(recordingId: Long): Flow<TranscriptEntity?> =
        transcripts.observeForRecording(recordingId)

    suspend fun saveTranscript(recordingId: Long, language: String, text: String, source: String) =
        withContext(Dispatchers.IO) {
            transcripts.upsert(
                TranscriptEntity(
                    recordingId = recordingId,
                    language = language,
                    text = text,
                    createdAt = System.currentTimeMillis(),
                    source = source,
                )
            )
        }

    suspend fun deleteTranscript(recordingId: Long) = withContext(Dispatchers.IO) {
        transcripts.deleteForRecording(recordingId)
    }
}
