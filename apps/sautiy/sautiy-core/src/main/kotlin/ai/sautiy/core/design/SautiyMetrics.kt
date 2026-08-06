package ai.sautiy.core.design

/**
 * Spacing, radius, type and motion tokens — Editorial Bible chapters 2.4, 5 and 6.
 *
 * Kept platform-neutral (plain numbers in dp/sp/ms) for the same reason as [SautiyTokens]:
 * one source of truth, testable without an Android device.
 */
public object Space {
    /** The rhythm unit. Every spacing value in SAUTIY is a multiple of this. */
    public const val UNIT: Int = 4

    public const val XXS: Int = 2
    public const val XS: Int = 4
    public const val S: Int = 8
    public const val M: Int = 12
    public const val L: Int = 16
    public const val XL: Int = 20
    public const val XXL: Int = 24
    public const val H3: Int = 32
    public const val H4: Int = 40
    public const val H5: Int = 48
    public const val H6: Int = 64

    /** Horizontal page inset. Every screen shares it so edges align across the product. */
    public const val PAGE_INSET: Int = 20

    /** Vertical gap between unrelated sections. */
    public const val SECTION_GAP: Int = 28

    public fun isOnGrid(dp: Int): Boolean = dp % UNIT == 0 || dp == XXS
}

public object Radius {
    public const val XS: Int = 4
    public const val S: Int = 8
    public const val M: Int = 12
    public const val L: Int = 16
    public const val XL: Int = 24
    public const val SHEET: Int = 28
    /** Fully rounded. Applied to transport controls and chips. */
    public const val PILL: Int = 1000
}

/**
 * Every size a component may be — chapter 5, and the reason Phase Ω exists.
 *
 * Before this object the app drew icons at 20, 22, 24 and 26 dp in four different places, dots at
 * 8 and 10, and strokes at 1.5 and 2. None of it was a decision; all of it was whatever was typed
 * at the time. A user cannot name that, but they can see it — it is precisely what makes an
 * interface feel assembled rather than designed.
 *
 * So the sizes live here, in the tested module, and a test scans the Compose sources to make sure
 * nothing invents a new one. **Consistency by enforcement, not by review**: a review catches this
 * once and a scan catches it forever.
 */
public object Sizes {
    /** Inline with body text — a chevron beside a label. */
    public const val ICON_SMALL: Int = 16

    /** The default. Every icon in a panel, a row or the status rail. */
    public const val ICON_MEDIUM: Int = 20

    /** Transport and other primary controls, where the icon *is* the control. */
    public const val ICON_LARGE: Int = 24

    /** A status dot: recording, a condition, a marker. One size, everywhere. */
    public const val DOT: Int = 8

    /** Hairline separators and unselected borders. */
    public const val HAIRLINE: Int = 1

    /** The border on a selected card. Thick enough to read at a glance, thin enough not to shout. */
    public const val BORDER_SELECTED: Int = 2

    /** The panel drag handle: one of chapter 4.4.1's four dismissal routes. */
    public const val HANDLE_WIDTH: Int = 36
    public const val HANDLE_HEIGHT: Int = 4

    /** The level meter's bar. */
    public const val METER_HEIGHT: Int = 8

    /** A gauge arc. Two sizes: beside text, and standing alone. */
    public const val GAUGE_SMALL: Int = 56
    public const val GAUGE_LARGE: Int = 64

    /** Transport buttons. The record control is larger because it is the one thumb target. */
    public const val TRANSPORT: Int = 52
    public const val TRANSPORT_PRIMARY: Int = 76

    /** The dock. Fixed, because chapter 4.3 says it never moves. */
    public const val DOCK_HEIGHT: Int = 108

    /** Minimum touch target — chapter 17. Never smaller, whatever it looks like. */
    public const val MIN_TOUCH_TARGET: Int = 48

    /** The icon in an empty state, which is illustration rather than control. */
    public const val ICON_HERO: Int = 48

    /** The context bar and the tools in it. */
    public const val CONTEXT_TOOL_HEIGHT: Int = 56
    public const val CONTEXT_BAR_HEIGHT: Int = 76

    /**
     * Every line drawn on a canvas — waveform bars, the playhead, marker rules.
     *
     * One width, not 1.5 for the bars and 2 for the playhead. The half-pixel difference was
     * invisible as intent and visible as inconsistency at the seam where they meet.
     */
    public const val CANVAS_STROKE: Int = 2

    /** The gap inside the record button's ring. On the grid, unlike the 5 dp it replaced. */
    public const val RING_INSET: Int = 4

    /** Every size this design system contains, for the scan to check against. */
    public val all: Set<Int> = setOf(
        ICON_SMALL, ICON_MEDIUM, ICON_LARGE, ICON_HERO, DOT, HAIRLINE, BORDER_SELECTED,
        HANDLE_WIDTH, HANDLE_HEIGHT, METER_HEIGHT, GAUGE_SMALL, GAUGE_LARGE,
        TRANSPORT, TRANSPORT_PRIMARY, DOCK_HEIGHT, MIN_TOUCH_TARGET,
        CONTEXT_TOOL_HEIGHT, CONTEXT_BAR_HEIGHT, CANVAS_STROKE, RING_INSET,
    )
}

