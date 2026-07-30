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

/** Plays back a rendered/exported WAV file for A/B preview against the original take. */
class AudioPlaybackEngine {
    private var track: AudioTrack? = null
    private var playbackJob: Job? = null

    private val _isPlaying = MutableStateFlow(false)
    val isPlaying: StateFlow<Boolean> = _isPlaying.asStateFlow()

    private val _positionMs = MutableStateFlow(0L)
    val positionMs: StateFlow<Long> = _positionMs.asStateFlow()

    fun play(file: File, scope: CoroutineScope, onComplete: () -> Unit = {}) {
        stop()
        val audio = WavIO.read(file.readBytes())

        val bufferSize = AudioTrack.getMinBufferSize(
            audio.sampleRate, AudioFormat.CHANNEL_OUT_MONO, AudioFormat.ENCODING_PCM_FLOAT,
        ).coerceAtLeast(audio.samples.size * 4)

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
        _isPlaying.value = true

        playbackJob = scope.launch(Dispatchers.IO) {
            val chunkSize = 4096
            var offset = 0
            while (isActive && offset < audio.samples.size && _isPlaying.value) {
                val end = (offset + chunkSize).coerceAtMost(audio.samples.size)
                newTrack.write(audio.samples, offset, end - offset, AudioTrack.WRITE_BLOCKING)
                offset = end
                _positionMs.value = (offset.toLong() * 1000L) / audio.sampleRate
            }
            _isPlaying.value = false
            onComplete()
        }
    }

    fun stop() {
        _isPlaying.value = false
        playbackJob?.cancel()
        playbackJob = null
        track?.apply {
            runCatching { stop() }
            release()
        }
        track = null
        _positionMs.value = 0L
    }
}
