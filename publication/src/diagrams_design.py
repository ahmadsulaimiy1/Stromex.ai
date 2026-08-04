"""Brand, design-system, UX and AI diagrams (Parts 0–4, 7, 8)."""
from svgkit import Svg, ORBIT, AURORA, VOID, SUCCESS, SUCCESS_S, WARNING, WARNING_S, \
    DANGER, DANGER_S, UI, MONO

W = 900


def decision_rules():
    s = Svg(W, 420, VOID[0])
    s.kicker(0, 12, "Figure — The decision rules, in priority order")
    s.text(0, 34, "When a decision is genuinely close, apply these in order. A higher rule overrides a lower one.",
           size=10.5, fill=VOID[600])

    rules = [
        ("1", "Uncertain?", "Choose simplicity", "The simple version can be made powerful later.\nThe complex version can almost never be made simple."),
        ("2", "Two features compete?", "Ship the better experience", "Even if the other tests better on engagement."),
        ("3", "It exists because a rival has it?", "Delete it", "“Parity” is not a user problem."),
        ("4", "Performance vs beauty?", "Performance wins", "A beautiful interface that stutters is not beautiful."),
        ("5", "Cleverness vs usability?", "Usability wins", "Nobody has ever loved a product for being clever at them."),
        ("6", "Privacy vs capability?", "Privacy by default", "The capability may be offered as an explicit,\ninformed, revocable choice — never quietly."),
        ("7", "Hard to reverse?", "Take the reversible path", "Buy time to learn."),
    ]
    y = 56
    for n, q, a, why in rules:
        s.rect(0, y, 250, 44, r=10, fill=VOID[50], stroke=VOID[200])
        s.circle(24, y + 22, 11, fill=ORBIT[500])
        s.text(24, y + 26, n, size=11, anchor="middle", weight=700, fill=VOID[0])
        s.text(44, y + 27, q, size=11, weight=600)
        s.arrow(250, y + 22, 274, y + 22, stroke=ORBIT[600])
        s.rect(280, y, 210, 44, r=10, fill=ORBIT[500])
        s.text(295, y + 27, a, size=11.5, weight=700, fill=VOID[0])
        for j, ln in enumerate(why.split("\n")):
            s.text(510, y + (20 if "\n" in why else 27) + j * 13, ln, size=9.5, fill=VOID[600])
        y += 50
    return "decision-rules", s, "Part 0 §0.9 — an ordered ladder, so a close call is resolved by rule rather than by whoever argues longest."


