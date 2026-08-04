package ai.sajjil.app.ui.record

import ai.sajjil.app.Services
import ai.sajjil.app.audio.RecorderError
import ai.sajjil.app.ui.Format
import ai.sajjil.app.ui.components.InputLevelMeter
import ai.sajjil.app.ui.components.RecordButton
import ai.sajjil.app.ui.components.CircularIconButton
import ai.sajjil.app.ui.theme.Radius
import ai.sajjil.app.ui.theme.Space
import ai.sajjil.app.ui.theme.TimerTextStyle
import ai.sajjil.app.ui.theme.sajjilColors
import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.provider.Settings
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.Pause
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Tune
import androidx.compose.material3.Button
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import kotlinx.coroutines.delay

/**
 * The Record screen.
 *
 * Everything here answers one of five questions, and nothing else is present: how long have I been
 * recording, how loud am I, is the level good, how much room is left, and where do I press. The
 * record button is the only large control on the screen.
 */
@Composable
fun RecordScreen(
    services: Services,
    onOpenInStudio: (Long) -> Unit,
    onOpenLibrary: () -> Unit,
) {
    val viewModel: RecordViewModel = viewModel(factory = RecordViewModel.Factory(services))
    val state by viewModel.state.collectAsStateWithLifecycle()
    val outOfSpace by viewModel.outOfSpace.collectAsStateWithLifecycle()
    val context = LocalContext.current
    val view = LocalView.current

    var hasPermission by remember {
        mutableStateOf(
            ContextCompat.checkSelfPermission(context, Manifest.permission.RECORD_AUDIO) ==
                PackageManager.PERMISSION_GRANTED
        )
    }
    var permissionRefused by remember { mutableStateOf(false) }

    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        hasPermission = granted
        permissionRefused = !granted
        if (granted) viewModel.onRecordPressed()
    }

    // The screen stays awake while recording. Watching a timer go dark mid-take and wondering
    // whether the recording survived is a genuinely stressful experience.
    LaunchedEffect(state.isActive) {
        view.keepScreenOn = state.isActive
    }

    // A live waveform needs a redraw cadence of its own; the level flow alone updates too
    // irregularly to look smooth.
    var waveformTick by remember { mutableStateOf(0) }
    LaunchedEffect(state.isActive) {
        while (state.isActive) {
            delay(50)
            waveformTick++
        }
    }

    LaunchedEffect(Unit) { viewModel.refreshSpace() }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = Space.pageHorizontal),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Spacer(Modifier.height(Space.lg))

        StorageBanner(
            remainingSeconds = state.remainingSeconds,
            sampleRate = state.sampleRate,
            channelCount = state.channelCount,
        )

        Spacer(Modifier.weight(1f))

        Text(
            text = Format.timer(state.elapsedMillis),
            style = TimerTextStyle,
            color = if (state.isActive) {
                MaterialTheme.colorScheme.onSurface
            } else {
                sajjilColors.onSurfaceFaint
            },
            modifier = Modifier.semantics {
                liveRegion = LiveRegionMode.Polite
                contentDescription = if (state.isActive) {
                    "Recording, ${Format.spokenDuration(state.elapsedMillis)}"
                } else {
                    "Ready to record"
                }
            },
        )

        Spacer(Modifier.height(Space.lg))

        LiveWaveformStrip(
            samples = remember(waveformTick) { viewModel.waveform.snapshot() },
            active = state.isActive && !state.isPaused,
        )

        Spacer(Modifier.height(Space.lg))

        InputLevelMeter(
            rms = state.levels.rms,
            peak = state.levels.peak,
            isClipping = state.levels.isClipping,
        )

        Spacer(Modifier.height(Space.sm))

        LiveQualityLine(quality = state.liveQuality)

        Spacer(Modifier.weight(1f))

        state.error?.let { error ->
            ErrorNotice(error = error, onOpenSettings = { context.openAppSettings() })
            Spacer(Modifier.height(Space.md))
        }

        if (permissionRefused && !hasPermission) {
            PermissionNotice(onOpenSettings = { context.openAppSettings() })
            Spacer(Modifier.height(Space.md))
        }

        if (outOfSpace) {
            OutOfSpaceNotice(onDismiss = viewModel::dismissOutOfSpace, onOpenLibrary = onOpenLibrary)
            Spacer(Modifier.height(Space.md))
        }

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceEvenly,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            // Pause only appears once there is something to pause, so an idle screen has exactly
            // one control on it.
            Box(Modifier.size(Space.minimumTouchTarget)) {
                androidx.compose.animation.AnimatedVisibility(
                    visible = state.isActive,
                    enter = fadeIn(),
                    exit = fadeOut(),
                ) {
                    CircularIconButton(
                        icon = if (state.isPaused) Icons.Filled.PlayArrow else Icons.Filled.Pause,
                        description = if (state.isPaused) "Resume recording" else "Pause recording",
                        onClick = viewModel::onPauseResumePressed,
                        tint = sajjilColors.onSurfaceMuted,
                    )
                }
            }

            RecordButton(
                isRecording = state.isActive,
                isPaused = state.isPaused,
                onClick = {
                    if (hasPermission) {
                        viewModel.onRecordPressed()
                    } else {
                        permissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
                    }
                },
            )

            Box(Modifier.size(Space.minimumTouchTarget)) {
                androidx.compose.animation.AnimatedVisibility(
                    visible = state.justFinishedId != null,
                    enter = fadeIn(),
                    exit = fadeOut(),
                ) {
                    CircularIconButton(
                        icon = Icons.Filled.Tune,
                        description = "Open the recording in Studio",
                        onClick = { state.justFinishedId?.let(onOpenInStudio) },
                        tint = MaterialTheme.colorScheme.primary,
                    )
                }
            }
        }

        Spacer(Modifier.height(Space.md))

        // The moment a recording finishes it is already saved and playable. This is an offer, not
        // a processing step, and dismissing it costs nothing.
        AnimatedVisibility(visible = state.justFinishedId != null && !state.isActive) {
            JustFinishedRow(
                onOpen = { state.justFinishedId?.let(onOpenInStudio) },
                onDismiss = viewModel::dismissFinished,
            )
        }

        Spacer(Modifier.height(Space.lg))
    }
}

