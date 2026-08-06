package ai.sautiy.ui.workspace

import ai.sautiy.core.analysis.Loudness
import ai.sautiy.core.codec.Encoders
import ai.sautiy.core.dsp.AcousticSpace
import ai.sautiy.core.dsp.RecitationProfile
import ai.sautiy.core.dsp.VoiceCharacter
import ai.sautiy.core.dsp.ListenerNote
import ai.sautiy.core.dsp.VoiceOutcome
import ai.sautiy.core.dsp.AmbienceSettings
import ai.sautiy.core.dsp.VoiceRefinement
import ai.sautiy.core.play.PlaybackSpeed
import ai.sautiy.core.workspace.Panel
import ai.sautiy.ui.components.QualityGauge
import ai.sautiy.ui.icons.SautiyIcons
import ai.sautiy.ui.theme.SautiyShapes
import ai.sautiy.ui.theme.SautiySpace
import ai.sautiy.ui.theme.SautiyTheme
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.sizeIn
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.TextField
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp

/**
 * Routes an open [Panel] to its content — Editorial Bible chapter 4.4.
 *
 * Every panel shares one scaffold, so the header, the drag affordance, the dismissal routes and
 * the insets are identical across all twelve and cannot drift apart. The panel bodies below are
 * therefore only ever *content*, never chrome.
 */
@Composable
fun PanelHost(
    panel: Panel,
    state: WorkspaceUiState,
    actions: WorkspaceActions,
) {
    PanelScaffold(title = panelTitle(panel), onDismiss = actions.onDismissPanel) {
        when (panel) {
            Panel.STUDIO -> StudioPanel(state, actions)
            Panel.EXPORT -> ExportPanel(state, actions)
            Panel.ANALYSIS -> AnalysisPanel(state)
            Panel.LIBRARY -> LibraryPanel(state, actions)
            Panel.HISTORY -> HistoryPanel(state, actions)
            Panel.LAYERS -> LayersPanel(state, actions)
            Panel.MARKERS -> MarkersPanel(state, actions)
            Panel.EQUALISER -> EqualiserPanel(state, actions)
            Panel.DYNAMICS -> DynamicsPanel(state)
            Panel.SPACE -> SpacePanel(state, actions)
            Panel.TRANSCRIPT -> TranscriptPanel()
            Panel.PROJECT -> ProjectPanel(state)
        }
    }
}

private fun panelTitle(panel: Panel): String = when (panel) {
    Panel.STUDIO -> "Studio"
    Panel.EQUALISER -> "Voice"
    Panel.DYNAMICS -> "Dynamics"
    Panel.SPACE -> "Space"
    Panel.ANALYSIS -> "Analysis"
    Panel.LAYERS -> "Layers"
    Panel.MARKERS -> "Markers"
    Panel.HISTORY -> "History"
    Panel.TRANSCRIPT -> "Transcript"
    Panel.LIBRARY -> "Library"
    Panel.PROJECT -> "Project"
    Panel.EXPORT -> "Export"
}

/**
 * The shared panel chrome.
 *
 * The drag handle is not decoration: it is one of the four dismissal routes chapter 4.4.1
 * requires, and it is the one a thumb finds without looking.
 */
@Composable
private fun PanelScaffold(
    title: String,
    onDismiss: () -> Unit,
    content: @Composable () -> Unit,
) {
    val colours = SautiyTheme.colours

    Column(modifier = Modifier.fillMaxWidth()) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .padding(top = SautiySpace.m, bottom = SautiySpace.xs),
            contentAlignment = Alignment.Center,
        ) {
            Box(
                modifier = Modifier
                    .width(36.dp)
                    .height(4.dp)
                    .background(colours.border, RoundedCornerShape(percent = 50)),
            )
        }

        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = SautiySpace.pageInset, vertical = SautiySpace.s),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                text = title,
                style = SautiyTheme.type.titleLarge,
                color = colours.textPrimary,
                modifier = Modifier.weight(1f),
            )
            Box(
                modifier = Modifier
                    .size(SautiySpace.minTouchTarget)
                    .clickable(onClickLabel = "Close panel", role = Role.Button, onClick = onDismiss),
                contentAlignment = Alignment.Center,
            ) {
                Icon(
                    imageVector = SautiyIcons.Close,
                    contentDescription = null,
                    tint = colours.textSecondary,
                    modifier = Modifier.size(20.dp),
                )
            }
        }

        Box(modifier = Modifier.padding(horizontal = SautiySpace.pageInset)) { content() }
    }
}

/**
 * The Studio panel — the twelve spaces, and the two buttons that skip choosing one.
 *
 * Named for places rather than processes, because a person knows they recorded a lecture and
 * does not know they want 3:1 at −18 dBFS with a 6 dB knee. Choosing a card applies it
 * immediately: to what is playing, and to what will be exported. Nothing here records an
 * intention it does not carry out.
 */
