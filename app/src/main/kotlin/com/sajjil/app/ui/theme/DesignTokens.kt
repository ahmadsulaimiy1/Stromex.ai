package com.sajjil.app.ui.theme

import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp

/**
 * SAJJIL's formal design system: named tokens rather than inline magic
 * numbers, so "Saudi Vision 2030 / NEOM / Apple Pro Apps / Dolby software"
 * quality is a consistent, referenceable set of decisions, not a vibe.
 *
 * Font honesty note: [SajjilFonts.executiveSans] and [SajjilFonts.arabicCompanion]
 * currently resolve to the platform default. Wiring real typefaces needs
 * either (a) licensed .ttf/.otf files bundled under `res/font/`, or (b) the
 * Android Downloadable Fonts API with Google's official
 * `com_google_android_gms_fonts_certs` certificate array from
 * https://developer.android.com/develop/ui/views/text-and-emoji/downloadable-fonts —
 * a large exact certificate blob that must come from that source, not be
 * reproduced from memory. Neither is available in this sandbox; the token
 * *names* and *roles* below are real and ready for either path to slot into.
 */
object SajjilColorTokens {
    val royalNavy = Color(0xFF082A66)
    val premiumGold = Color(0xFFD4AF37)
    val platinumWhite = Color(0xFFF5F5F7)
    val obsidianBlack = Color(0xFF0A0A0B)
}

object SajjilSpacing {
    val xs = 4.dp
    val sm = 8.dp
    val md = 16.dp
    val lg = 24.dp
    val xl = 32.dp
    val xxl = 48.dp
}

object SajjilRadius {
    val small = 8.dp
    val medium = 12.dp
    val large = 16.dp
    val executive = 20.dp // GlassCard and other Executive Dashboard surfaces
}

object SajjilElevation {
    val flat = 0.dp
    val card = 2.dp
    val raised = 6.dp
}

object SajjilFonts {
    /** Executive modern sans-serif role — headlines, dashboards, UI chrome. */
    val executiveSans: FontFamily = FontFamily.Default

    /** Premium Arabic companion role — Surah names, recitation-facing text. */
    val arabicCompanion: FontFamily = FontFamily.Default
}
