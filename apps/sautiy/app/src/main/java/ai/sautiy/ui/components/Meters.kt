package ai.sautiy.ui.components

import ai.sautiy.core.audio.Decibels
import ai.sautiy.core.design.Motion
import ai.sautiy.ui.theme.SautiySpace
import ai.sautiy.ui.theme.SautiyTheme
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import kotlin.math.roundToInt

/**
 * The input level meter — Editorial Bible chapter 1.4 principle 5 and chapter 2.6.
 *
 * The ballistics are broadcast-style and are the whole point: **instant attack, 20 dB/second
 * release, with a peak hold that dwells before it falls.** A meter that follows the signal
 * exactly is unreadable — it flickers faster than the eye integrates — and one that is smoothed
 * in both directions under-reports peaks, which is a meter that lies about the only thing it
 * exists to warn you about.
 *
 * The scale is deliberately not linear in dB either. The top 20 dB, where clipping lives, gets
 * half the width, because that is the region a person is actually watching.
 */
@Composable
fun LevelMeter(
    peakDb: Double,
    rmsDb: Double,
    modifier: Modifier = Modifier,
    height: androidx.compose.ui.unit.Dp = 8.dp,
) {
    val colours = SautiyTheme.colours

    var displayedPeak by remember { mutableFloatStateOf(FLOOR_DB.toFloat()) }
    var heldPeak by remember { mutableFloatStateOf(FLOOR_DB.toFloat()) }
    var holdUntil by remember { mutableLongStateOf(0L) }

    LaunchedEffect(peakDb) {
        val now = System.currentTimeMillis()
        // Instant attack.
        if (peakDb > displayedPeak) displayedPeak = peakDb.toFloat()
        if (peakDb >= heldPeak) {
            heldPeak = peakDb.toFloat()
            holdUntil = now + Motion.PEAK_HOLD_DWELL_MS
        }
    }

    // Release, driven by wall clock rather than by frame count so the stated dB-per-second is
    // true regardless of how the display is performing.
    LaunchedEffect(Unit) {
        var last = System.currentTimeMillis()
        while (true) {
            kotlinx.coroutines.delay(16)
            val now = System.currentTimeMillis()
            val elapsed = (now - last) / 1000.0
            last = now
            displayedPeak = (displayedPeak - Motion.METER_RELEASE_DB_PER_SEC * elapsed)
                .coerceAtLeast(FLOOR_DB).toFloat()
            if (now > holdUntil) {
                heldPeak = (heldPeak - Motion.PEAK_HOLD_FALL_DB_PER_SEC * elapsed)
                    .coerceAtLeast(FLOOR_DB).toFloat()
            }
        }
    }

    Canvas(
        modifier = modifier
            .fillMaxWidth()
            .height(height)
            .semantics { contentDescription = "Input level, ${peakDb.roundToInt()} decibels" },
    ) {
        val cornerRadius = androidx.compose.ui.geometry.CornerRadius(size.height / 2f)
        drawRoundRect(color = colours.surfaceRaised, cornerRadius = cornerRadius)

        val peakFraction = scalePosition(displayedPeak.toDouble())
        val rmsFraction = scalePosition(rmsDb)

        // The RMS body: what the recording will sound like.
        drawRoundRect(
            brush = Brush.horizontalGradient(
                0.0f to colours.safe,
                0.72f to colours.safe,
                0.88f to colours.caution,
                1.0f to colours.critical,
                startX = 0f,
                endX = size.width,
            ),
            size = Size((size.width * rmsFraction).toFloat().coerceAtLeast(0f), size.height),
            cornerRadius = cornerRadius,
        )

        // The peak line: what will clip.
        val peakX = (size.width * peakFraction).toFloat()
        drawLine(
            color = if (displayedPeak >= -0.1f) colours.critical else colours.textPrimary,
            start = Offset(peakX, 0f),
            end = Offset(peakX, size.height),
            strokeWidth = 2.dp.toPx(),
            cap = StrokeCap.Round,
        )

        // The held peak: still visible a second after it happened, which is the only way to
        // catch a transient you were not looking at.
        val heldX = (size.width * scalePosition(heldPeak.toDouble())).toFloat()
        drawLine(
            color = if (heldPeak >= -0.1f) colours.critical else colours.textTertiary,
            start = Offset(heldX, 0f),
            end = Offset(heldX, size.height),
            strokeWidth = 1.5.dp.toPx(),
            cap = StrokeCap.Round,
        )
    }
}

