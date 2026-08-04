package ai.sajjil.app

import ai.sajjil.app.ui.Format
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.util.Calendar

/**
 * Formatting is shared by every screen, so a mistake here shows up in several places at once and
 * is the kind of thing that reads as sloppiness rather than as a bug.
 */
class FormatTest {

    @Test
    fun `durations read as minutes and seconds`() {
        assertEquals("0:00", Format.duration(0))
        assertEquals("0:05", Format.duration(5_000))
        assertEquals("1:00", Format.duration(60_000))
        assertEquals("2:03", Format.duration(123_000))
        assertEquals("59:59", Format.duration(3_599_000))
    }

    @Test
    fun `durations past an hour gain an hours field`() {
        assertEquals("1:00:00", Format.duration(3_600_000))
        assertEquals("2:05:07", Format.duration(2 * 3_600_000L + 5 * 60_000 + 7_000))
    }

    @Test
    fun `a negative duration does not produce a negative display`() {
        // Clock skew or an arithmetic slip must not put "-1:-30" in front of a user.
        assertEquals("0:00", Format.duration(-5_000))
    }

    @Test
    fun `the timer shows tenths so it visibly moves`() {
        assertEquals("00:00.0", Format.timer(0))
        assertEquals("00:05.3", Format.timer(5_300))
        assertEquals("01:00.0", Format.timer(60_000))
        assertEquals("1:00:00.0", Format.timer(3_600_000))
    }

    @Test
    fun `spoken durations are words rather than a clock face`() {
        // Screen readers say "three minutes twelve seconds"; "3:12" would be read as a number.
        assertEquals("12 seconds", Format.spokenDuration(12_000))
        assertEquals("1 second", Format.spokenDuration(1_000))
        assertEquals("3 minutes 12 seconds", Format.spokenDuration(192_000))
        // A zero minutes field is dropped, but zero seconds is kept so the phrase never ends
        // mid-thought.
        assertEquals("1 hour 0 seconds", Format.spokenDuration(3_600_000))
        assertEquals("1 hour 30 minutes 0 seconds", Format.spokenDuration(5_400_000))
    }

    @Test
    fun `file sizes step through the usual units`() {
        assertEquals("512 bytes", Format.fileSize(512))
        assertEquals("2 KB", Format.fileSize(2_000))
        assertEquals("5 MB", Format.fileSize(5_000_000))
        assertEquals("1.5 GB", Format.fileSize(1_500_000_000))
    }

    @Test
    fun `recent dates are relative and older ones are absolute`() {
        val now = Calendar.getInstance().apply {
            set(2026, Calendar.MARCH, 15, 14, 30, 0)
            set(Calendar.MILLISECOND, 0)
        }.timeInMillis

        val earlierToday = now - 2 * 60 * 60 * 1000
        assertTrue(
            "expected a Today label, got ${Format.relativeDate(earlierToday, now)}",
            Format.relativeDate(earlierToday, now).startsWith("Today"),
        )

        val yesterday = now - 24 * 60 * 60 * 1000
        assertTrue(
            "expected a Yesterday label, got ${Format.relativeDate(yesterday, now)}",
            Format.relativeDate(yesterday, now).startsWith("Yesterday"),
        )

        val lastMonth = now - 40L * 24 * 60 * 60 * 1000
        val label = Format.relativeDate(lastMonth, now)
        assertTrue(
            "a date over a week old should not be relative, got $label",
            !label.startsWith("Today") && !label.startsWith("Yesterday"),
        )
    }

    @Test
    fun `remaining time is phrased as recording time`() {
        // The number only matters as "how much longer can I record", so that is what it says.
        assertEquals("2 hours left", Format.remainingRecordingTime(7_200))
        assertEquals("1 hour left", Format.remainingRecordingTime(3_600))
        assertEquals("30 minutes left", Format.remainingRecordingTime(1_800))
        assertEquals("1 minute left", Format.remainingRecordingTime(90))
        assertEquals("Less than a minute left", Format.remainingRecordingTime(30))
    }

    @Test
    fun `unmeasured loudness shows a dash rather than a fake number`() {
        assertEquals("—", Format.loudness(null))
        assertEquals("-16.0 LUFS", Format.loudness(-16.0))
    }

    @Test
    fun `silence is shown as minus infinity rather than a large negative number`() {
        assertEquals("−∞ dB", Format.decibels(-120.0))
        assertEquals("-6.0 dB", Format.decibels(-6.0))
    }

    @Test
    fun `percentages are clamped into range`() {
        assertEquals("0%", Format.percent(-1.0))
        assertEquals("50%", Format.percent(0.5))
        assertEquals("100%", Format.percent(2.0))
    }
}
