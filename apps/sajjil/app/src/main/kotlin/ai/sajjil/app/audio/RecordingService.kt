package ai.sajjil.app.audio

import ai.sajjil.app.MainActivity
import ai.sajjil.app.R
import ai.sajjil.app.SajjilApplication
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import androidx.core.app.ServiceCompat
import androidx.lifecycle.LifecycleService
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.launch

/**
 * Keeps the process alive and the microphone open while recording.
 *
 * The service holds no audio state of its own — [RecordingSession] owns the recorder. Its only
 * jobs are to satisfy Android's foreground-service requirement and to present the notification
 * with working controls, which is also what puts recording controls on the lock screen.
 */
class RecordingService : LifecycleService() {

    private val session: RecordingSession
        get() = (application as SajjilApplication).services.recordingSession

    override fun onCreate() {
        super.onCreate()
        createChannel()

        // The notification follows the recorder's own state, so pausing from the notification and
        // pausing in the app produce exactly the same result with no state to keep in sync.
        lifecycleScope.launch {
            combine(session.state, session.elapsedMillis) { state, elapsed -> state to elapsed }
                .collect { (state, elapsed) ->
                    if (state == RecorderState.IDLE) {
                        stopSelf()
                    } else {
                        notificationManager().notify(NOTIFICATION_ID, buildNotification(state, elapsed))
                    }
                }
        }
    }

    override fun onBind(intent: Intent): IBinder? {
        super.onBind(intent)
        return null
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        super.onStartCommand(intent, flags, startId)

        when (intent?.action) {
            ACTION_PAUSE -> session.pause()
            ACTION_RESUME -> session.resume()
            ACTION_STOP -> {
                lifecycleScope.launch { session.stop() }
                return START_NOT_STICKY
            }
        }

        startForegroundCompat()
        // START_NOT_STICKY: if the system kills us, the recording is already on disk and is
        // recovered at next launch. Silently restarting a service with no microphone stream would
        // be worse than stopping cleanly.
        return START_NOT_STICKY
    }

    private fun startForegroundCompat() {
        val notification = buildNotification(session.state.value, session.elapsedMillis.value)
        ServiceCompat.startForeground(
            this,
            NOTIFICATION_ID,
            notification,
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE
            } else {
                0
            },
        )
    }

    private fun buildNotification(state: RecorderState, elapsedMillis: Long): Notification {
        val openApp = PendingIntent.getActivity(
            this,
            0,
            Intent(this, MainActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP
            },
            PendingIntent.FLAG_IMMUTABLE,
        )

        val paused = state == RecorderState.PAUSED
        val builder = NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_notification_record)
            .setContentTitle(
                getString(
                    if (paused) R.string.notification_recording_paused else R.string.notification_recording_title
                )
            )
            .setContentText(formatElapsed(elapsedMillis))
            .setContentIntent(openApp)
            .setOngoing(true)
            .setSilent(true)
            .setCategory(NotificationCompat.CATEGORY_SERVICE)
            .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            // A running timer is the one thing worth glancing at from the lock screen.
            .setUsesChronometer(!paused)
            .setWhen(System.currentTimeMillis() - elapsedMillis)

        if (paused) {
            builder.addAction(
                R.drawable.ic_notification_record,
                getString(R.string.action_resume),
                servicePendingIntent(ACTION_RESUME, 1),
            )
        } else {
            builder.addAction(
                R.drawable.ic_notification_pause,
                getString(R.string.action_pause),
                servicePendingIntent(ACTION_PAUSE, 2),
            )
        }
        builder.addAction(
            R.drawable.ic_notification_stop,
            getString(R.string.action_stop),
            servicePendingIntent(ACTION_STOP, 3),
        )

        return builder.build()
    }

    private fun servicePendingIntent(action: String, requestCode: Int): PendingIntent =
        PendingIntent.getService(
            this,
            requestCode,
            Intent(this, RecordingService::class.java).setAction(action),
            PendingIntent.FLAG_IMMUTABLE,
        )

    private fun createChannel() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val channel = NotificationChannel(
            CHANNEL_ID,
            getString(R.string.notification_channel_recording),
            NotificationManager.IMPORTANCE_LOW,
        ).apply {
            description = getString(R.string.notification_channel_recording_description)
            setShowBadge(false)
            setSound(null, null)
            enableVibration(false)
        }
        notificationManager().createNotificationChannel(channel)
    }

    private fun notificationManager(): NotificationManager =
        getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

    private fun formatElapsed(millis: Long): String {
        val totalSeconds = millis / 1000
        val minutes = totalSeconds / 60
        val seconds = totalSeconds % 60
        return if (minutes >= 60) {
            String.format("%d:%02d:%02d", minutes / 60, minutes % 60, seconds)
        } else {
            String.format("%d:%02d", minutes, seconds)
        }
    }

    companion object {
        private const val CHANNEL_ID = "sajjil.recording"
        private const val NOTIFICATION_ID = 1001

        private const val ACTION_PAUSE = "ai.sajjil.app.RECORD_PAUSE"
        private const val ACTION_RESUME = "ai.sajjil.app.RECORD_RESUME"
        private const val ACTION_STOP = "ai.sajjil.app.RECORD_STOP"

        fun start(context: Context) {
            val intent = Intent(context, RecordingService::class.java)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(intent)
            } else {
                context.startService(intent)
            }
        }

        /** Nudges the service so the notification redraws immediately after a state change. */
        fun update(context: Context) {
            context.startService(Intent(context, RecordingService::class.java))
        }

        fun stop(context: Context) {
            context.stopService(Intent(context, RecordingService::class.java))
        }
    }
}
