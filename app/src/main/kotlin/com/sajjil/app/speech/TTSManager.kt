package com.sajjil.app.speech

import android.content.Context
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import com.sajjil.core.speech.TranscriptLanguage
import java.util.Locale
import kotlin.coroutines.resume
import kotlinx.coroutines.suspendCancellableCoroutine

/**
 * Offline-first playback of transcript text via Android's `TextToSpeech`
 * engine — the "read the transcript back to me" half of Voice Studio.
 * Whether a given utterance actually plays offline depends on whether an
 * offline voice is installed for that language; [hasOfflineVoice] is how
 * callers check before promising the user offline playback.
 */
class TTSManager(private val context: Context) {
    private var engine: TextToSpeech? = null
    private var ready = false

    /** Suspends until the engine reports init success/failure. Call once before [speak]. */
    suspend fun initialize(): Boolean = suspendCancellableCoroutine { cont ->
        var instance: TextToSpeech? = null
        instance = TextToSpeech(context) { status ->
            ready = status == TextToSpeech.SUCCESS
            engine = instance
            if (cont.isActive) cont.resume(ready)
        }
    }

    fun setProgressListener(listener: UtteranceProgressListener) {
        engine?.setOnUtteranceProgressListener(listener)
    }

    /** Returns false without speaking if the engine isn't ready or the language isn't supported. */
    fun speak(text: String, language: TranscriptLanguage, rate: Float = 1.0f, pitch: Float = 1.0f, utteranceId: String = "sajjil-tts"): Boolean {
        val tts = engine ?: return false
        if (!ready || text.isBlank()) return false

        val locale = Locale.forLanguageTag(language.bcp47)
        val languageResult = tts.setLanguage(locale)
        if (languageResult == TextToSpeech.LANG_MISSING_DATA || languageResult == TextToSpeech.LANG_NOT_SUPPORTED) return false

        tts.setSpeechRate(rate)
        tts.setPitch(pitch)
        return tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, utteranceId) == TextToSpeech.SUCCESS
    }

    fun stop() {
        engine?.stop()
    }

    fun shutdown() {
        engine?.shutdown()
        engine = null
        ready = false
    }

    /** True only when a voice for this language is installed AND does not require a network connection. */
    fun hasOfflineVoice(language: TranscriptLanguage): Boolean {
        val tts = engine ?: return false
        val targetLanguage = Locale.forLanguageTag(language.bcp47).language
        return tts.voices?.any { voice -> voice.locale.language == targetLanguage && !voice.isNetworkConnectionRequired } ?: false
    }

    fun voiceCatalog(): List<VoiceInfo> = VoiceCatalog.from(engine?.voices)
}