@Composable
private fun StudioPanel(state: WorkspaceUiState, actions: WorkspaceActions) {
    val colours = SautiyTheme.colours

    LazyColumn(verticalArrangement = Arrangement.spacedBy(SautiySpace.s)) {
        item {
            // The one tap for someone who does not yet know what any of the words below mean.
            // It proposes, with its reason, and waits: a starting point they can disagree with
            // rather than a decision taken on their behalf.
            val recommendation = state.recommendation
            if (recommendation != null) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(SautiyShapes.medium)
                        .background(colours.signalSelection)
                        .padding(SautiySpace.l),
                ) {
                    Text(
                        text = "Suggested: ${recommendation.outcome.displayName}",
                        style = SautiyTheme.type.titleMedium,
                        color = colours.signal,
                    )
                    Spacer(modifier = Modifier.height(SautiySpace.xxs))
                    Text(
                        text = "Voice Space ${VoiceCharacter(recommendation.intensity).percent}% " +
                            "· ${VoiceCharacter(recommendation.intensity).displayName}",
                        style = SautiyTheme.type.labelLarge,
                        color = colours.textSecondary,
                    )
                    Spacer(modifier = Modifier.height(SautiySpace.xs))
                    Text(
                        text = recommendation.reason,
                        style = SautiyTheme.type.bodyMedium,
                        color = colours.textTertiary,
                    )
                    Spacer(modifier = Modifier.height(SautiySpace.m))
                    Row(horizontalArrangement = Arrangement.spacedBy(SautiySpace.m)) {
                        PrimaryAction(
                            label = "Use this",
                            onClick = actions.onAcceptRecommendation,
                            modifier = Modifier.weight(1f),
                        )
                        PrimaryAction(
                            label = "Choose myself",
                            onClick = actions.onDismissRecommendation,
                            modifier = Modifier.weight(1f),
                            filled = false,
                        )
                    }
                }
            } else {
                PrimaryAction(
                    label = "✨ Auto Studio",
                    onClick = actions.onAutoStudio,
                    modifier = Modifier.fillMaxWidth(),
                )
            }
            Spacer(modifier = Modifier.height(SautiySpace.s))
        }

        item {
            // Choosing a room is a listening decision and nothing else. This plays one passage
            // through every space in turn, starting from the original, so the comparison is of
            // the same phrase rather than of two memories a minute apart.
            val auditioning = state.auditioning
            if (auditioning != null) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(SautiyShapes.medium)
                        .background(colours.signalSelection)
                        .padding(SautiySpace.l),
                ) {
                    Text(
                        text = "Listening: ${auditioning.displayName}",
                        style = SautiyTheme.type.titleMedium,
                        color = colours.signal,
                    )
                    Spacer(modifier = Modifier.height(SautiySpace.xxs))
                    Text(
                        text = auditioning.purpose,
                        style = SautiyTheme.type.bodyMedium,
                        color = colours.textTertiary,
                    )
                    if (state.comparingOriginal) {
                        Spacer(modifier = Modifier.height(SautiySpace.xxs))
                        Text(
                            text = "Original",
                            style = SautiyTheme.type.labelLarge,
                            color = colours.textSecondary,
                        )
                    }

                    Spacer(modifier = Modifier.height(SautiySpace.m))
                    Text(
                        text = "How does it sound?",
                        style = SautiyTheme.type.bodyMedium,
                        color = colours.textSecondary,
                    )
                    Spacer(modifier = Modifier.height(SautiySpace.xs))

                    // Seven words, each with a defined adjustment behind it. A listener says what
                    // they hear and the voice moves; nobody has to translate it into parameters,
                    // which is the step where tuning cycles normally stop happening.
                    ListenerNoteChips(onNote = actions.onListenerNote)

                    Spacer(modifier = Modifier.height(SautiySpace.m))
                    PrimaryAction(
                        label = "Keep this one",
                        onClick = actions.onStopAudition,
                        modifier = Modifier.fillMaxWidth(),
                    )
                }
            } else {
                PrimaryAction(
                    label = "Hear every space",
                    onClick = actions.onAuditionSpaces,
                    modifier = Modifier.fillMaxWidth(),
                    filled = false,
                )
            }
            Spacer(modifier = Modifier.height(SautiySpace.s))
        }

        item {
            Row(horizontalArrangement = Arrangement.spacedBy(SautiySpace.m)) {
                PrimaryAction(
                    label = "\u2728 Enhance Voice",
                    onClick = actions.onEnhanceVoice,
                    modifier = Modifier.weight(1f),
                )
                PrimaryAction(
                    label = "\uD83C\uDF99 Studio Voice",
                    onClick = actions.onStudioVoice,
                    modifier = Modifier.weight(1f),
                    filled = false,
                )
            }
        }

        item {
            // One control, five named stops, moving every parameter underneath it together.
            // Someone who likes a preset but finds it too much wants *less of this one* — a single
            // gesture. Almost nobody wants ten sliders; they want more, or less.
            val character = state.voice?.character?.position ?: VoiceCharacter.REFINED
            val stop = VoiceCharacter(character)
            StudioSlider(
                label = "Voice Space",
                value = character,
                range = 0f..1f,
                display = "${stop.percent}% · ${stop.displayName}",
            ) { actions.onCharacterChanged(it) }
            Spacer(modifier = Modifier.height(SautiySpace.s))
        }

        if (state.deferredStages.isNotEmpty()) {
            item {
                // Said plainly rather than implied. A preview that quietly differs from the
                // export is how a person ships something they never heard.
                Text(
                    text = "Heard on export, not in preview: " +
                        state.deferredStages.joinToString(", ").lowercase(),
                    style = SautiyTheme.type.bodyMedium,
                    color = colours.textTertiary,
                    modifier = Modifier.padding(vertical = SautiySpace.xs),
                )
            }
        }

        items(VoiceOutcome.cardOrder) { outcome ->
            val applied = state.appliedOutcome == outcome
            val isFirstOfGroup = VoiceOutcome.cardOrder.first { it.group == outcome.group } == outcome
            if (isFirstOfGroup) {
                Text(
                    text = outcome.group.displayName,
                    style = SautiyTheme.type.labelSmall,
                    color = colours.textTertiary,
                    modifier = Modifier.padding(top = SautiySpace.s, bottom = SautiySpace.xxs),
                )
            }
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(SautiyShapes.medium)
                    .background(if (applied) colours.signalSelection else colours.surfaceRaised)
                    .border(
                        width = if (applied) 1.5.dp else 0.dp,
                        color = if (applied) colours.signal else colours.surfaceRaised,
                        shape = SautiyShapes.medium,
                    )
                    .clickable(onClickLabel = outcome.displayName, role = Role.Button) {
                        actions.onApplyOutcome(outcome)
                    }
                    .padding(SautiySpace.l),
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = outcome.displayName,
                        style = SautiyTheme.type.titleMedium,
                        color = colours.textPrimary,
                        modifier = Modifier.weight(1f),
                    )
                    if (applied) {
                        Text(text = "Applied", style = SautiyTheme.type.labelSmall, color = colours.signal)
                    }
                }
                Spacer(modifier = Modifier.height(SautiySpace.xxs))
                Text(
                    text = outcome.purpose,
                    style = SautiyTheme.type.bodyMedium,
                    color = colours.textTertiary,
                )

                // Tier 3 (chapter 3.2.3): the real numbers, revealed only once this card is the
                // applied one. A professional is never limited; a beginner never has to look.
                if (applied) {
                    Spacer(modifier = Modifier.height(SautiySpace.m))
                    val settings = outcome.settings
                    settings.cleanup.highPassHz?.let { ParameterRow("High-pass", "${it.toInt()} Hz") }
                    settings.dynamics.compressor?.let {
                        ParameterRow("Compression", "${it.ratio}:1 at ${it.thresholdDb.toInt()} dB")
                    }
                    val space = settings.effectiveAmbience
                    if (!space.isBypassed) {
                        ParameterRow("Decay", "${space.decaySeconds} s")
                        ParameterRow("Pre-delay", "${space.preDelayMs.toInt()} ms")
                        ParameterRow("Room", "${(space.wetDryMix * 100).toInt()}%")
                    } else {
                        ParameterRow("Room", "None")
                    }
                    settings.loudness.target?.let {
                        ParameterRow("Loudness", "${Loudness.Target.valueOf(it).lufs} LUFS")
                    }

                    // The acoustic profile underneath, for a professional who wants to know.
                    // Transparency, not a second thing to choose between — which is why it lives
                    // here, behind a tap, rather than in the list.
                    Spacer(modifier = Modifier.height(SautiySpace.xs))
                    Text(
                        text = outcome.advancedDetail,
                        style = SautiyTheme.type.labelSmall,
                        color = colours.textTertiary,
                    )

                    Spacer(modifier = Modifier.height(SautiySpace.s))
                    Text(
                        text = "Revert to original",
                        style = SautiyTheme.type.labelLarge,
                        color = colours.signal,
                        modifier = Modifier
                            .sizeIn(minHeight = SautiySpace.minTouchTarget)
                            .clickable(
                                onClickLabel = "Revert to original",
                                role = Role.Button,
                                onClick = actions.onRevertPreset,
                            ),
                    )
                }
            }
        }

        // ── Layer two ────────────────────────────────────────────────────────────────────────
        // Below everything above, and deliberately quieter: smaller rows, no cards. Most people
        // will never scroll this far and lose nothing by it. Someone who wants a particular
        // acoustic character, rather than a particular result, finds it here.

        item {
            SectionHeading(
                title = "Acoustic Space",
                body = "These are not presets. They are acoustic environments. Choosing one " +
                    "changes the room around your voice and nothing about the voice itself.",
            )
        }

        items(AcousticSpace.order) { space ->
            ChooserRow(
                title = space.displayName,
                body = space.summary,
                selected = state.appliedSpace == space,
            ) { actions.onChooseSpace(space) }
        }

        item {
            SectionHeading(
                title = "Recitation Studio",
                body = "Complete voices for recitation, each in a space of its own character.",
            )
        }

        items(RecitationProfile.order) { profile ->
            ChooserRow(
                title = profile.displayName,
                body = profile.summary,
                selected = state.appliedRecitation == profile,
                trailing = "${VoiceCharacter(profile.defaultIntensity).percent}%",
            ) { actions.onChooseRecitation(profile) }
        }

        item {
            // Always shown, never behind a tap. The people who care most about these recordings
            // are exactly the people a name like "Makkah Inspired" could mislead.
            Text(
                text = RecitationProfile.DISCLOSURE,
                style = SautiyTheme.type.bodyMedium,
                color = colours.textTertiary,
                modifier = Modifier.padding(top = SautiySpace.s, bottom = SautiySpace.l),
            )
        }
    }
}

