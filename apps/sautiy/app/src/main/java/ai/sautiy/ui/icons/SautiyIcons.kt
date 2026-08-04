package ai.sautiy.ui.icons

import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.StrokeJoin
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.graphics.vector.path
import androidx.compose.ui.unit.dp

/**
 * The SAUTIY icon set — Editorial Bible chapter 2.5.
 *
 * Drawn rather than imported. Every glyph sits on the same 24 dp grid with a 20 dp live area,
 * a 1.75 dp round-capped, round-joined stroke, and optical rather than bounding-box centring.
 * A borrowed icon set mixes stroke weights and corner treatments from three different design
 * languages, and that inconsistency is precisely what makes an interface read as assembled
 * instead of designed.
 *
 * Filled variants exist only to indicate an engaged state (chapter 2.5, icon law 4), never for
 * decoration.
 */
object SautiyIcons {

    private const val GRID = 24f
    private const val STROKE = 1.75f

    private fun stroked(name: String, block: androidx.compose.ui.graphics.vector.ImageVector.Builder.() -> Unit) =
        ImageVector.Builder(
            name = name,
            defaultWidth = GRID.dp,
            defaultHeight = GRID.dp,
            viewportWidth = GRID,
            viewportHeight = GRID,
        ).apply(block).build()

    private fun androidx.compose.ui.graphics.vector.ImageVector.Builder.line(
        pathData: androidx.compose.ui.graphics.vector.PathBuilder.() -> Unit,
    ) = path(
        stroke = SolidColor(Color.Black),
        strokeLineWidth = STROKE,
        strokeLineCap = StrokeCap.Round,
        strokeLineJoin = StrokeJoin.Round,
        pathBuilder = pathData,
    )

    private fun androidx.compose.ui.graphics.vector.ImageVector.Builder.solid(
        pathData: androidx.compose.ui.graphics.vector.PathBuilder.() -> Unit,
    ) = path(fill = SolidColor(Color.Black), pathBuilder = pathData)

    // --- Transport --------------------------------------------------------------------------

    /** The record control is a filled disc: it is a state, not an outline. */
    val Record: ImageVector by lazy {
        stroked("sautiy.record") {
            solid {
                moveTo(12f, 4f)
                arcToRelative(8f, 8f, 0f, true, true, -0.01f, 0f)
                close()
            }
        }
    }

    val Stop: ImageVector by lazy {
        stroked("sautiy.stop") {
            solid {
                moveTo(6.5f, 8f)
                arcToRelative(1.5f, 1.5f, 0f, false, true, 1.5f, -1.5f)
                horizontalLineTo(16f)
                arcToRelative(1.5f, 1.5f, 0f, false, true, 1.5f, 1.5f)
                verticalLineTo(16f)
                arcToRelative(1.5f, 1.5f, 0f, false, true, -1.5f, 1.5f)
                horizontalLineTo(8f)
                arcToRelative(1.5f, 1.5f, 0f, false, true, -1.5f, -1.5f)
                close()
            }
        }
    }

    val Play: ImageVector by lazy {
        stroked("sautiy.play") {
            solid {
                moveTo(8.4f, 5.6f)
                lineTo(18.2f, 11.2f)
                arcToRelative(0.9f, 0.9f, 0f, false, true, 0f, 1.6f)
                lineTo(8.4f, 18.4f)
                arcTo(0.9f, 0.9f, 0f, false, true, 7f, 17.6f)
                verticalLineTo(6.4f)
                arcToRelative(0.9f, 0.9f, 0f, false, true, 1.4f, -0.8f)
                close()
            }
        }
    }

    val Pause: ImageVector by lazy {
        stroked("sautiy.pause") {
            solid {
                moveTo(8f, 5.5f)
                horizontalLineToRelative(2.2f)
                verticalLineToRelative(13f)
                horizontalLineToRelative(-2.2f)
                close()
                moveTo(13.8f, 5.5f)
                horizontalLineToRelative(2.2f)
                verticalLineToRelative(13f)
                horizontalLineToRelative(-2.2f)
                close()
            }
        }
    }