def ai_decision():
    s = Svg(W, 470, VOID[0])
    s.kicker(0, 12, "Figure — The AI privacy decision, in priority order")

    s.box(300, 32, 300, 46, "A new AI capability is proposed", None,
          fill=VOID[900], stroke=VOID[900], tcol=VOID[0], tsize=12.5)
    s.arrow(450, 78, 450, 100, stroke=VOID[400])

    # tier 1
    s.rect(230, 102, 440, 58, r=12, fill=ORBIT[50], stroke=ORBIT[300])
    s.text(450, 126, "Can a model small enough to run on the device do this well?", size=11.5,
           anchor="middle", weight=600, fill=ORBIT[700])
    s.text(450, 146, "This is the default, and where we invest first", size=9.5, anchor="middle", fill=VOID[600])

    s.path("M230,131 L120,131 L120,196", stroke=SUCCESS, marker=True)
    s.text(126, 124, "yes", size=10, weight=700, fill=SUCCESS)
    s.box(20, 198, 200, 62, "Run it on the device", ["plaintext never leaves", "no grant needed"],
          fill=SUCCESS_S, stroke="#9AD0AF", tcol=SUCCESS, tsize=12)

    s.arrow(450, 160, 450, 186, stroke=VOID[400])
    s.text(458, 178, "no", size=10, weight=700, fill=VOID[500])

    # tier 2
    s.rect(230, 188, 440, 74, r=12, fill=WARNING_S, stroke="#F0C79A")
    s.text(450, 212, "Will the user grant server-side processing", size=11.5, anchor="middle", weight=600)
    s.text(450, 230, "for this specific conversation?", size=11.5, anchor="middle", weight=600)
    s.text(450, 250, "visible in the header · revocable in one tap · disclosed to all participants",
           size=9, anchor="middle", fill=VOID[600])

    s.path("M670,225 L790,225 L790,286", stroke=WARNING, marker=True)
    s.text(700, 218, "granted", size=10, weight=700, fill=WARNING)
    s.box(690, 288, 210, 62, "Process on the server", ["for that conversation only", "deleted within 24 h of revoke"],
          fill=WARNING_S, stroke="#F0C79A", tcol=WARNING, tsize=12)

    s.arrow(450, 262, 450, 290, stroke=VOID[400])
    s.text(458, 282, "declined", size=10, weight=700, fill=VOID[500])
    s.box(300, 292, 300, 58, "The feature does not ship",
          "there is no third path where we process quietly",
          fill=DANGER_S, stroke="#E8A9A2", tcol=DANGER, tsize=12.5)

    s.rect(0, 376, W, 88, r=12, fill=VOID[50], stroke=VOID[200])
    s.text(20, 400, "The assistant conversation is a separate surface with separate rules", size=11.5, weight=700)
    s.text(20, 420, "When you talk to the assistant, you are talking to a server. That conversation is encrypted in transit and at rest, retained on a", size=10, fill=VOID[700])
    s.text(20, 436, "published schedule, never used for training without opt-in — and is visibly marked as not end-to-end encrypted. Pretending", size=10, fill=VOID[700])
    s.text(20, 452, "otherwise would be the more comfortable lie, and the one thing that would permanently destroy the brand. ADR-005.", size=10, fill=VOID[700])
    return "ai-decision", s, "The three-tier rule that resolves the product's one genuine contradiction — on-device, then granted, then not at all."