private const val FLOOR_DB = -60.0

/**
 * Non-linear meter scale: the top 20 dB occupy half the width.
 *
 * A linear-in-dB meter spends most of its length on levels nobody is watching and compresses
 * the region between "good" and "clipped" into a few pixels.
 */
private fun scalePosition(db: Double): Double {
    val clamped = db.coerceIn(FLOOR_DB, 0.0)
    return if (clamped >= -20.0) {
        0.5 + 0.5 * (clamped + 20.0) / 20.0
    } else {
        0.5 * (clamped - FLOOR_DB) / (-20.0 - FLOOR_DB)
    }
}

/**
 * The recording quality gauge.
 *
 * A single number is only useful if the user can act on it, so the ring is accompanied by the
 * one sentence that explains the largest deduction. A score with no explanation is a score
 * that gets ignored.
 */
@Composable
fun QualityGauge(
    score: Int,
    reason: String,
    modifier: Modifier = Modifier,
    diameter: androidx.compose.ui.unit.Dp = 56.dp,
) {
    val colours = SautiyTheme.colours
    val ringColour = when {
        score >= 85 -> colours.safe
        score >= 60 -> colours.caution
        else -> colours.critical
    }

    Column(
        modifier = modifier.semantics {
            contentDescription = "Recording quality, $score out of 100. $reason"
        },
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Box(contentAlignment = Alignment.Center) {
            Canvas(modifier = Modifier.size(diameter)) {
                val stroke = 4.dp.toPx()
                drawArc(
                    color = colours.surfaceRaised,
                    startAngle = 135f,
                    sweepAngle = 270f,
                    useCenter = false,
                    style = Stroke(width = stroke, cap = StrokeCap.Round),
                )
                drawArc(
                    color = ringColour,
                    startAngle = 135f,
                    sweepAngle = 270f * (score / 100f),
                    useCenter = false,
                    style = Stroke(width = stroke, cap = StrokeCap.Round),
                )
            }
            Text(
                text = "$score",
                style = SautiyTheme.type.numeric,
                color = colours.textPrimary,
            )
        }
        Text(
            text = reason,
            style = SautiyTheme.type.labelSmall,
            color = colours.textTertiary,
            textAlign = TextAlign.Center,
            modifier = Modifier.padding(top = SautiySpace.xs),
        )
    }
}

/**
 * The storage indicator, stated in **minutes remaining** rather than in megabytes free.
 *
 * Chapter 3.2.5: nobody can convert 412 MB into "will this last the lecture?" without knowing
 * the bitrate, so SAUTIY does that arithmetic and states the answer.
 */
@Composable
fun StorageIndicator(
    secondsRemaining: Long,
    critical: Boolean,
    modifier: Modifier = Modifier,
) {
    val colours = SautiyTheme.colours
    val label = when {
        secondsRemaining >= 7_200 -> "${secondsRemaining / 3_600} h left"
        secondsRemaining >= 120 -> "${secondsRemaining / 60} min left"
        else -> "${secondsRemaining}s left"
    }
    Row(
        modifier = modifier,
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(SautiySpace.xs),
    ) {
        Text(
            text = label,
            style = SautiyTheme.type.labelSmall,
            color = if (critical) colours.caution else colours.textTertiary,
        )
    }
}

/** A dB readout in the house style: tabular figures, true minus sign, real floor. */
@Composable
fun DecibelReadout(db: Double, modifier: Modifier = Modifier) {
    Text(
        text = Decibels.format(db),
        style = SautiyTheme.type.numeric,
        color = if (db >= -0.1) SautiyTheme.colours.critical else SautiyTheme.colours.textSecondary,
        modifier = modifier,
    )
}
