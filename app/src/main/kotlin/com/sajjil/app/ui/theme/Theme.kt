package com.sajjil.app.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.runtime.Composable
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

/** Tighter tracking on display sizes, generous tracking on labels — an editorial/executive-dashboard rhythm. */
val SajjilTypography = Typography(
    headlineLarge = TextStyle(fontFamily = SajjilFonts.executiveSans, fontWeight = FontWeight.SemiBold, fontSize = 30.sp, letterSpacing = (-0.3).sp),
    headlineMedium = TextStyle(fontFamily = SajjilFonts.executiveSans, fontWeight = FontWeight.SemiBold, fontSize = 24.sp, letterSpacing = (-0.2).sp),
    titleLarge = TextStyle(fontFamily = SajjilFonts.executiveSans, fontWeight = FontWeight.Medium, fontSize = 20.sp, letterSpacing = (-0.1).sp),
    titleMedium = TextStyle(fontFamily = SajjilFonts.executiveSans, fontWeight = FontWeight.Medium, fontSize = 16.sp, letterSpacing = 0.1.sp),
    bodyLarge = TextStyle(fontFamily = SajjilFonts.executiveSans, fontWeight = FontWeight.Normal, fontSize = 16.sp, letterSpacing = 0.15.sp),
    bodyMedium = TextStyle(fontFamily = SajjilFonts.executiveSans, fontWeight = FontWeight.Normal, fontSize = 14.sp, letterSpacing = 0.15.sp),
    labelLarge = TextStyle(fontFamily = SajjilFonts.executiveSans, fontWeight = FontWeight.Medium, fontSize = 14.sp, letterSpacing = 0.4.sp),
    labelMedium = TextStyle(fontFamily = SajjilFonts.executiveSans, fontWeight = FontWeight.Medium, fontSize = 12.sp, letterSpacing = 0.5.sp),
)

/** Applies the selected [SajjilTheme]; defaults to Royal Navy Deep when none is persisted yet. */
@Composable
fun SajjilAppTheme(
    theme: SajjilTheme = if (isSystemInDarkTheme()) SajjilTheme.ROYAL_NAVY_DEEP else SajjilTheme.PLATINUM_WHITE,
    content: @Composable () -> Unit,
) {
    MaterialTheme(
        colorScheme = theme.colorScheme,
        typography = SajjilTypography,
        content = content,
    )
}
