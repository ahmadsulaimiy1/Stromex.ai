package com.sajjil.app.audio

import android.media.AudioAttributes
import android.media.AudioFormat
import android.media.AudioTrack
import com.sajjil.core.audio.WavIO
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import java.io.File

/**
 * SAJJIL Audio Comparison Laboratory: switches between multiple named
 * sources (Original / Enhanced / Mastered, or any files the user picks) at
 * the *same playback position*, so A/B/C comparison means "how does this
 * exact moment sound differently processed," not "start over each time."
 *
 * Honesty note: switching stops the current `AudioTrack` and starts the new
 * one at the matching offset — a few tens of milliseconds of silence, not a
 * literally sample-accurate gapless splice. True gapless cross-source
 * switching would need both sources decoded and buffered simultaneously in
 * a mixer; this is the practical version of that idea.
 */
class ComparisonPlayer {
    private var track: AudioTrack? = null
    private var job: Job? = null
    private val cache = mutableMapOf<String, com.sajjil.core.audio.WavAudio>()

    private val _activeSlot = MutableStateFlow<String?>(null)
    val activeSlot: StateFlow<String?> = _activeSlot.asStateFlow()

    private val _isPlaying = MutableStateFlow(false)
    val isPlaying: StateFlow<Boolean> = _isPlaying.asStateFlow()

    private val _positionMs = MutableStateFlow(0L)
    val positionMs: StateFlow<Long> = _positionMs.asStateFlow()

    private var durationMs: Long = 0L
    val currentDurationMs: Long get() = durationMs

    fun switchTo(slot: String, file: File, scope: CoroutineScope) {
        val offsetMs = _positionMs.value
        stopPlaybackOnly()
        playFrom(slot, file, offsetMs, scope)
    }

    fun playFromStart(slot: String, file: File, scope: CoroutineScope) {
        stopPlaybackOnly()
        playFrom(slot, file, 0L, scope)
    }

    fun stop() {
        stopPlaybackOnly()
        _activeSlot.value = null
        _positionMs.value = 0L
    }

    private fun playFrom(slot: String, file: File, offsetMs: Long, scope: CoroutineScope) {
        val audio = cache.getOrPut(file.absolutePath) { WavIO.read(file.readBytes()) }
        durationMs = (audio.samples.size.toLong() * 1000L) / audio.sampleRate
        val startSample = ((offsetMs.coerceIn(0, durationMs) * audio.sampleRate) / 1000L).toInt().coerceIn(0, audio.samples.size)

        val bufferSize = AudioTrack.getMinBufferSize(
            audio.sampleRate, AudioFormat.CHANNEL_OUT_MONO, AudioFormat.ENCODING_PCM_FLOAT,
        ).coerceAtLeast(8192)

        val newTrack = AudioTrack.Builder()
            .setAudioAttributes(
                AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_MEDIA)
                    .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
                    .build(),
            )
            .setAudioFormat(
                AudioFormat.Builder()
                    .setEncoding(AudioFormat.ENCODING_PCM_FLOAT)
                    .setSampleRate(audio.sampleRate)
                    .setChannelMask(AudioFormat.CHANNEL_OUT_MONO)
                    .build(),
            )
            .setBufferSizeInBytes(bufferSize)
            .setTransferMode(AudioTrack.MODE_STREAM)
            .build()

        track = newTrack
        newTrack.play()
        _activeSlot.value = slot
        _isPlaying.value = true
        _positionMs.value = offsetMs

        job = scope.launch(Dispatchers.IO) {
            val chunkSize = 4096
            var offset = startSample
            while (isActive && offset < audio.samples.size && _isPlaying.value) {
                val end = (offset + chunkSize).coerceAtMost(audio.samples.size)
                newTrack.write(audio.samples, offset, end - offset, AudioTrack.WRITE_BLOCKING)
                offset = end
                _positionMs.value = (offset.toLong() * 1000L) / audio.sampleRate
            }
            _isPlaying.value = false
        }
    }

    private fun stopPlaybackOnly() {
        _isPlaying.value = false
        job?.cancel()
        job = null
        track?.apply {
            runCatching { stop() }
            release()
        }
        track = null
    }
}
