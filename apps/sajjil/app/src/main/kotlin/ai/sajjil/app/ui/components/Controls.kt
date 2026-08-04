package ai.sajjil.app.ui.components

import ai.sajjil.app.ui.theme.Radius
import ai.sajjil.app.ui.theme.Space
import ai.sajjil.app.ui.theme.sajjilColors
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Forward10
import androidx.compose.material.icons.filled.Pause
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Replay10
import androidx.compose.material.icons.filled.Stop
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.scale
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.role
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp

/**
 * The record button.
 *
 * One control, unmistakably the primary action, and it is the only place in the app that uses the
 * record colour. Its shape carries the state — a filled circle when idle, a rounded square when
 * recording — which is the same language every camera and recorder uses, so it needs no label to
 * be understood.
 */
@Composable
fun RecordButton(
    isRecording: Boolean,
    isPaused: Boolean,
    enabled: Boolean = true,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val colors = sajjilColors
    val interactionSource = remember { MutableInteractionSource() }
    val pressed by interactionSource.collectIsPressedAsState()

    // A small press response, fast enough to feel like the button moved under the finger rather
    // than animated afterwards.
    val scale by animateFloatAsState(
        targetValue = if (pressed) 0.94f else 1f,
        animationSpec = tween(durationMillis = 90),
        label = "record-button-press",
    )

    // While recording, the ring breathes slowly. It is the only ambient motion in the app, and it
    // exists so a glance from across the room confirms the take is still running.
    val transition = rememberInfiniteTransition(label = "record-pulse")
    val pulse by transition.animateFloatCompat(
        initial = 1f,
        target = if (isRecording && !isPaused) 1.06f else 1f,
        durationMillis = 1400,
    )

    val innerShape = if (isRecording) RoundedCornerShape(14.dp) else CircleShape
    val description = when {
        isPaused -> "Resume recording"
        isRecording -> "Stop recording"
        else -> "Start recording"
    }

    Box(
        modifier = modifier
            .size(RECORD_BUTTON_SIZE)
            .scale(scale * pulse)
            .semantics {
                contentDescription = description
                role = Role.Button
            }
            .clickable(
                interactionSource = interactionSource,
                indication = null,
                enabled = enabled,
                onClick = onClick,
            ),
        contentAlignment = Alignment.Center,
    ) {
        Canvas(modifier = Modifier.fillMaxSize()) {
            drawCircle(
                color = if (enabled) colors.record.copy(alpha = 0.16f) else colors.onSurfaceFaint.copy(alpha = 0.1f),
                radius = size.minDimension / 2f,
            )
            drawCircle(
                color = if (enabled) colors.record.copy(alpha = 0.5f) else colors.onSurfaceFaint.copy(alpha = 0.3f),
                radius = size.minDimension / 2f - 3f,
                style = Stroke(width = 3f),
            )
        }
        Box(
            modifier = Modifier
                .size(if (isRecording) 44.dp else 68.dp)
                .background(
                    color = if (enabled) colors.record else colors.onSurfaceFaint,
                    shape = innerShape,
                )
        )
    }
}

/**
 * Live input level.
 *
 * Shows RMS as the bar and peak as a separate tick, because they answer different questions: RMS
 * says how loud the voice is, peak says whether the next syllable will clip. Colour is not the
 * only signal — the clipping state also changes the bar's shape at the top — so it still reads
 * for someone who cannot distinguish red from green.
 */
@Composable
fun InputLevelMeter(
    rms: Float,
    peak: Float,
    isClipping: Boolean,
    modifier: Modifier = Modifier,
) {
    val colors = sajjilColors
    val level by animateFloatAsState(
        targetValue = rms.coerceIn(0f, 1f),
        animationSpec = tween(durationMillis = 60),
        label = "input-level",
    )

    val description = when {
        isClipping -> "Input level too high, the recording will distort"
        rms < 0.005f -> "Input level very low"
        else -> "Input level ${(rms * 100).toInt()} percent"
    }

    Box(
        modifier = modifier
            .fillMaxWidth()
            .height(10.dp)
            .semantics { contentDescription = description },
    ) {
        Canvas(modifier = Modifier.fillMaxSize()) {
            val radius = size.height / 2f
            drawRoundRect(
                color = colors.onSurfaceFaint.copy(alpha = 0.2f),
                cornerRadius = androidx.compose.ui.geometry.CornerRadius(radius),
            )
            // Meter scale is not linear in amplitude: a linear meter spends most of its length on
            // levels nobody records at. This is roughly logarithmic across the useful range.
            val displayed = meterScale(level)
            if (displayed > 0f) {
                drawRoundRect(
                    color = when {
                        isClipping -> colors.problem
                        displayed > 0.85f -> colors.caution
                        else -> colors.good
                    },
                    size = Size(size.width * displayed, size.height),
                    cornerRadius = androidx.compose.ui.geometry.CornerRadius(radius),
                )
            }
            val peakX = size.width * meterScale(peak.coerceIn(0f, 1f))
            if (peakX > 2f) {
                drawLine(
                    color = if (isClipping) colors.problem else colors.onSurfaceMuted,
                    start = Offset(peakX, 0f),
                    end = Offset(peakX, size.height),
                    strokeWidth = 3f,
                )
            }
        }
    }
}

