package ai.sautiy.record

import ai.sautiy.core.analysis.InstantLevel
import ai.sautiy.core.analysis.Waveform
import ai.sautiy.core.audio.AudioBuffer
import ai.sautiy.core.audio.CaptureQuality
import ai.sautiy.core.audio.PcmCodec
import ai.sautiy.core.codec.WavCodec
import ai.sautiy.core.record.CapturePolicy
import android.annotation.SuppressLint
import android.media.AudioFormat as AndroidAudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import android.media.audiofx.AcousticEchoCanceler
import android.media.audiofx.AudioEffect
import android.media.audiofx.AutomaticGainControl
import android.media.audiofx.NoiseSuppressor
import java.io.File
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch

/**
 * The capture engine — Editorial Bible chapter 7.
 *
 * The parts that need a device, and nothing else: opening `AudioRecord`, running the read loop
 * on a dedicated thread, and appending to the streaming WAV writer. Every *decision* — which
 * transitions are legal, how often to flush, when storage is a problem — lives in
 * `sautiy-core`, where it is unit-tested.
 *
 * Three things here are load-bearing:
 *
 * **`VOICE_PERFORMANCE` is the source of choice.** `MIC` gives whatever the vendor decided;
 * `VOICE_RECOGNITION` applies aggressive processing tuned for speech engines rather than for
 * listening. `VOICE_PERFORMANCE` asks the platform for the signal path with the least
 * processing and the lowest latency, which is the only honest starting point for a recorder
 * that has its own DSP chain.
 *
 * **The platform's own noise suppression, echo cancellation and AGC are switched off.** They
 * are tuned for telephony, they are not defeatable once applied, and they would sit ahead of
 * SAUTIY's own chain — so a user who turned noise reduction off would still be getting it.
 * Chapter 10.1 requires that nothing is applied without being asked.
 *
 * **The write path never allocates per buffer.** One `ShortArray` is reused for the life of the
 * recording, because a 90-minute lecture at 20 ms per read is 270,000 buffers, and allocating
 * one each time is 270,000 chances for a garbage collection to land in the middle of a read.
 */