/** The rolling level history, drawn as a mirrored bar trace. */
@Composable
private fun LiveWaveformStrip(
    samples: FloatArray,
    active: Boolean,
    modifier: Modifier = Modifier,
) {
    val colors = sajjilColors
    Box(
        modifier = modifier
            .fillMaxWidth()
            .height(140.dp)
            .background(colors.surfaceElevated, RoundedCornerShape(Radius.medium))
            .semantics {
                contentDescription = if (active) "Live audio waveform" else "Waveform, not recording"
            },
    ) {
        Canvas(modifier = Modifier.fillMaxSize().padding(Space.sm)) {
            val centreY = size.height / 2f
            if (samples.isEmpty()) return@Canvas
            val barWidth = size.width / samples.size
            for (i in samples.indices) {
                val amplitude = samples[i].coerceIn(0f, 1f)
                val half = amplitude * centreY * 0.92f
                val x = i * barWidth + barWidth / 2f
                // The newest samples are on the right and brightest, which gives the trace a
                // direction without needing an arrow or a label.
                val freshness = i.toFloat() / samples.size
                drawLine(
                    color = if (active) {
                        colors.waveformBody.copy(alpha = 0.35f + 0.65f * freshness)
                    } else {
                        colors.onSurfaceFaint.copy(alpha = 0.3f)
                    },
                    start = Offset(x, centreY - half),
                    end = Offset(x, centreY + half),
                    strokeWidth = (barWidth * 0.6f).coerceAtLeast(1.5f),
                )
            }
            drawLine(
                color = colors.onSurfaceFaint.copy(alpha = 0.25f),
                start = Offset(0f, centreY),
                end = Offset(size.width, centreY),
                strokeWidth = 1f,
            )
        }
    }
}

@Composable
private fun LiveQualityLine(quality: LiveQuality) {
    val colors = sajjilColors
    val tint = when (quality) {
        LiveQuality.CLIPPING, LiveQuality.TOO_QUIET -> colors.problem
        LiveQuality.HOT, LiveQuality.LOW -> colors.caution
        LiveQuality.GOOD -> colors.good
        LiveQuality.IDLE -> colors.onSurfaceMuted
    }
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .semantics {
                liveRegion = LiveRegionMode.Polite
                contentDescription = "${quality.label}. ${quality.detail}"
            },
        horizontalArrangement = Arrangement.Center,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Box(
            Modifier
                .size(8.dp)
                .background(tint, RoundedCornerShape(4.dp))
        )
        Spacer(Modifier.width(Space.sm))
        Text(
            text = quality.label,
            style = MaterialTheme.typography.labelLarge,
            color = tint,
        )
        Spacer(Modifier.width(Space.sm))
        Text(
            text = quality.detail,
            style = MaterialTheme.typography.bodySmall,
            color = colors.onSurfaceMuted,
        )
    }
}