/**
 * Motion — chapter 6. SAUTIY moves like a well-damped mechanism: fast, decisive, never
 * bouncy. Overshoot above [MAX_OVERSHOOT_FRACTION] is forbidden.
 */
public object Motion {
    /** State change the user must not perceive as animation at all. */
    public const val INSTANT_MS: Int = 90

    /** Control feedback: press, toggle, meter settle. */
    public const val FAST_MS: Int = 140

    /** The default. Sheets, reveals, list changes. */
    public const val STANDARD_MS: Int = 220

    /** Emphasised: a sheet arriving with content the user must read. */
    public const val EMPHASISED_MS: Int = 320

    /** Large surface transitions only. Nothing in SAUTIY may exceed this. */
    public const val LARGE_MS: Int = 480

    public const val MAX_DURATION_MS: Int = LARGE_MS

    public const val MAX_OVERSHOOT_FRACTION: Double = 0.03

    /** cubic-bezier control points. */
    public val STANDARD_EASING: FloatArray = floatArrayOf(0.20f, 0.00f, 0.00f, 1.00f)
    public val EMPHASISED_EASING: FloatArray = floatArrayOf(0.05f, 0.70f, 0.10f, 1.00f)
    public val EXIT_EASING: FloatArray = floatArrayOf(0.30f, 0.00f, 1.00f, 1.00f)

    /**
     * Meter ballistics. A level meter that follows the signal exactly is unreadable; one that
     * lags is dishonest. SAUTIY uses broadcast-style ballistics: instant attack, 20 dB/s
     * release, with a peak-hold that decays after a dwell.
     */
    public const val METER_ATTACK_MS: Int = 0
    public const val METER_RELEASE_DB_PER_SEC: Double = 20.0
    public const val PEAK_HOLD_DWELL_MS: Int = 1_200
    public const val PEAK_HOLD_FALL_DB_PER_SEC: Double = 12.0
}

/** A single entry in the type scale (chapter 2.4.1). Sizes are sp; line heights are sp. */
public data class TypeStyle(
    val family: TypeFamily,
    val weight: Int,
    val sizeSp: Int,
    val lineHeightSp: Int,
    val trackingSp: Double,
    /** Tabular figures — mandatory for any number that changes in place (chapter 2.4.2). */
    val tabularFigures: Boolean = false,
)

public enum class TypeFamily { DISPLAY, UI, QURANIC_ARABIC, UI_ARABIC }

/** The complete SAUTIY type scale. The UI layer may not invent a style outside this set. */
public object TypeScale {
    public val displayLarge: TypeStyle = TypeStyle(TypeFamily.DISPLAY, 300, 40, 46, -0.6)
    public val displaySmall: TypeStyle = TypeStyle(TypeFamily.DISPLAY, 600, 28, 34, -0.3)
    public val titleLarge: TypeStyle = TypeStyle(TypeFamily.UI, 700, 22, 28, -0.2)
    public val titleMedium: TypeStyle = TypeStyle(TypeFamily.UI, 700, 17, 24, 0.0)
    public val bodyLarge: TypeStyle = TypeStyle(TypeFamily.UI, 400, 16, 24, 0.0)
    public val bodyMedium: TypeStyle = TypeStyle(TypeFamily.UI, 400, 14, 20, 0.1)
    public val labelLarge: TypeStyle = TypeStyle(TypeFamily.UI, 700, 14, 18, 0.4)
    public val labelMedium: TypeStyle = TypeStyle(TypeFamily.UI, 700, 12, 16, 0.6)
    public val labelSmall: TypeStyle = TypeStyle(TypeFamily.UI, 700, 11, 14, 0.8)
    public val timerHero: TypeStyle = TypeStyle(TypeFamily.UI, 400, 44, 48, -1.2, tabularFigures = true)
    public val timerInline: TypeStyle = TypeStyle(TypeFamily.UI, 400, 15, 20, 0.0, tabularFigures = true)
    public val numeric: TypeStyle = TypeStyle(TypeFamily.UI, 700, 13, 16, 0.0, tabularFigures = true)
    public val quranAyah: TypeStyle = TypeStyle(TypeFamily.QURANIC_ARABIC, 400, 26, 48, 0.0)

    public val all: List<Pair<String, TypeStyle>> = listOf(
        "displayLarge" to displayLarge,
        "displaySmall" to displaySmall,
        "titleLarge" to titleLarge,
        "titleMedium" to titleMedium,
        "bodyLarge" to bodyLarge,
        "bodyMedium" to bodyMedium,
        "labelLarge" to labelLarge,
        "labelMedium" to labelMedium,
        "labelSmall" to labelSmall,
        "timerHero" to timerHero,
        "timerInline" to timerInline,
        "numeric" to numeric,
        "quranAyah" to quranAyah,
    )
}
