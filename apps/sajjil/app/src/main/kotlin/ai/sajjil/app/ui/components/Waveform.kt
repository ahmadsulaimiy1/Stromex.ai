package ai.sajjil.app.ui.components

import ai.sajjil.app.ui.Format
import ai.sajjil.app.ui.theme.Radius
import ai.sajjil.app.ui.theme.sajjilColors
import ai.sajjil.audio.edit.FrameRange
import ai.sajjil.audio.waveform.WaveformPeaks
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.gestures.detectTransformGestures
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import kotlin.math.abs
import kotlin.math.roundToInt

/** Which selection handle a drag has hold of. */
private enum class DragTarget { NONE, START, END, PLAYHEAD, NEW_SELECTION }

/**
 * The editable waveform.
 *
 * This is the editor — there is no separate edit mode and no dialog between the user and their
 * audio. Every gesture the design calls for acts directly on what is drawn:
 *
 * - drag on empty waveform to select
 * - drag a handle to adjust that selection
 * - pinch to zoom, drag with two fingers to pan
 * - tap to move the playhead
 * - double-tap to split
 * - long-press for the contextual actions
 *
 * Buckets are supplied already extracted; the view never touches audio itself, so scrolling a
 * two-hour recording costs the same as scrolling a two-minute one.
 */
