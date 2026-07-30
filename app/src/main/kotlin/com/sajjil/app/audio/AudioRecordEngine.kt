package com.sajjil.app.audio

import android.Manifest
import android.media.AudioDeviceInfo
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import androidx.annotation.RequiresPermission
import com.sajjil.core.audio.BitDepth
import com.sajjil.core.audio.WavStreamWriter
import com.sajjil.core.dsp.AudioProcessingChain
import com.sajjil.core.dsp.ParametricEqualizer
import com.sajjil.core.dsp.ProcessingChainConfig
import com.sajjil.core.modes.MicrophoneProfile
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File
import kotlin.math.abs
import kotlin.math.log10
import kotlin.math.max

data class RecordingLevel(val peakDb: Float, val rmsDb: Float, val gainReductionDb: Float)

/**
 * Captures microphone audio and runs it through the live SAJJIL AI Studio
 * chain (gate -> EQ -> de-esser -> compressor -> loudness maximizer) sample
 * by sample, streaming the processed signal straight to disk.
 *
 * Hardware capture always uses 16-bit PCM (the one format guaranteed across
 * Android devices) and is converted to normalized float for processing;
 * the *output* bit depth (16/24/32-float) is an encoding choice made when
 * writing the WAV, independent of the capture path.
 */
class AudioRecordEngine(
    private val outputFile: File,
    private val requestedSampleRate: Int,
    private val outputBitDepth: BitDepth,
    chainConfig: ProcessingChainConfig,
    microphoneProfile: MicrophoneProfile = MicrophoneProfile.default,
    private val preferredInputDevice: AudioDeviceInfo? = null,
) {
    private val chain = AudioProcessingChain(effectiveSampleRate(requestedSampleRate), chainConfig)
    private val microphoneCorrection = if (microphoneProfile.correctionBands.isEmpty()) {
        null
    } else {
        ParametricEqualizer.parametric(effectiveSampleRate(requestedSampleRate), microphoneProfile.correctionBands)
    }
    private var audioRecord: AudioRecord? = null
    private var writer: WavStreamWriter? = null
    private var recordingJob: Job? = null

    private val _level = MutableStateFlow(RecordingLevel(-100f, -100f, 0f))
    val level: StateFlow<RecordingLevel> = _level.asStateFlow()

    private val _isRecording = MutableStateFlow(false)
    val isRecording: StateFlow<Boolean> = _isRecording.asStateFlow()

    val sampleRate: Int = effectiveSampleRate(requestedSampleRate)

    @RequiresPermission(Manifest.permission.RECORD_AUDIO)
    fun start(scope: CoroutineScope) {
        if (_isRecording.value) return

        val minBufferSize = AudioRecord.getMinBufferSize(
            sampleRate, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT,
        ).let { if (it > 0) it else 4096 }
        val bufferSize = minBufferSize * 4

        val record = AudioRecord(
            MediaRecorder.AudioSource.VOICE_RECOGNITION,
            sampleRate,
            AudioFormat.CHANNEL_IN_MONO,
            AudioFormat.ENCODING_PCM_16BIT,
            bufferSize,
        )
        preferredInputDevice?.let { record.preferredDevice = it }
        audioRecord = record
        writer = WavStreamWriter(outputFile, sampleRate, channels = 1, bitDepth = outputBitDepth)

        record.startRecording()
        _isRecording.value = true

        recordingJob = scope.launch(Dispatchers.IO) {
            val shortBuffer = ShortArray(minBufferSize / 2)
            val floatBuffer = FloatArray(shortBuffer.size)
            while (_isRecording.value) {
                val read = record.read(shortBuffer, 0, shortBuffer.size)
                if (read <= 0) continue

                var peak = 0f
                var sumSquares = 0.0
                for (i in 0 until read) {
                    val normalized = shortBuffer[i] / 32768f
                    val calibrated = microphoneCorrection?.process(normalized) ?: normalized
                    val processed = chain.process(calibrated)
                    floatBuffer[i] = processed
                    val a = abs(processed)
                    if (a > peak) peak = a
                    sumSquares += processed.toDouble() * processed
                }
                writer?.write(floatBuffer, read)

                val rms = kotlin.math.sqrt(sumSquares / read)
                _level.value = RecordingLevel(
                    peakDb = 20f * log10(max(peak, 1e-6f)),
                    rmsDb = (20.0 * log10(max(rms, 1e-6))).toFloat(),
                    gainReductionDb = 0f,
                )
            }
        }
    }

    /** Stops capture, finalizes the WAV file, and returns it. Safe to call once. */
    suspend fun stop(): File = withContext(Dispatchers.IO) {
        _isRecording.value = false
        recordingJob?.join()
        recordingJob = null
        audioRecord?.apply {
            stop()
            release()
        }
        audioRecord = null
        writer?.close()
        writer = null
        outputFile
    }

    fun reset() {
        chain.reset()
        microphoneCorrection?.reset()
    }

    companion object {
        /** Falls back toward 48kHz if the device can't honor an exotic requested rate. */
        private fun effectiveSampleRate(requested: Int): Int {
            val minBuf = AudioRecord.getMinBufferSize(requested, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT)
            return if (minBuf > 0) requested else 48000
        }
    }
}
