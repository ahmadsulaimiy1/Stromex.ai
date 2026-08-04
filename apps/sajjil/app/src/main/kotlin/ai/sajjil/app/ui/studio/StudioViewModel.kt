package ai.sajjil.app.ui.studio

import ai.sajjil.app.Services
import ai.sajjil.app.audio.ExportFormat
import ai.sajjil.app.audio.ExportQuality
import ai.sajjil.app.audio.ExportResult
import ai.sajjil.app.data.RecordingEntity
import ai.sajjil.audio.AudioBuffer
import ai.sajjil.audio.analysis.QualityReport
import ai.sajjil.audio.chain.AmbienceProfile
import ai.sajjil.audio.chain.AmbienceProfiles
import ai.sajjil.audio.chain.EnhancementSettings
import ai.sajjil.audio.chain.StudioPreset
import ai.sajjil.audio.chain.StudioPresets
import ai.sajjil.audio.chain.VoiceStyle
import ai.sajjil.audio.chain.VoiceStyles
import ai.sajjil.audio.dsp.ReverbSettings
import ai.sajjil.audio.edit.EditSession
import ai.sajjil.audio.edit.FrameRange
import ai.sajjil.audio.waveform.WaveformPeaks
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/** What the Studio screen is doing right now, so the UI never has to guess. */
sealed interface StudioTask {
    data object Idle : StudioTask
    data class Working(val label: String, val progress: Double) : StudioTask
    data class Finished(val message: String) : StudioTask
    data class Failed(val title: String, val body: String) : StudioTask
}

data class StudioUiState(
    val recording: RecordingEntity? = null,
    val isLoading: Boolean = false,
    val peaks: WaveformPeaks? = null,
    val totalFrames: Int = 0,
    val sampleRate: Int = 48000,
    val playheadFrame: Int = 0,
    val selection: FrameRange? = null,
    val splitPoints: List<Int> = emptyList(),
    val zoom: Float = 1f,
    val scrollFraction: Float = 0f,
    val canUndo: Boolean = false,
    val canRedo: Boolean = false,
    val undoLabel: String? = null,
    val hasUnsavedEdits: Boolean = false,
    val quality: QualityReport? = null,
    val selectedPreset: StudioPreset? = null,
    val selectedVoiceStyle: VoiceStyle = VoiceStyles.NATURAL,
    val selectedAmbience: AmbienceProfile = AmbienceProfiles.DRY_STUDIO,
    val ambienceOverride: ReverbSettings? = null,
    val advancedOpen: Boolean = false,
    val task: StudioTask = StudioTask.Idle,
    val lastExport: ExportResult? = null,
) {
    /**
     * The settings that would be applied if the user tapped Enhance now.
     *
     * Composed from the preset, the voice style layered on top, and whatever the Echo panel has
     * been set to. One expression, so what the panel shows and what the engine runs cannot drift.
     */
    val effectiveSettings: EnhancementSettings?
        get() {
            val preset = selectedPreset ?: return null
            val withStyle = VoiceStyles.apply(preset.settings, selectedVoiceStyle)
            val reverb = ambienceOverride ?: selectedAmbience.reverb.takeIf { it.amount > 0.0 }
            return withStyle.copy(reverb = reverb ?: withStyle.reverb)
        }
}

class StudioViewModel(private val services: Services) : ViewModel() {

    private val repository = services.repository

    private val _state = MutableStateFlow(StudioUiState())
    val state: StateFlow<StudioUiState> = _state.asStateFlow()

    /** The editing model. Held here so it survives recomposition but not the screen. */
    private var session: EditSession? = null
    private var loadedRecordingId: Long? = null

