package com.sajjil.app.speech

import android.content.Context
import com.sajjil.core.speech.TranscriptLanguage
import java.io.File

/**
 * Fallback hierarchy every language-specific recognizer follows:
 *
 * 1. **Installed Android offline speech service** — implemented, via
 *    [AndroidNativeSpeechRecognizer].
 * 2. **A SAJJIL-branded downloadable Offline Speech Pack** — architecture
 *    reserved for this (see `docs/SPEECH_INTELLIGENCE.md`), not
 *    implemented: there is no way in this environment to source, bundle,
 *    or verify a real ASR model, and shipping an unverified one would
 *    risk silently mistranscribing Qur'anic recitation. A future
 *    implementation slots in here as another [SpeechRecognitionEngine].
 * 3. **Optional cloud processing** — only if a user explicitly opts in.
 *    Not implemented; SAJJIL never calls out to a network recognition
 *    service today, on-device or otherwise.
 *
 * [OfflineArabicRecognizer] and [OfflineEnglishRecognizer] exist as named,
 * stable extension points so a Priority-2 engine can be swapped in later
 * without changing anything that calls them — today they both simply
 * delegate to Priority 1.
 */
class OfflineArabicRecognizer(
    context: Context,
    wavCaptureFile: File? = null,
) : SpeechRecognitionEngine by AndroidNativeSpeechRecognizer(context, TranscriptLanguage.ARABIC, wavCaptureFile)

class OfflineEnglishRecognizer(
    context: Context,
    wavCaptureFile: File? = null,
) : SpeechRecognitionEngine by AndroidNativeSpeechRecognizer(context, TranscriptLanguage.ENGLISH, wavCaptureFile)
