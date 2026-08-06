package ai.sautiy.ui.components

import ai.sautiy.core.design.Motion
import ai.sautiy.ui.theme.SautiyMotion
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.LocalIndication
import androidx.compose.foundation.clickable
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.composed
import androidx.compose.ui.draw.scale
import androidx.compose.ui.semantics.Role

/**
 * Every tap answers — Phase Ω, directive 1.
 *
 * A control that does not change under the finger feels broken even when it works. The user has no
 * way to distinguish "the app received my tap and is thinking" from "the app missed my tap", and
 * the second guess makes them tap again — which is how a single action becomes two.
 *
 * So this is the only way a control becomes tappable in SAUTIY. It gives, in this order:
 *
 * 1. **An immediate scale change** — [PRESS_SCALE], applied on the *press*, not on the release, so
 *    the acknowledgement arrives before the work does. This is the whole point: the feedback is not
 *    a report that something happened, it is the confirmation that the tap landed.
 * 2. **Compose's own ripple**, which places the acknowledgement where the finger actually is.
 * 3. **A `Role` and a click label**, so the same control is announced properly by a screen reader.
 *    An interaction that is premium only for sighted users is not premium.
 *
 * The scale is deliberately small. 3% is felt rather than seen — a control that visibly shrinks
 * reads as a toy, and this has to survive being used for an hour. The duration is [Motion.FAST_MS],
 * the same tier as every other control feedback in the app, because inconsistent animation timing is
 * one of the things directive 6 names and the one nobody can point at.
 */
public object Press {
    /**
     * How far a control moves under a finger.
     *
     * 0.97 — felt, not watched. Chapter 6 forbids overshoot above 3%, and this stays inside that
     * on the way back as well as on the way down.
     */
    public const val PRESS_SCALE: Float = 0.97f

    /**
     * How far a large round control moves — the transport buttons.
     *
     * Two tiers rather than one, and this is a decision rather than the accident it started as: the
     * dock had 0.94 and everything else had 0.97, in two files, neither referring to the other. A
     * 3% press on a 76 dp record button is about 2 dp of travel and reads as nothing at all,
     * because the eye judges the *proportion of the shape* on something that large. 6% is what
     * makes the biggest target on screen feel like it was pressed.
     *
     * Anything that is not a round transport control uses [PRESS_SCALE]. There is no third tier.
     */
    public const val PRESS_SCALE_LARGE: Float = 0.94f

    /** Control feedback tier. The same one the meters and toggles use. */
    public const val DURATION_MS: Int = Motion.FAST_MS
}

/**
 * Makes a component tappable, with the press acknowledged before the work starts.
 *
 * Use this instead of `Modifier.clickable` for anything a user presses. The label is required rather
 * than optional: an unlabelled control is invisible to a screen reader, and there is no such thing
 * as a premium interaction that only works for some people.
 *
 * @param label what the control does, as a verb phrase. Announced, and used as the click label.
 * @param enabled when false the control neither responds nor animates, so "not now" is legible.
 */
public fun Modifier.pressable(
    label: String,
    enabled: Boolean = true,
    role: Role = Role.Button,
    onClick: () -> Unit,
): Modifier = composed {
    val interactions = remember { MutableInteractionSource() }
    val pressed by interactions.collectIsPressedAsState()
    // Animated rather than snapped: a step change reads as a glitch, and the eye reads a 140 ms
    // ease as the control yielding to the finger.
    val scale by animateFloatAsState(
        targetValue = if (pressed && enabled) Press.PRESS_SCALE else 1f,
        animationSpec = SautiyMotion.fast(),
        label = "press:$label",
    )

    this
        .scale(scale)
        .clickable(
            interactionSource = interactions,
            // The platform's own indication rather than a named Material one: it is stable
            // across Compose versions and it is what the user's device already does everywhere
            // else, which is the correct behaviour for something this fundamental.
            indication = LocalIndication.current,
            enabled = enabled,
            onClickLabel = label,
            role = role,
            onClick = onClick,
        )
}
