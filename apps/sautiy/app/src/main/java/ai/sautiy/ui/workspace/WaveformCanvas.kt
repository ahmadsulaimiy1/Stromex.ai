package ai.sautiy.ui.workspace

import ai.sautiy.core.analysis.WaveformColumns
import ai.sautiy.ui.theme.SautiySize
import ai.sautiy.ui.theme.SautiyTheme
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import kotlin.math.abs
import kotlin.math.roundToLong

/**
 * The waveform — the centre of the application and, by chapter 3.2.5, the most rewarding thing
 * in it. Watching one's own voice draw itself is why the canvas gets the middle of the screen.
 *
 * Drawing is deliberately dumb and fast. Every expensive decision — which pyramid level, which
 * frames belong to which pixel column — was made in `sautiy-core` before this composable ran,
 * so the draw phase is a loop over one pre-computed float array per column and nothing else.
 * That is what holds the 60 fps of chapter 1.6 while capture is running on another thread.
 *
 * @param columns one entry per pixel column, already resolved (see `WaveformPyramid.columns`)
 * @param onSelectionChanged emits a frame range as the user drags
 * @param onSeek emits a frame when the user taps
 */
@Composable
fun WaveformCanvas(
    columns: WaveformColumns?,
    playheadFrame: Long,
    totalFrames: Long,
    selection: LongRange?,
    markers: List<Long>,
    modifier: Modifier = Modifier,
    isRecording: Boolean = false,
    onSeek: (Long) -> Unit = {},
    onSelectionChanged: (LongRange?) -> Unit = {},
) {
    val colours = SautiyTheme.colours
    val density = LocalDensity.current
    var dragAnchorFrame by remember { mutableStateOf<Long?>(null) }

    val positionLabel = formatTimecode(playheadFrame, 48_000)
    val totalLabel = formatTimecode(totalFrames, 48_000)

    Box(
        modifier = modifier
            .fillMaxSize()
            .semantics {
                // Chapter 17: a waveform is a picture, and a picture with no description is a
                // blank space to a screen reader. The position and duration are spoken instead.
                contentDescription = "Waveform. $positionLabel of $totalLabel."
            }
            .pointerInput(totalFrames) {
                detectTapGestures(
                    onTap = { offset ->
                        if (size.width > 0 && totalFrames > 0) {
                            onSelectionChanged(null)
                            onSeek(frameAt(offset.x, size.width, columns, totalFrames))
                        }
                    },
                )
            }
            .pointerInput(totalFrames) {
                detectDragGestures(
                    onDragStart = { offset ->
                        dragAnchorFrame = frameAt(offset.x, size.width, columns, totalFrames)
                    },
                    onDragEnd = { dragAnchorFrame = null },
                    onDragCancel = { dragAnchorFrame = null },
                ) { change, _ ->
                    val anchor = dragAnchorFrame ?: return@detectDragGestures
                    val current = frameAt(change.position.x, size.width, columns, totalFrames)
                    // A drag shorter than a few pixels is a tap that wobbled, not a selection.
                    val minimum = totalFrames / 200
                    if (abs(current - anchor) > minimum) {
                        onSelectionChanged(minOf(anchor, current)..maxOf(anchor, current))
                    }
                }
            }
            // A third pointerInput used to detect a pinch and hand it to a callback wired to
            // `{}`: the user pinched, the app did nothing, and there was no way to tell that from
            // a missed gesture. Zoom belongs to waveform editing (chapter 9) and comes back with
            // the implementation rather than ahead of it.
            ,
    ) {
        Canvas(modifier = Modifier.fillMaxSize()) {
            val height = size.height
            val centre = height / 2f
            val strokeWidth = with(density) { SautiySize.canvasStroke.toPx() }

            drawCentreLine(centre, colours.border, strokeWidth / 2f)

            if (columns == null || columns.width == 0) return@Canvas

            val columnWidth = size.width / columns.width
            // While recording the waveform is ember, so the single most important fact about
            // the device — that it is capturing — is visible from across a room without
            // reading anything (chapter 2.3.4, clause 1).
            val waveColour = if (isRecording) colours.ember else colours.signal
            val rmsColour = waveColour.copy(alpha = 0.45f)

            selection?.let { range ->
                if (totalFrames > 0) {
                    val left = (range.first.toFloat() / totalFrames) * size.width
                    val right = (range.last.toFloat() / totalFrames) * size.width
                    drawRect(
                        color = colours.signalSelection,
                        topLeft = Offset(left, 0f),
                        size = Size((right - left).coerceAtLeast(1f), height),
                    )
                }
            }

            for (x in 0 until columns.width) {
                val left = x * columnWidth
                val peakTop = centre - columns.maxima[x] * centre
                val peakBottom = centre - columns.minima[x] * centre
                val rmsTop = centre - columns.rms[x] * centre
                val rmsBottom = centre + columns.rms[x] * centre

                // The peak envelope, drawn first and lighter: it is the outline of the sound.
                drawLine(
                    color = waveColour,
                    start = Offset(left, peakTop),
                    end = Offset(left, peakBottom),
                    strokeWidth = columnWidth.coerceAtLeast(1f),
                    cap = StrokeCap.Butt,
                )
                // The RMS body, drawn over it and denser: it is where the energy actually is.
                // Two envelopes rather than one is what lets the eye tell a plosive from a
                // sustained vowel at a glance.
                drawLine(
                    color = rmsColour,
                    start = Offset(left, rmsTop),
                    end = Offset(left, rmsBottom),
                    strokeWidth = columnWidth.coerceAtLeast(1f),
                    cap = StrokeCap.Butt,
                )
            }

            if (totalFrames > 0) {
                for (marker in markers) {
                    val x = (marker.toFloat() / totalFrames) * size.width
                    drawLine(
                        color = colours.caution,
                        start = Offset(x, 0f),
                        end = Offset(x, height),
                        strokeWidth = strokeWidth,
                    )
                }

                val playheadX = (playheadFrame.toFloat() / totalFrames) * size.width
                drawLine(
                    color = colours.textPrimary,
                    start = Offset(playheadX, 0f),
                    end = Offset(playheadX, height),
                    strokeWidth = with(density) { SautiySize.canvasStroke.toPx() },
                )
            }
        }
    }
}

