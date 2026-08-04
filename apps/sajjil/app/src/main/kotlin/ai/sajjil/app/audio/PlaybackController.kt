package ai.sajjil.app.audio

import android.content.ComponentName
import android.content.Context
import android.net.Uri
import androidx.media3.common.MediaItem
import androidx.media3.common.MediaMetadata
import androidx.media3.common.PlaybackParameters
import androidx.media3.common.Player
import androidx.media3.session.MediaController
import androidx.media3.session.SessionToken
import com.google.common.util.concurrent.MoreExecutors
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.io.File

/** What the transport bar and mini player render. */
data class PlaybackState(
    val recordingId: Long? = null,
    val isPlaying: Boolean = false,
    val positionMs: Long = 0,
    val durationMs: Long = 0,
    val speed: Float = 1f,
    val isLooping: Boolean = false,
    val isReady: Boolean = false,
)

/**
 * The app's single connection to the playback session.
 *
 * Connecting to the MediaController is asynchronous, but playback must not be. Commands issued
 * before the connection completes are queued and run the moment it does, so tapping play the
 * instant a screen opens starts audio rather than being dropped — which is the difference between
 * an app that feels immediate and one that feels unreliable.
 */
class PlaybackController(private val context: Context) {

    private var controller: MediaController? = null
    private val pending = ArrayDeque<(MediaController) -> Unit>()

    private val _state = MutableStateFlow(PlaybackState())
    val state: StateFlow<PlaybackState> = _state.asStateFlow()

    private val listener = object : Player.Listener {
        override fun onIsPlayingChanged(isPlaying: Boolean) = publish()
        override fun onPlaybackStateChanged(playbackState: Int) = publish()
        override fun onPlaybackParametersChanged(parameters: PlaybackParameters) = publish()
        override fun onRepeatModeChanged(repeatMode: Int) = publish()
        override fun onPositionDiscontinuity(
            oldPosition: Player.PositionInfo,
            newPosition: Player.PositionInfo,
            reason: Int,
        ) = publish()
    }

    fun connect() {
        if (controller != null) return
        val token = SessionToken(context, ComponentName(context, PlaybackService::class.java))
        val future = MediaController.Builder(context, token).buildAsync()
        future.addListener(
            {
                val connected = runCatching { future.get() }.getOrNull() ?: return@addListener
                controller = connected
                connected.addListener(listener)
                while (pending.isNotEmpty()) pending.removeFirst()(connected)
                publish()
            },
            MoreExecutors.directExecutor(),
        )
    }

    fun release() {
        controller?.removeListener(listener)
        controller?.release()
        controller = null
        pending.clear()
        _state.value = PlaybackState()
    }

    private fun withController(action: (MediaController) -> Unit) {
        val current = controller
        if (current != null) action(current) else pending.addLast(action)
    }

    /**
     * Loads and starts a recording.
     *
     * Playback begins as soon as the player is ready; nothing waits on waveform extraction,
     * quality analysis or metadata. Those all arrive afterwards and update in place.
     */
    fun play(recordingId: Long, file: File, title: String, startPositionMs: Long = 0) {
        _state.value = _state.value.copy(recordingId = recordingId, isReady = false)
        withController { controller ->
            val item = MediaItem.Builder()
                .setUri(Uri.fromFile(file))
                .setMediaId(recordingId.toString())
                .setMediaMetadata(
                    MediaMetadata.Builder()
                        .setTitle(title)
                        .setIsBrowsable(false)
                        .setIsPlayable(true)
                        .build()
                )
                .build()
            controller.setMediaItem(item, startPositionMs)
            controller.prepare()
            controller.play()
        }
    }

    fun togglePlayPause() = withController { controller ->
        if (controller.isPlaying) controller.pause() else controller.play()
    }

    fun pause() = withController { it.pause() }

    fun resume() = withController { it.play() }

    fun stop() = withController { controller ->
        controller.stop()
        controller.clearMediaItems()
        _state.value = PlaybackState()
    }

    fun seekTo(positionMs: Long) = withController { controller ->
        controller.seekTo(positionMs.coerceAtLeast(0))
        publish()
    }

    /** Ten seconds is the standard step and is what people expect from a voice app. */
    fun skipBack() = withController { controller ->
        controller.seekTo((controller.currentPosition - SKIP_MILLIS).coerceAtLeast(0))
        publish()
    }

    fun skipForward() = withController { controller ->
        val duration = controller.duration
        val target = controller.currentPosition + SKIP_MILLIS
        controller.seekTo(if (duration > 0) target.coerceAtMost(duration) else target)
        publish()
    }

    /**
     * Changes speed without changing pitch, which is the only version of this feature that is
     * usable on speech.
     */
    fun setSpeed(speed: Float) = withController { controller ->
        controller.playbackParameters = PlaybackParameters(speed.coerceIn(0.25f, 4f), 1f)
    }

    fun setLooping(looping: Boolean) = withController { controller ->
        controller.repeatMode = if (looping) Player.REPEAT_MODE_ONE else Player.REPEAT_MODE_OFF
    }

    /** Called on a UI ticker while playing; the position is not pushed by the player. */
    fun refreshPosition() {
        val current = controller ?: return
        if (!current.isPlaying) return
        publish()
    }

    private fun publish() {
        val current = controller ?: return
        _state.value = PlaybackState(
            recordingId = current.currentMediaItem?.mediaId?.toLongOrNull(),
            isPlaying = current.isPlaying,
            positionMs = current.currentPosition.coerceAtLeast(0),
            durationMs = current.duration.let { if (it > 0) it else 0 },
            speed = current.playbackParameters.speed,
            isLooping = current.repeatMode == Player.REPEAT_MODE_ONE,
            isReady = current.playbackState == Player.STATE_READY,
        )
    }

    private companion object {
        const val SKIP_MILLIS = 10_000L
    }
}