/** A quiet heading for a section that is optional rather than part of the main path. */
@Composable
private fun SectionHeading(title: String, body: String) {
    val colours = SautiyTheme.colours
    Column(modifier = Modifier.padding(top = SautiySpace.l, bottom = SautiySpace.xs)) {
        Text(text = title, style = SautiyTheme.type.titleMedium, color = colours.textPrimary)
        Spacer(modifier = Modifier.height(SautiySpace.xxs))
        Text(text = body, style = SautiyTheme.type.bodyMedium, color = colours.textTertiary)
    }
}

/**
 * One choice in a secondary list: a name, a line about it, and whether it is the one in force.
 *
 * A row rather than a card, because the outcome cards above are the primary decision and two sets
 * of identically-weighted cards would read as two competing answers to the same question.
 */
@Composable
private fun ChooserRow(
    title: String,
    body: String,
    selected: Boolean,
    trailing: String? = null,
    onClick: () -> Unit,
) {
    val colours = SautiyTheme.colours
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clip(SautiyShapes.small)
            .background(if (selected) colours.signalSelection else colours.surface)
            .clickable(onClickLabel = title, role = Role.Button, onClick = onClick)
            .padding(horizontal = SautiySpace.m, vertical = SautiySpace.s)
            .sizeIn(minHeight = SautiySpace.minTouchTarget),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = title,
                style = SautiyTheme.type.bodyLarge,
                color = if (selected) colours.signal else colours.textPrimary,
            )
            Text(
                text = body,
                style = SautiyTheme.type.bodyMedium,
                color = colours.textTertiary,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis,
            )
        }
        if (trailing != null) {
            Spacer(modifier = Modifier.width(SautiySpace.s))
            Text(text = trailing, style = SautiyTheme.type.numeric, color = colours.textSecondary)
        }
        if (selected) {
            Spacer(modifier = Modifier.width(SautiySpace.s))
            Text(text = "Applied", style = SautiyTheme.type.labelSmall, color = colours.signal)
        }
    }
}

