package com.sajjil.core.speechpack

import com.sajjil.core.speech.TranscriptLanguage
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull
import kotlin.test.assertTrue

class SpeechPackStateMachineTest {

    @Test
    fun `catalog lists exactly the four named packs, one per language-kind combination`() {
        assertEquals(4, SpeechPackCatalog.packs.size)
        val combinations = SpeechPackCatalog.packs.map { it.language to it.kind }.toSet()
        assertEquals(4, combinations.size)
        assertTrue(combinations.containsAll(
            listOf(
                TranscriptLanguage.ARABIC to SpeechPackKind.RECOGNITION,
                TranscriptLanguage.ENGLISH to SpeechPackKind.RECOGNITION,
                TranscriptLanguage.ARABIC to SpeechPackKind.VOICE,
                TranscriptLanguage.ENGLISH to SpeechPackKind.VOICE,
            ),
        ))
    }

    @Test
    fun `initial status is not installed`() {
        assertEquals(SpeechPackState.NOT_INSTALLED, SpeechPackStatus.initial.state)
    }

    @Test
    fun `download requested moves not-installed to downloading`() {
        val result = SpeechPackStateMachine.reduce(SpeechPackStatus.initial, SpeechPackEvent.DownloadRequested)
        assertEquals(SpeechPackState.DOWNLOADING, result.state)
        assertEquals(0.0, result.progressFraction)
    }

    @Test
    fun `progress updates while downloading are clamped to 0 to 1`() {
        val downloading = SpeechPackStatus(state = SpeechPackState.DOWNLOADING)

        val overshoot = SpeechPackStateMachine.reduce(downloading, SpeechPackEvent.ProgressUpdated(1.5))
        assertEquals(1.0, overshoot.progressFraction)

        val undershoot = SpeechPackStateMachine.reduce(downloading, SpeechPackEvent.ProgressUpdated(-0.2))
        assertEquals(0.0, undershoot.progressFraction)

        val mid = SpeechPackStateMachine.reduce(downloading, SpeechPackEvent.ProgressUpdated(0.4))
        assertEquals(0.4, mid.progressFraction)
    }

    @Test
    fun `download completed installs and records the version`() {
        val downloading = SpeechPackStatus(state = SpeechPackState.DOWNLOADING, progressFraction = 0.9)
        val result = SpeechPackStateMachine.reduce(downloading, SpeechPackEvent.DownloadCompleted("1.0.0"))

        assertEquals(SpeechPackState.INSTALLED, result.state)
        assertEquals("1.0.0", result.installedVersion)
        assertEquals(1.0, result.progressFraction)
    }

    @Test
    fun `download failed records the reason and can be retried`() {
        val downloading = SpeechPackStatus(state = SpeechPackState.DOWNLOADING, progressFraction = 0.5)
        val failed = SpeechPackStateMachine.reduce(downloading, SpeechPackEvent.DownloadFailed("network error"))

        assertEquals(SpeechPackState.FAILED, failed.state)
        assertEquals("network error", failed.errorMessage)

        val retried = SpeechPackStateMachine.reduce(failed, SpeechPackEvent.DownloadRequested)
        assertEquals(SpeechPackState.DOWNLOADING, retried.state)
        assertNull(retried.errorMessage)
    }

    @Test
    fun `new version detected moves installed to update available, which can re-download`() {
        val installed = SpeechPackStatus(state = SpeechPackState.INSTALLED, installedVersion = "1.0.0")
        val updateAvailable = SpeechPackStateMachine.reduce(installed, SpeechPackEvent.NewVersionDetected)
        assertEquals(SpeechPackState.UPDATE_AVAILABLE, updateAvailable.state)

        val redownloading = SpeechPackStateMachine.reduce(updateAvailable, SpeechPackEvent.DownloadRequested)
        assertEquals(SpeechPackState.DOWNLOADING, redownloading.state)
    }

    @Test
    fun `uninstalled resets installed or update-available packs to not installed`() {
        val installed = SpeechPackStatus(state = SpeechPackState.INSTALLED, installedVersion = "1.0.0")
        val afterUninstall = SpeechPackStateMachine.reduce(installed, SpeechPackEvent.Uninstalled)
        assertEquals(SpeechPackState.NOT_INSTALLED, afterUninstall.state)
        assertNull(afterUninstall.installedVersion)
    }

    @Test
    fun `marked unavailable is reachable from not-installed, installed, and failed`() {
        val fromNotInstalled = SpeechPackStateMachine.reduce(SpeechPackStatus.initial, SpeechPackEvent.MarkedUnavailable)
        val fromInstalled = SpeechPackStateMachine.reduce(
            SpeechPackStatus(state = SpeechPackState.INSTALLED), SpeechPackEvent.MarkedUnavailable,
        )
        val fromFailed = SpeechPackStateMachine.reduce(
            SpeechPackStatus(state = SpeechPackState.FAILED), SpeechPackEvent.MarkedUnavailable,
        )

        for (result in listOf(fromNotInstalled, fromInstalled, fromFailed)) {
            assertEquals(SpeechPackState.UNAVAILABLE, result.state)
            assertTrue(!result.errorMessage.isNullOrBlank())
        }
    }

    @Test
    fun `unavailable is terminal and ignores every event`() {
        val unavailable = SpeechPackStatus(state = SpeechPackState.UNAVAILABLE, errorMessage = "No verified offline model is available.")

        val events = listOf(
            SpeechPackEvent.DownloadRequested,
            SpeechPackEvent.ProgressUpdated(0.5),
            SpeechPackEvent.DownloadCompleted("1.0.0"),
            SpeechPackEvent.DownloadFailed("x"),
            SpeechPackEvent.NewVersionDetected,
            SpeechPackEvent.Uninstalled,
            SpeechPackEvent.MarkedUnavailable,
        )

        for (event in events) {
            assertEquals(unavailable, SpeechPackStateMachine.reduce(unavailable, event))
        }
    }

    @Test
    fun `an event invalid for the current state is a no-op`() {
        // Uninstalled has no meaning while nothing is installed yet.
        val result = SpeechPackStateMachine.reduce(SpeechPackStatus.initial, SpeechPackEvent.Uninstalled)
        assertEquals(SpeechPackStatus.initial, result)
    }
}
