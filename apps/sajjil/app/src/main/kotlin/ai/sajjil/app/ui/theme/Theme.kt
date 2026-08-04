package ai.sajjil.app.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp

/**
 * Colours that Material's scheme has no slot for — waveform parts, quality signals, the record
 * colour. Kept in a CompositionLocal so a screen never hard-codes a hex value.
 */
data class SajjilExtendedColors(
    val surfaceElevated: Color,
    val onSurfaceMuted: Color,
    val onSurfaceFaint: Color,
    val record: Color,
    val recordDim: Color,
    val good: Color,
    val caution: Color,
    val problem: Color,
    val waveformPeak: Color,
    val waveformBody: Color,
    val waveformPlayed: Color,
    val waveformSelection: Color,
    val playhead: Color,
)

val LocalSajjilColors = staticCompositionLocalOf {
    SajjilExtendedColors(
        surfaceElevated = SajjilColors.DarkSurfaceElevated,
        onSurfaceMuted = SajjilColors.DarkOnSurfaceMuted,
        onSurfaceFaint = SajjilColors.DarkOnSurfaceFaint,
        record = SajjilColors.Record,
        recordDim = SajjilColors.RecordDim,
        good = SajjilColors.Good,
        caution = SajjilColors.Caution,
        problem = SajjilColors.Problem,
        waveformPeak = SajjilColors.WaveformPeak,
        waveformBody = SajjilColors.WaveformBody,
        waveformPlayed = SajjilColors.WaveformPlayed,
        waveformSelection = SajjilColors.WaveformSelection,
        playhead = SajjilColors.Playhead,
    )
}

/**
 * The spacing scale.
 *
 * Everything in the app is spaced with one of these. The steps are wide apart on purpose — a
 * scale with 4, 6, 8, 10, 12 in it invites arbitrary choices and the result reads as sloppy, while
 * a coarse scale forces the layout into a rhythm.
 */
object Space {
    val xs: Dp = 4.dp
    val sm: Dp = 8.dp
    val md: Dp = 16.dp
    val lg: Dp = 24.dp
    val xl: Dp = 32.dp
    val xxl: Dp = 48.dp

    /** Standard page inset. Generous, because crowding the edges is what makes an app feel cheap. */
    val pageHorizontal: Dp = 20.dp

    /**
     * The minimum any tappable thing may be. Android's guidance is 48dp; this app holds to it
     * everywhere, including icon buttons that look smaller than their touch target.
     */
    val minimumTouchTarget: Dp = 48.dp
}

/** Corner radii. Large and consistent, which is most of what reads as "premium". */
object Radius {
    val small: Dp = 10.dp
    val medium: Dp = 16.dp
    val large: Dp = 22.dp
    val sheet: Dp = 28.dp
}

private val DarkScheme = darkColorScheme(
    primary = SajjilColors.BrassBright,
    onPrimary = Color(0xFF1A1400),
    primaryContainer = SajjilColors.BrassSoft,
    onPrimaryContainer = SajjilColors.BrassBright,
    secondary = SajjilColors.WaveformPeak,
    onSecondary = Color.White,
    background = SajjilColors.DarkBackground,
    onBackground = SajjilColors.DarkOnSurface,
    surface = SajjilColors.DarkSurface,
    onSurface = SajjilColors.DarkOnSurface,
    surfaceVariant = SajjilColors.DarkSurfaceElevated,
    onSurfaceVariant = SajjilColors.DarkOnSurfaceMuted,
    outline = SajjilColors.DarkOutline,
    outlineVariant = SajjilColors.DarkOutline,
    error = SajjilColors.Problem,
    onError = Color.White,
)

private val LightScheme = lightColorScheme(
    primary = SajjilColors.Brass,
    onPrimary = Color.White,
    primaryContainer = Color(0xFFF6EBC4),
    onPrimaryContainer = Color(0xFF3E3005),
    secondary = SajjilColors.WaveformPeak,
    onSecondary = Color.White,
    background = SajjilColors.LightBackground,
    onBackground = SajjilColors.LightOnSurface,
    surface = SajjilColors.LightSurface,
    onSurface = SajjilColors.LightOnSurface,
    surfaceVariant = Color(0xFFF0EDE7),
    onSurfaceVariant = SajjilColors.LightOnSurfaceMuted,
    outline = SajjilColors.LightOutline,
    outlineVariant = SajjilColors.LightOutline,
    error = SajjilColors.Problem,
    onError = Color.White,
)

@Composable
fun SajjilTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    val extended = if (darkTheme) {
        SajjilExtendedColors(
            surfaceElevated = SajjilColors.DarkSurfaceElevated,
            onSurfaceMuted = SajjilColors.DarkOnSurfaceMuted,
            onSurfaceFaint = SajjilColors.DarkOnSurfaceFaint,
            record = SajjilColors.Record,
            recordDim = SajjilColors.RecordDim,
            good = SajjilColors.Good,
            caution = SajjilColors.Caution,
            problem = SajjilColors.Problem,
            waveformPeak = SajjilColors.WaveformPeak,
            waveformBody = SajjilColors.WaveformBody,
            waveformPlayed = SajjilColors.WaveformPlayed,
            waveformSelection = SajjilColors.WaveformSelection,
            playhead = SajjilColors.Playhead,
        )
    } else {
        SajjilExtendedColors(
            surfaceElevated = SajjilColors.LightSurfaceElevated,
            onSurfaceMuted = SajjilColors.LightOnSurfaceMuted,
            onSurfaceFaint = SajjilColors.LightOnSurfaceFaint,
            record = SajjilColors.Record,
            recordDim = Color(0xFFF3C4C6),
            good = Color(0xFF1B9D63),
            caution = Color(0xFFB87503),
            problem = Color(0xFFC42F34),
            waveformPeak = Color(0xFF2C6BCB),
            waveformBody = Color(0xFF5B93E8),
            waveformPlayed = SajjilColors.Brass,
            waveformSelection = Color(0x332C6BCB),
            playhead = Color(0xFF10131A),
        )
    }

    // Dynamic colour is deliberately not used. A recording app's waveform, level meters and
    // quality signals have to mean the same thing on every device; letting the wallpaper retint
    // them would break the one thing this interface has to communicate reliably.
    CompositionLocalProvider(LocalSajjilColors provides extended) {
        MaterialTheme(
            colorScheme = if (darkTheme) DarkScheme else LightScheme,
            typography = SajjilTypography,
            content = content,
        )
    }
}

/** Shorthand for the extended palette. */
val sajjilColors: SajjilExtendedColors
    @Composable get() = LocalSajjilColors.current
