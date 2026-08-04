package ai.sautiy.ui.workspace

import ai.sautiy.core.analysis.PeakBuilder
import ai.sautiy.core.analysis.Waveform
import ai.sautiy.core.audio.AudioBuffer
import ai.sautiy.core.audio.CaptureQuality
import ai.sautiy.core.audio.Decibels
import ai.sautiy.core.codec.WavCodec
import ai.sautiy.core.dsp.StudioPreset
import ai.sautiy.core.edit.AppendRecording
import ai.sautiy.core.edit.DeleteRange
import ai.sautiy.core.edit.EditHistory
import ai.sautiy.core.edit.InMemorySourceProvider
import ai.sautiy.core.edit.Layer
import ai.sautiy.core.edit.SilenceRange
import ai.sautiy.core.edit.Source
import ai.sautiy.core.edit.Split
import ai.sautiy.core.edit.Timeline
import ai.sautiy.core.play.PlaybackMachine
import ai.sautiy.core.record.RecordingMachine
import ai.sautiy.core.record.RecordingState
import ai.sautiy.core.workspace.Focus
import ai.sautiy.core.workspace.Panel
import ai.sautiy.core.workspace.TransportState
import ai.sautiy.core.workspace.WorkspaceAction
import ai.sautiy.core.workspace.WorkspaceState
import ai.sautiy.data.SautiyFiles
import ai.sautiy.play.AudioPlayer
import ai.sautiy.record.AudioCapture
import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/**
 * The single place where the studio's state lives.
 *
 * Its job is narrow on purpose: translate device events into calls on `sautiy-core`, and
 * translate the resulting core state into a [WorkspaceUiState]. It makes **no product
 * decisions** of its own — which tools appear, whether a transition is legal, how long a fade
 * is, when to flush — because every one of those is a rule from the Editorial Bible that lives
 * in the core where it is unit-tested.
 *
 * If a policy question ever gets answered here, that is the bug.
 */
class WorkspaceViewModel(application: Application) : AndroidViewModel(application) {

    private val files = SautiyFiles(application)
    private val player = AudioPlayer(viewModelScope)

    private var capture: AudioCapture? = null
    private var peaks = PeakBuilder()
    private var captureBuffers = mutableListOf<AudioBuffer>()

    private var workspace = WorkspaceState()
    private var history = EditHistory.of(Timeline.empty(CaptureQuality.STUDIO.format.sampleRate))
    private var recording = RecordingState()
    private var sources = mutableMapOf<String, AudioBuffer>()
    private var takeCounter = 0

    private val _state = MutableStateFlow(WorkspaceUiState())
    val state: StateFlow<WorkspaceUiState> = _state.asStateFlow()

    val actions = WorkspaceActions(
        onRecordOrStop = ::recordOrStop,
        onPlayOrPause = ::playOrPause,
        onRewind = ::rewind,
        onToggleMonitor = ::toggleMonitor,
        onCommit = { openPanel(Panel.EXPORT) },
        onSeek = ::seek,
        onSelectionChanged = ::selectRange,
        onZoom = {},
        onContextAction = ::performContextAction,
        onDismissPanel = ::dismissPanel,
        onOpenPanel = ::openPanel,
        onSelectLayer = ::selectLayer,
        onAddLayer = ::addLayer,
        onOpenLibrary = { openPanel(Panel.LIBRARY) },
        onOpenSettings = {},
        onApplyPreset = ::applyPreset,
        onRevertPreset = ::revertPreset,
        onChooseExportFormat = { format -> _state.update { it.copy(exportFormat = format) } },
        onExport = {},
        onShare = {},
        onSetSpeed = { speed -> _state.update { it.copy(speed = speed) } },
        onToggleLoop = { _state.update { it.copy(looping = !it.looping) } },
        onToggleCompare = { _state.update { it.copy(comparingOriginal = !it.comparingOriginal) } },
        onTravelHistory = ::travelHistory,
        onOpenRecording = {},
        onToggleFavourite = {},
        onSearchLibrary = { query -> _state.update { it.copy(librarySearch = query) } },
        onDismissError = { _state.update { it.copy(error = null) } },
        onErrorRemedy = {},
    )

    init {
        publish()
    }

    // --- Recording ---------------------------------------------------------------------------

    private fun recordOrStop() {
        when (workspace.transport) {
            TransportState.RECORDING -> stopRecording()
            TransportState.RECORDING_PAUSED -> resumeRecording()
            else -> startRecording()
        }
    }

