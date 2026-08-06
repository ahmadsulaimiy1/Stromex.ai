package ai.sautiy.record

import ai.sautiy.R
import ai.sautiy.SautiyActivity
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
import android.os.PowerManager

/**
 * Keeps capture alive — Editorial Bible chapter 7 and chapter 1.3.5.
 *
 * This service exists for one reason: Dr Aisha records a ninety-minute lecture from a bag with
 * the screen off. Without a foreground service the process is a background app after a few
 * minutes and the system is entitled to kill it — and a recorder that dies at minute forty-two
 * is not a recorder.
 *
 * The notification it must post is not treated as an interruption under chapter 3.2.7, because
 * it is not an interruption: it is the operating system's contract for "this app is using your
 * microphone right now", it appears only while capturing, and the user would be entitled to be
 * alarmed by its absence. It is deliberately silent, unswipeable and free of any content beyond
 * the fact and the elapsed time.
 */
class RecordingService : Service() {

    private var wakeLock: PowerManager.WakeLock? = null

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_STOP -> {
                stopCapture()
                return START_NOT_STICKY
            }
        }

        createChannel()
        val paused = intent?.getBooleanExtra(EXTRA_PAUSED, false) ?: false
        startForegroundCompat(buildNotification(paused))
        acquireWakeLock()

        // START_STICKY on purpose. If the system does kill the process under memory pressure,
        // it restarts the service, and the take on disk is intact up to the last flush — so the
        // recording is recoverable rather than lost.
        return START_STICKY
    }

    override fun onDestroy() {
        releaseWakeLock()
        super.onDestroy()
    }

    private fun stopCapture() {
        releaseWakeLock()
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
    }

    private fun startForegroundCompat(notification: Notification) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            startForeground(NOTIFICATION_ID, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE)
        } else {
            startForeground(NOTIFICATION_ID, notification)
        }
    }

    /**
     * A partial wake lock only.
     *
     * The CPU must keep running to service the audio callback; the screen must not, because a
     * lecture recorded with the display on is a lecture that ends when the battery does.
     */
    private fun acquireWakeLock() {
        if (wakeLock != null) return
        val power = getSystemService(Context.POWER_SERVICE) as PowerManager
        wakeLock = power.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, WAKE_LOCK_TAG).apply {
            setReferenceCounted(false)
            acquire(MAX_RECORDING_MS)
        }
    }

    private fun releaseWakeLock() {
        wakeLock?.let { if (it.isHeld) it.release() }
        wakeLock = null
    }

    private fun createChannel() {
        val manager = getSystemService(NotificationManager::class.java)
        val channel = NotificationChannel(
            CHANNEL_ID,
            getString(R.string.notification_channel_recording),
            // LOW: it must be visible, and it must never make a sound or vibrate — SAUTIY is
            // recording, and a notification chime would end up in the recording.
            NotificationManager.IMPORTANCE_LOW,
        ).apply {
            setSound(null, null)
            enableVibration(false)
            setShowBadge(false)
        }
        manager.createNotificationChannel(channel)
    }

    private fun buildNotification(paused: Boolean): Notification {
        val open = PendingIntent.getActivity(
            this,
            0,
            Intent(this, SautiyActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP
            },
            PendingIntent.FLAG_IMMUTABLE,
        )

        return Notification.Builder(this, CHANNEL_ID)
            .setContentTitle(
                getString(
                    if (paused) R.string.notification_recording_paused else R.string.notification_recording_title,
                ),
            )
            .setSmallIcon(R.drawable.ic_launcher_monochrome)
            .setContentIntent(open)
            .setOngoing(true)
            .setShowWhen(true)
            .setUsesChronometer(!paused)
            .setCategory(Notification.CATEGORY_SERVICE)
            .setVisibility(Notification.VISIBILITY_PUBLIC)
            .build()
    }

    companion object {
        private const val CHANNEL_ID = "sautiy.recording"
        private const val NOTIFICATION_ID = 1
        private const val WAKE_LOCK_TAG = "sautiy:capture"
        private const val ACTION_STOP = "ai.sautiy.action.STOP_RECORDING"
        private const val EXTRA_PAUSED = "paused"

        /** Eight hours. Long enough for any real session, bounded so a bug cannot hold the CPU forever. */
        private const val MAX_RECORDING_MS = 8L * 60 * 60 * 1000

        fun start(context: Context, paused: Boolean = false) {
            val intent = Intent(context, RecordingService::class.java).putExtra(EXTRA_PAUSED, paused)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(intent)
            } else {
                context.startService(intent)
            }
        }

        fun stop(context: Context) {
            context.startService(Intent(context, RecordingService::class.java).setAction(ACTION_STOP))
        }
    }
}