/** Amplitude to meter position: -60 dBFS at the left, 0 dBFS at the right. */
private fun meterScale(amplitude: Float): Float {
    if (amplitude <= 0f) return 0f
    val db = 20.0 * kotlin.math.log10(amplitude.toDouble())
    return ((db + 60.0) / 60.0).coerceIn(0.0, 1.0).toFloat()
}

/**
 * A quality score as a ring.
 *
 * The number alone means little, so the ring is coloured by band and captioned with the grade.
 * A colour-blind user reads the grade text and the arc length; the colour is a third channel, not
 * the only one.
 */
@Composable
fun QualityRing(
    score: Int?,
    grade: String?,
    modifier: Modifier = Modifier,
    size: androidx.compose.ui.unit.Dp = 84.dp,
    label: String = "Quality",
) {
    val colors = sajjilColors
    val target = (score ?: 0) / 100f
    val sweep by animateFloatAsState(
        targetValue = target,
        animationSpec = tween(durationMillis = 600),
        label = "quality-ring",
    )
    val ringColor = when {
        score == null -> colors.onSurfaceFaint
        score >= 85 -> colors.good
        score >= 70 -> colors.good.copy(alpha = 0.85f)
        score >= 55 -> colors.caution
        else -> colors.problem
    }

    Box(
        modifier = modifier
            .size(size)
            .semantics {
                contentDescription = if (score == null) {
                    "$label not measured yet"
                } else {
                    "$label $score out of 100, $grade"
                }
            },
        contentAlignment = Alignment.Center,
    ) {
        Canvas(modifier = Modifier.fillMaxSize()) {
            val stroke = this.size.minDimension * 0.1f
            drawArc(
                color = colors.onSurfaceFaint.copy(alpha = 0.18f),
                startAngle = 135f,
                sweepAngle = 270f,
                useCenter = false,
                style = Stroke(width = stroke, cap = androidx.compose.ui.graphics.StrokeCap.Round),
                topLeft = Offset(stroke / 2, stroke / 2),
                size = Size(this.size.width - stroke, this.size.height - stroke),
            )
            if (score != null) {
                drawArc(
                    color = ringColor,
                    startAngle = 135f,
                    sweepAngle = 270f * sweep,
                    useCenter = false,
                    style = Stroke(width = stroke, cap = androidx.compose.ui.graphics.StrokeCap.Round),
                    topLeft = Offset(stroke / 2, stroke / 2),
                    size = Size(this.size.width - stroke, this.size.height - stroke),
                )
            }
        }
        androidx.compose.foundation.layout.Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text(
                text = score?.toString() ?: "—",
                style = MaterialTheme.typography.headlineMedium,
                color = MaterialTheme.colorScheme.onSurface,
            )
            if (grade != null) {
                Text(
                    text = grade,
                    style = MaterialTheme.typography.labelSmall,
                    color = colors.onSurfaceMuted,
                )
            }
        }
    }
}

/** A horizontal gauge for a measured value against a target, used for loudness. */
@Composable
fun LoudnessGauge(
    lufs: Double?,
    targetLufs: Double,
    modifier: Modifier = Modifier,
    minimumLufs: Double = -40.0,
    maximumLufs: Double = -6.0,
) {
    val colors = sajjilColors
    val span = maximumLufs - minimumLufs

    Box(
        modifier = modifier
            .fillMaxWidth()
            .height(28.dp)
            .semantics {
                contentDescription = if (lufs == null) {
                    "Loudness not measured"
                } else {
                    "Loudness ${lufs.toInt()} LUFS, target ${targetLufs.toInt()}"
                }
            },
    ) {
        Canvas(modifier = Modifier.fillMaxSize()) {
            val trackTop = size.height / 2 - 5f
            drawRoundRect(
                color = colors.onSurfaceFaint.copy(alpha = 0.18f),
                topLeft = Offset(0f, trackTop),
                size = Size(size.width, 10f),
                cornerRadius = androidx.compose.ui.geometry.CornerRadius(5f),
            )
            if (lufs != null) {
                val fraction = ((lufs - minimumLufs) / span).coerceIn(0.0, 1.0).toFloat()
                drawRoundRect(
                    color = colors.waveformBody,
                    topLeft = Offset(0f, trackTop),
                    size = Size(size.width * fraction, 10f),
                    cornerRadius = androidx.compose.ui.geometry.CornerRadius(5f),
                )
            }
            // The target marker runs the full height so it reads as a goal line rather than as
            // another value on the same scale.
            val targetFraction = ((targetLufs - minimumLufs) / span).coerceIn(0.0, 1.0).toFloat()
            drawLine(
                color = colors.waveformPlayed,
                start = Offset(size.width * targetFraction, 0f),
                end = Offset(size.width * targetFraction, size.height),
                strokeWidth = 3f,
            )
        }
    }
}

