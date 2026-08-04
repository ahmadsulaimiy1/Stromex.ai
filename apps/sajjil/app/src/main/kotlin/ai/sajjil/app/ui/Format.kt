package ai.sajjil.app.ui

import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Date
import java.util.Locale
import kotlin.math.abs

/**
 * Formatting shared across screens.
 *
 * Centralised so a duration reads identically on a Library card, in the transport bar and on the
 * export sheet. Inconsistent time formatting is a small thing that makes an interface feel
 * assembled rather than designed.
 */
object Format {

    /** `M:SS`, or `H:MM:SS` past an hour. The form people expect from a recorder. */
    fun duration(millis: Long): String {
        val totalSeconds = (millis / 1000).coerceAtLeast(0)
        val hours = totalSeconds / 3600
        val minutes = (totalSeconds % 3600) / 60
        val seconds = totalSeconds % 60
        return if (hours > 0) {
            String.format(Locale.US, "%d:%02d:%02d", hours, minutes, seconds)
        } else {
            String.format(Locale.US, "%d:%02d", minutes, seconds)
        }
    }

    /** `MM:SS.d` for the recording timer, where tenths show that something is happening. */
    fun timer(millis: Long): String {
        val totalSeconds = (millis / 1000).coerceAtLeast(0)
        val tenths = (millis % 1000) / 100
        val hours = totalSeconds / 3600
        val minutes = (totalSeconds % 3600) / 60
        val seconds = totalSeconds % 60
        return if (hours > 0) {
            String.format(Locale.US, "%d:%02d:%02d.%d", hours, minutes, seconds, tenths)
        } else {
            String.format(Locale.US, "%02d:%02d.%d", minutes, seconds, tenths)
        }
    }

    /** Spoken form for screen readers: "3 minutes 12 seconds", not "3:12". */
    fun spokenDuration(millis: Long): String {
        val totalSeconds = (millis / 1000).coerceAtLeast(0)
        val hours = totalSeconds / 3600
        val minutes = (totalSeconds % 3600) / 60
        val seconds = totalSeconds % 60
        return buildString {
            if (hours > 0) append("$hours ${plural(hours, "hour")} ")
            if (minutes > 0) append("$minutes ${plural(minutes, "minute")} ")
            append("$seconds ${plural(seconds, "second")}")
        }.trim()
    }

    fun fileSize(bytes: Long): String = when {
        bytes >= 1_000_000_000 -> String.format(Locale.US, "%.1f GB", bytes / 1_000_000_000.0)
        bytes >= 1_000_000 -> String.format(Locale.US, "%.0f MB", bytes / 1_000_000.0)
        bytes >= 1_000 -> String.format(Locale.US, "%.0f KB", bytes / 1_000.0)
        else -> "$bytes bytes"
    }

    /** "Today", "Yesterday", a weekday within the last week, then a date. */
    fun relativeDate(millis: Long, now: Long = System.currentTimeMillis()): String {
        val then = Calendar.getInstance().apply { timeInMillis = millis }
        val today = Calendar.getInstance().apply { timeInMillis = now }

        val sameYear = then.get(Calendar.YEAR) == today.get(Calendar.YEAR)
        val dayDifference = daysBetween(then, today)

        return when {
            dayDifference == 0 -> "Today, " + SimpleDateFormat("HH:mm", Locale.getDefault()).format(Date(millis))
            dayDifference == 1 -> "Yesterday, " + SimpleDateFormat("HH:mm", Locale.getDefault()).format(Date(millis))
            dayDifference in 2..6 -> SimpleDateFormat("EEEE, HH:mm", Locale.getDefault()).format(Date(millis))
            sameYear -> SimpleDateFormat("d MMM", Locale.getDefault()).format(Date(millis))
            else -> SimpleDateFormat("d MMM yyyy", Locale.getDefault()).format(Date(millis))
        }
    }

    /** Storage headroom phrased as recording time, which is what the number is actually for. */
    fun remainingRecordingTime(seconds: Long): String = when {
        seconds >= 7200 -> "${seconds / 3600} hours left"
        seconds >= 3600 -> "1 hour left"
        seconds >= 120 -> "${seconds / 60} minutes left"
        seconds >= 60 -> "1 minute left"
        else -> "Less than a minute left"
    }

    fun loudness(lufs: Double?): String =
        if (lufs == null) "—" else String.format(Locale.US, "%.1f LUFS", lufs)

    fun decibels(db: Double): String =
        if (db <= -119.0) "−∞ dB" else String.format(Locale.US, "%.1f dB", db)

    fun percent(fraction: Double): String =
        String.format(Locale.US, "%d%%", (fraction.coerceIn(0.0, 1.0) * 100).toInt())

    private fun plural(count: Long, word: String) = if (count == 1L) word else "${word}s"

    private fun daysBetween(then: Calendar, today: Calendar): Int {
        val a = then.clone() as Calendar
        val b = today.clone() as Calendar
        listOf(a, b).forEach {
            it.set(Calendar.HOUR_OF_DAY, 0)
            it.set(Calendar.MINUTE, 0)
            it.set(Calendar.SECOND, 0)
            it.set(Calendar.MILLISECOND, 0)
        }
        val difference = b.timeInMillis - a.timeInMillis
        return (abs(difference) / (24L * 60 * 60 * 1000)).toInt()
    }
}