/**
 * The seven words a listener can say, as chips.
 *
 * Kept to seven on purpose. A free-text box collects sentences nobody can act on; a list of
 * thirty adjectives is a vocabulary test. These are the descriptions that map onto a defined
 * change, and there is nothing here a listener has to learn.
 */
@Composable
private fun ListenerNoteChips(onNote: (ListenerNote) -> Unit) {
    val colours = SautiyTheme.colours
    Column(verticalArrangement = Arrangement.spacedBy(SautiySpace.xs)) {
        for (row in ListenerNote.order.chunked(2)) {
            Row(horizontalArrangement = Arrangement.spacedBy(SautiySpace.xs)) {
                for (note in row) {
                    val isAcceptance = note == ListenerNote.EXCELLENT
                    Box(
                        modifier = Modifier
                            .weight(1f)
                            .sizeIn(minHeight = SautiySpace.minTouchTarget)
                            .clip(SautiyShapes.pill)
                            .background(if (isAcceptance) colours.commit else colours.surface)
                            .clickable(onClickLabel = note.displayName, role = Role.Button) {
                                onNote(note)
                            },
                        contentAlignment = Alignment.Center,
                    ) {
                        Text(
                            text = note.displayName,
                            style = SautiyTheme.type.labelLarge,
                            color = if (isAcceptance) colours.onCommit else colours.textPrimary,
                            modifier = Modifier.padding(
                                horizontal = SautiySpace.s,
                                vertical = SautiySpace.s,
                            ),
                            maxLines = 1,
                        )
                    }
                }
                if (row.size == 1) Spacer(modifier = Modifier.weight(1f))
            }
        }
    }
}

/**
 * One control: a name, its value in the unit it is measured in, and a slider.
 *
 * The value is always printed. A dial whose position is the only record of its setting cannot be
 * described, compared or written down, and every professional eventually needs to do all three.
 */
@Composable
private fun StudioSlider(
    label: String,
    value: Double,
    range: ClosedFloatingPointRange<Float>,
    display: String,
    onChange: (Double) -> Unit,
) {
    val colours = SautiyTheme.colours
    Column(modifier = Modifier.fillMaxWidth().padding(vertical = SautiySpace.xxs)) {
        Row {
            Text(
                text = label,
                style = SautiyTheme.type.bodyMedium,
                color = colours.textSecondary,
                modifier = Modifier.weight(1f),
            )
            Text(text = display, style = SautiyTheme.type.numeric, color = colours.textPrimary)
        }
        Slider(
            value = value.toFloat().coerceIn(range.start, range.endInclusive),
            onValueChange = { onChange(it.toDouble()) },
            valueRange = range,
            colors = SliderDefaults.colors(
                thumbColor = colours.signal,
                activeTrackColor = colours.signal,
                inactiveTrackColor = colours.surfaceRaised,
            ),
            modifier = Modifier
                .fillMaxWidth()
                .sizeIn(minHeight = SautiySpace.minTouchTarget)
                .semantics { contentDescription = "$label, $display" },
        )
    }
}

private fun percent(value: Double): String = "${(value * 100).toInt()}%"

/** A bipolar refinement control, printed as the signed position it is at. */
private fun signed(value: Double): String {
    val rounded = (value * 100).toInt()
    return if (rounded > 0) "+$rounded" else "$rounded"
}

@Composable
private fun ParameterRow(label: String, value: String) {
    Row(
        modifier = Modifier.fillMaxWidth().padding(vertical = SautiySpace.xxs),
    ) {
        Text(
            text = label,
            style = SautiyTheme.type.bodyMedium,
            color = SautiyTheme.colours.textTertiary,
            modifier = Modifier.weight(1f),
        )
        Text(text = value, style = SautiyTheme.type.numeric, color = SautiyTheme.colours.textSecondary)
    }
}

/**
 * The Export panel — chapter 1.6's three-tap guarantee.
 *
 * Open it, tap a format, tap Export. The last-used format is already selected, so the common
 * case is two taps, and Export opens the destination picker directly rather than writing
 * somewhere the user then has to go and find.
 *
 * Only formats with a registered encoder appear. A format that cannot be written is absent
 * rather than present and failing at the moment it is pressed.
 */