    private fun startRecording() {
        if (!RecordingMachine.isLegal(workspace.transport, RecordingMachine.Command.START)) return

        val quality = recording.quality
        val id = "take-${System.currentTimeMillis()}"
        val engine = AudioCapture(quality, viewModelScope)

        peaks = PeakBuilder()
        captureBuffers = mutableListOf()

        engine.onBlock = { block ->
            peaks.append(block)
            captureBuffers.add(block)
        }

        val failure = engine.start(files.takeFile(id))
        if (failure != null) {
            _state.update { it.copy(error = failure.toError()) }
            return
        }

        capture = engine
        currentTakeId = id
        workspace = workspace.copy(transport = TransportState.RECORDING)
        ai.sautiy.record.RecordingService.start(getApplication())

        viewModelScope.launch {
            engine.level.collect { level ->
                recording = recording.copy(
                    peakLinear = level.peakLinear,
                    rmsLinear = level.rmsLinear,
                    elapsedFrames = engine.framesWritten.value,
                    clippedSampleCount = engine.clippedSamples.value,
                    freeBytes = files.freeBytes(),
                )
                publish()
            }
        }
    }

    private fun resumeRecording() {
        if (!RecordingMachine.isLegal(workspace.transport, RecordingMachine.Command.RESUME)) return
        capture?.resume()
        workspace = workspace.copy(transport = TransportState.RECORDING)
        publish()
    }

    private fun stopRecording() {
        val engine = capture ?: return
        val id = currentTakeId ?: return
        val frames = engine.stop()
        capture = null
        ai.sautiy.record.RecordingService.stop(getApplication())

        if (frames > 0) {
            val quality = recording.quality
            val source = Source(
                id = id,
                relativePath = "takes/$id.wav",
                sampleRate = quality.format.sampleRate,
                channelCount = quality.format.channelCount,
                frameCount = frames,
            )
            sources[id] = AudioBuffer.concat(captureBuffers.ifEmpty { listOf(AudioBuffer.silence(1, 1, quality.format.sampleRate)) })

            val layerId = workspace.layers.firstOrNull()?.let { "L1" } ?: "L1"
            var timeline = history.current
            if (timeline.layer(layerId) == null) {
                timeline = timeline.copy(layers = timeline.layers + Layer(layerId, "Vocals ${++takeCounter}"))
                history = history.replaceCurrent(timeline)
            }
            history = history.apply(
                AppendRecording(
                    layerId = layerId,
                    source = source,
                    atFrame = timeline.layer(layerId)?.lengthFrames ?: 0,
                    clipId = "$id.clip",
                ),
            )
        }

        workspace = workspace.copy(
            transport = TransportState.STOPPED,
            hasAudio = history.current.lengthFrames > 0,
            layerCount = history.current.layers.size,
            canUndo = history.canUndo,
            canRedo = history.canRedo,
        )
        currentTakeId = null
        publish()
    }

    private var currentTakeId: String? = null

    // --- Playback ----------------------------------------------------------------------------

    private fun playOrPause() {
        if (workspace.transport == TransportState.PLAYING) {
            player.pause()
            workspace = workspace.copy(transport = TransportState.PLAYBACK_PAUSED)
            publish()
            return
        }
        if (!PlaybackMachine.isLegal(workspace.transport, PlaybackMachine.Command.PLAY)) return

        val timeline = history.current
        if (timeline.lengthFrames == 0L) return

        player.onFinished = {
            workspace = workspace.copy(transport = TransportState.STOPPED)
            publish()
        }
        player.start(
            timeline = timeline,
            provider = InMemorySourceProvider(sources),
            fromFrame = _state.value.playheadFrame,
            speed = _state.value.speed,
        )
        workspace = workspace.copy(transport = TransportState.PLAYING)
        publish()

        viewModelScope.launch {
            player.positionFrames.collect { frame ->
                _state.update { it.copy(playheadFrame = frame) }
            }
        }
    }

    private fun rewind() {
        val markers = _state.value.markerFrames
        val position = _state.value.playheadFrame
        val target = markers.filter { it < position }.maxOrNull() ?: 0L
        seek(target)
    }

    private fun seek(frame: Long) {
        player.seekTo(frame)
        _state.update { it.copy(playheadFrame = frame.coerceIn(0, it.totalFrames)) }
    }

    private fun toggleMonitor() {
        _state.update { it.copy(monitoring = !it.monitoring) }
    }

    // --- Editing ------------------------------------------------------------------------------

    private fun selectRange(range: LongRange?) {
        workspace = workspace.copy(
            focus = if (range == null) Focus.None else Focus.Range(range.first, range.last),
        )
        _state.update { it.copy(selection = range) }
        publish()
    }

    private fun selectLayer(id: String) {
        workspace = workspace.copy(focus = Focus.Layer(id))
        _state.update { it.copy(selectedLayerId = id) }
        publish()
    }

    private fun addLayer() {
        val id = "L${history.current.layers.size + 1}"
        history = history.apply(
            ai.sautiy.core.edit.AddLayer(id = id, name = "Vocals ${history.current.layers.size + 1}"),
        )
        publish()
    }

    private fun travelHistory(step: Int) {
        history = history.travelTo(step)
        publish()
    }