    fun open(recordingId: Long) {
        if (loadedRecordingId == recordingId && session != null) return
        loadedRecordingId = recordingId
        _state.value = StudioUiState(isLoading = true)

        viewModelScope.launch {
            val recording = repository.byId(recordingId)
            if (recording == null) {
                _state.value = StudioUiState(
                    isLoading = false,
                    task = StudioTask.Failed(
                        "That recording is no longer here",
                        "It may have been deleted. Open another one from your Library.",
                    ),
                )
                return@launch
            }

            val audio = runCatching { repository.loadAudio(recording) }.getOrElse { error ->
                _state.value = StudioUiState(
                    isLoading = false,
                    recording = recording,
                    task = StudioTask.Failed(
                        "This recording could not be opened",
                        "The audio file appears to be damaged. Everything else in your Library is unaffected.",
                    ),
                )
                return@launch
            }

            val editSession = EditSession(audio)
            session = editSession

            _state.value = StudioUiState(
                recording = recording,
                isLoading = false,
                totalFrames = audio.frameCount,
                sampleRate = audio.sampleRate,
                peaks = withContext(Dispatchers.Default) {
                    WaveformPeaks.extract(audio, WAVEFORM_BUCKETS)
                },
                selectedPreset = recording.lastPresetId?.let(StudioPresets::byId),
                selectedVoiceStyle = recording.lastVoiceStyleId?.let(VoiceStyles::byId) ?: VoiceStyles.NATURAL,
                selectedAmbience = recording.lastAmbienceId?.let(AmbienceProfiles::byId)
                    ?: AmbienceProfiles.DRY_STUDIO,
            )

            // Quality arrives after the waveform. Neither blocks the other, and neither blocks
            // playback, which is already available the moment the screen appears.
            runCatching { repository.analyse(recording) }.getOrNull()?.let { report ->
                _state.value = _state.value.copy(quality = report)
            }
        }
    }

    // ---- transport -----------------------------------------------------------------------

    fun seekToFrame(frame: Int) {
        _state.value = _state.value.copy(playheadFrame = frame)
        val sampleRate = _state.value.sampleRate
        if (sampleRate > 0) {
            services.playback.seekTo(frame * 1000L / sampleRate)
        }
    }

    fun playFromPlayhead() {
        val recording = _state.value.recording ?: return
        val sampleRate = _state.value.sampleRate
        services.playback.play(
            recordingId = recording.id,
            file = repository.fileFor(recording),
            title = recording.title,
            startPositionMs = if (sampleRate > 0) _state.value.playheadFrame * 1000L / sampleRate else 0,
        )
    }

    fun setPlayheadFromMillis(millis: Long) {
        val sampleRate = _state.value.sampleRate
        if (sampleRate > 0) {
            _state.value = _state.value.copy(playheadFrame = (millis * sampleRate / 1000).toInt())
        }
    }

    // ---- editing -------------------------------------------------------------------------

    fun setSelection(range: FrameRange?) {
        session?.selection = range
        _state.value = _state.value.copy(selection = range)
    }

    fun setZoom(zoom: Float) {
        _state.value = _state.value.copy(zoom = zoom)
        refreshWaveform()
    }

    fun setScroll(fraction: Float) {
        _state.value = _state.value.copy(scrollFraction = fraction)
        refreshWaveform()
    }

    fun split(frame: Int) {
        session?.split(frame)
        _state.value = _state.value.copy(splitPoints = session?.splitPoints?.toList().orEmpty())
    }

    fun trimToSelection() = edit("Trim") { it.trimTo() }
    fun deleteSelection() = edit("Delete") { it.delete() }
    fun cutSelection() = edit("Cut") { it.cut() }
    fun copySelection() {
        session?.copy()
    }

    fun pasteAtPlayhead() = edit("Paste") { it.paste(_state.value.playheadFrame) }
    fun fadeInSelection() = edit("Fade in") { it.fadeIn() }
    fun fadeOutSelection() = edit("Fade out") { it.fadeOut() }

    fun insertSilence(seconds: Double) = edit("Insert silence") {
        it.insertSilence(_state.value.playheadFrame, (seconds * _state.value.sampleRate).toInt())
    }

