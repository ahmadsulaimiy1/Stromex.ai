package com.sajjil.app.speech

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import com.sajjil.core.audio.BitDepth
import com.sajjil.core.audio.WavStreamWriter
import com.sajjil.core.speech.TranscriptLanguage
import com.sajjil.core.speech.TranscriptSegment
import java.io.File
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow

/**
 * SAJJIL's Priority-1 recognizer: whatever offline-capable speech
 * recognition service Android itself has installed (Google's on-device
 * recognizer on most devices, or an OEM equivalent), reached through the
 * public `android.speech.SpeechRecognizer` API. This is genuinely
 * offline when [RecognizerIntent.EXTRA_PREFER_OFFLINE] is honored by the
 * installed recognizer and the on-device language model is downloaded —
 * SAJJIL asks for offline, it cannot force it, since Android does not
 * expose a way to verify a specific recognition happened without network.
 *
 * `SpeechRecognizer` must be created and driven on the main thread — this
 * class assumes it is called from one.
 *
 * Optionally captures the raw audio SpeechRecognizer is listening to via
 * [RecognitionListener.onBufferReceived], so a session can be transcribed
 * and saved as a take in one pass without a second, conflicting
 * microphone session. This buffer format is a genuine Android API but its
 * exact PCM parameters are **not publicly documented as an API contract**
 * — in practice it is 16-bit mono PCM at 16kHz on the AOSP/Google
 * recognizer, but that is observed behavior, not a guarantee, and may
 * differ on other OEM recognizer implementations. Treat captured audio as
 * a lower-fidelity reference take, not a replacement for SAJJIL's main
 * studio-quality [com.sajjil.app.audio.AudioRecordEngine] pipeline.
 */
class AndroidNativeSpeechRecognizer(
    private val context: Context,
    private val language: TranscriptLanguage,
    private val wavCaptureFile: File? = null,
    private val assumedCaptureSampleRate: Int = 16_000,
) : SpeechRecognitionEngine {

    override var isListening: Boolean = false
        private set

    private var recognizer: SpeechRecognizer? = null

    override fun start(): Flow<RecognitionEvent> = callbackFlow {
        if (!SpeechRecognizer.isRecognitionAvailable(context)) {
            trySend(RecognitionEvent.Error("No speech recognition service is available on this device.", recoverable = false))
            close()
            return@callbackFlow
        }

        val sessionStartMs = System.currentTimeMillis()
        var wavWriter: WavStreamWriter? = null

        val listener = object : RecognitionListener {
            override fun onReadyForSpeech(params: Bundle?) {
                trySend(RecognitionEvent.ReadyForSpeech)
            }

            override fun onBeginningOfSpeech() = Unit
            override fun onRmsChanged(rmsdB: Float) = Unit

            override fun onBufferReceived(buffer: ByteArray?) {
                val file = wavCaptureFile ?: return
                val bytes = buffer ?: return
                if (bytes.isEmpty()) return
                val writer = wavWriter ?: WavStreamWriter(file, assumedCaptureSampleRate, channels = 1, bitDepth = BitDepth.PCM_16)
                    .also { wavWriter = it }
                writer.write(pcm16BytesToFloatSamples(bytes))
            }

            override fun onEndOfSpeech() = Unit

            override fun onError(error: Int) {
                val message = describeError(error)
                val recoverable = error == SpeechRecognizer.ERROR_NO_MATCH || error == SpeechRecognizer.ERROR_SPEECH_TIMEOUT
                trySend(RecognitionEvent.Error(message, recoverable))
                if (!recoverable) {
                    wavWriter?.close()
                    close()
                }
            }

            override fun onResults(results: Bundle?) {
                val text = results
                    ?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                    ?.firstOrNull()
                val confidence = results
                    ?.getFloatArray(SpeechRecognizer.CONFIDENCE_SCORES)
                    ?.firstOrNull()
                if (!text.isNullOrBlank()) {
                    val nowMs = System.currentTimeMillis()
                    trySend(
                        RecognitionEvent.FinalSegment(
                            TranscriptSegment(
                                startMs = 0L,
                                endMs = nowMs - sessionStartMs,
                                text = text,
                                confidence = confidence,
                            ),
                        ),
                    )
                }
            }

            override fun onPartialResults(partialResults: Bundle?) {
                val text = partialResults
                    ?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                    ?.firstOrNull()
                if (!text.isNullOrBlank()) trySend(RecognitionEvent.PartialResult(text))
            }

            override fun onEvent(eventType: Int, params: Bundle?) = Unit
        }

        val sr = SpeechRecognizer.createSpeechRecognizer(context).also { it.setRecognitionListener(listener) }
        recognizer = sr
        isListening = true

        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, language.bcp47)
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
            putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE, true)
            putExtra(RecognizerIntent.EXTRA_CALLING_PACKAGE, context.packageName)
        }
        sr.startListening(intent)

        awaitClose {
            wavWriter?.close()
            sr.destroy()
            recognizer = null
            isListening = false
        }
    }

    override fun stop() {
        recognizer?.stopListening()
        isListening = false
    }

    private fun pcm16BytesToFloatSamples(bytes: ByteArray): FloatArray {
        val sampleCount = bytes.size / 2
        val samples = FloatArray(sampleCount)
        for (i in 0 until sampleCount) {
            val low = bytes[i * 2].toInt() and 0xFF
            val high = bytes[i * 2 + 1].toInt()
            val sample = (high shl 8) or low
            samples[i] = sample / 32768.0f
        }
        return samples
    }

    private fun describeError(error: Int): String = when (error) {
        SpeechRecognizer.ERROR_AUDIO -> "Audio recording error."
        SpeechRecognizer.ERROR_CLIENT -> "Speech recognition client error."
        SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> "Microphone permission is required."
        SpeechRecognizer.ERROR_NETWORK -> "Network error during recognition."
        SpeechRecognizer.ERROR_NETWORK_TIMEOUT -> "Network timed out during recognition."
        SpeechRecognizer.ERROR_NO_MATCH -> "No speech was recognized."
        SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> "The recognizer is busy."
        SpeechRecognizer.ERROR_SERVER -> "Recognition server error."
        SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> "No speech input detected."
        SpeechRecognizer.ERROR_LANGUAGE_NOT_SUPPORTED -> "${language.displayName} is not supported by the installed recognizer."
        SpeechRecognizer.ERROR_LANGUAGE_UNAVAILABLE -> "${language.displayName} language pack is not installed."
        else -> "Unknown recognition error ($error)."
    }
}
