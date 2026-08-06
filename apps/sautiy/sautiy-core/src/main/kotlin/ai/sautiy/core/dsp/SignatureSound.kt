package ai.sautiy.core.dsp

/**
 * The SAUTIY house sound, written down as rules the build enforces.
 *
 * A signature sound is not a preset. It is the set of things that are true of *every* SAUTIY
 * recording, whichever preset made it — the reason a listener could recognise the app across ten
 * different voices in ten different rooms. Reverb engines do not have a signature; record labels
 * and mastering houses do, and the difference is that a house has rules.
 *
 * The rules below are the house. They are deliberately negative more often than positive, because
 * an identity is mostly a list of things you never do:
 *
 * * **The voice is always in front of the room.** Pre-delay never below [MIN_PRE_DELAY_MS] and
 *   speech priority never below [MIN_SPEECH_PRIORITY], so the room answers the voice instead of
 *   arriving with it. This is the single most recognisable thing here: most mobile reverb puts the
 *   voice *inside* the effect, and the result is the sound people call "washy".
 * * **Never harsh.** The presence lift is capped at [MAX_PRESENCE], and the room never keeps its
 *   full top end in the consonant band. Brightness is what sells a demo in a shop and what makes
 *   an hour-long lecture unbearable.
 * * **Always some weight.** A voice with no low-mid is a telephone. Warmth never sits below
 *   [MIN_WARMTH] once any room is present, because a bright voice in a large space is the
 *   definition of thin.
 * * **The room is never louder than the voice.** Wet/dry mix capped at [MAX_WET_DRY], including
 *   after the Voice Space control has multiplied it. Past that point the effect becomes the
 *   subject.
 * * **A predictable delivery level.** One ceiling, [CEILING_DB], on everything that leaves.
 *
 * [verify] returns the rules a setting breaks; [applyTo] brings a setting inside them. Every
 * preset, outcome, acoustic space and recitation profile in the app is checked against [verify]
 * by a test, so a new preset that breaks the house style fails the build rather than shipping.
 *
 * **What this does not claim.** That the rules produce a sound anyone recognises is a listening
 * judgement and is not asserted here. What is asserted is that the rules hold everywhere, which
 * is the part a listener could not check for themselves and the part that has to be true first.
 */
public object SignatureSound {

    /**
     * The floor on how soon any room may answer, however small it is.
     *
     * Below about 5 ms the reflection is not heard as a space at all — the ear fuses it with the
     * direct sound and the voice simply takes on a colour it did not have.
     */
    public const val MIN_PRE_DELAY_MS: Double = 5.0

    /**
     * How much later a room must answer per second of its own tail.
     *
     * The rule that matters is not one number but a *relationship*: the larger the space, the
     * further away its surfaces, and the later its first reflection. A vocal booth genuinely
     * answers in 6 ms and it would be wrong to force it to 12 — that is what a small room is. A
     * 3.6-second hall answering in 6 ms is not a hall, it is a voice smeared with a hall.
     *
     * 3.5 ms per second is a house rule chosen to hold true of real rooms rather than derived from
     * Sabine's equation, and is stated as such.
     */
    public const val PRE_DELAY_MS_PER_SECOND: Double = 3.5

    /** How much the room must stand back while the speaker is speaking, at the very least. */
    public const val MIN_SPEECH_PRIORITY: Double = 0.30

    /**
     * The most room there may ever be, at any intensity.
     *
     * Not a taste limit. Past roughly 60% the room carries more energy than the voice, and no
     * amount of ducking recovers a word that was quieter than the tail it landed in. This is the
     * ceiling the Voice Space control clamps to, which is what makes turning it to 100% a safe
     * thing to do rather than a mistake the user has to learn about.
     */
    public const val MAX_WET_DRY: Double = 0.60

    /** The presence lift, as a fraction of full travel. Above this, consonants turn to edges. */
    public const val MAX_PRESENCE: Double = 0.55

    /** Air, likewise. A little openness reads as expensive; a lot reads as hiss. */
    public const val MAX_AIR: Double = 0.60

    /** Weight, once a room is present. Bright and large together is the thin sound. */
    public const val MIN_WARMTH: Double = -0.20

    /** How much of its top end a room may keep. Above this the room itself sibilates. */
    public const val MAX_ROOM_BRIGHTNESS: Double = 0.72