@Composable
private fun ExportPanel(state: WorkspaceUiState, actions: WorkspaceActions) {
    val colours = SautiyTheme.colours
    val available = remember { Encoders.available() }

    Column {
        for (format in available) {
            val chosen = state.exportFormat == format
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = SautiySpace.xxs)
                    .clip(SautiyShapes.medium)
                    .background(if (chosen) colours.signalSelection else colours.surfaceRaised)
                    .clickable(onClickLabel = format.displayName, role = Role.Button) {
                        actions.onChooseExportFormat(format)
                    }
                    .padding(SautiySpace.l),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = format.displayName,
                        style = SautiyTheme.type.titleMedium,
                        color = colours.textPrimary,
                    )
                    Text(
                        text = format.summary,
                        style = SautiyTheme.type.bodyMedium,
                        color = colours.textTertiary,
                    )
                }
                if (format.lossless) {
                    Text(text = "Exact", style = SautiyTheme.type.labelSmall, color = colours.safe)
                }
            }
        }

        Spacer(modifier = Modifier.height(SautiySpace.l))

        val progress = state.exportProgress
        when {
            progress != null -> {
                LinearProgressIndicator(
                    progress = { progress.toFloat() },
                    modifier = Modifier.fillMaxWidth(),
                    color = colours.signal,
                    trackColor = colours.surfaceRaised,
                )
                Spacer(modifier = Modifier.height(SautiySpace.xs))
                Text(
                    text = "Exporting ${(progress * 100).toInt()}%",
                    style = SautiyTheme.type.bodyMedium,
                    color = colours.textTertiary,
                )
            }

            else -> {
                Row(horizontalArrangement = Arrangement.spacedBy(SautiySpace.m)) {
                    PrimaryAction(
                        label = "Export",
                        onClick = actions.onExport,
                        modifier = Modifier.weight(1f),
                    )
                    PrimaryAction(
                        label = "Share",
                        onClick = actions.onShare,
                        modifier = Modifier.weight(1f),
                        filled = false,
                    )
                }
            }
        }

        // Where it went, said plainly. "Exported" with no destination is the version of this
        // message that sends people hunting through a file manager.
        state.savedTo?.let { destination ->
            Spacer(modifier = Modifier.height(SautiySpace.m))
            Text(
                text = "Saved as $destination",
                style = SautiyTheme.type.bodyMedium,
                color = colours.safe,
            )
        }
        if (state.exportClipped) {
            Spacer(modifier = Modifier.height(SautiySpace.xs))
            Text(
                text = "The exported audio reached full scale. Lower the output level and export again.",
                style = SautiyTheme.type.bodyMedium,
                color = colours.caution,
            )
        }
    }
}

@Composable
private fun PrimaryAction(
    label: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    filled: Boolean = true,
) {
    val colours = SautiyTheme.colours
    Box(
        modifier = modifier
            .sizeIn(minHeight = SautiySpace.minTouchTarget)
            .height(52.dp)
            .clip(SautiyShapes.pill)
            .background(if (filled) colours.commit else colours.surfaceRaised)
            .clickable(onClickLabel = label, role = Role.Button, onClick = onClick),
        contentAlignment = Alignment.Center,
    ) {
        Text(
            text = label,
            style = SautiyTheme.type.labelLarge,
            color = if (filled) colours.onCommit else colours.textPrimary,
        )
    }
}

/** The Analysis panel — every number measured, none estimated (chapter 10.4). */
@Composable
private fun AnalysisPanel(state: WorkspaceUiState) {
    Column {
        QualityGauge(score = state.qualityScore, reason = state.qualityReason)
        Spacer(modifier = Modifier.height(SautiySpace.l))
        ParameterRow("Peak", ai.sautiy.core.audio.Decibels.format(state.peakDb))
        ParameterRow("Noise floor", ai.sautiy.core.audio.Decibels.format(state.noiseFloorDb))
        ParameterRow("Signal to noise", "${(state.peakDb - state.noiseFloorDb).toInt()} dB")
        ParameterRow("Clipping", if (state.hasClipped) "Yes" else "None")
        ParameterRow("Duration", formatDuration(state.totalFrames, state.sampleRate))
    }
}

/** The Library panel. A panel, not a page (chapter 4.1). */
@Composable
private fun LibraryPanel(state: WorkspaceUiState, actions: WorkspaceActions) {
    val colours = SautiyTheme.colours
    var confirming by remember { mutableStateOf<String?>(null) }
    var renaming by remember { mutableStateOf<Pair<String, String>?>(null) }

    if (state.library.isEmpty()) {
        EmptyPanelState(
            title = "No recordings yet",
            body = "Recordings appear here as soon as you make them.",
        )
        return
    }

    LazyColumn(verticalArrangement = Arrangement.spacedBy(SautiySpace.xs)) {
        items(state.library) { row ->
            Column(modifier = Modifier.fillMaxWidth()) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .sizeIn(minHeight = SautiySpace.minTouchTarget)
                    .padding(vertical = SautiySpace.xxs),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(SautiySpace.xs),
            ) {
                Icon(
                    imageVector = SautiyIcons.Waveform,
                    contentDescription = null,
                    tint = colours.signal,
                    modifier = Modifier.size(20.dp),
                )
                Column(
                    modifier = Modifier
                        .weight(1f)
                        .clip(SautiyShapes.small)
                        .clickable(onClickLabel = row.title, role = Role.Button) {
                            actions.onOpenRecording(row.id)
                        }
                        .padding(vertical = SautiySpace.s),
                ) {
                    Text(
                        text = row.title,
                        style = SautiyTheme.type.bodyLarge,
                        color = colours.textPrimary,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                    )
                    Text(
                        text = formatDuration(row.durationFrames, row.sampleRate),
                        style = SautiyTheme.type.timerInline,
                        color = colours.textTertiary,
                    )
                }
                // Favourite, rename and delete, on the row itself. A recording that can be
                // opened but not renamed or removed is a library only in name — and these were
                // missing entirely from the first version of this panel.
                RowAction(
                    label = if (row.favourite) "Remove favourite" else "Favourite",
                    icon = SautiyIcons.Star,
                    tint = if (row.favourite) colours.caution else colours.textTertiary,
                ) { actions.onToggleFavourite(row.id) }

                RowAction(label = "Rename", icon = SautiyIcons.Edit, tint = colours.textTertiary) {
                    renaming = row.id to row.title
                }

                RowAction(label = "Delete", icon = SautiyIcons.Delete, tint = colours.textTertiary) {
                    confirming = row.id
                }
            }

            // Delete is never immediate and never final: it is confirmed here, and the store
            // moves it to the trash with a stated recovery window (chapter 13.5).
            if (confirming == row.id) {
                Row(
                    modifier = Modifier.fillMaxWidth().padding(bottom = SautiySpace.s),
                    horizontalArrangement = Arrangement.spacedBy(SautiySpace.m),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text(
                        text = "Moves to the trash for 30 days.",
                        style = SautiyTheme.type.bodyMedium,
                        color = colours.textTertiary,
                        modifier = Modifier.weight(1f),
                    )
                    Text(
                        text = "Keep",
                        style = SautiyTheme.type.labelLarge,
                        color = colours.textSecondary,
                        modifier = Modifier
                            .sizeIn(minHeight = SautiySpace.minTouchTarget)
                            .clickable(onClickLabel = "Keep", role = Role.Button) { confirming = null }
                            .padding(SautiySpace.s),
                    )
                    Text(
                        text = "Delete",
                        style = SautiyTheme.type.labelLarge,
                        color = colours.critical,
                        modifier = Modifier
                            .sizeIn(minHeight = SautiySpace.minTouchTarget)
                            .clickable(onClickLabel = "Delete ${row.title}", role = Role.Button) {
                                actions.onDelete(row.id)
                                confirming = null
                            }
                            .padding(SautiySpace.s),
                    )
                }
            }

            val pending = renaming
            if (pending != null && pending.first == row.id) {
                Row(
                    modifier = Modifier.fillMaxWidth().padding(bottom = SautiySpace.s),
                    horizontalArrangement = Arrangement.spacedBy(SautiySpace.m),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    TextField(
                        value = pending.second,
                        onValueChange = { renaming = row.id to it },
                        singleLine = true,
                        modifier = Modifier.weight(1f),
                    )
                    Text(
                        text = "Save",
                        style = SautiyTheme.type.labelLarge,
                        color = colours.signal,
                        modifier = Modifier
                            .sizeIn(minHeight = SautiySpace.minTouchTarget)
                            .clickable(onClickLabel = "Save name", role = Role.Button) {
                                val title = pending.second.trim()
                                if (title.isNotEmpty()) actions.onRename(row.id, title)
                                renaming = null
                            }
                            .padding(SautiySpace.s),
                    )
                }
            }
            }
        }
    }
}

