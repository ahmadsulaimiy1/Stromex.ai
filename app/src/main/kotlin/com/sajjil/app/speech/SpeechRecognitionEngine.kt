package com.sajjil.app.speech

import com.sajjil.core.speech.TranscriptSegment
import kotlinx.coroutines.flow.Flow

/**
 * The narrow contract every SAJJIL recognizer implements — live-mic
 * speech-to-text with timed segments. Everything above this interface
 * (Voice Studio's ViewModel, transcript storage, search) is written
 * against it, not against `android.speech.SpeechRecognizer` directly, so
 * a future recognizer (a bundled offline model, a cloud fallback the user
 * opts into) can be swapped in without touching the rest of the app.
 *
 * This is a LIVE recognition contract, not a "transcribe this file"
 * contract: Android's `SpeechRecognizer` has no public API to feed it a
 * pre-recorded WAV, so recognizers are expected to own the microphone for
 * the duration of a session and emit segments as speech is recognized.
 */
interface SpeechRecognitionEngine {

    /** True once a session is actively listening. */
    val isListening: Boolean

    /**
     * Starts a listening session. Emits [RecognitionEvent]s as they occur;
     * the flow completes when the session ends (explicit [stop] or the
     * recognizer itself finalizing after a period of silence).
     */
    fun start(): Flow<RecognitionEvent>

    /** Ends the current session, if any. Safe to call when not listening. */
    fun stop()
}

sealed interface RecognitionEvent {
    data object ReadyForSpeech : RecognitionEvent
    data class PartialResult(val text: String) : RecognitionEvent
    data class FinalSegment(val segment: TranscriptSegment) : RecognitionEvent
    data class Error(val message: String, val recoverable: Boolean) : RecognitionEvent
    data object EndOfSession : RecognitionEvent
}
