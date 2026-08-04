package ai.sajjil.app.audio

import ai.sajjil.app.data.AudioFileStore
import ai.sajjil.app.data.RecordingEntity
import ai.sajjil.app.data.SajjilDatabase
import ai.sajjil.audio.analysis.QualityAnalyzer
import android.content.Context
import android.util.Log
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * The single owner of an in-progress recording, for the lifetime of the process.
 *
 * There is exactly one of these because there is exactly one microphone. Holding it here rather
 * than inside the foreground service keeps the UI's access to recorder state a plain StateFlow
 * read instead of a service binding, and means a rotation or a backgrounded activity cannot
 * interrupt a take.
 */
class RecordingSession(
    private val context: Context,
    private val store: AudioFileStore,
    private val database: SajjilDatabase,
) {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    var recorder: AudioRecorder = AudioRecorder()
        private set

    val state: StateFlow<RecorderState> get() = recorder.state
    val levels: StateFlow<RecorderLevels> get() = recorder.levels
    val elapsedMillis: StateFlow<Long> get() = recorder.elapsedMillis
    val error: StateFlow<RecorderError?> get() = recorder.error

    private val _currentRecordingId = MutableStateFlow<Long?>(null)
    val currentRecordingId: StateFlow<Long?> = _currentRecordingId.asStateFlow()

    private val _remainingSeconds = MutableStateFlow(0L)

    /** Recording time left in the available storage. Shown live on the Record screen. */
    val remainingSeconds: StateFlow<Long> = _remainingSeconds.asStateFlow()

    /** Set when a finished recording is ready, so the UI can offer to play or open it at once. */
    private val _lastFinished = MutableStateFlow<Long?>(null)
    val lastFinished: StateFlow<Long?> = _lastFinished.asStateFlow()

    /**
     * When set, the next recording is appended to this one rather than starting a new file.
     * This is what "continue this recording later" means.
     */
    private var appendTargetId: Long? = null

    fun refreshRemainingSpace(config: RecordingConfig = recorder.config) {
        _remainingSeconds.value = store.remainingRecordingSeconds(
            config.sampleRate, config.channelCount, config.bytesPerSample,
        )
    }

    /**
     * Begins a new recording.
     *
     * The database row is created up front and marked incomplete. If the process dies mid-take,
     * that row is what tells the app on next launch that there is audio to recover.
     */
    suspend fun start(config: RecordingConfig = RecordingConfig()): Long? {
        if (state.value != RecorderState.IDLE) return _currentRecordingId.value

        refreshRemainingSpace(config)
        if (_remainingSeconds.value < MINIMUM_USABLE_SECONDS) {
            return null
        }

        if (recorder.config != config) recorder = AudioRecorder(config)

        val now = System.currentTimeMillis()
        val fileName = store.newRecordingFileName(now)
        val id = database.recordings().insert(
            RecordingEntity(
                title = defaultTitleFor(now),
                fileName = fileName,
                createdAt = now,
                updatedAt = now,
                durationMs = 0,
                sampleRate = config.sampleRate,
                channelCount = config.channelCount,
                sizeBytes = 0,
                isIncomplete = true,
            )
        )
        _currentRecordingId.value = id
        appendTargetId = null

        withContext(Dispatchers.Main) {
            recorder.start(store.fileFor(fileName))
        }
        RecordingService.start(context)
        return id
    }

    /**
     * Begins a take that will be appended to [recordingId] when it stops.
     *
     * Recorded to its own file first, then joined on stop. Appending to the original file in
     * place would put the existing recording at risk if the take failed; this way the worst case
     * is a stray temporary file.
     */
    suspend fun startAppending(recordingId: Long): Long? {
        val existing = database.recordings().byId(recordingId) ?: return null
        val started = start(
            RecordingConfig(
                sampleRate = existing.sampleRate,
                channelCount = existing.channelCount,
            )
        )
        if (started != null) appendTargetId = recordingId
        return started
    }

    fun pause() {
        recorder.pause()
        RecordingService.update(context)
    }

    fun resume() {
        recorder.resume()
        RecordingService.update(context)
    }

    /**
     * Stops and finalises.
     *
     * @return the id of the recording that now holds the audio, or null if nothing was captured.
     */
    suspend fun stop(): Long? {
        val id = _currentRecordingId.value ?: return null
        val frames = withContext(Dispatchers.Main) { recorder.stop() }
        RecordingService.stop(context)
        _currentRecordingId.value = null

        val row = database.recordings().byId(id)
        if (row == null || frames == null || frames == 0L) {
            // Nothing usable was captured. Remove the placeholder rather than leaving an empty
            // recording in the Library for the user to wonder about.
            row?.let {
                store.delete(it.fileName)
                database.recordings().delete(it)
            }
            return null
        }

        val target = appendTargetId
        appendTargetId = null
        val finishedId = if (target != null) {
            joinOntoExisting(target, row)
        } else {
            completeRow(row, frames)
            id
        }

        _lastFinished.value = finishedId
        analyseInBackground(finishedId)
        refreshRemainingSpace()
        return finishedId
    }

    private suspend fun completeRow(row: RecordingEntity, frames: Long) {
        val durationMs = frames * 1000 / row.sampleRate
        database.recordings().update(
            row.copy(
                durationMs = durationMs,
                sizeBytes = store.sizeOf(row.fileName),
                updatedAt = System.currentTimeMillis(),
                isIncomplete = false,
            )
        )
    }

    /** Concatenates a freshly recorded take onto an existing recording, then removes the take. */
    private suspend fun joinOntoExisting(targetId: Long, take: RecordingEntity): Long {
        val target = database.recordings().byId(targetId)
        if (target == null) {
            completeRow(take, take.durationMs)
            return take.id
        }
        return try {
            val existing = store.read(target.fileName)
            val addition = store.read(take.fileName)
            val joined = ai.sajjil.audio.AudioBuffer.concat(listOf(existing, addition))
            store.write(target.fileName, joined)

            store.delete(take.fileName)
            database.recordings().delete(take)
            database.recordings().update(
                target.copy(
                    durationMs = joined.frameCount * 1000L / joined.sampleRate,
                    sizeBytes = store.sizeOf(target.fileName),
                    updatedAt = System.currentTimeMillis(),
                    isIncomplete = false,
                )
            )
            targetId
        } catch (error: Exception) {
            // Joining failed, so the take is kept as its own recording. Losing it would be far
            // worse than ending up with two files.
            Log.w(TAG, "could not append to recording $targetId; keeping the take separately", error)
            completeRow(take, take.durationMs)
            take.id
        }
    }

    /**
     * Scores a finished recording off the main thread.
     *
     * Analysis never blocks anything: the recording is already saved and playable, and the score
     * simply appears on its card a moment later.
     */
    private fun analyseInBackground(recordingId: Long) {
        scope.launch {
            runCatching {
                val row = database.recordings().byId(recordingId) ?: return@launch
                val audio = store.read(row.fileName)
                val report = QualityAnalyzer(audio.sampleRate).analyse(audio)
                database.recordings().update(
                    row.copy(
                        qualityScore = report.score,
                        loudnessLufs = report.integratedLufs,
                    )
                )
            }.onFailure { error ->
                Log.w(TAG, "quality analysis failed for recording $recordingId", error)
            }
        }
    }

    /**
     * Recovers recordings interrupted by a crash or by the system.
     *
     * Called once at startup. Anything with real audio in it is repaired and kept; anything with
     * only a header is removed. The user is never asked to make this decision — there is only one
     * sensible answer and it should just have happened.
     *
     * @return the number of recordings recovered.
     */
    suspend fun recoverInterrupted(): Int {
        var recovered = 0
        for (row in database.recordings().incomplete()) {
            val frames = runCatching {
                store.repairIncomplete(row.fileName, row.channelCount, BYTES_PER_SAMPLE)
            }.getOrNull()

            if (frames == null || frames == 0L) {
                store.delete(row.fileName)
                database.recordings().delete(row)
                continue
            }

            database.recordings().update(
                row.copy(
                    title = row.title + RECOVERED_SUFFIX,
                    durationMs = frames * 1000 / row.sampleRate,
                    sizeBytes = store.sizeOf(row.fileName),
                    updatedAt = System.currentTimeMillis(),
                    isIncomplete = false,
                )
            )
            analyseInBackground(row.id)
            recovered++
        }
        return recovered
    }

    fun clearLastFinished() {
        _lastFinished.value = null
    }

    private fun defaultTitleFor(millis: Long): String =
        "Recording " + SimpleDateFormat("d MMM, HH:mm", Locale.getDefault()).format(Date(millis))

    private companion object {
        const val TAG = "SajjilSession"
        const val BYTES_PER_SAMPLE = 2
        const val MINIMUM_USABLE_SECONDS = 10L
        const val RECOVERED_SUFFIX = " (recovered)"
    }
}
