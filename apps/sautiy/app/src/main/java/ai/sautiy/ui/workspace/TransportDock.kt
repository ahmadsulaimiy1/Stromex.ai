package ai.sautiy.ui.workspace

import ai.sautiy.core.workspace.TransportState
import ai.sautiy.ui.icons.SautiyIcons
import ai.sautiy.ui.theme.SautiyMotion
import ai.sautiy.ui.theme.SautiySpace
import ai.sautiy.ui.theme.SautiyTheme
import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.sizeIn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Icon
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp

/**
 * The transport dock — Editorial Bible chapter 4.2.
 *
 * **Five slots. Immovable. For the life of the product.**
 *
 * The contents of this row never change with state. Play becomes pause and record becomes stop,
 * because those are the same control in two states, but nothing ever moves, appears or
 * disappears. A user who has learned that the red circle sits under their thumb is never made
 * wrong — which is the entire reason the adaptive part of the interface is somewhere else.
 */
@Composable
fun TransportDock(
    transport: TransportState,
    monitoring: Boolean,
    canExport: Boolean,
    modifier: Modifier = Modifier,
    onMonitor: () -> Unit,
    onRewind: () -> Unit,
    onRecord: () -> Unit,
    onPlay: () -> Unit,
    onCommit: () -> Unit,
) {
    val colours = SautiyTheme.colours

    Row(
        modifier = modifier
            .fillMaxWidth()
            .padding(horizontal = SautiySpace.pageInset, vertical = SautiySpace.l),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        // Slot 1 — monitor.
        TransportButton(
            icon = SautiyIcons.Monitor,
            description = "Listen to the input while recording",
            tint = if (monitoring) colours.signal else colours.textSecondary,
            onClick = onMonitor,
        )

        // Slot 2 — back to the previous marker.
        TransportButton(
            icon = SautiyIcons.Rewind,
            description = "Back to the previous marker",
            tint = colours.textSecondary,
            onClick = onRewind,
        )

        // Slot 3 — the primary action. The largest object on the display, centred in the
        // natural thumb zone (chapter 3.2.4).
        RecordButton(transport = transport, onClick = onRecord)

        // Slot 4 — play/pause.
        TransportButton(
            icon = if (transport == TransportState.PLAYING) SautiyIcons.Pause else SautiyIcons.Play,
            description = if (transport == TransportState.PLAYING) "Pause playback" else "Play",
            tint = colours.textPrimary,
            onClick = onPlay,
        )

        // Slot 5 — commit. Its label states what happens next (chapter 4.7).
        CommitButton(enabled = canExport, onClick = onCommit)
    }
}

/**
 * The record control.
 *
 * Ember is reserved for this and for the recording indicator, and for nothing else in the
 * product (chapter 2.3.4). When a user sees this red, the device is capturing.
 *
 * The shape carries the state as well as the colour: a disc while stopped, a rounded square
 * while recording. Colour alone would fail chapter 2.3.4 clause 2 and would be invisible to a
 * user with deuteranopia.
 */