    val Rewind: ImageVector by lazy {
        stroked("sautiy.rewind") {
            solid {
                moveTo(16.2f, 5.8f)
                lineTo(8.4f, 11.2f)
                arcToRelative(0.9f, 0.9f, 0f, false, false, 0f, 1.6f)
                lineTo(16.2f, 18.2f)
                arcToRelative(0.9f, 0.9f, 0f, false, false, 1.4f, -0.8f)
                verticalLineTo(6.6f)
                arcToRelative(0.9f, 0.9f, 0f, false, false, -1.4f, -0.8f)
                close()
            }
            line {
                moveTo(6.2f, 6f)
                verticalLineTo(18f)
            }
        }
    }

    val Monitor: ImageVector by lazy {
        stroked("sautiy.monitor") {
            line {
                // Headphones: a band and two cups.
                moveTo(4.5f, 14f)
                verticalLineTo(12f)
                arcToRelative(7.5f, 7.5f, 0f, false, true, 15f, 0f)
                verticalLineTo(14f)
            }
            line {
                moveTo(4.5f, 14f)
                horizontalLineTo(6.5f)
                verticalLineTo(18.5f)
                horizontalLineTo(4.5f)
                close()
            }
            line {
                moveTo(17.5f, 14f)
                horizontalLineTo(19.5f)
                verticalLineTo(18.5f)
                horizontalLineTo(17.5f)
                close()
            }
        }
    }

    /** The commit control: forward, toward a finished thing. */
    val Commit: ImageVector by lazy {
        stroked("sautiy.commit") {
            line {
                moveTo(4.5f, 12f)
                horizontalLineTo(19f)
            }
            line {
                moveTo(13.5f, 6.5f)
                lineTo(19f, 12f)
                lineTo(13.5f, 17.5f)
            }
        }
    }

    // --- Editing -------------------------------------------------------------------------------

    val Undo: ImageVector by lazy {
        stroked("sautiy.undo") {
            line {
                moveTo(4.5f, 9.5f)
                horizontalLineTo(14f)
                arcToRelative(5.5f, 5.5f, 0f, false, true, 0f, 11f)
                horizontalLineTo(9f)
            }
            line {
                moveTo(8f, 5.5f)
                lineTo(4.5f, 9.5f)
                lineTo(8f, 13.5f)
            }
        }
    }

    val Redo: ImageVector by lazy {
        stroked("sautiy.redo") {
            line {
                moveTo(19.5f, 9.5f)
                horizontalLineTo(10f)
                arcToRelative(5.5f, 5.5f, 0f, false, false, 0f, 11f)
                horizontalLineTo(15f)
            }
            line {
                moveTo(16f, 5.5f)
                lineTo(19.5f, 9.5f)
                lineTo(16f, 13.5f)
            }
        }
    }

    val Cut: ImageVector by lazy {
        stroked("sautiy.cut") {
            line {
                moveTo(6f, 4.5f)
                lineTo(18f, 19.5f)
            }
            line {
                moveTo(18f, 4.5f)
                lineTo(6f, 19.5f)
            }
        }
    }

    val Split: ImageVector by lazy {
        stroked("sautiy.split") {
            line {
                moveTo(12f, 3.5f)
                verticalLineTo(20.5f)
            }
            line {
                moveTo(4f, 8f)
                verticalLineTo(16f)
            }
            line {
                moveTo(20f, 8f)
                verticalLineTo(16f)
            }
        }
    }

    val Trim: ImageVector by lazy {
        stroked("sautiy.trim") {
            line {
                moveTo(7.5f, 3.5f)
                verticalLineTo(16.5f)
                horizontalLineTo(20.5f)
            }
            line {
                moveTo(3.5f, 7.5f)
                horizontalLineTo(16.5f)
                verticalLineTo(20.5f)
            }
        }
    }

    val Fade: ImageVector by lazy {
        stroked("sautiy.fade") {
            line {
                moveTo(4f, 18f)
                lineTo(20f, 6f)
            }
            line {
                moveTo(4f, 18f)
                horizontalLineTo(20f)
            }
        }
    }

