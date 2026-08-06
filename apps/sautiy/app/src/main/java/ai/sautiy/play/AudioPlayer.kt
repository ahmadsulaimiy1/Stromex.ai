package ai.sautiy.play

import ai.sautiy.core.audio.AudioBuffer
import ai.sautiy.core.dsp.LiveVoiceStudio
import ai.sautiy.core.dsp.Resampler
import ai.sautiy.core.dsp.VoiceStudio
import ai.sautiy.core.dsp.VoiceStudioSettings
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

    /**
     * The Voice Studio applied to every block on its way to the speaker.
     *
     * Volatile because it is written from the main thread when a space is chosen and read from
     * the render loop. Replacing it mid-playback is how "live preview" works: the next block
     * comes out of the new room, with no restart and no gap.
     */
    @Volatile
    private var voice: LiveVoiceStudio? = null
    private var voiceSampleRate = 0
    private var voiceChannelCount = 0

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
        voiceSettings: VoiceStudioSettings? = null,
    ) {
        stop()

        voiceSampleRate = timeline.sampleRate
        voiceChannelCount = channelCount
        voice = voiceSettings?.takeIf { !it.isTransparent }
            ?.let { VoiceStudio(it).live(timeline.sampleRate, channelCount) }

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
            // Set when a source stops being readable underneath us. Distinguishes "the take ended"
            // from "the audio went away", which are the same silence and not the same event.
            var unreadable = false

            while (isActive) {
                if (position >= total && loopRegion == null) break

                val wanted = blockFrames
                // Guarded, and it is the *reason* this loop had a crash in it.
                //
                // A source can stop being readable while it is playing: a file deleted by another
                // app, a card removed, or an owner that closed its reader while this loop was still
                // in flight. `scope.launch` carries no CoroutineExceptionHandler, so an exception
                // escaping here does not end playback — it kills the process. That is exactly what
                // happened to PlaybackLatencyTest (EBADF through WavStreamReader), and on a phone it
                // is a crash in the middle of listening.
                //
                // Every other risky call in this loop was already wrapped — `voice.process`, and
                // every `audioTrack.write`. This was the only one that reaches a file descriptor,
                // and it was the only one left bare.
                //
                // Read into a local and test it *outside* the lambda: `break` from inside an inline
                // lambda is not available on Kotlin 2.0.21 (non-local break/continue landed in 2.2),
                // so the obvious `getOrElse { break }` does not compile.
                val rendered = runCatching {
                    TimelineRenderer.render(
                        timeline = timeline,
                        provider = provider,
                        startFrame = position,
                        frameCount = wanted,
                        channelCount = channelCount,
                    )
                }.getOrNull()

                if (rendered == null) {
                    // Stop, rather than write silence and carry on.
                    //
                    // Substituting silence would keep the playhead moving over audio the app can no
                    // longer read — the transport would report playing, the position would advance,
                    // and the user would hear nothing. That is the app pretending, which the Trust
                    // Principle forbids outright. Stopping is audible, immediate and true.
                    unreadable = true
                    break
                }

                var block = rendered

                // The voice before the speed change: the Voice Studio's filters were designed
                // at the project's rate, and this is also the order the export uses, so what is
                // auditioned is what will be written.
                voice?.let { runCatching { it.process(block) } }

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

            // Reaching the end is a different event from being stopped, and only one of them
            // is news. A cancelled loop that reported "finished" would move the transport to
            // STOPPED behind the back of whatever just stopped it.
            val reachedTheEnd = isActive && !unreadable
            _playing.value = false

            // The track is released *here*, and only here.
            //
            // `AudioTrack.write` with WRITE_BLOCKING does not respond to coroutine
            // cancellation — it returns when the track is paused, flushed or drained, and not
            // before. Releasing it from stop() therefore freed the native pointer underneath a
            // write that was still in flight, and the resulting IllegalStateException killed
            // the process. Owning the release from inside the loop makes that impossible: the
            // last write has always returned by the time this line runs.
            runCatching { audioTrack.pause() }
            runCatching { audioTrack.flush() }
            runCatching { audioTrack.stop() }
            runCatching { audioTrack.release() }

            if (reachedTheEnd) onFinished?.invoke()
        }
    }

    /**
     * Writes one block, stopping early if the track stops accepting audio.
     *
     * A non-positive return means paused, flushed or in error — in every case there is nothing
     * further to write and the loop should look at its own cancellation instead of pushing on.
     */
    private fun writeBlock(audioTrack: AudioTrack, block: AudioBuffer) {
        val interleaved = block.interleave()
        var written = 0
        while (written < interleaved.size) {
            val count = runCatching {
                audioTrack.write(
                    interleaved,
                    written,
                    interleaved.size - written,
                    AudioTrack.WRITE_BLOCKING,
                )
            }.getOrElse { return }
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

    /**
     * Changes the voice without interrupting playback.
     *
     * The tail of the previous room is dropped rather than crossfaded: they are different rooms,
     * and hearing two at once while comparing presets is worse than hearing the join.
     */
    fun setVoice(settings: VoiceStudioSettings?) {
        voice = settings?.takeIf { !it.isTransparent && voiceSampleRate > 0 }
            ?.let { VoiceStudio(it).live(voiceSampleRate, voiceChannelCount) }
    }

    fun seekTo(frame: Long) {
        // A seek must not drag the old room across the cut.
        voice?.reset()
        _positionFrames.value = frame
    }

    /**
     * Stops playback, without waiting for the render loop to finish leaving.
     *
     * The right call for a thumb on a button: audio is silent by the time this returns, because the
     * pause and flush inside [stopping] are what actually end it. The loop then releases the track on
     * its own way out, a moment later.
     *
     * Use [stopAndAwait] instead if you are about to free something the player is reading.
     */
    fun stop() {
        stopping()
    }

    /**
     * Stops, and does not return until the render loop has actually left.
     *
     * [stop] cancels and returns immediately, which is right for a thumb on a button — the UI must
     * never block on audio teardown. It is wrong for anyone who owns the *source*: cancellation is a
     * request, not an event, and the loop can still be inside a block read when `stop` returns. A
     * caller that closes its reader on the next line is then racing it, and the loop reads a closed
     * descriptor.
     *
     * That race is what killed the test process, and guarding the render made it survivable rather
     * than impossible. This makes it impossible: anything that owns a file the player is reading
     * should stop it with this, not with [stop].
     */
    suspend fun stopAndAwait() {
        stopping()?.join()
    }

    /**
     * The shared body. Returns the loop that was cancelled, so [stopAndAwait] has something to join.
     *
     * Pause and flush come first, and they are what actually ends it: they unblock the write the
     * render loop is sitting in, so it can see its own cancellation. Nothing here touches the native
     * object, because doing so while a write is in flight is precisely the crash the loop's own
     * ownership of `release()` exists to prevent.
     */
    private fun stopping(): Job? {
        val running = loop
        val audioTrack = track
        loop = null
        track = null
        _playing.value = false

        audioTrack?.let {
            runCatching { it.pause() }
            runCatching { it.flush() }
        }
        running?.cancel()
        return running
    }
}
