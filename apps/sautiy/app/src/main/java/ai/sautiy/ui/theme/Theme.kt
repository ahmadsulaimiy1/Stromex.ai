package ai.sautiy.ui.theme

import ai.sautiy.R
import ai.sautiy.core.design.Motion
import ai.sautiy.core.design.Radius
import ai.sautiy.core.design.SautiyColours
import ai.sautiy.core.design.Sizes
import ai.sautiy.core.design.Space
import ai.sautiy.core.design.TypeScale
import ai.sautiy.core.design.TypeStyle
import androidx.compose.animation.core.CubicBezierEasing
import androidx.compose.animation.core.Easing
import androidx.compose.animation.core.tween
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.ReadOnlyComposable
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.LineHeightStyle
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/**
 * The SAUTIY theme.
 *
 * Every value here is read from `sautiy-core`'s design objects rather than declared locally.
 * That is the mechanism behind chapter 2: the palette, the type scale, the spacing grid and the
 * motion tiers have exactly one definition, it is unit-tested for contrast and rhythm on a
 * plain JVM, and the UI layer cannot quietly introduce a colour or a duration of its own.
 */

@Immutable
data class SautiyColourScheme(
    val isDark: Boolean,
    val canvas: Color,
    val surface: Color,
    val surfaceRaised: Color,
    val surfaceOverlay: Color,
    val border: Color,
    val borderStrong: Color,
    val textPrimary: Color,
    val textSecondary: Color,
    val textTertiary: Color,
    val textDisabled: Color,
    val signal: Color,
    val signalMuted: Color,
    val signalSelection: Color,
    val onSignal: Color,
    val ember: Color,
    val onEmber: Color,
    val commit: Color,
    val onCommit: Color,
    val safe: Color,
    val caution: Color,
    val critical: Color,
) {
    companion object {
        private fun from(core: SautiyColours) = SautiyColourScheme(
            isDark = core.isDark,
            canvas = Color(core.canvas),
            surface = Color(core.surface),
            surfaceRaised = Color(core.surfaceRaised),
            surfaceOverlay = Color(core.surfaceOverlay),
            border = Color(core.border),
            borderStrong = Color(core.borderStrong),
            textPrimary = Color(core.textPrimary),
            textSecondary = Color(core.textSecondary),
            textTertiary = Color(core.textTertiary),
            textDisabled = Color(core.textDisabled),
            signal = Color(core.signal),
            signalMuted = Color(core.signalMuted),
            signalSelection = Color(core.signalSelection),
            onSignal = Color(core.onSignal),
            ember = Color(core.ember),
            onEmber = Color(core.onEmber),
            commit = Color(core.commit),
            onCommit = Color(core.onCommit),
            safe = Color(core.safe),
            caution = Color(core.caution),
            critical = Color(core.critical),
        )

        val Dark = from(SautiyColours.Dark)
        val Light = from(SautiyColours.Light)
    }
}

/** Chapter 2.4: four families, each with one job, all bundled — SAUTIY never fetches a font. */
object SautiyFonts {
    val Display = FontFamily(
        Font(R.font.fraunces_light, FontWeight.Light),
        Font(R.font.fraunces_semibold, FontWeight.SemiBold),
    )
    val Ui = FontFamily(
        Font(R.font.archivo_regular, FontWeight.Normal),
        Font(R.font.archivo_bold, FontWeight.Bold),
    )
    val QuranicArabic = FontFamily(
        Font(R.font.amiri_regular, FontWeight.Normal),
        Font(R.font.amiri_bold, FontWeight.Bold),
    )
    val UiArabic = FontFamily(
        Font(R.font.cairo_regular, FontWeight.Normal),
        Font(R.font.cairo_bold, FontWeight.Bold),
    )
}