@Composable
private fun StorageBanner(remainingSeconds: Long, sampleRate: Int, channelCount: Int) {
    val colors = sajjilColors
    val label = Format.remainingRecordingTime(remainingSeconds)
    val quality = "${sampleRate / 1000} kHz ${if (channelCount == 1) "mono" else "stereo"}"

    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(
            text = quality,
            style = MaterialTheme.typography.labelMedium,
            color = colors.onSurfaceMuted,
        )
        Text(
            text = label,
            style = MaterialTheme.typography.labelMedium,
            // Turns amber only when the number starts to matter.
            color = if (remainingSeconds < 600) colors.caution else colors.onSurfaceMuted,
        )
    }
}

/**
 * An error notice.
 *
 * Says what happened, why, and what to do about it. No error code, no exception text — those tell
 * the user nothing they can act on.
 */
@Composable
private fun ErrorNotice(error: RecorderError, onOpenSettings: () -> Unit) {
    val (title, body, action) = when (error) {
        RecorderError.MicrophoneUnavailable -> Triple(
            "The microphone is busy",
            "Another app is using it. Close that app and try again.",
            null,
        )
        RecorderError.MicrophoneLost -> Triple(
            "The microphone disconnected",
            "Recording stopped and everything captured so far was saved.",
            null,
        )
        RecorderError.UnsupportedFormat -> Triple(
            "This device cannot record at that quality",
            "Choose a lower sample rate in Settings and try again.",
            "Open settings" to onOpenSettings,
        )
        RecorderError.OutOfSpace -> Triple(
            "The device ran out of space",
            "Recording stopped and what was captured has been saved. Free up space to continue.",
            null,
        )
        is RecorderError.CannotWrite -> Triple(
            "SAJJIL could not save the recording",
            "The storage could not be written to. Free up some space and try again.",
            null,
        )
    }
    Notice(title = title, body = body, action = action, tint = sajjilColors.problem)
}

@Composable
private fun PermissionNotice(onOpenSettings: () -> Unit) {
    Notice(
        title = "SAJJIL needs the microphone",
        body = "Recording is what this app does. Nothing leaves this device unless you export it yourself.",
        action = "Open settings" to onOpenSettings,
        tint = sajjilColors.caution,
        icon = Icons.Filled.Mic,
    )
}

@Composable
private fun OutOfSpaceNotice(onDismiss: () -> Unit, onOpenLibrary: () -> Unit) {
    Notice(
        title = "Not enough space to record",
        body = "There is less than a minute of recording room left. Deleting or exporting a few recordings will free some up.",
        action = "Open Library" to onOpenLibrary,
        secondaryAction = "Dismiss" to onDismiss,
        tint = sajjilColors.problem,
    )
}

@Composable
private fun Notice(
    title: String,
    body: String,
    action: Pair<String, () -> Unit>?,
    tint: androidx.compose.ui.graphics.Color,
    secondaryAction: Pair<String, () -> Unit>? = null,
    icon: androidx.compose.ui.graphics.vector.ImageVector? = null,
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(tint.copy(alpha = 0.10f), RoundedCornerShape(Radius.medium))
            .padding(Space.md),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            if (icon != null) {
                Icon(icon, contentDescription = null, tint = tint, modifier = Modifier.size(20.dp))
                Spacer(Modifier.width(Space.sm))
            }
            Text(text = title, style = MaterialTheme.typography.titleMedium, color = tint)
        }
        Spacer(Modifier.height(Space.xs))
        Text(
            text = body,
            style = MaterialTheme.typography.bodyMedium,
            color = sajjilColors.onSurfaceMuted,
        )
        if (action != null || secondaryAction != null) {
            Spacer(Modifier.height(Space.sm))
            Row {
                action?.let { (label, onClick) ->
                    Button(onClick = onClick) { Text(label) }
                }
                secondaryAction?.let { (label, onClick) ->
                    Spacer(Modifier.width(Space.sm))
                    TextButton(onClick = onClick) { Text(label) }
                }
            }
        }
    }
}

@Composable
private fun JustFinishedRow(onOpen: () -> Unit, onDismiss: () -> Unit) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(sajjilColors.surfaceElevated, RoundedCornerShape(Radius.medium))
            .padding(Space.md),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween,
    ) {
        Text(
            text = "Saved to your Library",
            style = MaterialTheme.typography.bodyMedium,
            color = sajjilColors.onSurfaceMuted,
            modifier = Modifier.weight(1f),
            textAlign = TextAlign.Start,
        )
        TextButton(onClick = onDismiss) { Text("Dismiss") }
        Spacer(Modifier.width(Space.xs))
        Button(onClick = onOpen) { Text("Open in Studio") }
    }
}

private fun android.content.Context.openAppSettings() {
    startActivity(
        Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
            data = Uri.fromParts("package", packageName, null)
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        }
    )
}