    fun removeSilence() {
        val editSession = session ?: return
        viewModelScope.launch {
            setTask(StudioTask.Working("Removing silence", 0.0))
            withContext(Dispatchers.Default) {
                editSession.transform("Remove silence") { audio ->
                    ai.sajjil.audio.edit.SilenceDetector(audio.sampleRate).removeSilence(audio)
                }
            }
            afterEdit()
            setTask(StudioTask.Finished("Silence shortened"))
        }
    }

    fun undo() {
        session?.undo()
        afterEditSync()
    }

    fun redo() {
        session?.redo()
        afterEditSync()
    }

    private fun edit(label: String, action: (EditSession) -> Unit) {
        val editSession = session ?: return
        runCatching { action(editSession) }
            .onFailure {
                setTask(
                    StudioTask.Failed(
                        "That edit needs a selection",
                        "Drag across the waveform to choose the part you want to $label.",
                    )
                )
                return
            }
        afterEditSync()
    }

    private fun afterEditSync() {
        viewModelScope.launch { afterEdit() }
    }

    private suspend fun afterEdit() {
        val editSession = session ?: return
        val audio = editSession.buffer
        val peaks = withContext(Dispatchers.Default) {
            WaveformPeaks.extract(audio, WAVEFORM_BUCKETS)
        }
        _state.value = _state.value.copy(
            peaks = peaks,
            totalFrames = audio.frameCount,
            selection = editSession.selection,
            splitPoints = editSession.splitPoints.toList(),
            canUndo = editSession.canUndo,
            canRedo = editSession.canRedo,
            undoLabel = editSession.undoLabel,
            hasUnsavedEdits = editSession.canUndo,
            playheadFrame = _state.value.playheadFrame.coerceIn(0, audio.frameCount),
        )
    }

    /** Writes the edited audio back to disk. Until this, edits live only in memory. */
    fun saveEdits() {
        val recording = _state.value.recording ?: return
        val editSession = session ?: return
        viewModelScope.launch {
            setTask(StudioTask.Working("Saving", 0.0))
            runCatching { repository.saveAudio(recording, editSession.buffer) }
                .onSuccess {
                    _state.value = _state.value.copy(hasUnsavedEdits = false)
                    setTask(StudioTask.Finished("Saved"))
                    reloadQuality()
                }
                .onFailure {
                    setTask(
                        StudioTask.Failed(
                            "Could not save",
                            "There may not be enough space left. Free some up and try again.",
                        )
                    )
                }
        }
    }

    private fun refreshWaveform() {
        val editSession = session ?: return
        viewModelScope.launch {
            val current = _state.value
            val visible = (current.totalFrames / current.zoom).toInt().coerceAtLeast(1)
            val from = ((current.totalFrames - visible) * current.scrollFraction).toInt()
                .coerceIn(0, (current.totalFrames - visible).coerceAtLeast(0))
            val peaks = withContext(Dispatchers.Default) {
                // Only the visible range is walked, so zooming into a long recording costs the
                // same as zooming into a short one.
                WaveformPeaks.extractRange(editSession.buffer, from, from + visible, WAVEFORM_BUCKETS)
            }
            _state.value = _state.value.copy(peaks = peaks)
        }
    }

    // ---- enhancement ---------------------------------------------------------------------

    fun selectPreset(preset: StudioPreset?) {
        _state.value = _state.value.copy(selectedPreset = preset)
        rememberChoices()
    }

    fun selectVoiceStyle(style: VoiceStyle) {
        _state.value = _state.value.copy(selectedVoiceStyle = style)
        rememberChoices()
    }

    fun selectAmbience(profile: AmbienceProfile) {
        _state.value = _state.value.copy(selectedAmbience = profile, ambienceOverride = null)
        rememberChoices()
    }

    fun adjustAmbience(settings: ReverbSettings) {
        _state.value = _state.value.copy(ambienceOverride = settings)
    }

    fun setAdvancedOpen(open: Boolean) {
        _state.value = _state.value.copy(advancedOpen = open)
        viewModelScope.launch { services.settings.setStudioAdvancedOpen(open) }
    }

