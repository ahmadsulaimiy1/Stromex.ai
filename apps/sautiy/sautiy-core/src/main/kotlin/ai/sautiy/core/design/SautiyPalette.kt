package ai.sautiy.core.design

/**
 * The SAUTIY colour system — Editorial Bible chapter 2.3.
 *
 * Deliberately platform-neutral: colours live here as packed `0xAARRGGBB` integers so that
 * the palette can be unit-tested for contrast on a plain JVM, and so that a single source of
 * truth serves the Android theme, any future desktop surface, and the documentation
 * generator. The Compose layer maps these to `Color` and never declares a literal of its own.
 *
 * Colour is requested by *role* ([SautiyColours]), never by raw token, at every call site.
 */
public object SautiyTokens {
    // --- Dark ramp -----------------------------------------------------------------
    public const val INK_900: Int = 0xFF05070A.toInt()
    public const val INK_850: Int = 0xFF0A0D13.toInt()
    public const val INK_800: Int = 0xFF11151D.toInt()
    public const val INK_750: Int = 0xFF161B25.toInt()
    public const val INK_700: Int = 0xFF1E2532.toInt()
    public const val INK_600: Int = 0xFF2A3341.toInt()

    // --- Paper ramp ----------------------------------------------------------------
    public const val PAPER_000: Int = 0xFFFFFFFF.toInt()
    public const val PAPER_050: Int = 0xFFF7F9FC.toInt()
    public const val PAPER_100: Int = 0xFFEDF1F6.toInt()
    public const val PAPER_200: Int = 0xFFE2E8F0.toInt()
    public const val PAPER_300: Int = 0xFFCBD3DE.toInt()

    // --- Type on dark ---------------------------------------------------------------
    public const val TYPE_ON_DARK_PRIMARY: Int = 0xFFF2F5F9.toInt()
    public const val TYPE_ON_DARK_SECONDARY: Int = 0xFFA9B3C1.toInt()
    public const val TYPE_ON_DARK_TERTIARY: Int = 0xFF8B95A4.toInt()
    public const val TYPE_ON_DARK_DISABLED: Int = 0xFF6A7382.toInt()

    // --- Type on light --------------------------------------------------------------
    public const val TYPE_ON_LIGHT_PRIMARY: Int = 0xFF080B11.toInt()
    public const val TYPE_ON_LIGHT_SECONDARY: Int = 0xFF48525F.toInt()
    public const val TYPE_ON_LIGHT_TERTIARY: Int = 0xFF5C6673.toInt()
    public const val TYPE_ON_LIGHT_DISABLED: Int = 0xFF767F8C.toInt()

    // --- Signal (SAUTIY's voice: waveform, analysis, selection) -----------------------
    public const val SIGNAL_300: Int = 0xFF7FB2FF.toInt()
    public const val SIGNAL_500: Int = 0xFF2F80FF.toInt()
    public const val SIGNAL_600: Int = 0xFF1A63D8.toInt()
    public const val SIGNAL_900: Int = 0xFF0D1B33.toInt()

    // --- Ember (reserved: recording, and nothing else) --------------------------------
    public const val EMBER_300: Int = 0xFFFF6A5E.toInt()
    public const val EMBER_500: Int = 0xFFE63329.toInt()
    public const val EMBER_600: Int = 0xFFC42A21.toInt()

    // --- Commit (the forward action) ---------------------------------------------------
    public const val ROSE_300: Int = 0xFFFF6FA3.toInt()
    public const val ROSE_500: Int = 0xFFE0246B.toInt()
    public const val ROSE_600: Int = 0xFFBE1B59.toInt()

    // --- Status ------------------------------------------------------------------------
    public const val VERDANT_400: Int = 0xFF4CD68C.toInt()
    public const val VERDANT_500: Int = 0xFF2FBF71.toInt()
    public const val VERDANT_600: Int = 0xFF1E9B58.toInt()
    public const val AMBER_400: Int = 0xFFFFC15E.toInt()
    public const val AMBER_500: Int = 0xFFF5A524.toInt()
    public const val AMBER_600: Int = 0xFFB87610.toInt()
    public const val CRIMSON_400: Int = 0xFFFF6A5E.toInt()
    public const val CRIMSON_500: Int = 0xFFF0483E.toInt()
    public const val CRIMSON_600: Int = 0xFFC93227.toInt()
}

/**
 * A fully resolved set of semantic colour roles. UI code asks for `colours.signal`, never for
 * `SIGNAL_500`, so a theme change is a single substitution and contrast can be proven for the
 * whole set at once.
 */
