package ai.sautiy.ui.components

import ai.sautiy.ui.theme.SautiySize
import ai.sautiy.ui.theme.SautiySpace
import ai.sautiy.ui.theme.SautiyTheme
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.size
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.Dp

/**
 * The visual vocabulary — arcs, rings and bars instead of sentences.
 *
 * A recorder that reports itself in prose makes the user read during the one activity where they
 * should be listening. An arc that sits in the middle when the level is right is understood without
 * being read, in peripheral vision, by somebody who is speaking at the time. That is the whole
 * argument for these: not that they look better, but that they can be understood while busy.
 *
 * Three rules hold across everything here, and they are the reason these are not decoration:
 *
 * * **A number is always available.** Every gauge carries its value as text, small, beside or
 *   under it. Professionals need to write settings down, compare two takes and describe a problem
 *   to somebody else, and a dial whose position is the only record of its value defeats all three.
 * * **Colour is never the only signal.** Position, length and a word carry the same information,
 *   because roughly one man in twelve cannot rely on the colour.
 * * **Nothing here animates faster than the eye integrates.** A gauge that flickers is a gauge
 *   nobody can read, and a calm screen is the point of the recording view.
 */

/**
 * A value from 0 to 1 as an arc, with its own label and reading.
 *
 * The workhorse. Used for level, enhancement strength, Voice Space intensity and approval, so
 * those four read as one family rather than four separate widgets.
 *
 * @param sweet the band the value ought to be in, drawn as a lighter arc behind the value.
 *   For level this is the comfortable recording window; for others there is no correct answer and
 *   it is null.
 */
@Composable
fun ValueArc(
    label: String,
    value: Double,
    reading: String,
    modifier: Modifier = Modifier,
    diameter: Dp = SautiySize.gaugeLarge,
    tint: Color? = null,
    sweet: ClosedFloatingPointRange<Float>? = null,
) {
    val colours = SautiyTheme.colours
    val colour = tint ?: colours.signal
    // Slow enough to read, fast enough not to lag behind a decision. The same easing as every
    // other transition in the app, so nothing here feels like a different product.
    val animated by animateFloatAsState(
        targetValue = value.toFloat().coerceIn(0f, 1f),
        label = label,
    )

    Column(
        modifier = modifier.semantics { contentDescription = "$label, $reading" },
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Box(modifier = Modifier.size(diameter), contentAlignment = Alignment.Center) {
            Canvas(modifier = Modifier.size(diameter)) {
                val stroke = size.minDimension * 0.11f
                val inset = stroke / 2
                val arcSize = Size(size.width - stroke, size.height - stroke)
                val topLeft = Offset(inset, inset)

                // 270° of travel with the gap at the bottom: an open arc reads as a scale, a
                // closed ring reads as progress, and this is a scale.
                val start = 135f
                val total = 270f

                drawArc(
                    color = colours.surfaceRaised,
                    startAngle = start,
                    sweepAngle = total,
                    useCenter = false,
                    topLeft = topLeft,
                    size = arcSize,
                    style = Stroke(width = stroke, cap = StrokeCap.Round),
                )

                if (sweet != null) {
                    drawArc(
                        color = colour.copy(alpha = 0.22f),
                        startAngle = start + total * sweet.start,
                        sweepAngle = total * (sweet.endInclusive - sweet.start),
                        useCenter = false,
                        topLeft = topLeft,
                        size = arcSize,
                        style = Stroke(width = stroke, cap = StrokeCap.Butt),
                    )
                }

                drawArc(
                    color = colour,
                    startAngle = start,
                    sweepAngle = total * animated,
                    useCenter = false,
                    topLeft = topLeft,
                    size = arcSize,
                    style = Stroke(width = stroke, cap = StrokeCap.Round),
                )
            }

            // The number lives inside the arc. Available without being prominent, which is the
            // right weight for something a professional needs and a beginner does not.
            Text(
                text = reading,
                style = SautiyTheme.type.numeric,
                color = colours.textPrimary,
                textAlign = TextAlign.Center,
            )
        }
        Spacer(modifier = Modifier.height(SautiySpace.xxs))
        Text(
            text = label,
            style = SautiyTheme.type.labelSmall,
            color = colours.textTertiary,
            textAlign = TextAlign.Center,
        )
    }
}

/**
 * A single condition as a dot and a word: quiet room, clean, clipped.
 *
 * The word is not a fallback for the colour — it is the primary signal, and the colour is the
 * thing that makes it findable at a glance. Written the other way round, the indicator would be
 * unusable for anyone who cannot separate ember from green.
 */
@Composable
fun ConditionDot(
    label: String,
    good: Boolean,
    warning: Boolean = false,
    modifier: Modifier = Modifier,
) {
    val colours = SautiyTheme.colours
    val colour = when {
        warning -> colours.critical
        good -> colours.commit
        else -> colours.textTertiary
    }
    Row(
        modifier = modifier.semantics { contentDescription = label },
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(SautiySpace.xs),
    ) {
        Canvas(modifier = Modifier.size(SautiySize.dot)) {
            drawCircle(color = colour)
        }
        Text(text = label, style = SautiyTheme.type.labelSmall, color = colours.textSecondary)
    }
}

/**
 * A row of arcs, evenly spaced, so a panel of instruments cannot drift out of alignment.
 *
 * Exists so the spacing is decided once rather than at each of the two call sites.
 */
@Composable
fun GaugeRow(
    modifier: Modifier = Modifier,
    content: @Composable () -> Unit,
) {
    Row(
        modifier = modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceEvenly,
        verticalAlignment = Alignment.Top,
    ) {
        content()
    }
}

// `RangeBar` and `GaugeGap` were here, and nothing ever called them.
//
// I wrote both two cycles ago while building the visual vocabulary, on the assumption that dynamic
// range wanted its own indicator and that a row of arcs would need a spacer. Neither turned out to
// be true: the range reads perfectly well as one of the arcs, and `GaugeRow` spaces itself.
//
// Sixty lines of composable that has never been drawn on a screen is not a component, it is a
// liability — it compiles, it looks finished, and the first person to use it will find out whether
// it works. Work already invested is not a reason to keep something.