private fun androidx.compose.ui.graphics.drawscope.DrawScope.drawCentreLine(
    centre: Float,
    colour: Color,
    strokeWidth: Float,
) {
    drawLine(
        color = colour,
        start = Offset(0f, centre),
        end = Offset(size.width, centre),
        strokeWidth = strokeWidth,
    )
}

private fun frameAt(x: Float, width: Int, columns: WaveformColumns?, totalFrames: Long): Long {
    if (width <= 0) return 0
    val fraction = (x / width).coerceIn(0f, 1f)
    val start = columns?.startFrame ?: 0
    val end = columns?.endFrame ?: totalFrames
    return (start + (end - start) * fraction.toDouble()).roundToLong().coerceIn(0, totalFrames)
}

/**
 * Timecode in the form the status rail and the timer use: `m:ss.d`, matching the reference
 * layout, with tenths because a trim point half a second out is audible and a trim point a
 * tenth of a second out generally is not.
 */
fun formatTimecode(frames: Long, sampleRate: Int): String {
    if (sampleRate <= 0) return "0:00.0"
    val totalTenths = (frames * 10 / sampleRate).coerceAtLeast(0)
    val tenths = totalTenths % 10
    val totalSeconds = totalTenths / 10
    val seconds = totalSeconds % 60
    val minutes = (totalSeconds / 60) % 60
    val hours = totalSeconds / 3600
    return if (hours > 0) {
        "%d:%02d:%02d.%d".format(hours, minutes, seconds, tenths)
    } else {
        "%d:%02d.%d".format(minutes, seconds, tenths)
    }
}

/** Duration for a list row: no tenths, because a library does not need them. */
fun formatDuration(frames: Long, sampleRate: Int): String {
    if (sampleRate <= 0) return "0:00"
    val totalSeconds = frames / sampleRate
    val seconds = totalSeconds % 60
    val minutes = (totalSeconds / 60) % 60
    val hours = totalSeconds / 3600
    return if (hours > 0) "%d:%02d:%02d".format(hours, minutes, seconds) else "%d:%02d".format(minutes, seconds)
}