class AudioCapture(
    private val quality: CaptureQuality,
    private val scope: CoroutineScope,
) {
    private var record: AudioRecord? = null
    private var writer: WavCodec.StreamingWriter? = null
    private var loop: Job? = null

    /**
     * The platform effect objects we opened purely to switch off. They must be held and released
     * explicitly: `AudioEffect` owns a native handle and does not implement `AutoCloseable`, so
     * dropping the reference leaks the handle for the life of the process — and on several
     * devices a leaked effect keeps the audio session alive and the next recording fails to open.
     */
    private val effects = mutableListOf<AudioEffect>()

    private val _level = MutableStateFlow(InstantLevel(0f, 0.0))
    val level: StateFlow<InstantLevel> = _level.asStateFlow()

    private val _framesWritten = MutableStateFlow(0L)
    val framesWritten: StateFlow<Long> = _framesWritten.asStateFlow()

    private val _clippedSamples = MutableStateFlow(0)
    val clippedSamples: StateFlow<Int> = _clippedSamples.asStateFlow()

    /**
     * Set when the take can no longer be written — a full volume, or storage removed mid-recording.
     *
     * Exists because the alternative is worse than an error. If a write fails and nothing says so,
     * the frame counter simply stops advancing while the transport still reads RECORDING: the app
     * showing a recording in progress that is no longer being recorded. That is the Trust Principle's
     * first prohibition, and a frozen timer is not a way of telling anybody.
     */
    private val _writeFailure = MutableStateFlow<CaptureFailure?>(null)
    val writeFailure: StateFlow<CaptureFailure?> = _writeFailure.asStateFlow()

    /** Emitted per captured block, for the live waveform. Consumers must not block. */
    var onBlock: ((AudioBuffer) -> Unit)? = null

    @Volatile
    private var paused = false

    val isRecording: Boolean get() = loop?.isActive == true

    /**
     * Opens the device and begins writing to [file].
     *
     * @return null on success, or the reason it could not start — which the workspace shows in
     *   place, as fact, consequence and remedy (chapter 3.2.6).
     */
    @SuppressLint("MissingPermission")
    fun start(file: File): CaptureFailure? {
        val format = quality.format
        val channelMask = if (format.channelCount == 1) {
            AndroidAudioFormat.CHANNEL_IN_MONO
        } else {
            AndroidAudioFormat.CHANNEL_IN_STEREO
        }

        val minimumBuffer = AudioRecord.getMinBufferSize(
            format.sampleRate,
            channelMask,
            AndroidAudioFormat.ENCODING_PCM_16BIT,
        )
        if (minimumBuffer <= 0) return CaptureFailure.UNSUPPORTED_FORMAT

        // Four times the constitutional read size, so a scheduler hiccup costs latency rather
        // than samples, but never smaller than what the platform demands.
        val readFrames = CapturePolicy.captureBufferFrames(format.sampleRate)
        val bufferBytes = maxOf(minimumBuffer, readFrames * format.channelCount * 2 * 4)

        val recorder = try {
            AudioRecord(
                MediaRecorder.AudioSource.VOICE_PERFORMANCE,
                format.sampleRate,
                channelMask,
                AndroidAudioFormat.ENCODING_PCM_16BIT,
                bufferBytes,
            )
        } catch (denied: SecurityException) {
            return CaptureFailure.PERMISSION_DENIED
        } catch (unavailable: IllegalArgumentException) {
            return CaptureFailure.UNSUPPORTED_FORMAT
        }

        if (recorder.state != AudioRecord.STATE_INITIALIZED) {
            recorder.release()
            return CaptureFailure.DEVICE_BUSY
        }

        disablePlatformProcessing(recorder.audioSessionId)

        val streamWriter = try {
            WavCodec.StreamingWriter(
                file = file,
                format = ai.sautiy.core.audio.AudioFormat(
                    sampleRate = format.sampleRate,
                    channelCount = format.channelCount,
                    encoding = quality.storageEncoding,
                ),
            )
        } catch (io: java.io.IOException) {
            recorder.release()
            return CaptureFailure.STORAGE_UNAVAILABLE
        }

        record = recorder
        writer = streamWriter
        paused = false

        recorder.startRecording()
        loop = scope.launch(Dispatchers.IO) { readLoop(recorder, streamWriter, readFrames) }
        return null
    }

    private suspend fun readLoop(
        recorder: AudioRecord,
        streamWriter: WavCodec.StreamingWriter,
        readFrames: Int,
    ) {
        val channelCount = quality.format.channelCount
        // Allocated once. See the class comment: a 90-minute lecture is a quarter of a million
        // reads, and a per-read allocation is a quarter of a million chances to stall.
        val scratch = ShortArray(readFrames * channelCount)
        val flushEvery = CapturePolicy.flushIntervalFrames(quality.format.sampleRate)
        var sinceFlush = 0L
        var clipped = 0

        while (currentCoroutineIsActive()) {
            if (paused) {
                Thread.sleep(10)
                continue
            }

            val read = recorder.read(scratch, 0, scratch.size)
            if (read <= 0) {
                // A negative result mid-recording means the route changed or the device was
                // taken. Chapter 3.2.7: pause rather than stop, so the take survives.
                if (read == AudioRecord.ERROR_INVALID_OPERATION || read == AudioRecord.ERROR_DEAD_OBJECT) break
                continue
            }

            val block = PcmCodec.decodeInt16(scratch, read, channelCount, quality.format.sampleRate)

            // Clipping is counted at capture, where it happens, and reported honestly
            // (chapter 1.4 principle 5). It cannot be undone later, so the user must see it now.
            clipped += block.clippedSampleCount()
            if (clipped != _clippedSamples.value) _clippedSamples.value = clipped

            _level.value = Waveform.instantLevel(block)
            onBlock?.invoke(block)

            // Guarded, and for the same reason the render loop in AudioPlayer is.
            //
            // `scope.launch` carries no CoroutineExceptionHandler, so an IOException from here does
            // not stop the recording — it kills the process, mid-take, which is the one outcome this
            // app may never produce. A volume that fills during a ninety-minute lecture is not an
            // exotic case; neither is storage being removed.
            val written = runCatching {
                streamWriter.append(block)
                sinceFlush += block.frameCount
                if (sinceFlush >= flushEvery) {
                    // The durability promise of chapter 1.3.5: after this returns, the file on disk
                    // is already a complete, playable WAV of everything captured.
                    streamWriter.flush()
                    sinceFlush = 0
                }
            }.isSuccess

            if (!written) {
                // Say so and stop. Everything flushed before this point is already a complete,
                // playable WAV on disk — that is what the flush interval is for — so the take up to
                // here survives. Continuing to spin against a dead file would only overwrite that
                // truth with a longer silence.
                _writeFailure.value = CaptureFailure.STORAGE_UNAVAILABLE
                break
            }

            _framesWritten.value = streamWriter.frameCount
        }
    }

    private suspend fun currentCoroutineIsActive(): Boolean = kotlin.coroutines.coroutineContext[Job]?.isActive ?: false

    /**
     * Pauses without closing the file, so resuming continues the same take.
     *
     * A read already in flight still lands. That is deliberate: the block the device is part
     * way through holds audio captured *before* the tap, and discarding it to make the frame
     * count freeze on the exact sample would lose audio the user did record — which is the one
     * thing SAUTIY may not do. Up to one buffer of room tone past the tap is the cheaper error.
     */
    fun pause() {
        paused = true
        writer?.flush()
    }

    fun resume() {
        paused = false
    }

    /** Stops, flushes and closes. Returns the frames captured. */
    fun stop(): Long {
        // Cancelled *and waited for*, before anything it writes to is closed.
        //
        // Cancellation is a request, not an event: the loop can be inside `append` or `flush` when
        // this returns, and the writer is closed a few lines below. That is the same race that killed
        // the test process in the playback path, and here it would cost the last block of a take as
        // well — writing to a descriptor that has just been closed.
        //
        // Bounded, and blocking is the right call rather than a compromise. The loop leaves within one
        // buffer period of cancellation — twenty milliseconds at the capture window — and `stop()` is
        // called once, when a thumb lifts off the record button. The timeout exists only so a wedged
        // read can never hang the app; it is not expected to be reached.
        val running = loop
        loop = null
        running?.cancel()
        if (running != null) {
            runCatching {
                kotlinx.coroutines.runBlocking {
                    kotlinx.coroutines.withTimeoutOrNull(LOOP_EXIT_TIMEOUT_MS) { running.join() }
                }
            }
        }

        record?.let { recorder ->
            runCatching { recorder.stop() }
            recorder.release()
        }
        record = null

        for (effect in effects) runCatching { effect.release() }
        effects.clear()

        val frames = writer?.frameCount ?: 0
        writer?.let { runCatching { it.close() } }
        writer = null
        return frames
    }

    /**
     * Switches off the platform's telephony processing.
     *
     * Each of these is tuned for a phone call, is not defeatable once engaged, and sits ahead of
     * SAUTIY's chain — so leaving them on would mean a user who turned noise reduction off was
     * still getting somebody's noise reduction.
     */
    private fun disablePlatformProcessing(sessionId: Int) {
        fun disable(create: () -> AudioEffect?) {
            runCatching {
                create()?.also { effect ->
                    effect.enabled = false
                    // Held so stop() can release the native handle. Dropping it here would leak
                    // the session on devices that keep it alive behind a live effect.
                    effects += effect
                }
            }
        }

        if (NoiseSuppressor.isAvailable()) disable { NoiseSuppressor.create(sessionId) }
        if (AcousticEchoCanceler.isAvailable()) disable { AcousticEchoCanceler.create(sessionId) }
        if (AutomaticGainControl.isAvailable()) disable { AutomaticGainControl.create(sessionId) }
    }

    private companion object {
        /**
         * How long [stop] waits for the read loop to leave before closing the file underneath it.
         *
         * Half a second against an expected twenty milliseconds. Generous on purpose: the cost of
         * waiting slightly too long is imperceptible, and the cost of not waiting is a write to a
         * closed descriptor at the end of somebody's recording.
         */
        const val LOOP_EXIT_TIMEOUT_MS = 500L
    }
}

/** Why capture could not start. Each maps to a `SautiyError` with a remedy. */
enum class CaptureFailure {
    PERMISSION_DENIED,
    DEVICE_BUSY,
    UNSUPPORTED_FORMAT,
    STORAGE_UNAVAILABLE,
    ;

    fun toError(): ai.sautiy.core.workspace.SautiyError = when (this) {
        PERMISSION_DENIED -> ai.sautiy.core.workspace.SautiyError.MicrophoneDenied
        DEVICE_BUSY -> ai.sautiy.core.workspace.SautiyError.MicrophoneBusy
        UNSUPPORTED_FORMAT -> ai.sautiy.core.workspace.SautiyError.MicrophoneBusy
        STORAGE_UNAVAILABLE -> ai.sautiy.core.workspace.SautiyError.StorageFull
    }
}
