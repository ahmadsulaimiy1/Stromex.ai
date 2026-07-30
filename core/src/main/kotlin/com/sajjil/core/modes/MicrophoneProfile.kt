package com.sajjil.core.modes

/**
 * SAJJIL microphone calibration. These are *generic character* correction
 * curves (a small parametric EQ nudge), not measured frequency-response
 * data for specific hardware — SAJJIL has no lab measurements of RØDE,
 * Shure, Audio-Technica, DJI, Hollyland, BOYA or Maono units to model
 * precisely, and shipping fabricated "exact" correction curves for named
 * products would be actively misleading. Each profile instead targets a
 * common microphone *character* and lists example products that typically
 * fit it, so a user can make an informed choice; true per-model profiling
 * (an "AI Microphone Calibration" that measures a specific unit) is a
 * roadmap item that needs real reference-microphone measurement to do
 * honestly.
 */
enum class MicrophoneProfile(
    val displayName: String,
    val description: String,
    val exampleHardware: List<String>,
    /** (frequencyHz, Q, gainDb) parametric correction bands. */
    val correctionBands: List<Triple<Double, Double, Double>>,
) {
    PHONE_BUILT_IN(
        "Phone Built-in",
        "Typical phone capsule: boxy low-mids, a presence dip, thin extreme top end.",
        listOf("Any built-in smartphone microphone"),
        listOf(Triple(300.0, 1.2, -2.0), Triple(3000.0, 1.0, 2.0), Triple(10000.0, 0.8, 2.0)),
    ),
    USB_CONDENSER_BRIGHT(
        "USB Condenser — Bright",
        "Present, airy top end typical of budget-to-mid USB condensers.",
        listOf("RØDE NT-USB / NT-USB Mini", "Audio-Technica AT2020USB+", "Maono PD200X"),
        listOf(Triple(200.0, 1.0, 1.0), Triple(8000.0, 1.0, -1.5)),
    ),
    USB_DYNAMIC_WARM(
        "USB Dynamic — Warm",
        "Broadcast-style dynamic capsules: warm low end, controlled sibilance, needs gain.",
        listOf("Shure MV7 / MV7+", "RØDE PodMic USB"),
        listOf(Triple(120.0, 1.0, 1.5), Triple(5000.0, 1.0, 1.0)),
    ),
    WIRELESS_LAVALIER(
        "Wireless Lavalier",
        "Clip-on lav capsules: proximity-boosted bass, compressed dynamics from the transmitter.",
        listOf("DJI Mic / Mic 2", "Hollyland Lark M2", "BOYA BY-M1"),
        listOf(Triple(150.0, 1.0, -2.0), Triple(4000.0, 1.0, 1.0)),
    ),
    FLAT_REFERENCE(
        "Flat / Reference",
        "No correction — use for a measurement mic or when you'd rather shape tone manually in Master.",
        listOf("Measurement microphones", "Studio condensers with a known flat response"),
        emptyList(),
    );

    companion object {
        /** A conservative default for an unrecognized/unspecified input device. */
        val default = FLAT_REFERENCE
    }
}
