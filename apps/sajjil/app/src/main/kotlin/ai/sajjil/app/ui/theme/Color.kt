package ai.sajjil.app.ui.theme

import androidx.compose.ui.graphics.Color

/**
 * SAJJIL's palette.
 *
 * Two decisions drive all of it. First, the dark theme is the primary one — audio work happens in
 * rooms that are dim more often than bright, and a waveform reads better against near-black than
 * against white. Second, there is exactly one accent colour (brass) plus one signal colour
 * (record red). Everything else is a neutral. A single accent is what makes a primary action
 * unmistakable; a palette of six competing accents is why most audio apps feel like control
 * panels.
 *
 * The neutrals are very slightly blue rather than pure grey, which keeps the brass looking warm
 * against them instead of muddy.
 */
object SajjilColors {

    // ---- Dark, the primary theme -------------------------------------------------------

    /** Page background. Not pure black: pure black crushes the waveform's darkest pixels. */
    val DarkBackground = Color(0xFF0B0D10)

    /** Cards and sheets sitting on the background. */
    val DarkSurface = Color(0xFF14171C)

    /** Raised surfaces — the studio panel, dialogs, the mini player. */
    val DarkSurfaceElevated = Color(0xFF1C2027)

    /** Hairlines and dividers. Deliberately low contrast; structure comes from space, not lines. */
    val DarkOutline = Color(0xFF2A2F38)

    val DarkOnSurface = Color(0xFFF2F4F7)
    val DarkOnSurfaceMuted = Color(0xFFA0A7B4)
    val DarkOnSurfaceFaint = Color(0xFF6B7280)

    // ---- Light -------------------------------------------------------------------------

    /** Warm off-white rather than #FFFFFF, which glares and makes the brass look dirty. */
    val LightBackground = Color(0xFFF7F5F2)
    val LightSurface = Color(0xFFFFFFFF)
    val LightSurfaceElevated = Color(0xFFFFFFFF)
    val LightOutline = Color(0xFFE2DED7)
    val LightOnSurface = Color(0xFF10131A)
    val LightOnSurfaceMuted = Color(0xFF5A6270)
    val LightOnSurfaceFaint = Color(0xFF8A929E)

    // ---- Accent ------------------------------------------------------------------------

    /** The single accent. Used for the primary action and nothing else. */
    val Brass = Color(0xFFC9A227)
    val BrassBright = Color(0xFFE8C64A)
    val BrassSoft = Color(0xFF6B5518)

    // ---- Signals -----------------------------------------------------------------------

    /** Recording. This colour appears nowhere else in the app, so it always means one thing. */
    val Record = Color(0xFFE5484D)
    val RecordDim = Color(0xFF7A2226)

    val Good = Color(0xFF3DD68C)
    val Caution = Color(0xFFF5A524)
    val Problem = Color(0xFFE5484D)

    // ---- Waveform ----------------------------------------------------------------------

    /** Peaks: the outer envelope. */
    val WaveformPeak = Color(0xFF3E85F3)

    /** RMS drawn inside the peaks. Brighter, because this is the part that reads as loudness. */
    val WaveformBody = Color(0xFF7EB2FF)

    /** Audio behind the playhead. */
    val WaveformPlayed = BrassBright

    /** Selected region wash. */
    val WaveformSelection = Color(0x333E85F3)

    val Playhead = Color(0xFFFFFFFF)
}
