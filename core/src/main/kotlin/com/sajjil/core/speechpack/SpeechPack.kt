package com.sajjil.core.speechpack

import com.sajjil.core.speech.TranscriptLanguage

enum class SpeechPackKind { RECOGNITION, VOICE }

data class SpeechPackDescriptor(
    val id: String,
    val language: TranscriptLanguage,
    val kind: SpeechPackKind,
    val displayName: String,
)

/** The four packs the "Download Once. Use Forever." directive named explicitly. */
object SpeechPackCatalog {
    val packs: List<SpeechPackDescriptor> = listOf(
        SpeechPackDescriptor("ar-recognition", TranscriptLanguage.ARABIC, SpeechPackKind.RECOGNITION, "Arabic Recognition Pack"),
        SpeechPackDescriptor("en-recognition", TranscriptLanguage.ENGLISH, SpeechPackKind.RECOGNITION, "English Recognition Pack"),
        SpeechPackDescriptor("ar-voice", TranscriptLanguage.ARABIC, SpeechPackKind.VOICE, "Arabic Voice Pack"),
        SpeechPackDescriptor("en-voice", TranscriptLanguage.ENGLISH, SpeechPackKind.VOICE, "English Voice Pack"),
    )
}

enum class SpeechPackState { NOT_INSTALLED, DOWNLOADING, INSTALLED, UPDATE_AVAILABLE, FAILED, UNAVAILABLE }

sealed interface SpeechPackEvent {
    data object DownloadRequested : SpeechPackEvent
    data class ProgressUpdated(val fraction: Double) : SpeechPackEvent
    data class DownloadCompleted(val version: String) : SpeechPackEvent
    data class DownloadFailed(val reason: String) : SpeechPackEvent
    data object NewVersionDetected : SpeechPackEvent
    data object Uninstalled : SpeechPackEvent
    data object MarkedUnavailable : SpeechPackEvent
}

data class SpeechPackStatus(
    val state: SpeechPackState,
    val progressFraction: Double = 0.0,
    val installedVersion: String? = null,
    val errorMessage: String? = null,
) {
    companion object {
        val initial = SpeechPackStatus(state = SpeechPackState.NOT_INSTALLED)
    }
}

/**
 * Pure transition logic for the speech-pack "Download Once. Use Forever."
 * lifecycle. This models the lifecycle for real and is fully testable —
 * what it deliberately does **not** do is talk to a network or bundle a
 * model: there is nothing in this sandbox to source, download, or verify
 * a real offline ASR/TTS model from (same reasoning as
 * `docs/SPEECH_INTELLIGENCE.md`), so every pack this build ships is
 * driven straight to [SpeechPackState.UNAVAILABLE] rather than pretending
 * a download would work. A future build that adds a real model source
 * only needs to start dispatching real
 * `DownloadRequested`/`ProgressUpdated`/`DownloadCompleted` events into
 * this same reducer — nothing here would need to change.
 *
 * Unhandled events for the current state are a no-op (the status is
 * returned unchanged) rather than an error — safe for a UI to dispatch
 * events without first checking whether they're currently valid.
 */
object SpeechPackStateMachine {

    fun reduce(current: SpeechPackStatus, event: SpeechPackEvent): SpeechPackStatus = when (current.state) {
        SpeechPackState.NOT_INSTALLED -> when (event) {
            SpeechPackEvent.DownloadRequested -> startDownload(current)
            SpeechPackEvent.MarkedUnavailable -> unavailable()
            else -> current
        }
        SpeechPackState.DOWNLOADING -> when (event) {
            is SpeechPackEvent.ProgressUpdated -> current.copy(progressFraction = event.fraction.coerceIn(0.0, 1.0))
            is SpeechPackEvent.DownloadCompleted -> current.copy(
                state = SpeechPackState.INSTALLED,
                progressFraction = 1.0,
                installedVersion = event.version,
                errorMessage = null,
            )
            is SpeechPackEvent.DownloadFailed -> current.copy(state = SpeechPackState.FAILED, errorMessage = event.reason)
            else -> current
        }
        SpeechPackState.INSTALLED -> when (event) {
            SpeechPackEvent.NewVersionDetected -> current.copy(state = SpeechPackState.UPDATE_AVAILABLE)
            SpeechPackEvent.Uninstalled -> uninstalled()
            SpeechPackEvent.MarkedUnavailable -> unavailable()
            else -> current
        }
        SpeechPackState.UPDATE_AVAILABLE -> when (event) {
            SpeechPackEvent.DownloadRequested -> startDownload(current)
            SpeechPackEvent.Uninstalled -> uninstalled()
            else -> current
        }
        SpeechPackState.FAILED -> when (event) {
            SpeechPackEvent.DownloadRequested -> startDownload(current)
            SpeechPackEvent.MarkedUnavailable -> unavailable()
            else -> current
        }
        // Terminal in this build: nothing can install what has no verified source to download from.
        SpeechPackState.UNAVAILABLE -> current
    }

    private fun startDownload(current: SpeechPackStatus) =
        current.copy(state = SpeechPackState.DOWNLOADING, progressFraction = 0.0, errorMessage = null)

    private fun uninstalled() =
        SpeechPackStatus(state = SpeechPackState.NOT_INSTALLED)

    private fun unavailable() = SpeechPackStatus(
        state = SpeechPackState.UNAVAILABLE,
        errorMessage = "No verified offline model is available to install in this build.",
    )
}