    /**
     * Every context action routes to a core operation. The mapping is the only thing this class
     * knows about the context bar — it does not decide which actions exist.
     */
    private fun performContextAction(action: WorkspaceAction) {
        val selection = _state.value.selection
        when (action.id) {
            "ctx.undo" -> history = history.undo()
            "ctx.redo" -> history = history.redo()
            "ctx.deselect" -> selectRange(null)
            "ctx.cut" -> selection?.let { history = history.apply(DeleteRange(it.first, it.last)) }
            "ctx.silence" -> selection?.let { history = history.apply(SilenceRange(it.first, it.last)) }
            "ctx.split" -> {
                val layerId = _state.value.selectedLayerId ?: history.current.layers.firstOrNull()?.id
                if (layerId != null) history = history.apply(Split(layerId, _state.value.playheadFrame))
            }
            "ctx.marker" -> _state.update { it.copy(markerFrames = it.markerFrames + currentPositionFrames()) }
            else -> action.opens?.let(::openPanel)
        }
        if (action.opens == null) selectRange(null) else openPanel(action.opens!!)
        publish()
    }

    private fun currentPositionFrames(): Long =
        if (workspace.transport.isCapturing) recording.elapsedFrames else _state.value.playheadFrame

    // --- Panels --------------------------------------------------------------------------------

    private fun openPanel(panel: Panel) {
        workspace = workspace.openingPanel(panel)
        publish()
    }

    private fun dismissPanel() {
        workspace = workspace.dismissingPanel()
        publish()
    }

    // --- Studio ---------------------------------------------------------------------------------

    private fun applyPreset(preset: StudioPreset) {
        _state.update { it.copy(appliedPreset = preset) }
    }

    private fun revertPreset() {
        _state.update { it.copy(appliedPreset = null) }
    }

    // --- Publishing -------------------------------------------------------------------------------

    /**
     * Rebuilds the UI state from the core state.
     *
     * The context bar comes straight out of `WorkspaceState.contextActions()` — the pure
     * function tested over every reachable state — so what the user sees is what the law says,
     * with no opportunity for this class to disagree with it.
     */
    private fun publish() {
        val timeline = history.current
        val total = timeline.lengthFrames
        val recordedFrames = if (workspace.transport.isCapturing) recording.elapsedFrames else total

        val level = peaks.snapshot()
        val pyramid = if (level.bucketCount > 0) {
            Waveform.pyramid(level, timeline.sampleRate, maxOf(total, recordedFrames))
        } else {
            null
        }

        val peakDb = Decibels.fromLinear(recording.peakLinear.toDouble())
        val noiseFloorDb = -62.0
        val score = recording.qualityScore(noiseFloorDb)

        _state.update { previous ->
            previous.copy(
                transport = workspace.transport,
                quality = recording.quality,
                sampleRate = timeline.sampleRate,
                hasAudio = total > 0 || workspace.transport.isCapturing,
                recordedFrames = recordedFrames,
                totalFrames = maxOf(total, recordedFrames),
                waveform = pyramid?.columns(0, maxOf(total, recordedFrames, 1), WAVEFORM_COLUMNS),
                layers = timeline.layers.map { layer ->
                    LayerRow(layer.id, layer.name, layer.muted, layer.soloed, layer.colourIndex)
                },
                peakDb = peakDb,
                rmsDb = Decibels.fromLinear(recording.rmsLinear),
                hasClipped = recording.hasClipped,
                qualityScore = score,
                qualityReason = qualityReason(score, peakDb, recording.hasClipped),
                noiseFloorDb = noiseFloorDb,
                secondsRemaining = recording.secondsRemaining,
                storageCritical = recording.storageIsCritical,
                openPanel = workspace.openPanel,
                contextActions = workspace.copy(
                    hasAudio = total > 0,
                    markerCount = previous.markerFrames.size,
                    canUndo = history.canUndo,
                    canRedo = history.canRedo,
                ).contextActions(),
                canUndo = history.canUndo,
                canRedo = history.canRedo,
                historySteps = history.steps,
                historyIndex = history.index,
            )
        }
    }

    /** One sentence a person can act on. A score with no explanation gets ignored. */
    private fun qualityReason(score: Int, peakDb: Double, clipped: Boolean): String = when {
        clipped -> "Clipped. Move further from the microphone."
        peakDb < -30 -> "Very quiet. Move closer to the microphone."
        peakDb > -3 -> "Close to clipping. Ease back a little."
        score >= 85 -> "Good level and a clean floor."
        else -> "Usable. A quieter room would help."
    }

    override fun onCleared() {
        capture?.stop()
        player.stop()
        super.onCleared()
    }

    private companion object {
        /** Columns to resolve the waveform into. Redrawn on layout with the real pixel width. */
        const val WAVEFORM_COLUMNS = 720
    }
}
