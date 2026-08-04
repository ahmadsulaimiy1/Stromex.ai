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
