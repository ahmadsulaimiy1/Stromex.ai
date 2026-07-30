package com.sajjil.app.ui.theme

import androidx.compose.material3.ColorScheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.ui.graphics.Color

/**
 * SAJJIL's flagship themes. Each maps to a full Material3 [ColorScheme] so
 * every screen automatically adopts the chosen identity. [ROYAL_NAVY_DEEP]
 * is the flagship default — a Saudi Vision 2030 / NEOM-publication-quality
 * deep navy (#082A66) with restrained gold accents.
 */
enum class SajjilTheme(val displayName: String) {
    ROYAL_NAVY_DEEP("Royal Navy Deep"),
    ROYAL_GOLD("Royal Gold"),
    MIDNIGHT_BLACK("Midnight Black"),
    EMERALD_PRESTIGE("Emerald Prestige"),
    SAPPHIRE_BLUE("Sapphire Blue"),
    MAKKAH_NIGHT("Makkah Night"),
    MADINAH_GREEN("Madinah Green"),
    PLATINUM_WHITE("Platinum White"),
    EXECUTIVE_DARK("Executive Dark");

    val colorScheme: ColorScheme
        get() = when (this) {
            ROYAL_NAVY_DEEP -> darkColorScheme(
                primary = Color(0xFFD4AF37),
                onPrimary = Color(0xFF071433),
                secondary = Color(0xFF6D8FD1),
                onSecondary = Color(0xFF071433),
                background = Color(0xFF050B1E),
                onBackground = Color(0xFFE7ECFA),
                surface = Color(0xFF082A66),
                onSurface = Color(0xFFE7ECFA),
                surfaceVariant = Color(0xFF11305F),
                error = Color(0xFFFF6B6B),
            )
            ROYAL_GOLD -> darkColorScheme(
                primary = Color(0xFFD4AF37),
                onPrimary = Color(0xFF241C00),
                secondary = Color(0xFFF2D879),
                onSecondary = Color(0xFF241C00),
                background = Color(0xFF141210),
                onBackground = Color(0xFFEFE7D8),
                surface = Color(0xFF1E1A15),
                onSurface = Color(0xFFEFE7D8),
                surfaceVariant = Color(0xFF2B241C),
                error = Color(0xFFCF6679),
            )
            MIDNIGHT_BLACK -> darkColorScheme(
                primary = Color(0xFFB0B3B8),
                onPrimary = Color(0xFF0A0A0B),
                secondary = Color(0xFF7C7F85),
                onSecondary = Color(0xFF0A0A0B),
                background = Color(0xFF000000),
                onBackground = Color(0xFFE7E7E9),
                surface = Color(0xFF0D0D0E),
                onSurface = Color(0xFFE7E7E9),
                surfaceVariant = Color(0xFF1C1C1E),
                error = Color(0xFFCF6679),
            )
            EMERALD_PRESTIGE -> darkColorScheme(
                primary = Color(0xFF2FB380),
                onPrimary = Color(0xFF00291B),
                secondary = Color(0xFF8FE3C2),
                onSecondary = Color(0xFF00291B),
                background = Color(0xFF0B1712),
                onBackground = Color(0xFFDFF3EA),
                surface = Color(0xFF12211B),
                onSurface = Color(0xFFDFF3EA),
                surfaceVariant = Color(0xFF1C332A),
                error = Color(0xFFCF6679),
            )
            SAPPHIRE_BLUE -> darkColorScheme(
                primary = Color(0xFF3E6FD9),
                onPrimary = Color(0xFF001947),
                secondary = Color(0xFF9AB6F5),
                onSecondary = Color(0xFF001947),
                background = Color(0xFF0A0E1A),
                onBackground = Color(0xFFDEE6FA),
                surface = Color(0xFF111830),
                onSurface = Color(0xFFDEE6FA),
                surfaceVariant = Color(0xFF1D2A4D),
                error = Color(0xFFCF6679),
            )
            MAKKAH_NIGHT -> darkColorScheme(
                primary = Color(0xFFE8C766),
                onPrimary = Color(0xFF201800),
                secondary = Color(0xFFB8975A),
                onSecondary = Color(0xFF201800),
                background = Color(0xFF060606),
                onBackground = Color(0xFFEFE6CE),
                surface = Color(0xFF0F0E0C),
                onSurface = Color(0xFFEFE6CE),
                surfaceVariant = Color(0xFF221F17),
                error = Color(0xFFCF6679),
            )
            MADINAH_GREEN -> lightColorScheme(
                primary = Color(0xFF2E6B4F),
                onPrimary = Color(0xFFFFFFFF),
                secondary = Color(0xFF7A9A85),
                onSecondary = Color(0xFFFFFFFF),
                background = Color(0xFFF7F3E9),
                onBackground = Color(0xFF1E241F),
                surface = Color(0xFFEFEAD9),
                onSurface = Color(0xFF1E241F),
                surfaceVariant = Color(0xFFDDE6DA),
                error = Color(0xFFB3261E),
            )
            PLATINUM_WHITE -> lightColorScheme(
                primary = Color(0xFF4A4A4F),
                onPrimary = Color(0xFFFFFFFF),
                secondary = Color(0xFF8A8A90),
                onSecondary = Color(0xFFFFFFFF),
                background = Color(0xFFFAFAFA),
                onBackground = Color(0xFF17171A),
                surface = Color(0xFFF1F1F3),
                onSurface = Color(0xFF17171A),
                surfaceVariant = Color(0xFFE3E3E7),
                error = Color(0xFFB3261E),
            )
            EXECUTIVE_DARK -> darkColorScheme(
                primary = Color(0xFF8C93A6),
                onPrimary = Color(0xFF11141C),
                secondary = Color(0xFF5C6478),
                onSecondary = Color(0xFF11141C),
                background = Color(0xFF0E0F13),
                onBackground = Color(0xFFE3E4E8),
                surface = Color(0xFF15171D),
                onSurface = Color(0xFFE3E4E8),
                surfaceVariant = Color(0xFF23252D),
                error = Color(0xFFCF6679),
            )
        }
}