@Immutable
data class SautiyTypography(
    val displayLarge: TextStyle,
    val displaySmall: TextStyle,
    val titleLarge: TextStyle,
    val titleMedium: TextStyle,
    val bodyLarge: TextStyle,
    val bodyMedium: TextStyle,
    val labelLarge: TextStyle,
    val labelMedium: TextStyle,
    val labelSmall: TextStyle,
    val timerHero: TextStyle,
    val timerInline: TextStyle,
    val numeric: TextStyle,
    val quranAyah: TextStyle,
)

private fun TypeStyle.toTextStyle(): TextStyle = TextStyle(
    fontFamily = when (family) {
        ai.sautiy.core.design.TypeFamily.DISPLAY -> SautiyFonts.Display
        ai.sautiy.core.design.TypeFamily.UI -> SautiyFonts.Ui
        ai.sautiy.core.design.TypeFamily.QURANIC_ARABIC -> SautiyFonts.QuranicArabic
        ai.sautiy.core.design.TypeFamily.UI_ARABIC -> SautiyFonts.UiArabic
    },
    fontWeight = FontWeight(weight),
    fontSize = sizeSp.sp,
    lineHeight = lineHeightSp.sp,
    letterSpacing = trackingSp.sp,
    // Chapter 2.4.2 clause 1: any number that changes in place must be tabular, or the timer
    // jitters as its digits change and the eye is dragged to it.
    fontFeatureSettings = if (tabularFigures) "tnum" else null,
    lineHeightStyle = LineHeightStyle(
        alignment = LineHeightStyle.Alignment.Center,
        trim = LineHeightStyle.Trim.None,
    ),
)

private val sautiyTypography = SautiyTypography(
    displayLarge = TypeScale.displayLarge.toTextStyle(),
    displaySmall = TypeScale.displaySmall.toTextStyle(),
    titleLarge = TypeScale.titleLarge.toTextStyle(),
    titleMedium = TypeScale.titleMedium.toTextStyle(),
    bodyLarge = TypeScale.bodyLarge.toTextStyle(),
    bodyMedium = TypeScale.bodyMedium.toTextStyle(),
    labelLarge = TypeScale.labelLarge.toTextStyle(),
    labelMedium = TypeScale.labelMedium.toTextStyle(),
    labelSmall = TypeScale.labelSmall.toTextStyle(),
    timerHero = TypeScale.timerHero.toTextStyle(),
    timerInline = TypeScale.timerInline.toTextStyle(),
    numeric = TypeScale.numeric.toTextStyle(),
    quranAyah = TypeScale.quranAyah.toTextStyle(),
)

/** Chapter 6, as Compose specs. Nothing in SAUTIY animates outside these tiers. */
object SautiyMotion {
    val Standard: Easing = CubicBezierEasing(
        Motion.STANDARD_EASING[0], Motion.STANDARD_EASING[1],
        Motion.STANDARD_EASING[2], Motion.STANDARD_EASING[3],
    )
    val Emphasised: Easing = CubicBezierEasing(
        Motion.EMPHASISED_EASING[0], Motion.EMPHASISED_EASING[1],
        Motion.EMPHASISED_EASING[2], Motion.EMPHASISED_EASING[3],
    )
    val Exit: Easing = CubicBezierEasing(
        Motion.EXIT_EASING[0], Motion.EXIT_EASING[1],
        Motion.EXIT_EASING[2], Motion.EXIT_EASING[3],
    )

    fun <T> instant() = tween<T>(Motion.INSTANT_MS, easing = Standard)
    fun <T> fast() = tween<T>(Motion.FAST_MS, easing = Standard)
    fun <T> standard() = tween<T>(Motion.STANDARD_MS, easing = Standard)
    fun <T> emphasised() = tween<T>(Motion.EMPHASISED_MS, easing = Emphasised)
    fun <T> exit() = tween<T>(Motion.FAST_MS, easing = Exit)
}

