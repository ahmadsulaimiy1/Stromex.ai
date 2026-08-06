package ai.sautiy.ui.workspace

import ai.sautiy.core.analysis.PeakBuilder
import ai.sautiy.core.analysis.Waveform
import ai.sautiy.core.audio.CaptureQuality
import ai.sautiy.core.audio.Decibels
import ai.sautiy.core.codec.ExportJob
import ai.sautiy.core.codec.WavStreamReader
import ai.sautiy.core.dsp.AmbienceMode
import ai.sautiy.core.dsp.AmbienceSettings
import ai.sautiy.core.dsp.ListenerNote
import ai.sautiy.core.dsp.OneTap
import ai.sautiy.core.dsp.VoiceOutcome
import ai.sautiy.core.dsp.VoiceRefinement
import ai.sautiy.core.dsp.VoiceSpacePreset
import ai.sautiy.core.dsp.VoiceStudio
import ai.sautiy.core.dsp.VoiceStudioSettings
import ai.sautiy.core.edit.AppendRecording
import ai.sautiy.core.edit.DeleteRange
import ai.sautiy.core.edit.EditHistory
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
import ai.sautiy.core.workspace.SautiyError
import ai.sautiy.core.workspace.TransportState
import ai.sautiy.core.workspace.WorkspaceAction
import ai.sautiy.core.library.Library
import ai.sautiy.core.library.RecordingEntry
import ai.sautiy.core.library.RecordingStore
import ai.sautiy.core.workspace.WorkspaceState
import ai.sautiy.data.SautiyFiles
import ai.sautiy.play.AudioPlayer
import ai.sautiy.record.AudioCapture
import android.app.Application
import android.net.Uri
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.Dispatchers
import ai.sautiy.core.play.LoopRegion
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

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

    /**
     * Source audio is read from disk in ranges, never accumulated in memory.
     *
     * Holding every captured buffer would be about 500 MB for a ninety-minute lecture — four
     * times the constitutional ceiling of chapter 16.3, breached on exactly the recording that
     * matters most to the person making it. Only the peaks are kept, at roughly 8 MB per hour,
     * which is what lets the whole waveform be drawn while the audio stays on the platter.
     */
    private val audioSources = ai.sautiy.data.FileSourceProvider(files)

    /** The library. Verified on the JVM; this class only calls it. */
    private val store = RecordingStore(files.libraryIndex)

    private var workspace = WorkspaceState()
    private var history = EditHistory.of(Timeline.empty(CaptureQuality.STUDIO.format.sampleRate))
    private var recording = RecordingState()
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
        onEnhanceVoice = { applyVoice(OneTap.enhanceVoice(), preset = null) },
        onStudioVoice = { applyVoice(OneTap.studioVoice(), preset = null) },
        onAmbienceChanged = ::changeAmbience,
        onAmbienceModeChanged = ::changeAmbienceMode,
        onAuditionSpaces = ::auditionSpaces,
        onApplyOutcome = ::applyOutcome,
        onListenerNote = ::applyListenerNote,
        onStopAudition = ::stopAudition,
        onRefinementChanged = ::changeRefinement,
        onChooseExportFormat = { format -> _state.update { it.copy(exportFormat = format) } },
        onExport = ::export,
        onShare = ::share,
        onSetSpeed = { speed -> _state.update { it.copy(speed = speed) } },
        onToggleLoop = { _state.update { it.copy(looping = !it.looping) } },
        onToggleCompare = ::toggleCompare,
        onTravelHistory = ::travelHistory,
        onOpenRecording = ::openRecording,
        onToggleFavourite = ::toggleFavourite,
        onRename = ::rename,
        onDelete = ::delete,
        onSearchLibrary = { query ->
            _state.update { it.copy(librarySearch = query) }
            refreshLibrary()
        },
        onDismissError = { _state.update { it.copy(error = null) } },
        onErrorRemedy = {},
    )

    init {
        pruneTrash()
        refreshLibrary()
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

        // Only the peak envelope is retained. The audio itself is already on disk, written by
        // the streaming WAV writer, and is read back in ranges when it is needed.
        engine.onBlock = { block -> peaks.append(block) }

        _state.update { it.copy(channelCount = quality.format.channelCount) }

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
            // The take lands on the selected layer, or on the first one, or on a layer created
            // for it — a user who has never thought about layers never has to.
            val layerId = _state.value.selectedLayerId
                ?: history.current.layers.firstOrNull()?.id
                ?: "L1"
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

        if (frames > 0) {
            saveTake(id, frames, recording.quality.format.sampleRate, recording.quality.format.channelCount)
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
            provider = audioSources,
            fromFrame = _state.value.playheadFrame,
            speed = _state.value.speed,
            channelCount = _state.value.channelCount,
            voiceSettings = if (_state.value.comparingOriginal) null else _state.value.voice,
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

    /**
     * Chooses a space, and applies it — to what is playing right now, and to what is exported.
     *
     * The first version of this method set a field and stopped. The card highlighted, the panel
     * printed numbers, and not one sample was ever processed. Nothing here is allowed to record
     * an intention without carrying it out.
     */
    private fun applyPreset(preset: VoiceSpacePreset) {
        applyVoice(preset.settings, preset)
    }

    private fun applyVoice(settings: VoiceStudioSettings, preset: VoiceSpacePreset?) {
        _state.update {
            it.copy(
                appliedPreset = preset,
                voice = settings,
                deferredStages = VoiceStudio(settings).deferredStages,
            )
        }
        // Heard immediately, without restarting playback.
        player.setVoice(if (_state.value.comparingOriginal) null else settings)
    }

    private fun revertPreset() {
        _state.update { it.copy(appliedPreset = null, voice = null, deferredStages = emptyList()) }
        player.setVoice(null)
    }

    /**
     * Plays one short passage through every space in turn.
     *
     * This exists because choosing a room is a listening decision and nothing else, and the only
     * honest way to make it is to hear the *same* phrase in each one. Reading the parameters, or
     * comparing two presets a minute apart, tells you almost nothing — ears have no memory for
     * timbre over that distance. So the passage loops, the space changes underneath it every few
     * seconds, and the name of what is playing is on screen.
     */
    private fun auditionSpaces() {
        val timeline = history.current
        if (timeline.lengthFrames == 0L) return
        auditionJob?.cancel()

        val rate = timeline.sampleRate
        val span = minOf(timeline.lengthFrames, AUDITION_SECONDS * rate)
        val start = _state.value.playheadFrame
            .coerceIn(0, (timeline.lengthFrames - span).coerceAtLeast(0))

        // The comparison has to start from the original, so the first thing heard is the thing
        // every space is being judged against.
        player.onFinished = null
        player.start(
            timeline = timeline,
            provider = audioSources,
            fromFrame = start,
            speed = _state.value.speed,
            loopRegion = LoopRegion(start, start + span),
            channelCount = _state.value.channelCount,
            voiceSettings = null,
        )
        workspace = workspace.copy(transport = TransportState.PLAYING)
        publish()

        val mode = _state.value.voice?.ambienceMode ?: AmbienceMode.STUDIO
        auditionJob = viewModelScope.launch {
            _state.update { it.copy(auditioning = null, appliedPreset = null, voice = null) }
            player.setVoice(null)
            delay(AUDITION_SECONDS * 1_000L)

            for (outcome in VoiceOutcome.cardOrder) {
                val settings = outcome.settings.copy(ambienceMode = mode)
                _state.update {
                    it.copy(
                        auditioning = outcome,
                        appliedOutcome = outcome,
                        voice = settings,
                        deferredStages = VoiceStudio(settings).deferredStages,
                    )
                }
                player.setVoice(settings)
                delay(AUDITION_SECONDS * 1_000L)

                // Back to the original between every one. A listener should never have to
                // remember how the previous version sounded — the comparison is put in front of
                // them instead of being left to their memory, which is the whole difference
                // between an A/B and a slideshow.
                _state.update { it.copy(comparingOriginal = true) }
                player.setVoice(null)
                delay(ORIGINAL_SECONDS * 1_000L)
                _state.update { it.copy(comparingOriginal = false) }
                player.setVoice(settings)
            }
            // Ends on whatever was last heard rather than reverting, so a space the listener
            // liked is already applied when the cycle stops.
            _state.update { it.copy(auditioning = null) }
        }
    }

    /** A preset named for the job it does. What the panel actually offers. */
    private fun applyOutcome(outcome: VoiceOutcome) {
        val mode = _state.value.voice?.ambienceMode ?: outcome.mode
        applyVoice(outcome.settings.copy(ambienceMode = mode), preset = null)
        _state.update { it.copy(appliedOutcome = outcome) }
    }

    /**
     * A listener said something about what they are hearing.
     *
     * The note is applied immediately and heard on the next block, so the loop is listen, say a
     * word, listen again. Nothing here needs the listener to know what a parameter is, and
     * nothing needs an engineer to interpret them — the mapping lives in `ListenerNote`.
     */
    private fun applyListenerNote(note: ListenerNote) {
        if (note == ListenerNote.EXCELLENT) {
            stopAudition()
            return
        }
        val base = _state.value.voice ?: VoiceStudioSettings()
        val adjusted = note.applyTo(base)
        // Hand-adjusted, so it is no longer the named preset it started as.
        _state.update { it.copy(appliedOutcome = null) }
        applyVoice(adjusted, preset = null)
    }

    /** Stops the cycle and keeps whatever was playing when it stopped. */
    private fun stopAudition() {
        auditionJob?.cancel()
        auditionJob = null
        _state.update { it.copy(auditioning = null) }
    }

    private var auditionJob: kotlinx.coroutines.Job? = null

    /** An ambience control moved. The space stops being a named preset the moment it is edited. */
    private fun changeAmbience(ambience: AmbienceSettings) {
        val base = _state.value.voice ?: VoiceStudioSettings()
        applyVoice(base.copy(ambience = ambience), preset = null)
    }

    /** The mode changes how much room, and keeps the preset it was chosen for. */
    private fun changeAmbienceMode(mode: AmbienceMode) {
        val base = _state.value.voice ?: VoiceStudioSettings()
        applyVoice(base.copy(ambienceMode = mode), preset = _state.value.appliedPreset)
    }

    private fun changeRefinement(refinement: VoiceRefinement) {
        val base = _state.value.voice ?: VoiceStudioSettings()
        applyVoice(base.copy(refinement = refinement), preset = null)
    }

    /**
     * A/B against the original, without stopping.
     *
     * The comparison has to reach the audio, not just the label. Toggling this used to flip a
     * boolean in the state and nothing else, so the button lit up and both sides sounded the same.
     */
    private fun toggleCompare() {
        val comparing = !_state.value.comparingOriginal
        _state.update { it.copy(comparingOriginal = comparing) }
        player.setVoice(if (comparing) null else _state.value.voice)
    }

    // --- Export -----------------------------------------------------------------------------

    /**
     * The file name to offer the destination picker.
     *
     * Derived from the project title, because that is the name the user already gave it. Stripped
     * of anything a file system would reject rather than allowed to fail at the moment of saving.
     */
    val suggestedExportName: String
        get() {
            // Letters, digits, spaces and the three punctuation marks a file name may safely
            // carry. Written as what is *allowed* rather than what is forbidden, so an Arabic
            // or Urdu title survives — a title stripped to nothing is not a fixed file name.
            val base = _state.value.projectName
                .replace(Regex("[^\\p{L}\\p{N} ._-]"), "")
                .trim()
                .ifBlank { "SAUTIY recording" }
            return "$base.${_state.value.exportFormat.extension}"
        }

    /**
     * Writes the project into a destination the user chose, through the same Voice Studio that
     * was auditioned.
     *
     * The document comes from the Storage Access Framework, so it can be internal storage, an SD
     * card, or a cloud provider — SAUTIY does not need to know which, and never asks for
     * storage permission to reach any of them.
     *
     * Export reports its progress and its failures. A silent failure here is the worst bug this
     * application can have: the user believes they have a file, and finds out they do not at the
     * moment they need it.
     */
    fun exportTo(destination: Uri) {
        runExport(destination = destination, thenShare = false)
    }

    /** The user dismissed the destination picker. Nothing was written, and nothing is claimed. */
    fun exportCancelled() {
        shareAfterExport = false
        _state.update { it.copy(exportProgress = null) }
    }

    /** Export into app storage, which is the staging area the share sheet reads from. */
    private fun export() {
        runExport(destination = null, thenShare = shareAfterExport)
    }

    private fun runExport(destination: Uri?, thenShare: Boolean) {
        val timeline = history.current
        if (timeline.lengthFrames == 0L) return
        if (_state.value.exportProgress != null) return

        val format = _state.value.exportFormat
        val voice = _state.value.voice
        val staging = files.exports.resolve(suggestedExportName)

        _state.update { it.copy(exportProgress = 0.0) }
        viewModelScope.launch {
            val outcome = withContext(Dispatchers.IO) {
                runCatching {
                    val stream = if (destination != null) {
                        getApplication<Application>().contentResolver.openOutputStream(destination)
                            ?: error("The chosen destination could not be opened for writing.")
                    } else {
                        staging.outputStream()
                    }
                    stream.use { out ->
                        ExportJob(
                            timeline = timeline,
                            provider = audioSources,
                            format = format,
                            voice = voice,
                            channelCount = _state.value.channelCount,
                        ).run(out) { fraction, _ ->
                            _state.update { it.copy(exportProgress = fraction) }
                        }
                    }
                }
            }
            outcome.fold(
                onSuccess = { result ->
                    _state.update { state ->
                        state.copy(
                            exportProgress = null,
                            lastExportPath = if (destination == null) staging.absolutePath else state.lastExportPath,
                            savedTo = destination?.let { describe(it) },
                            exportClipped = result.clipped,
                        )
                    }
                    if (thenShare) {
                        shareAfterExport = false
                        share()
                    }
                },
                onFailure = { failure ->
                    shareAfterExport = false
                    // A half-written export that opens in nothing is worse than no export,
                    // because it looks like success. Remove what was started.
                    if (destination == null) {
                        runCatching { staging.delete() }
                    } else {
                        runCatching {
                            android.provider.DocumentsContract.deleteDocument(
                                getApplication<Application>().contentResolver,
                                destination,
                            )
                        }
                    }
                    _state.update { state ->
                        state.copy(
                            exportProgress = null,
                            savedTo = null,
                            error = SautiyError(
                                fact = "The export stopped before it finished.",
                                consequence = "No ${format.displayName} file was written. " +
                                    (failure.message ?: "The device reported no reason."),
                                remedy = SautiyError.Remedy("Try again", "error.retryExport"),
                            ),
                        )
                    }
                },
            )
        }
    }

    /** What to tell the user about where their file went, in their own terms. */
    private fun describe(uri: Uri): String =
        runCatching {
            getApplication<Application>().contentResolver
                .query(uri, arrayOf(android.provider.OpenableColumns.DISPLAY_NAME), null, null, null)
                ?.use { cursor ->
                    if (cursor.moveToFirst()) cursor.getString(0) else null
                }
        }.getOrNull() ?: uri.lastPathSegment ?: "the chosen folder"

    // --- Library ----------------------------------------------------------------------------------

    /**
     * Saves a finished take into the library.
     *
     * Chapter 13.2: the recording is never named before it exists. It is saved immediately under
     * a date-and-time title, so a user who dismisses the naming prompt still has a findable
     * library, and renaming afterwards is an ordinary edit rather than a rescue.
     */
    private fun saveTake(takeId: String, frames: Long, sampleRate: Int, channelCount: Int) {
        val created = System.currentTimeMillis()
        val title = Library.uniqueTitle(
            Library.defaultTitle(created),
            store.all().map { it.title }.toSet(),
        )
        store.save(
            RecordingEntry(
                id = takeId,
                title = title,
                takeId = takeId,
                createdAtEpochMs = created,
                durationFrames = frames,
                sampleRate = sampleRate,
                channelCount = channelCount,
                markerLabels = _state.value.markerFrames.map { formatTimecode(it, sampleRate) },
            ),
        )
        refreshLibrary()
    }

    /**
     * Hands the exported file to the system share sheet.
     *
     * Exports first if there is nothing to share yet, so "Share" never silently does nothing —
     * and shares a `content://` URI through the declared provider rather than a file path, which
     * every Android since Nougat rejects.
     */
    private fun share() {
        val path = _state.value.lastExportPath
        if (path == null) {
            shareAfterExport = true
            export()
            return
        }
        val file = java.io.File(path)
        if (!file.isFile) {
            shareAfterExport = true
            export()
            return
        }
        val context = getApplication<Application>()
        val uri = androidx.core.content.FileProvider.getUriForFile(
            context,
            "${context.packageName}.files",
            file,
        )
        val intent = android.content.Intent(android.content.Intent.ACTION_SEND).apply {
            type = _state.value.exportFormat.mimeType
            putExtra(android.content.Intent.EXTRA_STREAM, uri)
            putExtra(android.content.Intent.EXTRA_TITLE, _state.value.projectName)
            addFlags(android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        val chooser = android.content.Intent.createChooser(intent, "Share recording")
            .addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK)
        runCatching { context.startActivity(chooser) }
    }

    /** Set when Share was pressed before anything had been exported. */
    private var shareAfterExport = false

    private fun rename(id: String, title: String) {
        store.rename(id, title)
        refreshLibrary()
    }

    /** Delete is never final: it goes to the trash with a stated recovery window (chapter 13.5). */
    private fun delete(id: String) {
        store.find(id)?.let { audioSources.invalidate(it.takeId) }
        store.trash(id)
        refreshLibrary()
    }

    private fun toggleFavourite(id: String) {
        store.find(id)?.let { store.setFavourite(id, !it.favourite) }
        refreshLibrary()
    }

    private fun openRecording(id: String) {
        val entry = store.find(id) ?: return
        val source = Source(
            id = entry.takeId,
            relativePath = "takes/${entry.takeId}.wav",
            sampleRate = entry.sampleRate,
            channelCount = entry.channelCount,
            frameCount = entry.durationFrames,
        )
        val layer = Layer("L1", "Vocals 1")
        val timeline = Timeline(sampleRate = entry.sampleRate, layers = listOf(layer))
        history = EditHistory.of(timeline).apply(
            AppendRecording(layerId = "L1", source = source, atFrame = 0, clipId = "${entry.takeId}.clip"),
        )
        workspace = workspace.copy(transport = TransportState.STOPPED, hasAudio = true).dismissingPanel()
        _state.update {
            it.copy(projectName = entry.title, playheadFrame = 0, channelCount = entry.channelCount)
        }
        publish()

        // The waveform has to be rebuilt from the file. Without this the peak builder still
        // holds whatever the last recording left in it — usually nothing — and a saved
        // recording opens to an empty canvas. It runs off the main thread and streams the file
        // in blocks, so a ninety-minute lecture does not stall the interface or the heap.
        rebuildPeaks(entry.takeId)
    }

    private fun rebuildPeaks(takeId: String) {
        peaks = PeakBuilder()
        publish()
        viewModelScope.launch {
            val rebuilt = withContext(Dispatchers.IO) {
                val file = files.takeFile(takeId)
                if (!file.isFile) return@withContext null
                runCatching {
                    WavStreamReader(file).use { reader ->
                        PeakBuilder().also { builder ->
                            var position = 0L
                            while (position < reader.frameCount) {
                                val frames = minOf((1 shl 18).toLong(), reader.frameCount - position).toInt()
                                builder.append(reader.read(position, frames))
                                position += frames
                            }
                        }
                    }
                }.getOrNull()
            } ?: return@launch
            peaks = rebuilt
            publish()
        }
    }

    /**
     * Purges expired trash on launch and deletes the audio it orphaned.
     *
     * The store reports the orphans; deleting them is this class's job, because one component
     * owning both the index and the media is how an index bug becomes lost recordings.
     */
    private fun pruneTrash() {
        for (takeId in store.purgeExpired()) files.deleteTake(takeId)
        files.pruneExportStaging(System.currentTimeMillis())
    }

    private fun refreshLibrary() {
        val query = _state.value.librarySearch
        val rows = if (query.isBlank()) {
            store.live()
        } else {
            store.search(query).map { it.entry }
        }
        _state.update { previous ->
            previous.copy(
                library = rows.map { entry ->
                    LibraryRow(
                        id = entry.id,
                        title = entry.title,
                        durationFrames = entry.durationFrames,
                        sampleRate = entry.sampleRate,
                        createdAtEpochMs = entry.createdAtEpochMs,
                        favourite = entry.favourite,
                        tags = entry.tags,
                    )
                },
            )
        }
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
        auditionJob?.cancel()
        capture?.stop()
        player.stop()
        audioSources.close()
        super.onCleared()
    }

    private companion object {
        /** Columns to resolve the waveform into. Redrawn on layout with the real pixel width. */
        const val WAVEFORM_COLUMNS = 720

        /**
         * Seconds each space gets during an audition.
         *
         * Long enough to hear a tail decay and short enough that the previous space is still in
         * the listener's ear. Below about three seconds a long hall never finishes speaking;
         * above about six the comparison stops being a comparison.
         */
        const val AUDITION_SECONDS = 5L

        /**
         * Seconds of the original between presets.
         *
         * Shorter than the preset itself: it is a reference point, not a candidate, and the
         * listener already knows what it sounds like — they need reminding, not convincing.
         */
        const val ORIGINAL_SECONDS = 2L
    }
}