    /** One ceiling everywhere, so no SAUTIY export ever arrives at a different loudness policy. */
    public const val CEILING_DB: Double = -1.0

    /** One rule, and what breaking it sounds like. */
    public data class Violation(val rule: String, val heardAs: String)

    /**
     * The soonest a room with this much tail may answer.
     *
     * See [PRE_DELAY_MS_PER_SECOND]: the rule is the relationship, not the number.
     */
    public fun minPreDelayMs(decaySeconds: Double): Double =
        maxOf(MIN_PRE_DELAY_MS, decaySeconds * PRE_DELAY_MS_PER_SECOND)

    /**
     * How hard a room this loud must duck while the speaker is speaking.
     *
     * **This is the central law of the house sound.** A big room is allowed; a big room that
     * competes with the words is not. So the two are tied together: every decibel of room level
     * buys a corresponding amount of standing back, and the relationship is enforced rather than
     * left to whoever writes the next preset.
     *
     * Below 15% wet there is nothing to protect against and this returns zero. The 1.15 slope
     * means the loudest room the house allows (60%) must duck by about half, which is audible as
     * the room breathing around the speech rather than sitting on top of it.
     */
    public fun requiredProtection(wetDryMix: Double): Double =
        ((wetDryMix - 0.15) * 1.15).coerceIn(0.0, 0.92)

    /**
     * Every house rule this setting breaks, with what each one sounds like.
     *
     * Empty means the setting is inside the house style. The `heardAs` text is not decoration:
     * a rule whose consequence cannot be described in listening terms is a rule that was invented
     * for the code rather than for the ear, and should not be here.
     */
    public fun verify(settings: VoiceStudioSettings): List<Violation> = buildList {
        // `effectiveAmbience` has already had depth and the character control applied, so this is
        // the room as it will actually be heard rather than as it was written down.
        val room = settings.effectiveAmbience
        val voice = settings.character.applyTo(settings.refinement)

        if (!room.isBypassed) {
            val soonest = minPreDelayMs(room.decaySeconds)
            if (room.preDelayMs < soonest) {
                add(
                    Violation(
                        "Pre-delay ${round2(room.preDelayMs)} ms is sooner than ${round2(soonest)} ms " +
                            "for a ${round2(room.decaySeconds)} s tail",
                        "The room arrives with the voice instead of after it, so the voice takes " +
                            "on the colour of the room instead of sitting inside it.",
                    ),
                )
            }
            val needed = maxOf(MIN_SPEECH_PRIORITY, requiredProtection(room.wetDryMix))
            if (room.speechPriority < needed) {
                add(
                    Violation(
                        "Speech priority ${round2(room.speechPriority)} is below the " +
                            "${round2(needed)} that ${round2(room.wetDryMix)} of room requires",
                        "The room does not stand back far enough for how loud it is, and words " +
                            "start landing inside the previous word's tail.",
                    ),
                )
            }
            if (room.wetDryMix > MAX_WET_DRY) {
                add(
                    Violation(
                        "Room level ${round2(room.wetDryMix)} is above $MAX_WET_DRY",
                        "The space becomes the subject of the recording rather than the voice.",
                    ),
                )
            }
            if (room.brightness > MAX_ROOM_BRIGHTNESS) {
                add(
                    Violation(
                        "Room brightness ${round2(room.brightness)} is above $MAX_ROOM_BRIGHTNESS",
                        "The room itself sibilates, which is the metallic sound reverb is blamed for.",
                    ),
                )
            }
            if (voice.warmth < MIN_WARMTH) {
                add(
                    Violation(
                        "Warmth ${round2(voice.warmth)} is below $MIN_WARMTH with a room present",
                        "Bright and large together: a thin voice in a big space.",
                    ),
                )
            }
        }

        if (voice.presence > MAX_PRESENCE) {
            add(
                Violation(
                    "Presence ${round2(voice.presence)} is above $MAX_PRESENCE",
                    "Consonants become edges. It sells in a shop and is unbearable for an hour.",
                ),
            )
        }
        if (voice.air > MAX_AIR) {
            add(
                Violation(
                    "Air ${round2(voice.air)} is above $MAX_AIR",
                    "Openness turns into audible hiss, and any room noise comes with it.",
                ),
            )
        }

        val ceiling = settings.loudness.limiterCeilingDb
        if (ceiling == null || ceiling > CEILING_DB) {
            add(
                Violation(
                    "Ceiling ${ceiling ?: "none"} is not $CEILING_DB dBTP",
                    "Some exports arrive louder and closer to clipping than others, so the app " +
                        "has no consistent delivery level.",
                ),
            )
        }
    }

