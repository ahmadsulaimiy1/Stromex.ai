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
