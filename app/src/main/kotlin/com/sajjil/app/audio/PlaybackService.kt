package com.sajjil.app.audio

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder
import android.support.v4.media.MediaMetadataCompat
import android.support.v4.media.session.MediaSessionCompat
import android.support.v4.media.session.PlaybackStateCompat
import androidx.core.app.NotificationCompat
import androidx.media.app.NotificationCompat.MediaStyle
import com.sajjil.app.MainActivity
import com.sajjil.app.R
import com.sajjil.app.SajjilApplication
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.launch

/**
 * Lock-screen and notification playback controls for the app-wide shared player (the same
 * engine backing the mini-player). Uses the classic MediaSessionCompat/PlaybackStateCompat APIs
 * rather than Media3's Player-based MediaSession: the engine underneath is a raw
 * android.media.MediaPlayer, which does not implement Media3's Player interface, whereas
 * MediaSessionCompat works with any playback backend since its state is driven by hand here
 * instead of being introspected from a Player object.
 *
 * Not exercised by CI's smoke test: that test only launches MainActivity and never starts
 * playback, so this service's actual behaviour (does the notification render correctly, do the
 * transport buttons work, does the lock screen widget show up) has not been verified beyond
 * compiling and matching documented Android API contracts.
 */
class PlaybackService : Service() {
    private lateinit var mediaSession: MediaSessionCompat
    private var scope: CoroutineScope? = null

    override fun onCreate() {
        super.onCreate()
        val app = application as SajjilApplication
        ensureChannel()

        mediaSession = MediaSessionCompat(this, "SajjilPlayback").apply {
            setCallback(object : MediaSessionCompat.Callback() {
                override fun onPlay() {
                    app.playbackEngine.resume(app.playbackScope())
                }

                override fun onPause() {
                    app.playbackEngine.pause()
                }

                override fun onStop() {
                    app.playbackEngine.stop()
                }

                override fun onSeekTo(pos: Long) {
                    app.playbackEngine.seekTo(pos)
                }
            })
            isActive = true
        }

        val serviceScope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
        scope = serviceScope
        serviceScope.launch {
            combine(
                app.playbackEngine.playingFile,
                app.playbackEngine.nowPlayingLabel,
                app.playbackEngine.isPlaying,
                app.playbackEngine.positionMs,
                app.playbackEngine.durationMs,
            ) { file, label, isPlaying, positionMs, durationMs ->
                PlaybackSnapshot(hasFile = file != null, label = label, isPlaying = isPlaying, positionMs = positionMs, durationMs = durationMs)
            }.collect { snapshot ->
                if (!snapshot.hasFile) {
                    stopForeground(STOP_FOREGROUND_REMOVE)
                    stopSelf()
                    return@collect
                }
                updateSession(snapshot)
                startForeground(NOTIFICATION_ID, buildNotification(snapshot), foregroundServiceType())
            }
        }
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val app = application as SajjilApplication
        when (intent?.action) {
            ACTION_PLAY -> app.playbackEngine.resume(app.playbackScope())
            ACTION_PAUSE -> app.playbackEngine.pause()
            ACTION_STOP -> app.playbackEngine.stop()
        }
        return START_NOT_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        super.onDestroy()
        scope?.cancel()
        mediaSession.isActive = false
        mediaSession.release()
    }

    private fun updateSession(snapshot: PlaybackSnapshot) {
        mediaSession.setMetadata(
            MediaMetadataCompat.Builder()
                .putString(MediaMetadataCompat.METADATA_KEY_TITLE, snapshot.label ?: getString(R.string.app_name))
                .putLong(MediaMetadataCompat.METADATA_KEY_DURATION, snapshot.durationMs)
                .build(),
        )
        val state = if (snapshot.isPlaying) PlaybackStateCompat.STATE_PLAYING else PlaybackStateCompat.STATE_PAUSED
        mediaSession.setPlaybackState(
            PlaybackStateCompat.Builder()
                .setActions(
                    PlaybackStateCompat.ACTION_PLAY or PlaybackStateCompat.ACTION_PAUSE or
                        PlaybackStateCompat.ACTION_SEEK_TO or PlaybackStateCompat.ACTION_STOP,
                )
                .setState(state, snapshot.positionMs, 1f)
                .build(),
        )
    }

    private fun buildNotification(snapshot: PlaybackSnapshot): Notification {
        val contentIntent = PendingIntent.getActivity(
            this, 0, Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
        )
        val playPauseAction = if (snapshot.isPlaying) {
            NotificationCompat.Action.Builder(android.R.drawable.ic_media_pause, "Pause", servicePendingIntent(ACTION_PAUSE)).build()
        } else {
            NotificationCompat.Action.Builder(android.R.drawable.ic_media_play, "Play", servicePendingIntent(ACTION_PLAY)).build()
        }
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle(snapshot.label ?: getString(R.string.app_name))
            .setContentText(getString(R.string.app_name))
            .setSmallIcon(android.R.drawable.presence_audio_online)
            .setContentIntent(contentIntent)
            .addAction(playPauseAction)
            .setStyle(MediaStyle().setMediaSession(mediaSession.sessionToken).setShowActionsInCompactView(0))
            .setOngoing(snapshot.isPlaying)
            .build()
    }

    private fun servicePendingIntent(action: String): PendingIntent {
        val intent = Intent(this, PlaybackService::class.java).setAction(action)
        return PendingIntent.getService(this, action.hashCode(), intent, PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
    }

    private fun ensureChannel() {
        val manager = getSystemService(NotificationManager::class.java)
        if (manager.getNotificationChannel(CHANNEL_ID) == null) {
            manager.createNotificationChannel(
                NotificationChannel(CHANNEL_ID, getString(R.string.playback_notification_channel), NotificationManager.IMPORTANCE_LOW),
            )
        }
    }

    private fun foregroundServiceType(): Int =
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PLAYBACK else 0

    private data class PlaybackSnapshot(
        val hasFile: Boolean,
        val label: String?,
        val isPlaying: Boolean,
        val positionMs: Long,
        val durationMs: Long,
    )

    companion object {
        private const val CHANNEL_ID = "sajjil_playback"
        private const val NOTIFICATION_ID = 1002
        const val ACTION_PLAY = "com.sajjil.app.action.PLAY"
        const val ACTION_PAUSE = "com.sajjil.app.action.PAUSE"
        const val ACTION_STOP = "com.sajjil.app.action.STOP"
    }
}