    /**
     * One-touch Studio Enhance.
     *
     * Runs against the in-memory edit session so it is undoable like any other edit, and is only
     * written to disk when the user saves.
     */
    fun enhance() {
        val editSession = session ?: return
        val settings = _state.value.effectiveSettings ?: StudioPresets.CLEAN_VOICE.settings

        viewModelScope.launch {
            setTask(StudioTask.Working("Enhancing", 0.0))
            val audio = editSession.buffer
            val result = runCatching {
                withContext(Dispatchers.Default) {
                    ai.sajjil.audio.chain.EnhancementChain(audio.sampleRate).apply(audio, settings) { progress ->
                        setTask(StudioTask.Working("Enhancing", progress))
                    }
                }
            }.getOrElse {
                setTask(
                    StudioTask.Failed(
                        "Enhancement did not finish",
                        "The recording is unchanged. Try a different preset, or a shorter selection.",
                    )
                )
                return@launch
            }

            val (processed, report) = result
            editSession.replaceAll("Enhance", processed)
            afterEdit()

            setTask(
                StudioTask.Finished(
                    buildString {
                        append("Enhanced")
                        report.humFundamentalHz?.let { append(" · ${it.toInt()} Hz hum removed") }
                        if (report.clicksRepaired > 0) append(" · ${report.clicksRepaired} clicks repaired")
                        report.loudnessAfterLufs?.let {
                            append(" · ${String.format(java.util.Locale.US, "%.1f", it)} LUFS")
                        }
                        if (report.loudnessTargetOutOfReach) {
                            append(" · too quiet to reach the full target")
                        }
                    }
                )
            )
            reloadQuality()
        }
    }

    private fun reloadQuality() {
        val editSession = session ?: return
        viewModelScope.launch {
            val report = withContext(Dispatchers.Default) {
                ai.sajjil.audio.analysis.QualityAnalyzer(editSession.buffer.sampleRate)
                    .analyse(editSession.buffer)
            }
            _state.value = _state.value.copy(quality = report)
        }
    }

    private fun rememberChoices() {
        val recording = _state.value.recording ?: return
        viewModelScope.launch {
            repository.rememberStudioChoices(
                recording,
                _state.value.selectedPreset?.id,
                _state.value.selectedVoiceStyle.id,
                _state.value.selectedAmbience.id,
            )
        }
    }

    // ---- export --------------------------------------------------------------------------

    fun export(format: ExportFormat, quality: ExportQuality) {
        val recording = _state.value.recording ?: return
        viewModelScope.launch {
            setTask(StudioTask.Working("Exporting ${format.displayName}", 0.0))
            runCatching {
                // Whatever is on screen is what gets exported, saved or not — exporting an older
                // version of the audio than the user is looking at would be indefensible.
                session?.let { repository.saveAudio(recording, it.buffer) }
                repository.export(recording, format, quality) { progress ->
                    setTask(StudioTask.Working("Exporting ${format.displayName}", progress))
                }
            }.onSuccess { result ->
                _state.value = _state.value.copy(lastExport = result, hasUnsavedEdits = false)
                setTask(StudioTask.Finished("Exported as ${format.displayName}"))
            }.onFailure { error ->
                setTask(
                    StudioTask.Failed(
                        "Export did not finish",
                        (error as? ai.sajjil.app.audio.ExportException)?.userMessage
                            ?: "Something went wrong writing the file. Exporting as WAV will always work.",
                    )
                )
            }
        }
    }

    fun clearTask() {
        _state.value = _state.value.copy(task = StudioTask.Idle)
    }

    private fun setTask(task: StudioTask) {
        _state.value = _state.value.copy(task = task)
    }

    private companion object {
        /** Enough detail for a phone screen without walking the file more than once. */
        const val WAVEFORM_BUCKETS = 1200
    }

    class Factory(private val services: Services) : ViewModelProvider.Factory {
        @Suppress("UNCHECKED_CAST")
        override fun <T : ViewModel> create(modelClass: Class<T>): T =
            StudioViewModel(services) as T
    }
}