/** A 48 dp icon control on a library row. Small on screen, never small to the thumb. */
@Composable
private fun RowAction(
    label: String,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    tint: androidx.compose.ui.graphics.Color,
    onClick: () -> Unit,
) {
    Box(
        modifier = Modifier
            .size(SautiySpace.minTouchTarget)
            .clip(SautiyShapes.small)
            .clickable(onClickLabel = label, role = Role.Button, onClick = onClick),
        contentAlignment = Alignment.Center,
    ) {
        Icon(imageVector = icon, contentDescription = label, tint = tint, modifier = Modifier.size(20.dp))
    }
}

/** The History panel — chapter 9.5's time travel. Tap any step to go there. */
@Composable
private fun HistoryPanel(state: WorkspaceUiState, actions: WorkspaceActions) {
    val colours = SautiyTheme.colours

    LazyColumn(verticalArrangement = Arrangement.spacedBy(SautiySpace.xxs)) {
        items(state.historySteps.size) { index ->
            val current = index == state.historyIndex
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .sizeIn(minHeight = SautiySpace.minTouchTarget)
                    .clip(SautiyShapes.small)
                    .background(if (current) colours.signalSelection else colours.surface)
                    .clickable(onClickLabel = state.historySteps[index], role = Role.Button) {
                        actions.onTravelHistory(index)
                    }
                    .padding(horizontal = SautiySpace.m, vertical = SautiySpace.m),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    text = state.historySteps[index],
                    style = SautiyTheme.type.bodyMedium,
                    color = if (index <= state.historyIndex) colours.textPrimary else colours.textDisabled,
                    modifier = Modifier.weight(1f),
                )
                if (current) {
                    Text(text = "Now", style = SautiyTheme.type.labelSmall, color = colours.signal)
                }
            }
        }
    }
}

@Composable
private fun LayersPanel(state: WorkspaceUiState, actions: WorkspaceActions) {
    val colours = SautiyTheme.colours
    LazyColumn(verticalArrangement = Arrangement.spacedBy(SautiySpace.xs)) {
        items(state.layers) { layer ->
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .sizeIn(minHeight = SautiySpace.minTouchTarget)
                    .clickable(onClickLabel = layer.name, role = Role.Button) { actions.onSelectLayer(layer.id) }
                    .padding(vertical = SautiySpace.m),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    text = layer.name,
                    style = SautiyTheme.type.bodyLarge,
                    color = if (layer.muted) colours.textDisabled else colours.textPrimary,
                    modifier = Modifier.weight(1f),
                )
                if (layer.soloed) Text("Solo", style = SautiyTheme.type.labelSmall, color = colours.signal)
                if (layer.muted) Text("Muted", style = SautiyTheme.type.labelSmall, color = colours.textTertiary)
            }
        }
    }
}

@Composable
private fun MarkersPanel(state: WorkspaceUiState, actions: WorkspaceActions) {
    if (state.markerFrames.isEmpty()) {
        EmptyPanelState(
            title = "No markers",
            body = "Drop a marker while recording to find a moment again later.",
        )
        return
    }
    LazyColumn(verticalArrangement = Arrangement.spacedBy(SautiySpace.xxs)) {
        items(state.markerFrames) { frame ->
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .sizeIn(minHeight = SautiySpace.minTouchTarget)
                    .clickable(onClickLabel = "Jump", role = Role.Button) { actions.onSeek(frame) }
                    .padding(vertical = SautiySpace.m),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    text = formatTimecode(frame, state.sampleRate),
                    style = SautiyTheme.type.timerInline,
                    color = SautiyTheme.colours.textPrimary,
                )
            }
        }
    }
}