    val Marker: ImageVector by lazy {
        stroked("sautiy.marker") {
            line {
                moveTo(6.5f, 3.5f)
                verticalLineTo(20.5f)
            }
            line {
                moveTo(6.5f, 4.5f)
                horizontalLineTo(17.5f)
                lineTo(14.5f, 8.5f)
                lineTo(17.5f, 12.5f)
                horizontalLineTo(6.5f)
            }
        }
    }

    val Layers: ImageVector by lazy {
        stroked("sautiy.layers") {
            line {
                moveTo(12f, 3.5f)
                lineTo(20.5f, 8f)
                lineTo(12f, 12.5f)
                lineTo(3.5f, 8f)
                close()
            }
            line {
                moveTo(3.5f, 12.5f)
                lineTo(12f, 17f)
                lineTo(20.5f, 12.5f)
            }
            line {
                moveTo(3.5f, 16.5f)
                lineTo(12f, 21f)
                lineTo(20.5f, 16.5f)
            }
        }
    }

    val Add: ImageVector by lazy {
        stroked("sautiy.add") {
            line {
                moveTo(12f, 5f)
                verticalLineTo(19f)
            }
            line {
                moveTo(5f, 12f)
                horizontalLineTo(19f)
            }
        }
    }

    val Close: ImageVector by lazy {
        stroked("sautiy.close") {
            line {
                moveTo(6f, 6f)
                lineTo(18f, 18f)
            }
            line {
                moveTo(18f, 6f)
                lineTo(6f, 18f)
            }
        }
    }

    // --- Studio ----------------------------------------------------------------------------------

    val Enhance: ImageVector by lazy {
        stroked("sautiy.enhance") {
            // A wand with two sparks: enhancement, not magic.
            line {
                moveTo(5f, 19f)
                lineTo(15f, 9f)
            }
            line {
                moveTo(14f, 8f)
                lineTo(16f, 10f)
            }
            line {
                moveTo(17.5f, 3.5f)
                verticalLineTo(7.5f)
            }
            line {
                moveTo(15.5f, 5.5f)
                horizontalLineTo(19.5f)
            }
            line {
                moveTo(19f, 12f)
                verticalLineTo(15f)
            }
            line {
                moveTo(17.5f, 13.5f)
                horizontalLineTo(20.5f)
            }
        }
    }

    val Equaliser: ImageVector by lazy {
        stroked("sautiy.equaliser") {
            line {
                moveTo(6.5f, 4f)
                verticalLineTo(20f)
            }
            line {
                moveTo(4f, 9f)
                horizontalLineTo(9f)
            }
            line {
                moveTo(12f, 4f)
                verticalLineTo(20f)
            }
            line {
                moveTo(9.5f, 15f)
                horizontalLineTo(14.5f)
            }
            line {
                moveTo(17.5f, 4f)
                verticalLineTo(20f)
            }
            line {
                moveTo(15f, 8f)
                horizontalLineTo(20f)
            }
        }
    }

    val Analysis: ImageVector by lazy {
        stroked("sautiy.analysis") {
            line {
                moveTo(4f, 20f)
                verticalLineTo(4f)
            }
            line {
                moveTo(4f, 20f)
                horizontalLineTo(20f)
            }
            line {
                moveTo(7.5f, 16f)
                verticalLineTo(11f)
            }
            line {
                moveTo(12f, 16f)
                verticalLineTo(7f)
            }
            line {
                moveTo(16.5f, 16f)
                verticalLineTo(13f)
            }
        }
    }

    val Space: ImageVector by lazy {
        stroked("sautiy.space") {
            // Concentric arcs: a room, not a repeat.
            line {
                moveTo(8f, 8f)
                arcToRelative(6f, 6f, 0f, false, false, 0f, 8f)
            }
            line {
                moveTo(5f, 5.5f)
                arcToRelative(9.5f, 9.5f, 0f, false, false, 0f, 13f)
            }
            line {
                moveTo(13f, 7f)
                verticalLineTo(17f)
            }
            line {
                moveTo(17f, 9.5f)
                verticalLineTo(14.5f)
            }
        }
    }