public data class SautiyColours(
    val isDark: Boolean,
    val canvas: Int,
    val surface: Int,
    val surfaceRaised: Int,
    val surfaceOverlay: Int,
    val border: Int,
    val borderStrong: Int,
    val textPrimary: Int,
    val textSecondary: Int,
    val textTertiary: Int,
    val textDisabled: Int,
    val signal: Int,
    val signalMuted: Int,
    val signalSelection: Int,
    val onSignal: Int,
    val ember: Int,
    val onEmber: Int,
    val commit: Int,
    val onCommit: Int,
    val safe: Int,
    val caution: Int,
    val critical: Int,
) {
    public companion object {
        public val Dark: SautiyColours = SautiyColours(
            isDark = true,
            canvas = SautiyTokens.INK_900,
            surface = SautiyTokens.INK_850,
            surfaceRaised = SautiyTokens.INK_800,
            surfaceOverlay = SautiyTokens.INK_750,
            border = SautiyTokens.INK_600,
            borderStrong = SautiyTokens.INK_700,
            textPrimary = SautiyTokens.TYPE_ON_DARK_PRIMARY,
            textSecondary = SautiyTokens.TYPE_ON_DARK_SECONDARY,
            textTertiary = SautiyTokens.TYPE_ON_DARK_TERTIARY,
            textDisabled = SautiyTokens.TYPE_ON_DARK_DISABLED,
            signal = SautiyTokens.SIGNAL_500,
            signalMuted = SautiyTokens.SIGNAL_600,
            signalSelection = SautiyTokens.SIGNAL_900,
            onSignal = SautiyTokens.PAPER_000,
            ember = SautiyTokens.EMBER_500,
            onEmber = SautiyTokens.PAPER_000,
            commit = SautiyTokens.ROSE_500,
            onCommit = SautiyTokens.PAPER_000,
            safe = SautiyTokens.VERDANT_400,
            caution = SautiyTokens.AMBER_400,
            critical = SautiyTokens.CRIMSON_400,
        )

        public val Light: SautiyColours = SautiyColours(
            isDark = false,
            canvas = SautiyTokens.PAPER_050,
            surface = SautiyTokens.PAPER_000,
            surfaceRaised = SautiyTokens.PAPER_100,
            surfaceOverlay = SautiyTokens.PAPER_000,
            border = SautiyTokens.PAPER_300,
            borderStrong = SautiyTokens.PAPER_200,
            textPrimary = SautiyTokens.TYPE_ON_LIGHT_PRIMARY,
            textSecondary = SautiyTokens.TYPE_ON_LIGHT_SECONDARY,
            textTertiary = SautiyTokens.TYPE_ON_LIGHT_TERTIARY,
            textDisabled = SautiyTokens.TYPE_ON_LIGHT_DISABLED,
            signal = SautiyTokens.SIGNAL_600,
            signalMuted = SautiyTokens.SIGNAL_500,
            signalSelection = 0xFFDCE9FF.toInt(),
            onSignal = SautiyTokens.PAPER_000,
            ember = SautiyTokens.EMBER_600,
            onEmber = SautiyTokens.PAPER_000,
            commit = SautiyTokens.ROSE_600,
            onCommit = SautiyTokens.PAPER_000,
            safe = SautiyTokens.VERDANT_600,
            caution = SautiyTokens.AMBER_600,
            critical = SautiyTokens.CRIMSON_600,
        )
    }
}

/**
 * WCAG 2.1 relative luminance and contrast, used by [ContrastTest] to hold chapter 2.3.4's
 * contrast floors as an executable rule rather than an aspiration.
 */
public object Contrast {
    private fun channel(component: Int): Double {
        val c = component / 255.0
        return if (c <= 0.03928) c / 12.92 else Math.pow((c + 0.055) / 1.055, 2.4)
    }

    /** WCAG relative luminance of an opaque `0xAARRGGBB` colour. */
    public fun luminance(argb: Int): Double {
        val r = channel((argb shr 16) and 0xFF)
        val g = channel((argb shr 8) and 0xFF)
        val b = channel(argb and 0xFF)
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    }

    /** WCAG contrast ratio between two opaque colours, in the range 1.0..21.0. */
    public fun ratio(foreground: Int, background: Int): Double {
        val a = luminance(foreground)
        val b = luminance(background)
        val lighter = maxOf(a, b)
        val darker = minOf(a, b)
        return (lighter + 0.05) / (darker + 0.05)
    }

    /** Body-text floor from chapter 2.3.4. */
    public const val BODY_TEXT_FLOOR: Double = 4.5

    /** Large-text, icon, meter and focus-ring floor from chapter 2.3.4. */
    public const val LARGE_AND_NON_TEXT_FLOOR: Double = 3.0
}