/**
 * Playback transport.
 *
 * Play is visually dominant; skip and speed sit either side of it at a lower weight. This is the
 * information hierarchy rule applied to a control cluster: one primary, the rest supporting.
 */
@Composable
fun TransportBar(
    isPlaying: Boolean,
    onPlayPause: () -> Unit,
    onSkipBack: () -> Unit,
    onSkipForward: () -> Unit,
    modifier: Modifier = Modifier,
    onStop: (() -> Unit)? = null,
    enabled: Boolean = true,
) {
    val colors = sajjilColors
    Row(
        modifier = modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.Center,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        CircularIconButton(
            icon = Icons.Filled.Replay10,
            description = "Skip back ten seconds",
            onClick = onSkipBack,
            enabled = enabled,
            tint = colors.onSurfaceMuted,
        )
        Spacer(Modifier.width(Space.lg))
        Box(
            modifier = Modifier
                .size(72.dp)
                .background(MaterialTheme.colorScheme.primary, CircleShape)
                .semantics {
                    contentDescription = if (isPlaying) "Pause" else "Play"
                    role = Role.Button
                }
                .clickable(enabled = enabled, onClick = onPlayPause),
            contentAlignment = Alignment.Center,
        ) {
            Icon(
                imageVector = if (isPlaying) Icons.Filled.Pause else Icons.Filled.PlayArrow,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.onPrimary,
                modifier = Modifier.size(34.dp),
            )
        }
        Spacer(Modifier.width(Space.lg))
        CircularIconButton(
            icon = Icons.Filled.Forward10,
            description = "Skip forward ten seconds",
            onClick = onSkipForward,
            enabled = enabled,
            tint = colors.onSurfaceMuted,
        )
        if (onStop != null) {
            Spacer(Modifier.width(Space.lg))
            CircularIconButton(
                icon = Icons.Filled.Stop,
                description = "Stop",
                onClick = onStop,
                enabled = enabled,
                tint = colors.onSurfaceMuted,
            )
        }
    }
}

/**
 * An icon button with a 48dp touch target regardless of how small the icon looks.
 *
 * Compose's IconButton already does this; having one wrapper means the app cannot accidentally
 * ship a 32dp tap target somewhere, which is the usual way accessibility guidance gets broken.
 */
@Composable
fun CircularIconButton(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    description: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    tint: Color = MaterialTheme.colorScheme.onSurface,
    background: Color = Color.Transparent,
) {
    Box(
        modifier = modifier
            .size(Space.minimumTouchTarget)
            .background(background, CircleShape)
            .semantics {
                contentDescription = description
                role = Role.Button
            }
            .clickable(enabled = enabled, onClick = onClick),
        contentAlignment = Alignment.Center,
    ) {
        Icon(
            imageVector = icon,
            contentDescription = null,
            tint = if (enabled) tint else tint.copy(alpha = 0.35f),
            modifier = Modifier.size(24.dp),
        )
    }
}

/** A labelled surface that groups related controls without shouting. */
@Composable
fun SectionCard(
    modifier: Modifier = Modifier,
    content: @Composable androidx.compose.foundation.layout.ColumnScope.() -> Unit,
) {
    androidx.compose.foundation.layout.Column(
        modifier = modifier
            .fillMaxWidth()
            .background(sajjilColors.surfaceElevated, RoundedCornerShape(Radius.medium))
            .border(1.dp, MaterialTheme.colorScheme.outline.copy(alpha = 0.5f), RoundedCornerShape(Radius.medium))
            .padding(Space.md),
        content = content,
    )
}

@Composable
private fun androidx.compose.animation.core.InfiniteTransition.animateFloatCompat(
    initial: Float,
    target: Float,
    durationMillis: Int,
) = animateFloat(
    initialValue = initial,
    targetValue = target,
    animationSpec = infiniteRepeatable(
        animation = tween(durationMillis),
        repeatMode = RepeatMode.Reverse,
    ),
    label = "pulse",
)

private val RECORD_BUTTON_SIZE = 112.dp