    val Library: ImageVector by lazy {
        stroked("sautiy.library") {
            line {
                moveTo(4.5f, 5f)
                verticalLineTo(19f)
            }
            line {
                moveTo(8.5f, 5f)
                verticalLineTo(19f)
            }
            line {
                moveTo(12.5f, 5.5f)
                lineTo(17.5f, 4.5f)
                lineTo(20f, 18f)
                lineTo(15f, 19f)
                close()
            }
        }
    }

    val History: ImageVector by lazy {
        stroked("sautiy.history") {
            line {
                moveTo(12f, 6.5f)
                verticalLineTo(12f)
                lineTo(15.5f, 14f)
            }
            line {
                moveTo(4f, 12f)
                arcToRelative(8f, 8f, 0f, true, false, 2.4f, -5.7f)
            }
            line {
                moveTo(3.5f, 4f)
                verticalLineTo(8f)
                horizontalLineTo(7.5f)
            }
        }
    }

    val Settings: ImageVector by lazy {
        stroked("sautiy.settings") {
            line {
                moveTo(7f, 5f)
                verticalLineTo(19f)
            }
            line {
                moveTo(7f, 8.5f)
                moveToRelative(-2f, 0f)
                arcToRelative(2f, 2f, 0f, true, true, 4f, 0f)
                arcToRelative(2f, 2f, 0f, true, true, -4f, 0f)
            }
            line {
                moveTo(17f, 5f)
                verticalLineTo(19f)
            }
            line {
                moveTo(17f, 15.5f)
                moveToRelative(-2f, 0f)
                arcToRelative(2f, 2f, 0f, true, true, 4f, 0f)
                arcToRelative(2f, 2f, 0f, true, true, -4f, 0f)
            }
        }
    }

    val Speed: ImageVector by lazy {
        stroked("sautiy.speed") {
            line {
                moveTo(4f, 17f)
                arcToRelative(8f, 8f, 0f, false, true, 16f, 0f)
            }
            line {
                moveTo(12f, 17f)
                lineTo(16f, 10.5f)
            }
        }
    }

    val Loop: ImageVector by lazy {
        stroked("sautiy.loop") {
            line {
                moveTo(6.5f, 8f)
                horizontalLineTo(17.5f)
                verticalLineTo(13f)
            }
            line {
                moveTo(17.5f, 16f)
                horizontalLineTo(6.5f)
                verticalLineTo(11f)
            }
            line {
                moveTo(9.5f, 5f)
                lineTo(6.5f, 8f)
                lineTo(9.5f, 11f)
            }
            line {
                moveTo(14.5f, 13f)
                lineTo(17.5f, 16f)
                lineTo(14.5f, 19f)
            }
        }
    }

    val Compare: ImageVector by lazy {
        stroked("sautiy.compare") {
            line {
                moveTo(12f, 4f)
                verticalLineTo(20f)
            }
            line {
                moveTo(4f, 9f)
                horizontalLineTo(9f)
            }
            line {
                moveTo(15f, 15f)
                horizontalLineTo(20f)
            }
            line {
                moveTo(6.5f, 6.5f)
                lineTo(4f, 9f)
                lineTo(6.5f, 11.5f)
            }
            line {
                moveTo(17.5f, 12.5f)
                lineTo(20f, 15f)
                lineTo(17.5f, 17.5f)
            }
        }
    }

    val Waveform: ImageVector by lazy {
        stroked("sautiy.waveform") {
            line {
                moveTo(3.5f, 10.5f)
                verticalLineTo(13.5f)
            }
            line {
                moveTo(7.75f, 7f)
                verticalLineTo(17f)
            }
            line {
                moveTo(12f, 4f)
                verticalLineTo(20f)
            }
            line {
                moveTo(16.25f, 7f)
                verticalLineTo(17f)
            }
            line {
                moveTo(20.5f, 10.5f)
                verticalLineTo(13.5f)
            }
        }
    }
}