@Composable
fun WaveformView(
    peaks: WaveformPeaks?,
    totalFrames: Int,
    playheadFrame: Int,
    modifier: Modifier = Modifier,
    height: Dp = 180.dp,
    selection: FrameRange? = null,
    splitPoints: List<Int> = emptyList(),
    bookmarks: List<Int> = emptyList(),
    zoom: Float = 1f,
    scrollFraction: Float = 0f,
    showTimeRuler: Boolean = true,
    interactive: Boolean = true,
    onSeek: (Int) -> Unit = {},
    onSelectionChange: (FrameRange?) -> Unit = {},
    onSplit: (Int) -> Unit = {},
    onLongPress: (Int) -> Unit = {},
    onZoomChange: (Float) -> Unit = {},
    onScrollChange: (Float) -> Unit = {},
) {
    val colors = sajjilColors
    val density = LocalDensity.current
    val handleTouchSlop = with(density) { 24.dp.toPx() }

    var dragTarget by remember { mutableStateOf(DragTarget.NONE) }
    var dragAnchorFrame by remember { mutableStateOf(0) }
    var canvasWidth by remember { mutableFloatStateOf(1f) }

    // The frame range currently on screen, derived from zoom and scroll.
    val visibleFrames = (totalFrames / zoom).roundToInt().coerceAtLeast(1)
    val firstVisibleFrame = ((totalFrames - visibleFrames) * scrollFraction)
        .roundToInt()
        .coerceIn(0, (totalFrames - visibleFrames).coerceAtLeast(0))

    fun frameAtX(x: Float): Int =
        (firstVisibleFrame + (x / canvasWidth).coerceIn(0f, 1f) * visibleFrames)
            .roundToInt()
            .coerceIn(0, totalFrames)

    fun xForFrame(frame: Int): Float =
        ((frame - firstVisibleFrame).toFloat() / visibleFrames) * canvasWidth

    val description = buildString {
        append("Waveform. ")
        if (totalFrames > 0 && peaks != null) {
            append("Position ${Format.spokenDuration(frameToMillis(playheadFrame, peaks.sampleRate))}. ")
        }
        selection?.let {
            append("Selection from ${it.from} to ${it.until} frames. ")
        }
        append("Drag to select, double tap to split, long press for actions.")
    }

    Box(
        modifier = modifier
            .fillMaxWidth()
            .height(height)
            .background(colors.surfaceElevated, RoundedCornerShape(Radius.medium))
            .semantics { contentDescription = description }
            .then(
                if (!interactive) Modifier else Modifier
                    .pointerInput(totalFrames, zoom, scrollFraction, selection) {
                        detectTapGestures(
                            onTap = { offset -> onSeek(frameAtX(offset.x)) },
                            onDoubleTap = { offset -> onSplit(frameAtX(offset.x)) },
                            onLongPress = { offset -> onLongPress(frameAtX(offset.x)) },
                        )
                    }
                    .pointerInput(totalFrames, zoom, scrollFraction, selection) {
                        detectDragGestures(
                            onDragStart = { offset ->
                                val frame = frameAtX(offset.x)
                                val current = selection
                                dragTarget = when {
                                    // Grabbing a handle takes priority over starting a new
                                    // selection, so adjusting an existing range is possible
                                    // without having to redraw it from scratch.
                                    current != null &&
                                        abs(offset.x - xForFrame(current.from)) < handleTouchSlop ->
                                        DragTarget.START
                                    current != null &&
                                        abs(offset.x - xForFrame(current.until)) < handleTouchSlop ->
                                        DragTarget.END
                                    else -> DragTarget.NEW_SELECTION
                                }
                                dragAnchorFrame = when (dragTarget) {
                                    DragTarget.START -> current?.until ?: frame
                                    DragTarget.END -> current?.from ?: frame
                                    else -> frame
                                }
                            },
                            onDrag = { change, _ ->
                                change.consume()
                                val frame = frameAtX(change.position.x)
                                val from = minOf(dragAnchorFrame, frame)
                                val until = maxOf(dragAnchorFrame, frame)
                                onSelectionChange(
                                    if (until - from < MINIMUM_SELECTION_FRAMES) null
                                    else FrameRange(from, until)
                                )
                            },
                            onDragEnd = { dragTarget = DragTarget.NONE },
                            onDragCancel = { dragTarget = DragTarget.NONE },
                        )
                    }
                    .pointerInput(totalFrames) {
                        detectTransformGestures { _, pan, gestureZoom, _ ->
                            if (gestureZoom != 1f) {
                                onZoomChange((zoom * gestureZoom).coerceIn(1f, MAXIMUM_ZOOM))
                            }
                            if (pan.x != 0f && zoom > 1f) {
                                val fractionMoved = -pan.x / canvasWidth / zoom
                                onScrollChange((scrollFraction + fractionMoved).coerceIn(0f, 1f))
                            }
                        }
                    }
            ),
    ) {
        androidx.compose.foundation.Canvas(modifier = Modifier.fillMaxSize()) {
            canvasWidth = size.width
            val rulerHeight = if (showTimeRuler) RULER_HEIGHT_PX else 0f
            val waveHeight = size.height - rulerHeight

            if (peaks == null || peaks.bucketCount == 0) {
                drawEmptyWaveform(colors.onSurfaceFaint, waveHeight)
                return@Canvas
            }

            drawWaveform(
                peaks = peaks,
                waveHeight = waveHeight,
                firstVisibleFrame = firstVisibleFrame,
                visibleFrames = visibleFrames,
                playheadFrame = playheadFrame,
                peakColor = colors.waveformPeak,
                bodyColor = colors.waveformBody,
                playedColor = colors.waveformPlayed,
            )

            selection?.let { range ->
                val startX = ((range.from - firstVisibleFrame).toFloat() / visibleFrames) * size.width
                val endX = ((range.until - firstVisibleFrame).toFloat() / visibleFrames) * size.width
                drawSelection(startX, endX, waveHeight, colors.waveformSelection, colors.waveformPlayed)
            }

            for (point in splitPoints) {
                val x = ((point - firstVisibleFrame).toFloat() / visibleFrames) * size.width
                if (x in 0f..size.width) {
                    drawLine(
                        color = colors.caution,
                        start = Offset(x, 0f),
                        end = Offset(x, waveHeight),
                        strokeWidth = 2f,
                    )
                }
            }

            for (bookmark in bookmarks) {
                val x = ((bookmark - firstVisibleFrame).toFloat() / visibleFrames) * size.width
                if (x in 0f..size.width) {
                    drawCircle(color = colors.good, radius = 6f, center = Offset(x, 8f))
                }
            }

            val playheadX = ((playheadFrame - firstVisibleFrame).toFloat() / visibleFrames) * size.width
            if (playheadX in 0f..size.width) {
                drawLine(
                    color = colors.playhead,
                    start = Offset(playheadX, 0f),
                    end = Offset(playheadX, waveHeight),
                    strokeWidth = 3f,
                )
            }

            if (showTimeRuler) {
                drawTimeRuler(
                    peaks = peaks,
                    firstVisibleFrame = firstVisibleFrame,
                    visibleFrames = visibleFrames,
                    top = waveHeight,
                    height = rulerHeight,
                    color = colors.onSurfaceFaint,
                )
            }
        }
    }
}

