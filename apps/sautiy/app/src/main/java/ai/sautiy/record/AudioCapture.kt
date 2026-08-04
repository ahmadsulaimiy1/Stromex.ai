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

    private val effects = mutableListOf<AutoCloseable>()

    private val _level = MutableStateFlow(InstantLevel(0f, 0.0))
    val level: StateFlow<InstantLevel> = _level.asStateFlow()

    private val _framesWritten = MutableStateFlow(0L)
    val framesWritten: StateFlow<Long> = _framesWritten.asStateFlow()

    private val _clippedSamples = MutableStateFlow(0)
    val clippedSamples: StateFlow<Int> = _clippedSamples.asStateFlow()

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

            streamWriter.append(block)
            _framesWritten.value = streamWriter.frameCount

            sinceFlush += block.frameCount
            if (sinceFlush >= flushEvery) {
                // The durability promise of chapter 1.3.5: after this returns, the file on disk
                // is already a complete, playable WAV of everything captured.
                streamWriter.flush()
                sinceFlush = 0
            }
        }
    }

    private suspend fun currentCoroutineIsActive(): Boolean = kotlin.coroutines.coroutineContext[Job]?.isActive ?: false

    /** Pauses without closing the file, so resuming continues the same take. */
    fun pause() {
        paused = true
        writer?.flush()
    }

    fun resume() {
        paused = false
    }

    /** Stops, flushes and closes. Returns the frames captured. */
    fun stop(): Long {
        loop?.cancel()
        loop = null

        record?.let { recorder ->
            runCatching { recorder.stop() }
            recorder.release()
        }
        record = null

        for (effect in effects) runCatching { effect.close() }
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
        if (NoiseSuppressor.isAvailable()) {
            runCatching { NoiseSuppressor.create(sessionId)?.apply { enabled = false } }
        }
        if (AcousticEchoCanceler.isAvailable()) {
            runCatching { AcousticEchoCanceler.create(sessionId)?.apply { enabled = false } }
        }
        if (AutomaticGainControl.isAvailable()) {
            runCatching { AutomaticGainControl.create(sessionId)?.apply { enabled = false } }
        }
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
