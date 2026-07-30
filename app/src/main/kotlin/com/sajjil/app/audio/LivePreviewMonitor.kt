package com.sajjil.app.audio

import android.Manifest
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import androidx.annotation.RequiresPermission
import com.sajjil.core.analysis.DirectorGuidance
import com.sajjil.core.analysis.LiveDirector
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch

/**
 * SAJJIL Intelligent Recording Director: keeps the microphone live before
 * the user commits to a take, continuously re-running [LiveDirector] over
 * a short rolling window so the UI reads like an engineer watching levels
 * — "lower gain by 3 dB," updated a few times a second — rather than a
 * one-shot report. Writes nothing to disk; that's [AudioRecordEngine]'s job
 * once the user actually presses record.
 */
class LivePreviewMonitor {
    private var record: AudioRecord? = null
    private var job: Job? = null

    private val _guidance = MutableStateFlow<DirectorGuidance?>(null)
    val guidance: StateFlow<DirectorGuidance?> = _guidance.asStateFlow()

    private val _isMonitoring = MutableStateFlow(false)
    val isMonitoring: StateFlow<Boolean> = _isMonitoring.asStateFlow()

    @RequiresPermission(Manifest.permission.RECORD_AUDIO)
    fun start(scope: CoroutineScope, sampleRate: Int = 48000, windowSeconds: Double = 0.75) {
        if (_isMonitoring.value) return

        val minBufferSize = AudioRecord.getMinBufferSize(
            sampleRate, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT,
        ).let { if (it > 0) it else 4096 }

        val newRecord = AudioRecord(
            MediaRecorder.AudioSource.VOICE_RECOGNITION,
            sampleRate,
            AudioFormat.CHANNEL_IN_MONO,
            AudioFormat.ENCODING_PCM_16BIT,
            minBufferSize * 2,
        )
        record = newRecord
        newRecord.startRecording()
        _isMonitoring.value = true

        job = scope.launch(Dispatchers.IO) {
            val shortBuffer = ShortArray(minBufferSize / 2)
            val windowSize = (sampleRate * windowSeconds).toInt().coerceAtLeast(shortBuffer.size)
            val ring = FloatArray(windowSize)
            var ringPos = 0
            var filled = 0

            while (isActive && _isMonitoring.value) {
                val read = newRecord.read(shortBuffer, 0, shortBuffer.size)
                if (read > 0) {
                    for (i in 0 until read) {
                        ring[ringPos] = shortBuffer[i] / 32768f
                        ringPos = (ringPos + 1) % windowSize
                    }
                    filled = (filled + read).coerceAtMost(windowSize)
                    _guidance.value = LiveDirector.assess(if (filled < windowSize) ring.copyOf(filled) else ring)
                }
                delay(250)
            }
        }
    }

    fun stop() {
        _isMonitoring.value = false
        job?.cancel()
        job = null
        record?.apply {
            runCatching { stop() }
            release()
        }
        record = null
        _guidance.value = null
    }
}