private fun DrawScope.drawWaveform(
    peaks: WaveformPeaks,
    waveHeight: Float,
    firstVisibleFrame: Int,
    visibleFrames: Int,
    playheadFrame: Int,
    peakColor: Color,
    bodyColor: Color,
    playedColor: Color,
) {
    val centreY = waveHeight / 2f
    val columns = size.width.toInt().coerceAtLeast(1)

    for (x in 0 until columns) {
        val frame = firstVisibleFrame + (x.toFloat() / columns * visibleFrames).toInt()
        val bucket = peaks.bucketForFrame(frame)
        if (bucket !in 0 until peaks.bucketCount) continue

        val minimum = peaks.minima[bucket]
        val maximum = peaks.maxima[bucket]
        val rms = peaks.rms[bucket]

        // Behind the playhead the waveform takes the accent colour, which is a far clearer
        // progress indicator than a separate bar would be.
        val played = frame <= playheadFrame
        val outer = if (played) playedColor else peakColor
        val inner = if (played) playedColor else bodyColor

        val topY = centreY - maximum * centreY
        val bottomY = centreY - minimum * centreY
        drawLine(
            color = outer.copy(alpha = 0.55f),
            start = Offset(x.toFloat(), topY),
            end = Offset(x.toFloat(), bottomY),
            strokeWidth = 1f,
        )

        // RMS drawn inside the envelope: this is the part that reads as loudness.
        val rmsTop = centreY - rms * centreY
        val rmsBottom = centreY + rms * centreY
        drawLine(
            color = inner,
            start = Offset(x.toFloat(), rmsTop),
            end = Offset(x.toFloat(), rmsBottom),
            strokeWidth = 1f,
        )
    }
}

private fun DrawScope.drawEmptyWaveform(color: Color, waveHeight: Float) {
    // A flat line rather than a blank box: it says "no audio here yet" instead of "still loading".
    drawLine(
        color = color.copy(alpha = 0.4f),
        start = Offset(0f, waveHeight / 2f),
        end = Offset(size.width, waveHeight / 2f),
        strokeWidth = 2f,
    )
}

private fun DrawScope.drawSelection(
    startX: Float,
    endX: Float,
    waveHeight: Float,
    fill: Color,
    handleColor: Color,
) {
    val left = minOf(startX, endX).coerceIn(0f, size.width)
    val right = maxOf(startX, endX).coerceIn(0f, size.width)
    drawRect(
        color = fill,
        topLeft = Offset(left, 0f),
        size = Size(right - left, waveHeight),
    )
    // Handles are drawn wide because they have to be grabbable, not just visible.
    for (x in listOf(left, right)) {
        drawLine(
            color = handleColor,
            start = Offset(x, 0f),
            end = Offset(x, waveHeight),
            strokeWidth = 4f,
        )
        drawCircle(color = handleColor, radius = 14f, center = Offset(x, waveHeight / 2f))
        drawCircle(
            color = Color.Black.copy(alpha = 0.35f),
            radius = 14f,
            center = Offset(x, waveHeight / 2f),
            style = Stroke(width = 2f),
        )
    }
}

private fun DrawScope.drawTimeRuler(
    peaks: WaveformPeaks,
    firstVisibleFrame: Int,
    visibleFrames: Int,
    top: Float,
    height: Float,
    color: Color,
) {
    val sampleRate = peaks.sampleRate
    val visibleSeconds = visibleFrames.toDouble() / sampleRate
    // Pick a tick spacing that yields roughly five to ten labels, whatever the zoom level.
    val step = TICK_STEPS.firstOrNull { visibleSeconds / it <= 10 } ?: TICK_STEPS.last()

    val firstSecond = (firstVisibleFrame.toDouble() / sampleRate / step).toInt() * step
    var second = firstSecond.toDouble()
    while (second <= firstVisibleFrame.toDouble() / sampleRate + visibleSeconds) {
        val frame = (second * sampleRate).toInt()
        val x = ((frame - firstVisibleFrame).toFloat() / visibleFrames) * size.width
        if (x in 0f..size.width) {
            drawLine(
                color = color.copy(alpha = 0.5f),
                start = Offset(x, top),
                end = Offset(x, top + height * 0.35f),
                strokeWidth = 1f,
            )
        }
        second += step
    }
}

private fun frameToMillis(frame: Int, sampleRate: Int): Long =
    if (sampleRate <= 0) 0 else frame * 1000L / sampleRate

private const val MINIMUM_SELECTION_FRAMES = 64
private const val MAXIMUM_ZOOM = 200f
private const val RULER_HEIGHT_PX = 28f

/** Tick spacings in seconds, coarse to fine. */
private val TICK_STEPS = listOf(0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0, 1800.0)
