package com.sajjil.app.speech

import com.sajjil.core.speech.TranscriptLanguage

/**
 * What SAJJIL actually found on this device — never a claim of what
 * *should* be there. Every screen that shows speech/TTS status renders
 * this report directly rather than assuming a capability exists.
 */
enum class SpeechCapabilityStatus {
    /** Fully usable right now, offline, no further setup needed. */
    AVAILABLE,
    /** The recognizer/TTS engine is installed, but the specific language/voice isn't. */
    LANGUAGE_PACK_MISSING,
    /** No recognition service or TTS engine at all is present on this device. */
    UNSUPPORTED,
}

data class CapabilityDetail(
    val status: SpeechCapabilityStatus,
    val message: String,
    /** Package name of the engine SAJJIL would hand this request to, when known. */
    val engineId: String? = null,
)

data class LanguageSpeechCapability(
    val language: TranscriptLanguage,
    val recognition: CapabilityDetail,
    val textToSpeech: CapabilityDetail,
)

data class SpeechCapabilityReport(
    val languages: List<LanguageSpeechCapability>,
    /** True when at least one speech-recognition service is registered on the device at all. */
    val anyRecognitionServiceInstalled: Boolean,
    /** True when at least one text-to-speech engine is registered on the device at all. */
    val anyTtsEngineInstalled: Boolean,
) {
    fun forLanguage(language: TranscriptLanguage): LanguageSpeechCapability? =
        languages.firstOrNull { it.language == language }

    val allRecognitionAvailable: Boolean get() = languages.all { it.recognition.status == SpeechCapabilityStatus.AVAILABLE }
    val allTtsAvailable: Boolean get() = languages.all { it.textToSpeech.status == SpeechCapabilityStatus.AVAILABLE }
}
