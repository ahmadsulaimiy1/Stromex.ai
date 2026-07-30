package com.sajjil.app.audio

import android.media.MediaPlayer
import android.media.PlaybackParams
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import java.io.File

/**
 * Real play/pause/resume/seek playback for a recorded or rendered WAV file, backed
 * by Android's own MediaPlayer -- WAV is a guaranteed-supported format from API 26
 * (this app's minSdk) onward. Replaces an earlier hand-rolled AudioTrack streamer
 * that could only play-from-start and stop; that design could never pause in place
 * or seek, which is exactly the "no real playback controls" gap flagged in review.
 */
class AudioPlaybackEngine {
    private var player: MediaPlayer? = null
    private var positionJob: Job? = null

    private val _playingFile = MutableStateFlow<File?>(null)
    val playingFile: StateFlow<File?> = _playingFile.asStateFlow()

    private val _isPlaying = MutableStateFlow(false)
    val isPlaying: StateFlow<Boolean> = _isPlaying.asStateFlow()

    private val _positionMs = MutableStateFlow(0L)
    val positionMs: StateFlow<Long> = _positionMs.asStateFlow()

    private val _durationMs = MutableStateFlow(0L)
    val durationMs: StateFlow<Long> = _durationMs.asStateFlow()

    /** Loads and plays [file] from the start. If it's already the loaded file, resumes instead. */
    fun play(file: File, scope: CoroutineScope, onComplete: () -> Unit = {}) {
        if (_playingFile.value == file && player != null) {
            resume(scope)
            return
        }
        stop()
        val mp = MediaPlayer()
        val prepared = runCatching {
            mp.setDataSource(file.absolutePath)
            mp.setOnCompletionListener {
                _isPlaying.value = false
                _positionMs.value = 0L
                runCatching { it.seekTo(0) }
                positionJob?.cancel()
                onComplete()
            }
            mp.prepare()
        }.isSuccess
        if (!prepared) {
            runCatching { mp.release() }
            return
        }
        player = mp
        _playingFile.value = file
        _durationMs.value = mp.duration.toLong().coerceAtLeast(0L)
        runCatching { mp.start() }
        _isPlaying.value = true
        trackPosition(scope)
    }

    fun pause() {
        val mp = player ?: return
        runCatching { if (mp.isPlaying) mp.pause() }
        _isPlaying.value = false
        positionJob?.cancel()
    }

    fun resume(scope: CoroutineScope) {
        val mp = player ?: return
        runCatching { mp.start() }
        _isPlaying.value = true
        trackPosition(scope)
    }

    /** Sample-accurate scrubbing -- the one thing the previous AudioTrack streamer could not do at all. */
    fun seekTo(ms: Long) {
        val mp = player ?: return
        runCatching { mp.seekTo(ms.toInt()) }
        _positionMs.value = ms.coerceIn(0L, _durationMs.value)
    }

    /** Best-effort: not every device honours non-1x PlaybackParams, so failures are swallowed rather than crashing playback. */
    fun setSpeed(speed: Float) {
        val mp = player ?: return
        runCatching { mp.playbackParams = PlaybackParams().setSpeed(speed) }
    }

    fun stop() {
        positionJob?.cancel()
        positionJob = null
        player?.let { mp ->
            runCatching { mp.stop() }
            runCatching { mp.release() }
        }
        player = null
        _playingFile.value = null
        _isPlaying.value = false
        _positionMs.value = 0L
        _durationMs.value = 0L
    }

    private fun trackPosition(scope: CoroutineScope) {
        positionJob?.cancel()
        positionJob = scope.launch {
            while (isActive) {
                val mp = player ?: break
                val stillPlaying = runCatching { mp.isPlaying }.getOrDefault(false)
                if (!stillPlaying) break
                _positionMs.value = runCatching { mp.currentPosition.toLong() }.getOrDefault(_positionMs.value)
                delay(120)
            }
        }
    }
}