/**
 * The Voice and Space panels: the two halves of the Voice Studio a person actually turns.
 *
 * They are controls, not read-outs. The first version of these showed the applied preset's
 * numbers and moved nothing — the panel looked complete and did nothing at all. Every control
 * here writes back through [WorkspaceActions] and is audible on the next block of playback.
 */
@Composable
private fun EqualiserPanel(state: WorkspaceUiState, actions: WorkspaceActions) {
    val voice = state.voice
    val refinement = voice?.refinement ?: VoiceRefinement()

    fun update(next: VoiceRefinement) = actions.onRefinementChanged(next)

    Column {
        Text(
            text = "Eight controls, each centred at zero. A control at rest changes nothing.",
            style = SautiyTheme.type.bodyMedium,
            color = SautiyTheme.colours.textTertiary,
        )
        Spacer(modifier = Modifier.height(SautiySpace.m))

        val bipolar = -1f..1f
        StudioSlider("Clarity", refinement.clarity, bipolar, signed(refinement.clarity)) {
            update(refinement.copy(clarity = it))
        }
        StudioSlider("Warmth", refinement.warmth, bipolar, signed(refinement.warmth)) {
            update(refinement.copy(warmth = it))
        }
        StudioSlider("Richness", refinement.richness, bipolar, signed(refinement.richness)) {
            update(refinement.copy(richness = it))
        }
        StudioSlider("Presence", refinement.presence, bipolar, signed(refinement.presence)) {
            update(refinement.copy(presence = it))
        }
        StudioSlider("Body", refinement.body, bipolar, signed(refinement.body)) {
            update(refinement.copy(body = it))
        }
        StudioSlider("Air", refinement.air, bipolar, signed(refinement.air)) {
            update(refinement.copy(air = it))
        }
        StudioSlider("Brightness", refinement.brightness, bipolar, signed(refinement.brightness)) {
            update(refinement.copy(brightness = it))
        }
        StudioSlider("Depth", refinement.depth, bipolar, signed(refinement.depth)) {
            update(refinement.copy(depth = it))
        }

        if (voice?.ambience?.isBypassed != false && refinement.depth != 0.0) {
            // Depth is distance, and distance is a room. Saying so is better than letting a
            // control sit at a position that does nothing.
            Text(
                text = "Depth needs a space. Choose one in Studio.",
                style = SautiyTheme.type.bodyMedium,
                color = SautiyTheme.colours.textTertiary,
                modifier = Modifier.padding(top = SautiySpace.s),
            )
        }
    }
}

@Composable
private fun DynamicsPanel(state: WorkspaceUiState) {
    val dynamics = state.voice?.dynamics
    val compressor = dynamics?.compressor
    if (compressor == null) {
        EmptyPanelState("No compression", "This voice leaves the dynamics alone.")
        return
    }
    Column {
        ParameterRow("Threshold", "${compressor.thresholdDb} dB")
        ParameterRow("Ratio", "${compressor.ratio}:1")
        ParameterRow("Attack", "${compressor.attackMs} ms")
        ParameterRow("Release", "${compressor.releaseMs} ms")
        ParameterRow("Knee", "${compressor.kneeDb} dB")
        dynamics.deEsser?.let {
            ParameterRow("De-esser", "${(it.frequencyHz / 1000).toInt()} kHz at ${it.ratio}:1")
        }
        state.voice?.loudness?.limiterCeilingDb?.let { ParameterRow("Limiter ceiling", "$it dBTP") }
    }
}

/**
 * The Space panel — one control by default, and everything behind a tap.
 *
 * Fifteen sliders is the correct set of controls and the wrong first screen. Almost everyone who
 * opens this wants the room to be a bit more, or a bit less, and one control does that to every
 * parameter at once in the way each parameter should move. The rest are for the person who came
 * here to change a specific number, and they know they did.
 */
@Composable
private fun SpacePanel(state: WorkspaceUiState, actions: WorkspaceActions) {
    val ambience = state.voice?.ambience
    if (ambience == null || ambience.isBypassed) {
        Column {
            EmptyPanelState(
                "No space",
                "This voice adds no room. Choose a space in Studio, or start one here.",
            )
            Spacer(modifier = Modifier.height(SautiySpace.m))
            PrimaryAction(
                label = "Add a room",
                onClick = { actions.onAmbienceChanged(AmbienceSettings()) },
                modifier = Modifier.fillMaxWidth(),
                filled = false,
            )
        }
        return
    }

    fun update(next: AmbienceSettings) = actions.onAmbienceChanged(next)

    Column {
        // The one control. Named for what it is rather than for the parameter it moves, because
        // nobody thinks "I would like a higher wet/dry mix".
        val character = state.voice?.character?.position ?: VoiceCharacter.REFINED
        val stop = VoiceCharacter(character)
        StudioSlider(
            label = "Voice Space",
            value = character,
            range = 0f..1f,
            display = "${stop.percent}% · ${stop.displayName}",
        ) { actions.onCharacterChanged(it) }

        Spacer(modifier = Modifier.height(SautiySpace.s))
        Text(
            text = if (state.advanced) "Hide Advanced Studio" else "Advanced Studio",
            style = SautiyTheme.type.labelLarge,
            color = SautiyTheme.colours.signal,
            modifier = Modifier
                .sizeIn(minHeight = SautiySpace.minTouchTarget)
                .clickable(
                    onClickLabel = "Advanced Studio",
                    role = Role.Button,
                    onClick = actions.onToggleAdvanced,
                ),
        )

        Spacer(modifier = Modifier.height(SautiySpace.s))
        if (state.advanced) {
            AdvancedAmbienceControls(ambience) { update(it) }
        } else {
            Text(
                text = "One control moves decay, size, reflections and mix together, in the " +
                    "proportions a real space moves them.",
                style = SautiyTheme.type.bodyMedium,
                color = SautiyTheme.colours.textTertiary,
            )
        }

        Spacer(modifier = Modifier.height(SautiySpace.m))
        PrimaryAction(
            label = "Remove the room",
            onClick = { actions.onAmbienceChanged(AmbienceSettings.NONE) },
            modifier = Modifier.fillMaxWidth(),
            filled = false,
        )
    }
}