@Composable
private fun RecordButton(transport: TransportState, onClick: () -> Unit) {
    val colours = SautiyTheme.colours
    val recording = transport == TransportState.RECORDING
    val paused = transport == TransportState.RECORDING_PAUSED

    val interaction = remember { MutableInteractionSource() }
    val pressed by interaction.collectIsPressedAsState()
    val pressScale by animateFloatAsState(
        targetValue = if (pressed) 0.94f else 1f,
        animationSpec = SautiyMotion.fast(),
        label = "recordPress",
    )

    // A slow breath while recording, so the state is legible from across a room without the
    // motion ever drawing attention (chapter 2.6: no bounce, no rotation, nothing decorative).
    val breathing = rememberInfiniteTransition(label = "recordBreath")
    val breath by breathing.animateFloat(
        initialValue = 1f,
        targetValue = if (recording) 1.06f else 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(1_400, easing = SautiyMotion.Standard),
            repeatMode = androidx.compose.animation.core.RepeatMode.Reverse,
        ),
        label = "breath",
    )

    val fill by animateColorAsState(
        targetValue = when {
            recording -> colours.ember
            paused -> colours.ember.copy(alpha = 0.55f)
            else -> colours.ember
        },
        animationSpec = SautiyMotion.standard(),
        label = "recordFill",
    )

    val cornerPercent by animateFloatAsState(
        targetValue = if (recording || paused) 28f else 50f,
        animationSpec = SautiyMotion.standard(),
        label = "recordCorner",
    )

    Box(
        modifier = Modifier
            .size(RECORD_DIAMETER)
            .scale(pressScale * breath)
            .border(width = 2.dp, color = colours.textPrimary.copy(alpha = 0.85f), shape = CircleShape)
            .padding(5.dp)
            .background(
                color = fill,
                shape = androidx.compose.foundation.shape.RoundedCornerShape(percent = cornerPercent.toInt()),
            )
            .clickableTarget(
                interactionSource = interaction,
                description = when {
                    recording -> "Stop recording"
                    paused -> "Resume recording"
                    else -> "Start recording"
                },
                onClick = onClick,
            ),
    )
}

@Composable
private fun CommitButton(enabled: Boolean, onClick: () -> Unit) {
    val colours = SautiyTheme.colours
    val interaction = remember { MutableInteractionSource() }
    val pressed by interaction.collectIsPressedAsState()
    val scale by animateFloatAsState(
        targetValue = if (pressed) 0.94f else 1f,
        animationSpec = SautiyMotion.fast(),
        label = "commitPress",
    )

    Box(
        modifier = Modifier
            .size(SECONDARY_DIAMETER)
            .scale(scale)
            .background(
                color = if (enabled) colours.commit else colours.surfaceRaised,
                shape = CircleShape,
            )
            .clickableTarget(
                interactionSource = interaction,
                description = "Export this recording",
                enabled = enabled,
                onClick = onClick,
            ),
        contentAlignment = Alignment.Center,
    ) {
        Icon(
            imageVector = SautiyIcons.Commit,
            contentDescription = null,
            tint = if (enabled) colours.onCommit else colours.textDisabled,
            modifier = Modifier.size(22.dp),
        )
    }
}

@Composable
private fun TransportButton(
    icon: ImageVector,
    description: String,
    tint: Color,
    onClick: () -> Unit,
) {
    val interaction = remember { MutableInteractionSource() }
    val pressed by interaction.collectIsPressedAsState()
    val scale by animateFloatAsState(
        targetValue = if (pressed) 0.9f else 1f,
        animationSpec = SautiyMotion.fast(),
        label = "transportPress",
    )

    Box(
        modifier = Modifier
            // Chapter 3.2.4 and 17: 48 dp minimum, whatever the icon's own size.
            .sizeIn(minWidth = SautiySpace.minTouchTarget, minHeight = SautiySpace.minTouchTarget)
            .size(SECONDARY_DIAMETER)
            .scale(scale)
            .clickableTarget(interactionSource = interaction, description = description, onClick = onClick),
        contentAlignment = Alignment.Center,
    ) {
        Icon(
            imageVector = icon,
            contentDescription = null,
            tint = tint,
            modifier = Modifier.size(26.dp),
        )
    }
}

/**
 * A tap target with the accessibility contract already satisfied: a role, a spoken description,
 * a 48 dp minimum, and no ripple — chapter 2.6 permits motion that explains, and a ripple
 * spreading across a dark studio surface explains nothing.
 */
private fun Modifier.clickableTarget(
    interactionSource: MutableInteractionSource,
    description: String,
    enabled: Boolean = true,
    onClick: () -> Unit,
): Modifier = this
    .sizeIn(minWidth = SautiySpace.minTouchTarget, minHeight = SautiySpace.minTouchTarget)
    .clickable(
        interactionSource = interactionSource,
        indication = null,
        enabled = enabled,
        role = Role.Button,
        onClickLabel = description,
        onClick = onClick,
    )
    .semantics { contentDescription = description }

private val RECORD_DIAMETER: Dp = 76.dp
private val SECONDARY_DIAMETER: Dp = 52.dp