def ai_pipeline():
    s = Svg(W, 450, VOID[0])
    s.kicker(0, 12, "Figure — The AI pipeline")

    s.rect(0, 30, 560, 300, r=14, fill=AURORA["050"], stroke=AURORA[300])
    s.text(20, 54, "On device — the default path", size=12.5, weight=700, fill=AURORA[800])
    s.text(20, 70, "Target: over 85 % of all AI invocations. This is the privacy promise made measurable.",
           size=9.5, fill=VOID[600])

    feats = [
        ("Reply suggestions", "always local — never a round trip", "drafts only; the user presses send"),
        ("Tap to translate", "downloadable language pack", "original always shown, never replaced"),
        ("Voice transcription", "speech model, on device", "sender sees it before sending too"),
        ("Semantic search", "local embedding index", "covers what is on this device"),
        ("Scam detection", "classifier on incoming messages", "content never leaves for this purpose"),
    ]
    y = 84
    for t, mid, d in feats:
        s.rect(20, y, 520, 42, r=8, fill=VOID[0], stroke=AURORA[300], sw=1)
        s.circle(38, y + 21, 5, fill=AURORA[500])
        s.text(52, y + 18, t, size=10.5, weight=600)
        s.text(52, y + 32, d, size=9, fill=VOID[600])
        s.text(530, y + 25, mid, size=9, anchor="end", fill=AURORA[700])
        y += 47

    s.rect(580, 30, 320, 138, r=14, fill=WARNING_S, stroke="#F0C79A")
    s.text(600, 54, "Server — only with a grant", size=12, weight=700, fill=WARNING)
    for i, t in enumerate(["unread summaries", "higher-quality translation where",
                           "   on-device quality is insufficient", "call summaries (every participant consents)"]):
        s.text(600, 76 + i * 15, t, size=9.5, fill=VOID[700])
    s.text(600, 148, "Shown in the header for the whole time it is active.", size=9, fill=VOID[600])

    s.rect(580, 186, 320, 144, r=14, fill=DANGER_S, stroke="#E8A9A2")
    s.text(600, 210, "Never built", size=12, weight=700, fill=DANGER)
    for i, t in enumerate(["emotion detection on users", "auto-send without the user pressing send",
                           "personality simulation of real people", "engagement optimisation of any kind",
                           "silent scanning of private conversations", "a ranking model — there is no feed"]):
        s.line(600, 228 + i * 16, 608, 228 + i * 16, stroke=DANGER, sw=2)
        s.text(616, 232 + i * 16, t, size=9.5, fill=VOID[700])

    s.rect(0, 350, W, 90, r=12, fill=VOID[50], stroke=VOID[200])
    s.text(20, 374, "Non-negotiable properties of every path above", size=11.5, weight=700)
    props = [("Labelled", "Aurora colour, never a human colour"), ("Attributable", "you always know a model wrote it"),
             ("Never sends", "drafts only, no exceptions"), ("Disableable", "one setting, product stays complete"),
             ("Not in the path", "0 ms added to send or receive"), ("Audited", "zero ungranted invocations, continuously")]
    for i, (k, v) in enumerate(props):
        x = 20 + (i % 3) * 300
        yy = 396 + (i // 3) * 22
        s.text(x, yy, k, size=10, weight=700, fill=ORBIT[700])
        s.text(x + 92, yy, v, size=9.5, fill=VOID[600])
    return "ai-pipeline", s, "What runs where — and the six properties that hold on every path."


def navigation_ia():
    s = Svg(W, 560, VOID[0])
    s.kicker(0, 12, "Figure — Information architecture and navigation")

    s.box(340, 32, 220, 40, "SpaceTalk", None, fill=VOID[900], stroke=VOID[900], tcol=VOID[0], tsize=13)
    s.text(450, 88, "Four destinations. Maximum depth three levels. Adding a fifth requires CPO and CDO sign-off.",
           size=10, anchor="middle", fill=VOID[600])

    tabs = [
        ("Chats", 0, ORBIT[500], ["Filter: All · Unread · Groups · Channels", "Conversation rows — people, groups,",
                                  "channels and the assistant in ONE list", "Archived (never badged)", "→ Conversation"]),
        ("Calls", 1, VOID[600], ["History — all · missed", "Start a call"]),
        ("Stories", 2, VOID[600], ["Others' stories", "My story + viewers (private)", "Create — audience chosen", "   before posting, every time"]),
        ("Settings", 3, VOID[600], ["Profile", "Privacy", "Devices", "Notifications", "Assistant", "Storage & data", "Appearance", "Help & about"]),
    ]
    for name, i, col, items in tabs:
        x = i * 228
        s.line(450, 72, x + 100, 104, stroke=VOID[300], sw=1.5)
        s.rect(x, 106, 208, 40, r=10, fill=col, stroke=col)
        s.text(x + 104, 131, name, size=12.5, anchor="middle", weight=700, fill=VOID[0])
        s.rect(x, 154, 208, 26 + len(items) * 16, r=10, fill=VOID[50], stroke=VOID[200])
        for j, it in enumerate(items):
            s.text(x + 14, 176 + j * 16, it, size=9.5,
                   fill=ORBIT[700] if it.startswith("→") else VOID[700],
                   weight=600 if it.startswith("→") else 400)

    # conversation subtree
    s.rect(0, 320, 440, 190, r=12, fill=ORBIT[50], stroke=ORBIT[200])
    s.text(20, 344, "Conversation — the atomic unit of the product", size=11.5, weight=700, fill=ORBIT[700])
    sub = [("Transcript", "message runs, reply quotes, reactions"),
           ("Composer", "text · attach · voice · send — never moves"),
           ("Conversation profile", "members · media · files · links · encryption"),
           ("Search within", "local index, results in under 50 ms")]
    for j, (k, v) in enumerate(sub):
        s.rect(20, 358 + j * 36, 400, 30, r=8, fill=VOID[0], stroke=ORBIT[200], sw=1)
        s.text(34, 377 + j * 36, k, size=10.5, weight=600)
        s.text(170, 377 + j * 36, v, size=9.5, fill=VOID[600])

    s.rect(460, 320, 440, 190, r=12, fill=VOID[0], stroke=VOID[200])
    s.text(480, 344, "The rules that keep it learnable", size=11.5, weight=700)
    rules = ["A channel, a group, a person and the assistant differ in what",
             "they contain — not in where they live. One list, by recency.",
             "",
             "No hamburger menu. No nested tabs. No fifth destination.",
             "",
             "Nothing lives in two places. A shortcut that duplicates a",
             "Settings item creates a second mental model of the app.",
             "",
             "Archived is a place, not a state to be badged."]
    for j, r in enumerate(rules):
        s.text(480, 366 + j * 15, r, size=9.5, fill=VOID[700])

    s.text(0, 538, "Global search spans conversations, messages, media, files and people — but is not a destination, because searching is something you do from somewhere.",
           size=9.5, fill=VOID[500])
    return "navigation-ia", s, "Four destinations, one conversation list, and the rules that stop the structure from growing."


def design_token_hierarchy():
    s = Svg(W, 430, VOID[0])
    s.kicker(0, 12, "Figure — Design token hierarchy")

    tiers = [
        ("Tier 1 — Primitive", VOID[900], VOID[0],
         ["orbit-500", "void-100", "space-4", "radius-lg", "dur-medium"],
         "Raw values. Theme-independent. Never referenced by a screen."),
        ("Tier 2 — Semantic", ORBIT[500], VOID[0],
         ["color.surface.primary", "color.text.secondary", "color.action.primary"],
         "Meaning, resolved per theme. This is the only place light and dark diverge."),
        ("Tier 3 — Component", AURORA[700], VOID[0],
         ["bubble.outgoing.background", "composer.height", "button.primary.label"],
         "Component-scoped. What screens actually reference."),
    ]
    y = 34
    for name, fill, tcol, examples, note in tiers:
        s.rect(0, y, 250, 92, r=12, fill=fill)
        s.text(20, y + 32, name, size=12.5, weight=700, fill=tcol)
        s.text(20, y + 54, "generated, never hand-edited", size=9.5, fill=VOID[0], op=0.75)
        s.rect(268, y, 340, 92, r=12, fill=VOID[50], stroke=VOID[200])
        for j, e in enumerate(examples):
            s.text(286, y + 28 + j * 18, e, size=10, fill=VOID[700], font=MONO)
        s.text(628, y + 34, note.split(".")[0] + ".", size=10, fill=VOID[700])
        rest = ".".join(note.split(".")[1:]).strip()
        if rest:
            s.text(628, y + 52, rest, size=10, fill=VOID[600])
        if y < 200:
            s.arrow(125, y + 92, 125, y + 110, stroke=VOID[400])
            s.text(136, y + 106, "references", size=9, fill=VOID[500])
        y += 110

    s.rect(0, 366, W, 62, r=12, fill=ORBIT[50], stroke=ORBIT[200])
    s.text(20, 390, "One JSON source → Figma variables · Dart · CSS, generated in CI", size=11.5, weight=700, fill=ORBIT[700])
    s.text(20, 412, "Generation is one-directional. Hand-editing a generated file is a build failure — which is what keeps design and code from drifting apart, the failure mode of every design system that dies.",
           size=9.5, fill=VOID[700])
    return "design-token-hierarchy", s, "Three tiers, one generated source. A screen that reaches past tier 3 is a bug."


def palette_sheet():
    s = Svg(W, 700, VOID[0])
    s.kicker(0, 12, "Figure — The colour system, with measured contrast")

    def swatch(x, y, name, hexv, ratio=None, dark=False, wide=81, h=62):
        fg = VOID[0] if dark else VOID[900]
        s.rect(x, y, wide, h, r=8, fill=hexv, stroke=VOID[200], sw=1)
        s.text(x + 8, y + 20, name, size=9, weight=700, fill=fg)
        s.text(x + 8, y + 34, hexv, size=8.5, font=MONO, fill=fg)
        if ratio:
            s.text(x + 8, y + 50, ratio, size=8.5, weight=600, fill=fg)

    s.text(0, 42, "Orbit — the brand action colour", size=12, weight=700)
    s.text(0, 58, "Hue ≈ 231°. The violet lean keeps it distinct from iOS system blue, Telegram and Meta blue at a glance.", size=9.5, fill=VOID[600])
    orbit = [("50", ORBIT[50], None, False), ("100", ORBIT[100], "14.33:1", False), ("200", ORBIT[200], None, False),
             ("300", ORBIT[300], "7.93 dk", False), ("400", ORBIT[400], "5.26 dk", False),
             ("500", ORBIT[500], "5.16 wht", True), ("600", ORBIT[600], "6.92 wht", True),
             ("700", ORBIT[700], "9.33 wht", True), ("800", ORBIT[800], "10.61:1", True),
             ("900", ORBIT[900], None, True), ("950", ORBIT[950], None, True)]
    for i, (n, h, r, d) in enumerate(orbit):
        swatch(i * 82, 68, "orbit-" + n, h, r, d)

    s.text(0, 158, "Aurora — the intelligence colour", size=12, weight=700)
    s.text(0, 174, "Reserved absolutely for assistant output. Human content and machine content never wear the same colour.", size=9.5, fill=VOID[600])
    aur = [("050", AURORA["050"], None, False), ("300", AURORA[300], "11.53 dk", False),
           ("400", AURORA[400], "9.23 dk", False), ("500", AURORA[500], "fill only", False),
           ("700", AURORA[700], "5.67 wht", True), ("800", AURORA[800], "8.24 wht", True),
           ("950", AURORA[950], None, True)]
    for i, (n, h, r, d) in enumerate(aur):
        swatch(i * 82, 184, "aurora-" + n, h, r, d)

    s.text(0, 274, "Void — neutrals, cool-tinted so they sit with Orbit rather than fight it", size=12, weight=700)
    voids = [(0, False), (25, False), (50, False), (100, False), (200, False), (300, False), (400, False),
             (500, True), (600, True), (700, True), (800, True), (850, True), (900, True), (950, True)]
    for i, (k, d) in enumerate(voids):
        swatch(i * 64.5, 290, "void-" + str(k), VOID[k], None, d, wide=63)

    s.text(0, 380, "Semantic — light-mode values first, then their dark-mode counterparts", size=12, weight=700)
    sem = [("success-text", SUCCESS, "7.71 wht", True), ("warning-text", WARNING, "5.02 wht", True),
           ("danger-text", DANGER, "5.92 wht", True), ("success-dark", "#35D07F", "9.04 dk", False),
           ("warning-dark", "#FFC46B", "11.53 dk", False), ("danger-dark", "#FF6B60", "6.49 dk", False)]
    for i, (n, h, r, d) in enumerate(sem):
        swatch(i * 150.5, 396, n, h, r, d, wide=149)

    # the honest note
    s.rect(0, 476, W, 108, r=12, fill=WARNING_S, stroke="#F0C79A")
    s.text(20, 500, "A measured note on colour-blind safety, recorded honestly", size=11.5, weight=700, fill=WARNING)
    for i, t in enumerate([
        "We wanted to claim the semantic trio is distinguishable in greyscale. It is not fully, and the constraint is physical: in light mode every",
        "semantic text colour must clear 4.5 : 1 on white, which caps it near CIE L* 48. Measured — success L* 35.2, danger L* 42.4, warning L* 46.9.",
        "Success is comfortably separable; warning and danger differ by about 4.5 L*. The design consequence is a hard rule, not a caveat:",
        "every semantic state ships a distinct glyph and, wherever space allows, a word. Delivery states differ in tick geometry, not tick colour."]):
        s.text(20, 522 + i * 16, t, size=9.5, fill=VOID[800])

    s.text(0, 606, "Every ratio on this page was computed against the WCAG relative-luminance formula. None was estimated.", size=10, weight=600, fill=ORBIT[700])

    # usage bar
    s.rect(0, 626, W, 62, r=12, fill=VOID[50], stroke=VOID[200])
    s.text(20, 650, "The interface is 90 % neutral.", size=11, weight=700)
    s.text(212, 650, "Brand colour appears on roughly one element per screen. A screen with three coloured things has one too many.", size=10, fill=VOID[700])
    s.text(20, 672, "Colour encodes meaning — identity, state, hierarchy — never mood. If it is not communicating one of those, it should be a neutral.", size=10, fill=VOID[600])
    return "colour-palette", s, "The full palette with measured WCAG ratios, and the accessibility limit we found by measuring rather than asserting."


def spacing_radius():
    s = Svg(W, 440, VOID[0])
    s.kicker(0, 12, "Figure — Spacing, radius and elevation")

    s.text(0, 44, "Spacing — a 4 px base unit", size=12, weight=700)
    s.text(0, 60, "All spacing is a token. An arbitrary value is a lint failure.", size=9.5, fill=VOID[600])
    spaces = [("1", 4), ("2", 8), ("3", 12), ("4", 16), ("5", 20), ("6", 24), ("8", 32), ("10", 40), ("12", 48), ("16", 64)]
    x = 0
    for n, v in spaces:
        s.rect(x, 74, v, 40, r=2, fill=ORBIT[500])
        s.text(x, 128, "space-" + n, size=8.5, fill=VOID[600])
        s.text(x, 140, str(v), size=8.5, font=MONO, fill=VOID[900], weight=700)
        x += max(v, 34) + 26

    s.text(0, 178, "Radius — one geometric family, so the product feels cut from one material", size=12, weight=700)
    radii = [("xs", 4, "tags, inline code"), ("sm", 8, "inputs, buttons"), ("md", 12, "cards, media"),
             ("lg", 18, "message bubbles"), ("xl", 24, "sheets, dialogs"), ("full", 34, "avatars, pills")]
    x = 0
    for n, r, use in radii:
        s.rect(x, 194, 120, 68, r=r, fill=VOID[50], stroke=ORBIT[400], sw=1.5)
        s.text(x + 60, 224, "radius-" + n, size=10, anchor="middle", weight=700)
        s.text(x + 60, 240, f"{r} px" if n != "full" else "999 px", size=9, anchor="middle", font=MONO, fill=VOID[600])
        s.text(x + 60, 276, use, size=8.5, anchor="middle", fill=VOID[500])
        x += 148

    s.text(0, 314, "Elevation — six levels; in dark mode elevation is expressed by lightness, not shadow", size=12, weight=700)
    elev = [("e0", "flat content, bubbles", VOID[0]), ("e1", "cards, list rows", VOID[0]),
            ("e2", "composer, sticky headers", VOID[0]), ("e3", "sheets, menus", VOID[0]),
            ("e4", "dialogs", VOID[0]), ("e5", "incoming call", VOID[0])]
    x = 0
    for i, (n, use, f) in enumerate(elev):
        s.rect(x + 4, 336 + i * 0, 130, 54, r=10, fill=VOID[100], op=0.0 if i == 0 else 0.55)
        s.rect(x, 332, 130, 54, r=10, fill=f, stroke=VOID[200], sw=1)
        s.text(x + 65, 356, n, size=11, anchor="middle", weight=700, font=MONO)
        s.text(x + 65, 372, use, size=8.5, anchor="middle", fill=VOID[600])
        x += 148
    s.text(0, 410, "Message bubbles cast no shadow — they are content, not objects. A transcript with 200 shadowed bubbles is 200 unnecessary composited layers.",
           size=10, fill=VOID[600])
    return "spacing-radius-elevation", s, "The three geometric systems, drawn to scale."


def thumb_zones():
    s = Svg(W, 440, VOID[0])
    s.kicker(0, 12, "Figure — Thumb reach and one-handed use")

    # phone
    px, py, pw, ph = 40, 34, 190, 380
    s.rect(px, py, pw, ph, r=26, fill=VOID[0], stroke=VOID[300], sw=2)
    s.rect(px + 6, py + 6, pw - 12, ph * 0.25, r=20, fill=DANGER_S)
    s.rect(px + 6, py + 6 + ph * 0.25, pw - 12, ph * 0.35, r=4, fill=WARNING_S)
    s.rect(px + 6, py + 6 + ph * 0.60, pw - 12, ph * 0.40 - 12, r=20, fill=SUCCESS_S)
    s.text(px + pw / 2, py + ph * 0.13, "HARD", size=11, anchor="middle", weight=700, fill=DANGER)
    s.text(px + pw / 2, py + ph * 0.145 + 14, "top 25 %", size=9, anchor="middle", fill=VOID[600])
    s.text(px + pw / 2, py + ph * 0.42, "STRETCH", size=11, anchor="middle", weight=700, fill=WARNING)
    s.text(px + pw / 2, py + ph * 0.42 + 14, "middle 35 %", size=9, anchor="middle", fill=VOID[600])
    s.text(px + pw / 2, py + ph * 0.80, "NATURAL", size=11, anchor="middle", weight=700, fill=SUCCESS)
    s.text(px + pw / 2, py + ph * 0.80 + 14, "bottom 40 %", size=9, anchor="middle", fill=VOID[600])
    s.path(f"M{px+pw-14},{py+ph-16} Q{px+10},{py+ph-40} {px+16},{py+ph*0.42}",
           stroke=ORBIT[500], sw=2, dash="5 4")
    s.text(px, py + ph + 24, "Thumb arc, right hand, 6.1–6.9″ device", size=9, fill=VOID[500])

    zones = [
        ("Natural — bottom 40 %", SUCCESS, SUCCESS_S,
         ["composer, send, mic", "tab bar", "answer / end call", "sheet actions", "reply, react"]),
        ("Stretch — middle 35 %", WARNING, WARNING_S,
         ["message content", "list rows — large targets,", "   tap anywhere in the row"]),
        ("Hard — top 25 %", DANGER, DANGER_S,
         ["screen titles", "back (also served by the", "   edge-swipe gesture)", "secondary actions"]),
    ]
    y = 34
    for name, col, bg, items in zones:
        h = 30 + len(items) * 16
        s.rect(270, y, 300, h, r=10, fill=bg)
        s.text(288, y + 22, name, size=11, weight=700, fill=col)
        for j, it in enumerate(items):
            s.text(288, y + 40 + j * 16, it, size=9.5, fill=VOID[700])
        y += h + 12

    s.rect(600, 34, 300, 380, r=12, fill=VOID[50], stroke=VOID[200])
    s.text(620, 58, "Rules that follow", size=11.5, weight=700)
    rules = ["Every high-frequency action is in the natural",
             "zone. Send, record, react, reply, answer and",
             "end call are all reachable without regrip.",
             "",
             "Destructive actions are never in the natural",
             "zone. Delete and block live in menus,",
             "deliberately requiring intent.",
             "",
             "Sheets over dialogs. A bottom sheet puts its",
             "actions where the thumb is; a centred dialog",
             "puts them where it is not.",
             "",
             "Primary actions sit bottom-right in LTR and",
             "bottom-left in RTL, mirroring with the layout.",
             "",
             "Every new screen is reviewed on a 6.7″ device,",
             "held in one hand, by someone who is not the",
             "designer. If a common task needs a regrip,",
             "it is not done."]
    for j, r in enumerate(rules):
        s.text(620, 80 + j * 16, r, size=9.5, fill=VOID[700])
    return "thumb-zones", s, "The reach model the whole interface is laid out against."
