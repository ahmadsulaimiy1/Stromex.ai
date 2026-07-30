package com.sajjil.app.speech

import android.speech.tts.Voice
import com.sajjil.core.speech.TranscriptLanguage

data class VoiceInfo(
    val name: String,
    val language: TranscriptLanguage?,
    val localeTag: String,
    val isOffline: Boolean,
    val qualityLabel: String,
)

/**
 * Turns the raw `Set<android.speech.tts.Voice>` a `TextToSpeech` engine
 * reports into the flat, sorted, human-readable list the Speech &
 * Language Packs settings screen shows — offline voices first, so a user
 * scanning for "will this work without internet" sees the answer
 * immediately rather than having to inspect each entry.
 */
object VoiceCatalog {

    fun from(voices: Set<Voice>?): List<VoiceInfo> {
        if (voices == null) return emptyList()
        return voices
            .map { voice ->
                VoiceInfo(
                    name = voice.name,
                    language = matchLanguage(voice.locale.language),
                    localeTag = voice.locale.toLanguageTag(),
                    isOffline = !voice.isNetworkConnectionRequired,
                    qualityLabel = qualityLabel(voice.quality),
                )
            }
            .sortedWith(compareByDescending<VoiceInfo> { it.isOffline }.thenBy { it.localeTag })
    }

    fun forLanguage(voices: Set<Voice>?, language: TranscriptLanguage): List<VoiceInfo> =
        from(voices).filter { it.language == language }

    private fun matchLanguage(isoLanguage: String): TranscriptLanguage? =
        TranscriptLanguage.entries.firstOrNull { it.bcp47.startsWith(isoLanguage) }

    private fun qualityLabel(quality: Int): String = when {
        quality >= Voice.QUALITY_VERY_HIGH -> "Very High"
        quality >= Voice.QUALITY_HIGH -> "High"
        quality >= Voice.QUALITY_NORMAL -> "Normal"
        else -> "Low"
    }
}