    /** True when nothing is broken. What a test asserts of every preset in the app. */
    public fun holds(settings: VoiceStudioSettings): Boolean = verify(settings).isEmpty()

    /**
     * Brings a setting inside the house style, changing as little as possible.
     *
     * Used on anything the user has hand-edited or loaded from a saved sound, so a voice that
     * came from outside the presets still leaves the app sounding like SAUTIY. It clamps rather
     * than re-tunes: a person who deliberately made something dry and close keeps it dry and
     * close, and only the things that would make it *not a SAUTIY recording* move.
     */
    public fun applyTo(settings: VoiceStudioSettings): VoiceStudioSettings {
        val room = settings.ambience
        val cappedRoom = if (room.isBypassed) {
            room
        } else {
            // Compensated for everything downstream that will multiply the mix — the depth control
            // and then the character control — so the rule holds at Immersive rather than only at
            // the position the sound was saved in.
            val mix = room.wetDryMix.coerceAtMost(
                MAX_WET_DRY / (characterMixFactor(settings.character) * depthMixFactor(settings)),
            )
            room.copy(
                wetDryMix = mix,
                // The floor is computed from the decay this room will actually have, not the one
                // written down: the character control lengthens the tail, and a longer tail must be
                // kept further back. Computing it from the stored value left every saved sound one
                // notch of intensity away from breaking its own rule.
                preDelayMs = room.preDelayMs.coerceAtLeast(
                    minPreDelayMs(room.decaySeconds * characterDecayFactor(settings.character)),
                ),
                // Protection scales with the *final* room level, not the stored one: a sound saved
                // at 20% and played at Immersive needs the protection Immersive requires.
                speechPriority = room.speechPriority.coerceAtLeast(
                    maxOf(
                        MIN_SPEECH_PRIORITY,
                        requiredProtection(
                            (mix * characterMixFactor(settings.character) * depthMixFactor(settings))
                                .coerceAtMost(MAX_WET_DRY),
                        ),
                    ),
                ),
                brightness = room.brightness.coerceAtMost(MAX_ROOM_BRIGHTNESS),
            )
        }

        val voice = settings.refinement
        // The character control adds air above Rich, so the stored value has to leave room for it
        // or a saved sound would break the rule the moment somebody turned the intensity up.
        val addedAir = (settings.character.position - VoiceCharacter.RICH).coerceAtLeast(0.0) * 0.24
        val cappedVoice = voice.copy(
            presence = voice.presence.coerceAtMost(MAX_PRESENCE),
            air = voice.air.coerceAtMost(MAX_AIR - addedAir),
            warmth = if (cappedRoom.isBypassed) voice.warmth else voice.warmth.coerceAtLeast(MIN_WARMTH),
        )

        return settings.copy(
            ambience = cappedRoom,
            refinement = cappedVoice,
            loudness = settings.loudness.copy(limiterCeilingDb = CEILING_DB),
        )
    }

    /**
     * What [VoiceCharacter] multiplies a room's level by at this position.
     *
     * Mirrors the factor in `VoiceCharacter.applyTo`. Kept here so [applyTo] can leave headroom
     * for it; a test asserts the two agree, because a signature that only held at one intensity
     * would not be a signature.
     */
    private fun characterMixFactor(character: VoiceCharacter): Double =
        0.45 + character.position * 1.55

    /** Likewise for depth, which moves the listener back and so raises the room's level. */
    private fun depthMixFactor(settings: VoiceStudioSettings): Double =
        (1.0 + settings.refinement.depth.coerceAtLeast(0.0) * 0.8)

    /**
     * What [VoiceCharacter] multiplies a room's decay by at this position.
     *
     * Mirrors `VoiceCharacter.applyTo`, as [characterMixFactor] does, and for the same reason: the
     * house rules have to be enforced against the room the listener gets.
     */
    private fun characterDecayFactor(character: VoiceCharacter): Double =
        1.0 + character.position * 0.35

    private fun round2(value: Double): Double = kotlin.math.round(value * 100) / 100.0
}
