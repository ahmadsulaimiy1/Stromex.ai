package ai.sajjil.app.ui.record

import ai.sajjil.app.Services
import ai.sajjil.app.audio.RecorderError
import ai.sajjil.app.audio.RecorderLevels
import ai.sajjil.app.audio.RecorderState
import ai.sajjil.app.audio.RecordingConfig
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

/** Everything the Record screen renders. */
data class RecordUiState(
    val recorderState: RecorderState = RecorderState.IDLE,
    val elapsedMillis: Long = 0,
    val levels: RecorderLevels = RecorderLevels(),
    val remainingSeconds: Long = 0,
    val sampleRate: Int = 48000,
    val channelCount: Int = 1,
    val error: RecorderError? = null,
    val justFinishedId: Long? = null,
) {
    val isRecording: Boolean get() = recorderState == RecorderState.RECORDING
    val isPaused: Boolean get() = recorderState == RecorderState.PAUSED
    val isActive: Boolean get() = recorderState != RecorderState.IDLE

    /**
     * A one-line quality read-out while recording, so problems are caught during the take rather
     * than discovered afterwards.
     */
    val liveQuality: LiveQuality
        get() = when {
            levels.isClipping -> LiveQuality.CLIPPING
            !isActive -> LiveQuality.IDLE
            levels.isTooQuiet -> LiveQuality.TOO_QUIET
            levels.peakDb > -6 -> LiveQuality.HOT
            levels.peakDb < -30 -> LiveQuality.LOW
            else -> LiveQuality.GOOD
        }
}

enum class LiveQuality(val label: String, val detail: String) {
    IDLE("Ready", "Level looks fine"),
    GOOD("Good level", "This will record cleanly"),
    LOW("A little quiet", "Move closer to the microphone"),
    HOT("Close to the limit", "Ease back slightly"),
    TOO_QUIET("Too quiet", "SAJJIL can barely hear anything"),
    CLIPPING("Too loud", "Move back — this is distorting"),
}

class RecordViewModel(private val services: Services) : ViewModel() {

    private val session = services.recordingSession

    private val justFinished = MutableStateFlow<Long?>(null)

    val waveform get() = session.recorder.waveform

    val state: StateFlow<RecordUiState> = combine(
        session.state,
        session.elapsedMillis,
        session.levels,
        session.remainingSeconds,
        combine(session.error, justFinished) { error, finished -> error to finished },
    ) { recorderState, elapsed, levels, remaining, (error, finished) ->
        RecordUiState(
            recorderState = recorderState,
            elapsedMillis = elapsed,
            levels = levels,
            remainingSeconds = remaining,
            sampleRate = session.recorder.config.sampleRate,
            channelCount = session.recorder.config.channelCount,
            error = error,
            justFinishedId = finished,
        )
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), RecordUiState())

    private val _outOfSpace = MutableStateFlow(false)
    val outOfSpace: StateFlow<Boolean> = _outOfSpace.asStateFlow()

    init {
        session.refreshRemainingSpace()
    }

    /**
     * One control for the whole transport.
     *
     * Idle starts, recording stops. That is the Two-Tap rule applied to the most common flow
     * there is: record, then stop, and the recording exists.
     */
    fun onRecordPressed() {
        viewModelScope.launch {
            when (session.state.value) {
                RecorderState.IDLE -> {
                    val settings = services.settings.settings.first()
                    val started = session.start(
                        RecordingConfig(
                            sampleRate = settings.sampleRate,
                            channelCount = settings.channelCount,
                            usePlatformProcessing = settings.usePlatformProcessing,
                        )
                    )
                    _outOfSpace.value = started == null
                }
                RecorderState.RECORDING, RecorderState.PAUSED -> {
                    justFinished.value = session.stop()
                }
            }
        }
    }

    fun onPauseResumePressed() {
        when (session.state.value) {
            RecorderState.RECORDING -> session.pause()
            RecorderState.PAUSED -> session.resume()
            RecorderState.IDLE -> Unit
        }
    }

    /** Continues an existing recording rather than creating a second file to join later. */
    fun continueRecording(recordingId: Long) {
        viewModelScope.launch { session.startAppending(recordingId) }
    }

    fun dismissFinished() {
        justFinished.value = null
        session.clearLastFinished()
    }

    fun dismissOutOfSpace() {
        _outOfSpace.value = false
    }

    fun refreshSpace() = session.refreshRemainingSpace()

    class Factory(private val services: Services) : ViewModelProvider.Factory {
        @Suppress("UNCHECKED_CAST")
        override fun <T : ViewModel> create(modelClass: Class<T>): T =
            RecordViewModel(services) as T
    }
}
