package com.sajjil.app.ui.components

import android.graphics.Bitmap
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.unit.dp
import com.sajjil.core.analysis.LoudnessSample
import com.sajjil.core.analysis.Spectrogram

/**
 * SAJJIL Professional Spectrogram: a time x frequency heatmap rendered from
 * a computed [Spectrogram]. Builds an [Bitmap] once per data set (cheap:
 * one `setPixel` per time/frequency cell) and lets Canvas scale it, rather
 * than issuing thousands of individual `drawRect` calls per frame.
 */
@Composable
fun SpectrogramView(spectrogram: Spectrogram, modifier: Modifier = Modifier.fillMaxWidth().height(220.dp)) {
    val bitmap = remember(spectrogram) { spectrogramBitmap(spectrogram) }
    Canvas(modifier = modifier) {
        drawImage(
            image = bitmap.asImageBitmap(),
            dstSize = IntSize(size.width.toInt(), size.height.toInt()),
        )
    }
}

@Composable
fun LoudnessHistoryView(
    history: List<LoudnessSample>,
    modifier: Modifier = Modifier.fillMaxWidth().height(120.dp),
    lineColor: Color = Color(0xFFD4AF37),
    floorDb: Double = -60.0,
) {
    Canvas(modifier = modifier) {
        if (history.size < 2) return@Canvas
        val maxTime = history.last().timeSeconds.coerceAtLeast(0.001)
        fun point(sample: LoudnessSample): Offset {
            val x = (sample.timeSeconds / maxTime).toFloat() * size.width
            val normalized = ((sample.rmsDb - floorDb) / -floorDb).coerceIn(0.0, 1.0)
            val y = size.height - (normalized * size.height).toFloat()
            return Offset(x, y)
        }
        var previous = point(history.first())
        for (i in 1 until history.size) {
            val current = point(history[i])
            drawLine(lineColor, previous, current, strokeWidth = 3f, cap = StrokeCap.Round)
            previous = current
        }
    }
}

/**
 * A live scrolling waveform fed directly from `AudioRecordEngine.waveformHistory` —
 * the fan-out point `docs/STREAMING_ARCHITECTURE.md` describes: the same
 * per-buffer loop that writes audio to disk also emits the peak level
 * this view bars out, no separate capture needed.
 */
@Composable
fun LiveWaveformView(
    history: List<Float>,
    modifier: Modifier = Modifier.fillMaxWidth().height(60.dp),
    barColor: Color = Color(0xFFD4AF37),
) {
    Canvas(modifier = modifier) {
        if (history.isEmpty()) return@Canvas
        val barWidth = size.width / history.size
        history.forEachIndexed { index, amplitude ->
            val barHeight = amplitude.coerceIn(0f, 1f) * size.height
            val x = index * barWidth + barWidth / 2
            drawLine(
                color = barColor,
                start = Offset(x, size.height / 2 - barHeight / 2),
                end = Offset(x, size.height / 2 + barHeight / 2),
                strokeWidth = (barWidth * 0.6f).coerceAtLeast(1f),
                cap = StrokeCap.Round,
            )
        }
    }
}

private fun spectrogramBitmap(spectrogram: Spectrogram): Bitmap {
    val width = spectrogram.frames.size.coerceAtLeast(1)
    val height = (spectrogram.frames.firstOrNull()?.size ?: 1).coerceAtLeast(1)
    val bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)
    val range = -spectrogram.floorDb

    for (x in spectrogram.frames.indices) {
        val frame = spectrogram.frames[x]
        for (y in frame.indices) {
            val normalized = ((frame[y] - spectrogram.floorDb) / range).coerceIn(0.0, 1.0)
            // Flip vertically: bin 0 (lowest frequency) at the bottom of the image.
            bitmap.setPixel(x, height - 1 - y, heatColor(normalized))
        }
    }
    return bitmap
}

/** Deep navy (quiet) through gold (loud), matching SAJJIL's Royal Navy Deep identity. */
private fun heatColor(t: Double): Int {
    val navy = Triple(8, 24, 60)
    val gold = Triple(230, 190, 110)
    val r = (navy.first + t * (gold.first - navy.first)).toInt().coerceIn(0, 255)
    val g = (navy.second + t * (gold.second - navy.second)).toInt().coerceIn(0, 255)
    val b = (navy.third + t * (gold.third - navy.third)).toInt().coerceIn(0, 255)
    return android.graphics.Color.rgb(r, g, b)
}