/** Chapter 5. Radii by role, so a corner is never chosen at a call site. */
object SautiyShapes {
    val extraSmall = RoundedCornerShape(Radius.XS.dp)
    val small = RoundedCornerShape(Radius.S.dp)
    val medium = RoundedCornerShape(Radius.M.dp)
    val large = RoundedCornerShape(Radius.L.dp)
    val extraLarge = RoundedCornerShape(Radius.XL.dp)
    val sheet = RoundedCornerShape(topStart = Radius.SHEET.dp, topEnd = Radius.SHEET.dp)
    val pill = RoundedCornerShape(percent = 50)
}

/** Chapter 5. The spacing grid, as dp. */
object SautiySpace {
    val xxs = Space.XXS.dp
    val xs = Space.XS.dp
    val s = Space.S.dp
    val m = Space.M.dp
    val l = Space.L.dp
    val xl = Space.XL.dp
    val xxl = Space.XXL.dp
    val h3 = Space.H3.dp
    val h4 = Space.H4.dp
    val h5 = Space.H5.dp
    val h6 = Space.H6.dp
    val pageInset = Space.PAGE_INSET.dp
    val sectionGap = Space.SECTION_GAP.dp

    /** Chapter 3.2.4 / 17: nothing interactive is ever smaller than this. */
    val minTouchTarget = ai.sautiy.core.PerformanceBudget.MIN_TOUCH_TARGET_DP.dp
}

/**
 * Every component size, as dp — Phase Ω.
 *
 * A call site never chooses a size, the same way it never chooses a corner radius or a colour. Each
 * of these comes from `Sizes` in the tested module, and a test scans the Compose sources to make
 * sure no new number gets invented in a hurry. That scan is the point: four icon sizes in four
 * files is not something a person can hold in their head, and it is exactly what makes an interface
 * feel assembled rather than designed.
 */
object SautiySize {
    val iconSmall = Sizes.ICON_SMALL.dp
    val icon = Sizes.ICON_MEDIUM.dp
    val iconLarge = Sizes.ICON_LARGE.dp
    val dot = Sizes.DOT.dp
    val hairline = Sizes.HAIRLINE.dp
    val borderSelected = Sizes.BORDER_SELECTED.dp
    val handleWidth = Sizes.HANDLE_WIDTH.dp
    val handleHeight = Sizes.HANDLE_HEIGHT.dp
    val meterHeight = Sizes.METER_HEIGHT.dp
    val gaugeSmall = Sizes.GAUGE_SMALL.dp
    val gaugeLarge = Sizes.GAUGE_LARGE.dp
    val transport = Sizes.TRANSPORT.dp
    val transportPrimary = Sizes.TRANSPORT_PRIMARY.dp
    val dockHeight = Sizes.DOCK_HEIGHT.dp
    val iconHero = Sizes.ICON_HERO.dp
    val contextToolHeight = Sizes.CONTEXT_TOOL_HEIGHT.dp
    val contextBarHeight = Sizes.CONTEXT_BAR_HEIGHT.dp
    val canvasStroke = Sizes.CANVAS_STROKE.dp
    val ringInset = Sizes.RING_INSET.dp

    /** Zero, named, so "no border" is a stated choice rather than a bare literal. */
    val none = 0.dp
}

private val LocalSautiyColours = staticCompositionLocalOf { SautiyColourScheme.Dark }
private val LocalSautiyTypography = staticCompositionLocalOf { sautiyTypography }

object SautiyTheme {
    val colours: SautiyColourScheme
        @Composable @ReadOnlyComposable get() = LocalSautiyColours.current

    val type: SautiyTypography
        @Composable @ReadOnlyComposable get() = LocalSautiyTypography.current
}

/**
 * SAUTIY is dark-first (chapter 2.3) — recording happens at night, in mosques, in studios, and
 * a bright screen is a physical intrusion. The light theme is a first-class citizen, not an
 * afterthought, and follows the system unless the user has chosen otherwise.
 */
@Composable
fun SautiyTheme(
    dark: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    CompositionLocalProvider(
        LocalSautiyColours provides if (dark) SautiyColourScheme.Dark else SautiyColourScheme.Light,
        LocalSautiyTypography provides sautiyTypography,
        content = content,
    )
}
