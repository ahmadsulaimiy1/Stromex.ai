package ai.sautiy.ui.workspace

import ai.sautiy.core.analysis.WaveformColumns
import ai.sautiy.core.audio.CaptureQuality
import ai.sautiy.core.codec.ExportFormat
import ai.sautiy.core.dsp.StudioPreset
import ai.sautiy.core.play.PlaybackSpeed
import ai.sautiy.core.workspace.Panel
import ai.sautiy.core.workspace.SautiyError
import ai.sautiy.core.workspace.TransportState
import ai.sautiy.core.workspace.WorkspaceAction
import androidx.compose.runtime.Immutable

/** One row of the layer strip. */
@Immutable
data class LayerRow(
    val id: String,
    val name: String,
    val muted: Boolean,
    val soloed: Boolean,
    val colourIndex: Int,
)

/** One row of the library panel. */
@Immutable
data class LibraryRow(
    val id: String,
    val title: String,
    val durationFrames: Long,
    val sampleRate: Int,
    val createdAtEpochMs: Long,
    val favourite: Boolean,
    val tags: List<String> = emptyList(),
)

/**
 * Everything the workspace draws, in one immutable value.
 *
 * Deliberately flat and already-resolved: the composable does no computation, no formatting
 * decisions and no policy. Anything that required a decision was decided in `sautiy-core` and
 * arrives here as a fact. That is what keeps the draw phase inside the frame budget of
 * chapter 1.6 while capture runs on another thread.
 */
@Immutable
data class WorkspaceUiState(
    val transport: TransportState = TransportState.IDLE,
    val projectName: String = "Untitled",
    val quality: CaptureQuality = CaptureQuality.STUDIO,
    val sampleRate: Int = 48_000,

    val hasAudio: Boolean = false,
    val recordedFrames: Long = 0,
    val playheadFrame: Long = 0,
    val totalFrames: Long = 0,

    val waveform: WaveformColumns? = null,
    val selection: LongRange? = null,
    val markerFrames: List<Long> = emptyList(),

    val layers: List<LayerRow> = emptyList(),
    val selectedLayerId: String? = null,

    val peakDb: Double = -120.0,
    val rmsDb: Double = -120.0,
    val hasClipped: Boolean = false,
    val qualityScore: Int = 100,
    val qualityReason: String = "",
    val noiseFloorDb: Double = -120.0,

    val secondsRemaining: Long = 0,
    val storageCritical: Boolean = false,
    val monitoring: Boolean = false,

    val speed: PlaybackSpeed = PlaybackSpeed.NORMAL,
    val looping: Boolean = false,
    val comparingOriginal: Boolean = false,

    val openPanel: Panel? = null,
    val contextActions: List<WorkspaceAction> = emptyList(),

    val canUndo: Boolean = false,
    val canRedo: Boolean = false,
    val historySteps: List<String> = emptyList(),
    val historyIndex: Int = 0,

    val appliedPreset: StudioPreset? = null,
    val exportFormat: ExportFormat = ExportFormat.WAV,
    val exportProgress: Double? = null,

    val library: List<LibraryRow> = emptyList(),
    val librarySearch: String = "",

    val error: SautiyError? = null,
) {
    val qualityName: String get() = quality.displayName
}

/**
 * Every callback the workspace can raise.
 *
 * Passed as one object rather than as twenty parameters so that adding a capability does not
 * ripple through every call site, and so the whole surface of what the UI can ask for is
 * readable in one place.
 */
@Immutable
data class WorkspaceActions(
    val onRecordOrStop: () -> Unit = {},
    val onPlayOrPause: () -> Unit = {},
    val onRewind: () -> Unit = {},
    val onToggleMonitor: () -> Unit = {},
    val onCommit: () -> Unit = {},

    val onSeek: (Long) -> Unit = {},
    val onSelectionChanged: (LongRange?) -> Unit = {},
    val onZoom: (Float) -> Unit = {},

    val onContextAction: (WorkspaceAction) -> Unit = {},
    val onDismissPanel: () -> Unit = {},
    val onOpenPanel: (Panel) -> Unit = {},

    val onSelectLayer: (String) -> Unit = {},
    val onAddLayer: () -> Unit = {},

    val onOpenLibrary: () -> Unit = {},
    val onOpenSettings: () -> Unit = {},

    val onApplyPreset: (StudioPreset) -> Unit = {},
    val onRevertPreset: () -> Unit = {},
    val onChooseExportFormat: (ExportFormat) -> Unit = {},
    val onExport: () -> Unit = {},
    val onShare: () -> Unit = {},

    val onSetSpeed: (PlaybackSpeed) -> Unit = {},
    val onToggleLoop: () -> Unit = {},
    val onToggleCompare: () -> Unit = {},

    val onTravelHistory: (Int) -> Unit = {},
    val onOpenRecording: (String) -> Unit = {},
    val onToggleFavourite: (String) -> Unit = {},
    val onSearchLibrary: (String) -> Unit = {},

    val onDismissError: () -> Unit = {},
    val onErrorRemedy: (SautiyError) -> Unit = {},
)
