package com.sajjil.app.ui.components

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.unit.dp

/**
 * Bar-style waveform for an already-recorded file (as opposed to [LiveWaveformView], which is
 * fed live mic input while recording). Bars up to [progress] are drawn in [playedColor], the
 * rest in [unplayedColor] -- a scrubber look, not just a static shape. [peaks] is expected to be
 * pre-computed (see `com.sajjil.core.analysis.WaveformPeaks`) since decoding a whole recording on
 * every recomposition would be wasteful; pass null while it's still loading and nothing is drawn.
 */
@Composable
fun PlaybackWaveformView(
    peaks: FloatArray?,
    progress: Float,
    modifier: Modifier = Modifier.fillMaxWidth().height(40.dp),
    playedColor: Color = MaterialTheme.colorScheme.primary,
    unplayedColor: Color = MaterialTheme.colorScheme.primary.copy(alpha = 0.3f),
) {
    Canvas(modifier = modifier) {
        if (peaks == null || peaks.isEmpty()) return@Canvas
        val barWidth = size.width / peaks.size
        val playedBars = (progress.coerceIn(0f, 1f) * peaks.size).toInt()
        peaks.forEachIndexed { index, amplitude ->
            val barHeight = (amplitude.coerceIn(0f, 1f) * size.height).coerceAtLeast(2f)
            val x = index * barWidth + barWidth / 2
            drawLine(
                color = if (index < playedBars) playedColor else unplayedColor,
                start = Offset(x, size.height / 2 - barHeight / 2),
                end = Offset(x, size.height / 2 + barHeight / 2),
                strokeWidth = (barWidth * 0.65f).coerceAtLeast(1f),
                cap = StrokeCap.Round,
            )
        }
    }
}

/**
 * Same bar-style rendering as [PlaybackWaveformView], but showing a trim/cut SELECTION range
 * ([selectionStart]..[selectionEnd], both 0f..1f fractions of the whole recording) instead of
 * playback progress -- bars inside the selection are drawn in [selectedColor], bars outside in
 * [unselectedColor]. Purely a visual reference; the selection itself is driven by sliders in
 * `EditorScreen` rather than a drag gesture directly on this canvas, since a hand-rolled two-handle
 * drag gesture is materially riskier to get right without the ability to visually test it here,
 * and the Slider component is already proven working in this app.
 */
@Composable
fun WaveformSelectionView(
    peaks: FloatArray?,
    selectionStart: Float,
    selectionEnd: Float,
    modifier: Modifier = Modifier.fillMaxWidth().height(40.dp),
    selectedColor: Color = MaterialTheme.colorScheme.primary,
    unselectedColor: Color = MaterialTheme.colorScheme.primary.copy(alpha = 0.25f),
) {
    Canvas(modifier = modifier) {
        if (peaks == null || peaks.isEmpty()) return@Canvas
        val barWidth = size.width / peaks.size
        val start = selectionStart.coerceIn(0f, 1f)
        val end = selectionEnd.coerceIn(start, 1f)
        peaks.forEachIndexed { index, amplitude ->
            val fraction = index.toFloat() / peaks.size
            val inSelection = fraction in start..end
            val barHeight = (amplitude.coerceIn(0f, 1f) * size.height).coerceAtLeast(2f)
            val x = index * barWidth + barWidth / 2
            drawLine(
                color = if (inSelection) selectedColor else unselectedColor,
                start = Offset(x, size.height / 2 - barHeight / 2),
                end = Offset(x, size.height / 2 + barHeight / 2),
                strokeWidth = (barWidth * 0.65f).coerceAtLeast(1f),
                cap = StrokeCap.Round,
            )
        }
    }
}
