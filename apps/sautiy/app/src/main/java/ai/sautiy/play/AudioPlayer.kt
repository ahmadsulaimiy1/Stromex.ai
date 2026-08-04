package ai.sautiy.play

import ai.sautiy.core.audio.AudioBuffer
import ai.sautiy.core.dsp.Resampler
import ai.sautiy.core.edit.SourceProvider
import ai.sautiy.core.edit.Timeline
import ai.sautiy.core.edit.TimelineRenderer
import ai.sautiy.core.play.PlaybackPolicy
import ai.sautiy.core.play.PlaybackSpeed
import android.media.AudioAttributes
import android.media.AudioFormat as AndroidAudioFormat
import android.media.AudioTrack
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch

/**
 * The playback engine — Editorial Bible chapter 8.
 *
 * Chapter 1.3.4 is absolute: **listening outranks everything.** Nothing here waits for waveform
 * generation, loudness measurement or transcription, and there is deliberately no reference to
 * any of them, so there is nothing for playback to wait on even by accident.
 *
 * The engine renders **windows of the timeline** rather than decoding a file, which is what
 * makes playback start instantly on a two-hour project and makes an edit audible the moment it
 * is made — there is no intermediate rendered file to invalidate.
 *
 * `AudioTrack` is used directly rather than a higher-level player because the workspace needs
 * two things a general media player does not offer: a frame-accurate position for the playhead,
 * and the ability to feed audio that does not exist as a file.
 */
class AudioPlayer(
    private val scope: CoroutineScope,
) {
    private var track: AudioTrack? = null
    private var loop: Job? = null

    private val _positionFrames = MutableStateFlow(0L)
    val positionFrames: StateFlow<Long> = _positionFrames.asStateFlow()

    private val _playing = MutableStateFlow(false)
    val playing: StateFlow<Boolean> = _playing.asStateFlow()

    /** Called when playback reaches the end of the material. */
    var onFinished: (() -> Unit)? = null

    fun start(
        timeline: Timeline,
        provider: SourceProvider,
        fromFrame: Long,
        speed: PlaybackSpeed = PlaybackSpeed.NORMAL,
        loopRegion: ai.sautiy.core.play.LoopRegion? = null,
        channelCount: Int = 1,
    ) {
        stop()

        val sampleRate = timeline.sampleRate
        val channelMask = if (channelCount == 1) {
            AndroidAudioFormat.CHANNEL_OUT_MONO
        } else {
            AndroidAudioFormat.CHANNEL_OUT_STEREO
        }

        val blockFrames = PlaybackPolicy.outputBufferFrames(sampleRate)
        val minimumBuffer = AudioTrack.getMinBufferSize(
            sampleRate,
            channelMask,
            AndroidAudioFormat.ENCODING_PCM_FLOAT,
        )
        val bufferBytes = maxOf(
            minimumBuffer,
            blockFrames * channelCount * 4 * PlaybackPolicy.RENDER_AHEAD_BUFFERS,
        )

        val audioTrack = AudioTrack.Builder()
            .setAudioAttributes(
                AudioAttributes.Builder()
                    // MEDIA rather than a call or notification usage: SAUTIY's output belongs in
                    // the media stream, so it respects the volume the user set for listening and
                    // ducks correctly against other apps.
                    .setUsage(AudioAttributes.USAGE_MEDIA)
                    .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                    .build(),
            )
            .setAudioFormat(
                AndroidAudioFormat.Builder()
                    // Float output, so the last conversion from SAUTIY's working format happens
                    // in the platform rather than costing a quantisation of our own.
                    .setEncoding(AndroidAudioFormat.ENCODING_PCM_FLOAT)
                    .setSampleRate(sampleRate)
                    .setChannelMask(channelMask)
                    .build(),
            )
            .setBufferSizeInBytes(bufferBytes)
            .setTransferMode(AudioTrack.MODE_STREAM)
            .build()

        track = audioTrack
        _positionFrames.value = fromFrame
        _playing.value = true
        audioTrack.play()

        loop = scope.launch(Dispatchers.IO) {
            var position = fromFrame
            val total = timeline.lengthFrames

            while (isActive) {
                if (position >= total && loopRegion == null) break

                val wanted = blockFrames
                var block = TimelineRenderer.render(
                    timeline = timeline,
                    provider = provider,
                    startFrame = position,
                    frameCount = wanted,
                    channelCount = channelCount,
                )

                if (speed != PlaybackSpeed.NORMAL) {
                    // FAST quality here on purpose: this is a preview being heard once, at
                    // speed, and TRANSPARENT would spend thirty-two taps per sample to improve
                    // something nobody is auditioning.
                    block = Resampler.changeSpeed(block, speed.factor, Resampler.Quality.FAST)
                }

                writeBlock(audioTrack, block)

                position += (wanted * speed.factor).toLong()
                if (loopRegion != null && position >= loopRegion.endFrame) {
                    position = loopRegion.startFrame
                }
                _positionFrames.value = position.coerceAtMost(total)
            }

            _playing.value = false
            onFinished?.invoke()
        }
    }

    private fun writeBlock(audioTrack: AudioTrack, block: AudioBuffer) {
        val interleaved = block.interleave()
        var written = 0
        while (written < interleaved.size) {
            val count = audioTrack.write(
                interleaved,
                written,
                interleaved.size - written,
                AudioTrack.WRITE_BLOCKING,
            )
            if (count <= 0) return
            written += count
        }
    }

    fun pause() {
        track?.pause()
        _playing.value = false
    }

    fun resume() {
        track?.play()
        _playing.value = true
    }

    fun seekTo(frame: Long) {
        _positionFrames.value = frame
    }

    fun stop() {
        loop?.cancel()
        loop = null
        track?.let { audioTrack ->
            runCatching { audioTrack.pause() }
            runCatching { audioTrack.flush() }
            runCatching { audioTrack.stop() }
            audioTrack.release()
        }
        track = null
        _playing.value = false
    }
}
