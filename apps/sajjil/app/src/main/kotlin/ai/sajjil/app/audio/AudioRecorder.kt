package ai.sajjil.app.audio

import ai.sajjil.audio.codec.WavBitDepth
import ai.sajjil.audio.codec.WavWriter
import ai.sajjil.audio.linearToDb
import ai.sajjil.audio.waveform.LiveWaveform
import android.annotation.SuppressLint
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import android.media.audiofx.AcousticEchoCanceler
import android.media.audiofx.AutomaticGainControl
import android.media.audiofx.NoiseSuppressor
import android.util.Log
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.io.BufferedOutputStream
import java.io.File
import java.io.FileOutputStream
import java.io.IOException
import java.io.RandomAccessFile
import kotlin.concurrent.thread
import kotlin.math.abs
import kotlin.math.sqrt

/** Capture settings. Defaults are chosen for voice, not for music. */
data class RecordingConfig(
    val sampleRate: Int = 48000,
    val channelCount: Int = 1,
    val bitDepth: WavBitDepth = WavBitDepth.PCM_16,
    /**
     * Whether to let the platform apply its own noise suppression and gain control.
     *
     * Off by default. These are tuned for phone calls and fight with SAJJIL's own enhancement
     * chain — the platform's AGC in particular will pump the level under a compressor. Recording
     * clean and processing deliberately gives a far better result than two processors guessing at
     * each other.
     */
    val usePlatformProcessing: Boolean = false,
) {
    val bytesPerSample: Int get() = bitDepth.bits / 8
    val bytesPerSecond: Int get() = sampleRate * channelCount * bytesPerSample
}

/** Live capture state, published to the UI. */
enum class RecorderState { IDLE, RECORDING, PAUSED }

/** What the meters on the Record screen show. */
data class RecorderLevels(
    /** Instantaneous peak, 0..1. */
    val peak: Float = 0f,
    /** Short-window RMS, 0..1. Drives the meter body; peak drives the tip. */
    val rms: Float = 0f,
    val peakDb: Double = -120.0,
    /** True while the input is at or above full scale — the one thing that ruins a take. */
    val isClipping: Boolean = false,
    /** True when the input is so quiet the recording will be unusable. */
    val isTooQuiet: Boolean = false,
)

/**
 * Captures audio to a WAV file.
 *
 * Writes the header first with placeholder lengths and finalises it on stop. That ordering is
 * what makes a crash survivable: the samples already on disk are valid audio, and
 * [ai.sajjil.app.data.AudioFileStore.repairIncomplete] only has to rewrite two integers to turn
 * the file back into a complete recording.
 *
 * Pause keeps the file and the AudioRecord open and simply stops draining it, so resuming is
 * instant and the recording stays one continuous file rather than a set of fragments to join.
 */