/**
 * Advanced Studio: every parameter of the room, in the order a room is built.
 *
 * Hidden by default, and complete once shown. A professional who opens this is not helped by a
 * curated subset — the reason they came here is the one control that was left out.
 */
@Composable
private fun AdvancedAmbienceControls(
    ambience: AmbienceSettings,
    update: (AmbienceSettings) -> Unit,
) {
    Column {
        StudioSlider("Amount", ambience.amount, 0f..1f, percent(ambience.amount)) {
            update(ambience.copy(amount = it))
        }
        StudioSlider("Wet / dry mix", ambience.wetDryMix, 0f..1f, percent(ambience.wetDryMix)) {
            update(ambience.copy(wetDryMix = it))
        }
        StudioSlider("Room size", ambience.roomSize, 0f..1f, percent(ambience.roomSize)) {
            update(ambience.copy(roomSize = it))
        }
        StudioSlider(
            label = "Decay time",
            value = ambience.decaySeconds,
            range = 0.1f..12f,
            display = String.format("%.2f s", ambience.decaySeconds),
        ) { update(ambience.copy(decaySeconds = it)) }
        StudioSlider(
            label = "Pre-delay",
            value = ambience.preDelayMs,
            range = 0f..200f,
            display = "${ambience.preDelayMs.toInt()} ms",
        ) { update(ambience.copy(preDelayMs = it)) }
        StudioSlider(
            "Early reflections",
            ambience.earlyReflections,
            0f..1f,
            percent(ambience.earlyReflections),
        ) { update(ambience.copy(earlyReflections = it)) }
        StudioSlider(
            "Late reflections",
            ambience.lateReflections,
            0f..1f,
            percent(ambience.lateReflections),
        ) { update(ambience.copy(lateReflections = it)) }
        StudioSlider("Diffusion", ambience.diffusion, 0f..1f, percent(ambience.diffusion)) {
            update(ambience.copy(diffusion = it))
        }
        StudioSlider("Damping", ambience.damping, 0f..1f, percent(ambience.damping)) {
            update(ambience.copy(damping = it))
        }
        StudioSlider("Presence", ambience.presence, 0f..1f, percent(ambience.presence)) {
            update(ambience.copy(presence = it))
        }
        StudioSlider(
            "Tail smoothness",
            ambience.tailSmoothness,
            0f..1f,
            percent(ambience.tailSmoothness),
        ) { update(ambience.copy(tailSmoothness = it)) }
        StudioSlider(
            "Speech priority",
            ambience.speechPriority,
            0f..1f,
            percent(ambience.speechPriority),
        ) { update(ambience.copy(speechPriority = it)) }
        StudioSlider("Width", ambience.width, 0f..1f, percent(ambience.width)) {
            update(ambience.copy(width = it))
        }
        StudioSlider("Warmth", ambience.warmth, 0f..1f, percent(ambience.warmth)) {
            update(ambience.copy(warmth = it))
        }
        StudioSlider("Brightness", ambience.brightness, 0f..1f, percent(ambience.brightness)) {
            update(ambience.copy(brightness = it))
        }

        Spacer(modifier = Modifier.height(SautiySpace.s))
        Text(
            text = "Presence and speech priority keep words above the room: one takes the room " +
                "out of the consonant band, the other makes it stand back while you speak.",
            style = SautiyTheme.type.bodyMedium,
            color = SautiyTheme.colours.textTertiary,
        )
        Spacer(modifier = Modifier.height(SautiySpace.xs))
        Text(
            text = "Warmth and brightness here shape the room. The same controls in Voice shape " +
                "the speaker.",
            style = SautiyTheme.type.bodyMedium,
            color = SautiyTheme.colours.textTertiary,
        )
    }
}

@Composable
private fun TranscriptPanel() {
    EmptyPanelState(
        title = "No transcript",
        body = "Transcription runs on this device when a recording is finished. Nothing is uploaded.",
    )
}

@Composable
private fun ProjectPanel(state: WorkspaceUiState) {
    Column {
        ParameterRow("Project", state.projectName)
        ParameterRow("Quality", state.quality.displayName)
        ParameterRow("Sample rate", "${state.sampleRate} Hz")
        ParameterRow("Layers", "${state.layers.size}")
        ParameterRow("Duration", formatDuration(state.totalFrames, state.sampleRate))
    }
}

/**
 * The empty state pattern of chapter 18: say what this is for, in the product's own voice, and
 * never apologise for the absence of content.
 */
@Composable
private fun EmptyPanelState(title: String, body: String) {
    Column(
        modifier = Modifier.fillMaxWidth().padding(vertical = SautiySpace.h4),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(text = title, style = SautiyTheme.type.titleMedium, color = SautiyTheme.colours.textPrimary)
        Spacer(modifier = Modifier.height(SautiySpace.xs))
        Text(
            text = body,
            style = SautiyTheme.type.bodyMedium,
            color = SautiyTheme.colours.textTertiary,
            textAlign = androidx.compose.ui.text.style.TextAlign.Center,
        )
    }
}
