package com.sajjil.app.speech

import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.speech.RecognitionService
import android.speech.SpeechRecognizer
import com.sajjil.core.speech.TranscriptLanguage

/**
 * Detects what speech capabilities this specific device actually has —
 * never assumed, always queried — and turns that into the
 * [SpeechCapabilityReport] every "Speech & Language Packs" and Voice
 * Studio screen renders from. This is the one place capability-detection
 * logic lives, named per the speech-architecture requirement so it's the
 * single spot to change if detection needs to improve.
 */
class AndroidSpeechBridge(private val context: Context) {

    fun anyRecognitionServiceInstalled(): Boolean = SpeechRecognizer.isRecognitionAvailable(context)

    /** Package names of every app registering an `android.speech.RecognitionService`. Requires `<queries>` visibility on API 30+. */
    fun installedRecognitionServicePackages(): List<String> {
        val intent = Intent(RecognitionService.SERVICE_INTERFACE)
        return context.packageManager
            .queryIntentServices(intent, PackageManager.MATCH_DEFAULT_ONLY)
            .mapNotNull { it.serviceInfo?.packageName }
            .distinct()
    }

    /** Spins up a throwaway TextToSpeech engine long enough to inspect its installed voices, then shuts it down. */
    suspend fun detect(): SpeechCapabilityReport {
        val recognitionInstalled = anyRecognitionServiceInstalled()
        val ttsManager = TTSManager(context)
        val ttsReady = ttsManager.initialize()

        val languages = TranscriptLanguage.entries.map { language ->
            LanguageSpeechCapability(
                language = language,
                recognition = recognitionCapability(language, recognitionInstalled),
                textToSpeech = ttsCapability(language, ttsManager, ttsReady),
            )
        }

        ttsManager.shutdown()

        return SpeechCapabilityReport(
            languages = languages,
            anyRecognitionServiceInstalled = recognitionInstalled,
            anyTtsEngineInstalled = ttsReady,
        )
    }

    private fun recognitionCapability(language: TranscriptLanguage, recognitionInstalled: Boolean): CapabilityDetail {
        if (!recognitionInstalled) {
            return CapabilityDetail(SpeechCapabilityStatus.UNSUPPORTED, "No speech recognition service is installed on this device.")
        }
        // Android's SpeechRecognizer has no public API to ask "is <language> available offline"
        // ahead of a session — the only way to find out is to start listening and see whether
        // ERROR_LANGUAGE_UNAVAILABLE comes back. Report installed-but-unverified rather than
        // claiming a certainty this API cannot give us.
        return CapabilityDetail(
            SpeechCapabilityStatus.AVAILABLE,
            "A speech recognition service is installed. ${language.displayName} is confirmed the first time you use it.",
        )
    }

    private fun ttsCapability(language: TranscriptLanguage, ttsManager: TTSManager, ttsReady: Boolean): CapabilityDetail {
        if (!ttsReady) {
            return CapabilityDetail(SpeechCapabilityStatus.UNSUPPORTED, "No text-to-speech engine is installed on this device.")
        }
        return if (ttsManager.hasOfflineVoice(language)) {
            CapabilityDetail(SpeechCapabilityStatus.AVAILABLE, "An offline ${language.displayName} voice is installed.")
        } else {
            CapabilityDetail(
                SpeechCapabilityStatus.LANGUAGE_PACK_MISSING,
                "${language.displayName} voice is missing or requires a network connection. Install an offline voice pack in system settings.",
            )
        }
    }
}