class AudioRecorder(
    val config: RecordingConfig = RecordingConfig(),
) {

    private val _state = MutableStateFlow(RecorderState.IDLE)
    val state: StateFlow<RecorderState> = _state.asStateFlow()

    private val _levels = MutableStateFlow(RecorderLevels())
    val levels: StateFlow<RecorderLevels> = _levels.asStateFlow()

    private val _elapsedMillis = MutableStateFlow(0L)
    val elapsedMillis: StateFlow<Long> = _elapsedMillis.asStateFlow()

    /** Rolling level history for the live waveform. */
    val waveform = LiveWaveform(capacity = 180)

    /** Set when capture fails; the UI turns this into an explanation the user can act on. */
    private val _error = MutableStateFlow<RecorderError?>(null)
    val error: StateFlow<RecorderError?> = _error.asStateFlow()

    private var audioRecord: AudioRecord? = null
    private var output: BufferedOutputStream? = null
    private var captureThread: Thread? = null
    private var targetFile: File? = null

    @Volatile
    private var running = false

    @Volatile
    private var paused = false

    private var framesWritten = 0L
    private var effects = mutableListOf<AutoCloseable>()

    /** Frames captured so far. Used to finalise the header and to report duration. */
    val frameCount: Long get() = framesWritten

    /**
     * Starts capturing into [file].
     *
     * @throws SecurityException if the microphone permission was revoked between the check and
     *   here, which the caller surfaces as a permission prompt rather than a crash.
     */
    @SuppressLint("MissingPermission")
    fun start(file: File) {
        check(_state.value == RecorderState.IDLE) { "the recorder is already running" }
        _error.value = null

        val channelMask = if (config.channelCount == 1) {
            AudioFormat.CHANNEL_IN_MONO
        } else {
            AudioFormat.CHANNEL_IN_STEREO
        }
        val encoding = AudioFormat.ENCODING_PCM_16BIT

        val minimumBuffer = AudioRecord.getMinBufferSize(config.sampleRate, channelMask, encoding)
        if (minimumBuffer == AudioRecord.ERROR || minimumBuffer == AudioRecord.ERROR_BAD_VALUE) {
            _error.value = RecorderError.UnsupportedFormat
            return
        }
        // Four times the minimum. The extra headroom is what stops a dropout when the system
        // briefly starves the capture thread, which on mid-range devices it will.
        val bufferBytes = minimumBuffer * 4

        val record = try {
            AudioRecord(
                // VOICE_RECOGNITION applies the least platform processing of the useful sources,
                // which is what this app wants: capture clean, enhance deliberately.
                MediaRecorder.AudioSource.VOICE_RECOGNITION,
                config.sampleRate,
                channelMask,
                encoding,
                bufferBytes,
            )
        } catch (error: IllegalArgumentException) {
            _error.value = RecorderError.UnsupportedFormat
            return
        }

        if (record.state != AudioRecord.STATE_INITIALIZED) {
            record.release()
            _error.value = RecorderError.MicrophoneUnavailable
            return
        }

        applyPlatformEffects(record.audioSessionId)

        val stream = try {
            BufferedOutputStream(FileOutputStream(file), BUFFER_BYTES)
        } catch (error: IOException) {
            record.release()
            _error.value = RecorderError.CannotWrite(error.message)
            return
        }

        try {
            // Placeholder lengths; finalise() rewrites them once the true length is known.
            WavWriter.writeHeader(stream, config.sampleRate, config.channelCount, config.bitDepth, 0)
        } catch (error: IOException) {
            record.release()
            stream.close()
            _error.value = RecorderError.CannotWrite(error.message)
            return
        }

        audioRecord = record
        output = stream
        targetFile = file
        framesWritten = 0
        _elapsedMillis.value = 0
        waveform.clear()
        running = true
        paused = false

        record.startRecording()
        _state.value = RecorderState.RECORDING

        captureThread = thread(name = "sajjil-capture", priority = Thread.MAX_PRIORITY) {
            captureLoop(record, stream)
        }
    }

    fun pause() {
        if (_state.value != RecorderState.RECORDING) return
        paused = true
        _state.value = RecorderState.PAUSED
        _levels.value = RecorderLevels()
    }

    fun resume() {
        if (_state.value != RecorderState.PAUSED) return
        paused = false
        _state.value = RecorderState.RECORDING
    }

    /**
     * Stops and finalises the file.
     *
     * @return the number of frames written, or null if nothing was captured.
     */
    fun stop(): Long? {
        if (_state.value == RecorderState.IDLE) return null
        running = false
        paused = false

        captureThread?.join(STOP_TIMEOUT_MILLIS)
        captureThread = null

        audioRecord?.let { record ->
            runCatching { record.stop() }
            record.release()
        }
        audioRecord = null

        releaseEffects()

        runCatching {
            output?.flush()
            output?.close()
        }
        output = null

        val file = targetFile
        targetFile = null
        _state.value = RecorderState.IDLE
        _levels.value = RecorderLevels()

        if (file == null || framesWritten == 0L) {
            file?.delete()
            return null
        }
        return finalise(file)
    }

    private fun captureLoop(record: AudioRecord, stream: BufferedOutputStream) {
        val samplesPerRead = config.sampleRate / 20 * config.channelCount // ~50 ms
        val samples = ShortArray(samplesPerRead)
        val bytes = ByteArray(samplesPerRead * 2)

        while (running) {
            val read = record.read(samples, 0, samples.size)
            if (read <= 0) {
                if (read == AudioRecord.ERROR_INVALID_OPERATION || read == AudioRecord.ERROR_DEAD_OBJECT) {
                    _error.value = RecorderError.MicrophoneLost
                    running = false
                }
                continue
            }

            // Metering runs even while paused so the level meter stays live and the user can set
            // their gain before committing to a take.
            publishLevels(samples, read)

            if (paused) continue

            var offset = 0
            for (i in 0 until read) {
                val value = samples[i].toInt()
                bytes[offset++] = (value and 0xFF).toByte()
                bytes[offset++] = ((value shr 8) and 0xFF).toByte()
            }

            try {
                stream.write(bytes, 0, offset)
            } catch (error: IOException) {
                _error.value = if (error.message?.contains("space", ignoreCase = true) == true) {
                    RecorderError.OutOfSpace
                } else {
                    RecorderError.CannotWrite(error.message)
                }
                running = false
                continue
            }

            framesWritten += read / config.channelCount
            _elapsedMillis.value = framesWritten * 1000 / config.sampleRate
        }
    }

    private fun publishLevels(samples: ShortArray, count: Int) {
        var peak = 0
        var sumSquares = 0.0
        for (i in 0 until count) {
            val value = samples[i].toInt()
            val magnitude = abs(value)
            if (magnitude > peak) peak = magnitude
            sumSquares += value.toDouble() * value
        }
        val peakLinear = peak / 32768f
        val rmsLinear = sqrt(sumSquares / count).toFloat() / 32768f

        _levels.value = RecorderLevels(
            peak = peakLinear,
            rms = rmsLinear,
            peakDb = linearToDb(peakLinear.toDouble()),
            isClipping = peak >= CLIPPING_THRESHOLD,
            isTooQuiet = peakLinear < TOO_QUIET_THRESHOLD,
        )
        // The waveform tracks RMS rather than peak: it is what reads as loudness, and a peak
        // trace on a live meter looks like noise.
        waveform.push(rmsLinear * LIVE_WAVEFORM_GAIN)
    }

    /** Rewrites the two length fields now that the true length is known. */
    private fun finalise(file: File): Long {
        val dataBytes = framesWritten * config.channelCount * config.bytesPerSample
        runCatching {
            RandomAccessFile(file, "rw").use { handle ->
                val header = ByteArray(WavWriter.HEADER_BYTES)
                handle.readFully(header)
                WavWriter.repairTruncated(header, WavWriter.HEADER_BYTES + dataBytes)
                handle.seek(0)
                handle.write(header)
            }
        }.onFailure { error ->
            Log.w(TAG, "could not finalise the WAV header; the file is still recoverable", error)
        }
        return framesWritten
    }

    private fun applyPlatformEffects(sessionId: Int) {
        if (!config.usePlatformProcessing) return
        runCatching {
            if (NoiseSuppressor.isAvailable()) {
                NoiseSuppressor.create(sessionId)?.let { suppressor ->
                    suppressor.enabled = true
                    effects += AutoCloseable { suppressor.release() }
                }
            }
            if (AutomaticGainControl.isAvailable()) {
                AutomaticGainControl.create(sessionId)?.let { control ->
                    control.enabled = true
                    effects += AutoCloseable { control.release() }
                }
            }
            if (AcousticEchoCanceler.isAvailable()) {
                AcousticEchoCanceler.create(sessionId)?.let { canceler ->
                    canceler.enabled = true
                    effects += AutoCloseable { canceler.release() }
                }
            }
        }.onFailure { error ->
            // Platform effects are a nicety. Failing to attach one must never stop a recording.
            Log.w(TAG, "platform audio effects unavailable", error)
        }
    }

    private fun releaseEffects() {
        effects.forEach { runCatching { it.close() } }
        effects.clear()
    }

    private companion object {
        const val TAG = "SajjilRecorder"
        const val BUFFER_BYTES = 64 * 1024
        const val STOP_TIMEOUT_MILLIS = 2000L
        /** -0.1 dBFS in 16-bit terms. */
        const val CLIPPING_THRESHOLD = 32400
        /** About -46 dBFS: below this a voice will be buried in the noise floor. */
        const val TOO_QUIET_THRESHOLD = 0.005f
        /** Live meters look dead without a little makeup gain; speech RMS is low. */
        const val LIVE_WAVEFORM_GAIN = 3.5f
    }
}

/**
 * Why a recording could not start or continue.
 *
 * Each case carries enough for the UI to say what happened, why, and what to do — never a raw
 * exception message.
 */
sealed interface RecorderError {
    data object MicrophoneUnavailable : RecorderError
    data object MicrophoneLost : RecorderError
    data object UnsupportedFormat : RecorderError
    data object OutOfSpace : RecorderError
    data class CannotWrite(val detail: String?) : RecorderError
}
