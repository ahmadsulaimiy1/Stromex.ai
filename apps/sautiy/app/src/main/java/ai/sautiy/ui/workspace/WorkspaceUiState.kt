package ai.sautiy.ui.workspace

import ai.sautiy.core.analysis.WaveformColumns
import ai.sautiy.core.audio.CaptureQuality
import ai.sautiy.core.codec.ExportFormat
import ai.sautiy.core.dsp.AcousticSpace
import ai.sautiy.core.dsp.AutoStudio
import ai.sautiy.core.dsp.ListenerNote
import ai.sautiy.core.dsp.RecitationProfile
import ai.sautiy.core.dsp.Restraint
import ai.sautiy.core.dsp.VoiceDna
import ai.sautiy.core.record.RecordingAdvisor
import ai.sautiy.core.dsp.VoiceOutcome
import ai.sautiy.core.dsp.AmbienceSettings
import ai.sautiy.core.dsp.VoiceRefinement
import ai.sautiy.core.dsp.VoiceStudioSettings
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
    /**
     * Channels in the material being worked on, which is not always the capture setting.
     *
     * Opening a stereo recording while the capture quality is mono used to play and export it
     * as mono, silently discarding one side.
     */
    val channelCount: Int = 1,

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

    /** Null until storage has actually been measured, so the readout can be absent rather than wrong. */
    val secondsRemaining: Long? = null,
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

    /** The preset currently being auditioned, when the listening cycle is running. */
    val auditioning: VoiceOutcome? = null,
    /** The preset in force, named for the job it does. Null once controls have been hand-moved. */
    val appliedOutcome: VoiceOutcome? = null,
    /** The acoustic environment chosen deliberately in layer two, if any. */
    val appliedSpace: AcousticSpace? = null,
    /** The recitation profile in force, if the Recitation Studio was used. */
    val appliedRecitation: RecitationProfile? = null,
    /** What one tap recommended, awaiting acceptance. */
    val recommendation: AutoStudio.Recommendation? = null,
    /** Whether the detailed controls are shown. Hidden by default. */
    val advanced: Boolean = false,
    /**
     * Guidance about the live input, or silence.
     *
     * Silence is the normal case and the intended one: this speaks when something is wrong and
     * says nothing when it is not, so what it says is read rather than ignored.
     */
    val guidance: RecordingAdvisor.Guidance = RecordingAdvisor.Guidance.NONE,
    /** How much work the current recording actually needs, once it has been looked at. */
    val restraint: Restraint? = null,
    /** The user's own saved sounds, most-reached-for first. */
    val savedSounds: List<VoiceDna> = emptyList(),
    /** Which saved sound is in force, if one was recalled and nothing has been changed since. */
    val activeSoundId: String? = null,
    /** What listeners have said about the applied preset, or null when too few have said anything. */
    val listeningEvidence: String? = null,
    /**
     * True when the take that just finished was cleaned up without being asked.
     *
     * Shown as one line, once, with the way to undo it. The first thirty seconds of this app are
     * open, Record, speak, Stop, Play — and until this existed, the sound at "Play" was a phone
     * recording of a room, which is what every other recorder gives you. Nothing worth reacting to
     * at the only moment a first-time user decides whether this is different.
     */
    val autoImproved: Boolean = false,
    /** The live voice, including any hand edits made after a space was chosen. */
    val voice: VoiceStudioSettings? = null,
    /**
     * Stages the preview cannot run, named so the panel can say so.
     *
     * Noise reduction needs a profile from the whole recording and loudness needs the finished
     * programme; neither can exist under a playback callback. Saying which is missing is the
     * difference between an honest preview and one that quietly differs from the export.
     */
    val deferredStages: List<String> = emptyList(),

    val exportFormat: ExportFormat = ExportFormat.WAV,
    val exportProgress: Double? = null,
    /** Set once an export has written a file, so it can be shared without exporting twice. */
    val lastExportPath: String? = null,
    /** Where the last export landed, named the way the user would name it. */
    val savedTo: String? = null,
    /** True when the exported audio reached full scale, which the user is told rather than not. */
    val exportClipped: Boolean = false,

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

    val onContextAction: (WorkspaceAction) -> Unit = {},
    val onDismissPanel: () -> Unit = {},
    val onOpenPanel: (Panel) -> Unit = {},

    val onSelectLayer: (String) -> Unit = {},
    val onAddLayer: () -> Unit = {},

    val onOpenLibrary: () -> Unit = {},

    val onRevertPreset: () -> Unit = {},
    val onAmbienceChanged: (AmbienceSettings) -> Unit = {},
    /** Natural through Immersive, as one continuous control. */
    val onCharacterChanged: (Double) -> Unit = {},
    val onChooseSpace: (AcousticSpace) -> Unit = {},
    val onChooseRecitation: (RecitationProfile) -> Unit = {},
    /** One tap: analyse, recommend an outcome and an intensity, and say why. */
    val onAutoStudio: () -> Unit = {},
    val onAcceptRecommendation: () -> Unit = {},
    val onDismissRecommendation: () -> Unit = {},
    val onToggleAdvanced: () -> Unit = {},
    /** Save everything currently set up as one of the user's own sounds. */
    val onSaveSound: (String) -> Unit = {},
    /** One tap: the complete sound back, exactly as it was saved. */
    val onRecallSound: (String) -> Unit = {},
    val onRenameSound: (String, String) -> Unit = { _, _ -> },
    val onDeleteSound: (String) -> Unit = {},
    /** Play one passage through every space in turn — the only honest way to choose one. */
    val onAuditionSpaces: () -> Unit = {},
    val onStopAudition: () -> Unit = {},
    val onApplyOutcome: (VoiceOutcome) -> Unit = {},
    /** What a listener said about what they are hearing. Seven words, each a defined change. */
    val onListenerNote: (ListenerNote) -> Unit = {},
    val onRefinementChanged: (VoiceRefinement) -> Unit = {},
    val onChooseExportFormat: (ExportFormat) -> Unit = {},
    val onExport: () -> Unit = {},
    val onShare: () -> Unit = {},

    val onSetSpeed: (PlaybackSpeed) -> Unit = {},
    val onToggleLoop: () -> Unit = {},
    val onToggleCompare: () -> Unit = {},

    val onTravelHistory: (Int) -> Unit = {},
    val onOpenRecording: (String) -> Unit = {},
    val onToggleFavourite: (String) -> Unit = {},
    val onRename: (String, String) -> Unit = { _, _ -> },
    val onDelete: (String) -> Unit = {},
    val onSearchLibrary: (String) -> Unit = {},

    val onDismissError: () -> Unit = {},
)
