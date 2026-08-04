"""Product, journey, roadmap and governance diagrams (Parts 5, 8, 9, 10, 13)."""
from svgkit import Svg, ORBIT, AURORA, VOID, SUCCESS, SUCCESS_S, WARNING, WARNING_S, \
    DANGER, DANGER_S, UI, MONO

W = 900


def message_anatomy():
    s = Svg(W, 502, VOID[0])
    s.kicker(0, 12, "Figure — Anatomy of the message bubble")
    s.text(0, 34, "The most important component in the product. Everything else is held to a lower ambition ceiling.",
           size=10, fill=VOID[600])

    # incoming run — three bubbles, only the last takes the tight corner
    s.rect(0, 52, 420, 386, r=14, fill=VOID[25], stroke=VOID[200])
    s.text(20, 76, "Light mode", size=10, weight=700, fill=VOID[500])

    s.rrect(20, 88, 216, 36, 18, 18, 18, 18, fill=VOID[100])
    s.text(34, 111, "Are we still on for Thursday?", size=11, fill=VOID[900])
    s.rrect(20, 126, 158, 36, 18, 18, 18, 18, fill=VOID[100])
    s.text(34, 149, "Same place as before", size=11, fill=VOID[900])
    s.rrect(20, 164, 122, 36, 18, 18, 18, 4, fill=VOID[100])          # ← last in run
    s.text(34, 187, "Let me know", size=11, fill=VOID[900])
    s.text(20, 216, "09:14", size=8.5, fill=VOID[500])
    s.line(150, 182, 176, 182, stroke=ORBIT[500], sw=1.2)
    s.text(180, 178, "radius-xs 4 px,", size=8, fill=ORBIT[600])
    s.text(180, 189, "last in run only", size=8, fill=ORBIT[600])

    # outgoing
    s.rrect(178, 246, 216, 36, 18, 18, 4, 18, fill=ORBIT[100])
    s.text(192, 269, "Thursday works. 7pm?", size=11, fill=VOID[900])
    s.rect(214, 288, 46, 22, r=11, fill=VOID[0], stroke=VOID[200], sw=1)
    s.heart(228, 300, 6, DANGER)
    s.text(244, 304, "2", size=9.5, anchor="middle", fill=VOID[700])
    s.text(300, 302, "09:16", size=8.5, fill=VOID[500])
    s.path("M338,298 l4,4 l9,-10", stroke=ORBIT[600], sw=1.8)
    s.path("M350,298 l4,4 l9,-10", stroke=ORBIT[600], sw=1.8)
    s.text(370, 302, "read", size=8, fill=VOID[500])

    s.text(20, 344, "Consecutive messages within 60 s form a run:", size=9.5, weight=600, fill=VOID[700])
    for j, ln in enumerate([
            "spacing tightens to 2 px, and only the last bubble takes the small",
            "corner nearest the sender's edge. This is the single most important",
            "detail in the transcript's visual rhythm — and the reason a burst of",
            "messages reads as one utterance rather than four interruptions."]):
        s.text(20, 360 + j * 14, ln, size=9.5, fill=VOID[600])
    s.text(20, 424, "Delivery states differ in glyph geometry, never in colour alone.", size=9, fill=VOID[500])

    # spec callouts
    specs = [
        ("Radius", "radius-lg 18 px on three corners; radius-xs 4 px on the corner nearest the sender — last in run only"),
        ("Incoming fill", "void-100 #E9EDF4 · text void-900 at 15.43 : 1"),
        ("Outgoing fill", "orbit-100 #DDE4FF · text void-900 at 14.33 : 1 — the highest-traffic surface, so the most readable"),
        ("Type", "body 16 / 22, weight 400. Never smaller than 16 px — not for density, not on tablets"),
        ("Shadow", "none. Bubbles are content, not objects"),
        ("Delivery", "four states with distinct glyph geometry — pending, sent, delivered, read. Never colour alone"),
        ("Reactions", "one emoji per person; a compact pill below the bubble; tap to see who"),
        ("Slots", "reply-quote · content · attachments · reactions · meta"),
    ]
    y = 52
    for k, v in specs:
        words, line, lines = v.split(), "", []
        for wd in words:
            if len(line) + len(wd) > 64:
                lines.append(line)
                line = wd
            else:
                line = (line + " " + wd).strip()
        lines.append(line)
        h = 30 + len(lines) * 12
        s.rect(440, y, 460, h, r=8, fill=VOID[50])
        s.text(456, y + 18, k, size=10, weight=700, fill=ORBIT[700])
        for j, ln in enumerate(lines):
            s.text(456, y + 32 + j * 12, ln, size=9, fill=VOID[600])
        y += h + 6
    return "message-anatomy", s, "Bubble geometry, fills, contrast and run-grouping — specified once so it is never re-decided."


def journey_first_run():
    s = Svg(W, 400, VOID[0])
    s.kicker(0, 12, "Figure — J1: first run to first message sent")
    s.text(0, 34, "Target: under 90 seconds, four screens. Nothing is requested until it is needed for something the user already wants.",
           size=10, fill=VOID[600])

    steps = [
        ("Open", "one line of value,\none button", "no carousel,\nno feature tour", ORBIT[50], ORBIT[200]),
        ("Username", "live availability,\nsuggestions on conflict", "identity is not\na phone number", ORBIT[50], ORBIT[200]),
        ("Recovery", "phone or email —\noptional", "if skipped, the\nconsequence is stated", WARNING_S, "#F0C79A"),
        ("Name / photo", "skippable, and\nvisibly so", "no pressure to\nlook complete", ORBIT[50], ORBIT[200]),
        ("Empty Chats", "one action:\nfind someone", "QR, link, or\nusername search", VOID[50], VOID[200]),
        ("First message", "the conversation\nbegins", "", SUCCESS_S, "#9AD0AF"),
        ("Ask to notify", "\"so you know\nwhen they reply\"", "only now — after\nvalue, never before", SUCCESS_S, "#9AD0AF"),
    ]
    x = 0
    for i, (t, d, note, fill, stroke) in enumerate(steps):
        s.rect(x, 58, 116, 104, r=10, fill=fill, stroke=stroke)
        s.circle(x + 58, 80, 11, fill=ORBIT[600])
        s.text(x + 58, 84, str(i + 1), size=11, anchor="middle", weight=700, fill=VOID[0])
        s.text(x + 58, 108, t, size=10.5, anchor="middle", weight=700)
        for j, ln in enumerate(d.split("\n")):
            s.text(x + 58, 124 + j * 12, ln, size=8.5, anchor="middle", fill=VOID[600])
        for j, ln in enumerate(note.split("\n")):
            if ln:
                s.text(x + 58, 176 + j * 12, ln, size=8.5, anchor="middle", fill=VOID[500])
        if i < len(steps) - 1:
            s.arrow(x + 116, 110, x + 128, 110, stroke=ORBIT[600])
        x += 128

    s.rect(0, 218, 440, 160, r=12, fill=DANGER_S, stroke="#E8A9A2")
    s.text(20, 242, "Where this journey fails", size=11.5, weight=700, fill=DANGER)
    fails = [("Username taken repeatedly", "mitigated with genuinely good suggestions"),
             ("Nobody to talk to", "the entire weight of ADR-010 lands here — the empty\nstate must offer a share link worth sending"),
             ("Notification permission denied", "the app stays fully usable, with a non-nagging\npath to reconsider")]
    y = 262
    for k, v in fails:
        s.text(20, y, k, size=10, weight=700, fill=VOID[900])
        for j, ln in enumerate(v.split("\n")):
            s.text(20, y + 14 + j * 12, ln, size=9, fill=VOID[700])
        y += 38 + (10 if "\n" in v else 0)

    s.rect(460, 218, 440, 160, r=12, fill=VOID[50], stroke=VOID[200])
    s.text(480, 242, "What we measure", size=11.5, weight=700)
    for i, (k, v) in enumerate([("Completion rate", "per step, so we know which step loses people"),
                                ("Time to first message", "the 90-second target"),
                                ("Share-link send rate", "the proxy for whether ADR-010 is survivable"),
                                ("D1 return", "did the first conversation mean anything")]):
        s.text(480, 266 + i * 26, k, size=10, weight=700, fill=ORBIT[700])
        s.text(480, 280 + i * 26, v, size=9, fill=VOID[600])
    return "journey-first-run", s, "The onboarding journey, its three failure modes, and the four numbers that tell us whether it works."


def journey_translation():
    s = Svg(W, 340, VOID[0])
    s.kicker(0, 12, "Figure — J4: a conversation across a language barrier")
    s.text(0, 34, "The journey that most defines the product's differentiation.", size=10, fill=VOID[600])

    s.rect(0, 52, 430, 250, r=12, fill=VOID[25], stroke=VOID[200])
    s.rect(20, 72, 250, 34, r=18, fill=VOID[100])
    s.text(34, 94, "¿Nos vemos el jueves?", size=11)
    s.rect(20, 112, 132, 22, r=11, fill=AURORA["050"], stroke=AURORA[300], sw=1)
    s.text(32, 127, "Translate", size=9.5, weight=600, fill=AURORA[700])

    s.arrow(300, 100, 300, 128, stroke=AURORA[700])
    s.text(310, 118, "one tap", size=9, fill=VOID[500])

    s.rect(20, 146, 250, 34, r=18, fill=VOID[100])
    s.text(34, 168, "¿Nos vemos el jueves?", size=11)
    s.rect(20, 184, 250, 30, r=8, fill=AURORA["050"])
    s.text(34, 203, "Shall we meet on Thursday?", size=11, fill=AURORA[800])
    s.circle(258, 199, 5, fill=AURORA[500])
    s.text(20, 232, "The original is always present and always primary.", size=9.5, weight=600, fill=VOID[700])
    s.text(20, 246, "The translation is an annotation, never a replacement.", size=9.5, fill=VOID[600])
    s.text(20, 266, "Tap the translation to collapse it. Names, @mentions,", size=9.5, fill=VOID[600])
    s.text(20, 280, "code and numbers are never translated.", size=9.5, fill=VOID[600])

    steps = [("Detect", "per message, not per conversation — conversations code-switch"),
             ("Offer", "\"Translate\" appears; nothing is translated without a first tap"),
             ("Show", "beneath the original, in Aurora, labelled"),
             ("Persist", "\"Always translate this conversation?\" — a header indicator if accepted"),
             ("Reply", "optionally see the translation and back-translation before sending"),
             ("Disclose", "the recipient is told the message was translated, and by which side")]
    y = 56
    for i, (k, v) in enumerate(steps):
        s.circle(468, y + 12, 10, fill=AURORA[700])
        s.text(468, y + 16, str(i + 1), size=10, anchor="middle", weight=700, fill=VOID[0])
        s.text(488, y + 9, k, size=10.5, weight=700)
        s.text(488, y + 23, v, size=9.5, fill=VOID[600])
        if i < len(steps) - 1:
            s.line(468, y + 24, 468, y + 34, stroke=VOID[300])
        y += 41

    s.rect(460, 302, 440, 0, r=0, fill=VOID[0])
    s.text(0, 322, "Hidden translation would create a false impression of shared fluency — so it is disclosed. Low-confidence output is labelled \"Rough translation\" rather than presented as reliable.",
           size=9.5, fill=VOID[600])
    return "journey-translation", s, "Translation as an annotation on the conversation, never a replacement for what was actually said."


def roadmap_timeline():
    s = Svg(W, 580, VOID[0])
    s.kicker(0, 12, "Figure — Five phases, gated by evidence rather than by calendar")

    phases = [
        ("1", "MVP", "Months 0–12", ORBIT[500],
         ["13 features, nothing else", "iOS · Android · web linked client", "on-device AI only", "one region, four deployables"],
         ["D30 retention ≥ 40 %", "every performance budget met on Tier-C", "security audit published, criticals closed",
          "notification opt-out below 10 %"]),
        ("2", "Public beta & depth", "Months 12–24", ORBIT[600],
         ["native desktop", "group depth: threads, polls, roles", "group calls to 32, captions", "first granted server AI"],
         ["1 M MAU, retention holding", "budgets held at 10× load", "subscription conversion ≥ 3 %", "no privacy incident in two quarters"]),
        ("3", "Creator tools & protocol", "Months 24–42", ORBIT[700],
         ["paid channels, 10 % take rate", "MLS migration", "post-quantum key agreement", "live call translation"],
         ["10 M MAU", "creators call it a primary channel", "MLS complete, no regression", "unit-economics profitability"]),
        ("4", "Business platform", "Months 42–66", ORBIT[800],
         ["business API, shared inboxes", "payments, market by market", "verified institutions", "enterprise controls"],
         ["business revenue > consumer", "approvals in top five markets", "no consumer standard degraded"]),
        ("5", "Platform ecosystem", "Months 66+", VOID[900],
         ["sandboxed mini-apps", "narrow bot API", "interoperability where required", "open protocol documentation"],
         ["— permanent boundaries hold —"]),
    ]

    x = 0
    for n, name, when, col, builds, gates in phases:
        w = 172
        s.rect(x, 34, w, 6, r=3, fill=col)
        s.circle(x + 14, 37, 9, fill=col)
        s.text(x + 14, 41, n, size=10, anchor="middle", weight=700, fill=VOID[0])
        s.text(x, 66, name, size=12, weight=700, fill=col)
        s.text(x, 82, when, size=9, fill=VOID[500], font=MONO)

        s.rect(x, 94, w, 132, r=10, fill=VOID[50], stroke=VOID[200])
        s.kicker(x + 12, 114, "Builds")
        for i, b in enumerate(builds):
            words, line, lines = b.split(), "", []
            for wd in words:
                if len(line) + len(wd) > 25:
                    lines.append(line); line = wd
                else:
                    line = (line + " " + wd).strip()
            lines.append(line)
            s.circle(x + 15, 130 + i * 24 - 3, 2, fill=col)
            for j, ln in enumerate(lines[:2]):
                s.text(x + 24, 130 + i * 24 + j * 11, ln, size=8.5, fill=VOID[700])

        s.rect(x, 236, w, 126, r=10, fill=ORBIT[50] if n != "5" else VOID[0],
               stroke=ORBIT[200] if n != "5" else VOID[200])
        s.kicker(x + 12, 256, "Gate to next", fill=ORBIT[600])
        for i, g in enumerate(gates):
            words, line, lines = g.split(), "", []
            for wd in words:
                if len(line) + len(wd) > 25:
                    lines.append(line); line = wd
                else:
                    line = (line + " " + wd).strip()
            lines.append(line)
            for j, ln in enumerate(lines[:2]):
                s.text(x + 12, 272 + i * 24 + j * 11, ln, size=8.5, fill=VOID[700])
        x += 182

    # constants band
    s.rect(0, 386, W, 178, r=12, fill=VOID[900])
    s.text(24, 414, "What never changes between Phase 1 and Phase 5", size=13, weight=700, fill=VOID[0])
    s.text(24, 434, "The infrastructure required to hold these standards changes enormously. The standards do not change at all. That is what makes them standards.",
           size=10, fill=VOID[300])
    consts = [("Cold start, Tier C, p95", "< 1,500 ms", "< 1,500 ms"),
              ("E2EE default for personal messages", "yes", "yes"),
              ("AI without an explicit grant", "never", "never"),
              ("Notifications from non-humans", "zero", "zero"),
              ("Primary navigation destinations", "4", "4"),
              ("Advertising", "none", "none")]
    s.text(24, 466, "Standard", size=9, weight=700, fill=VOID[400], ls=1)
    s.text(560, 466, "Phase 1", size=9, weight=700, fill=VOID[400], ls=1)
    s.text(720, 466, "Phase 5", size=9, weight=700, fill=VOID[400], ls=1)
    for i, (k, a, b) in enumerate(consts):
        y = 486 + i * 13
        s.text(24, y, k, size=9.5, fill=VOID[100])
        s.text(560, y, a, size=9.5, fill=AURORA[300], font=MONO)
        s.text(720, y, b, size=9.5, fill=AURORA[300], font=MONO)
    return "roadmap-timeline", s, "Each phase begins because the previous one met its gate — not because it ran out of time."


def scope_funnel():
    s = Svg(W, 430, VOID[0])
    s.kicker(0, 12, "Figure — How the full ecosystem became thirteen features")

    s.rect(0, 34, 250, 120, r=12, fill=VOID[50], stroke=VOID[200])
    s.text(20, 58, "The founding brief", size=12, weight=700)
    s.text(20, 78, "Every feature of seven competing", size=9.5, fill=VOID[700])
    s.text(20, 92, "products, plus payments, healthcare,", size=9.5, fill=VOID[700])
    s.text(20, 106, "education, commerce, government", size=9.5, fill=VOID[700])
    s.text(20, 120, "services and a creator studio.", size=9.5, fill=VOID[700])
    s.text(20, 142, "≈ 90 proposals", size=11, weight=700, fill=VOID[900], font=MONO)

    s.arrow(250, 94, 288, 94, stroke=ORBIT[600])

    s.rect(296, 34, 300, 120, r=12, fill=ORBIT[50], stroke=ORBIT[200])
    s.text(316, 58, "Six questions, asked of each", size=12, weight=700, fill=ORBIT[700])
    for i, q in enumerate(["Which of the three identity pillars does it strengthen?",
                           "What is its performance budget?",
                           "What is its row in the AI privacy table?",
                           "What does it cost users who never use it?",
                           "Can we build and maintain it at the quality bar?",
                           "What are we deleting to make room?"]):
        s.text(316, 76 + i * 13, f"{i+1}. {q}", size=8.5, fill=VOID[700])

    s.arrow(596, 94, 634, 94, stroke=ORBIT[600])

    s.rect(642, 34, 258, 120, r=12, fill=SUCCESS_S, stroke="#9AD0AF")
    s.text(662, 58, "The MVP", size=12, weight=700, fill=SUCCESS)
    s.text(662, 78, "Thirteen features, each specified", size=9.5, fill=VOID[700])
    s.text(662, 92, "to purpose, problem, metrics, UI,", size=9.5, fill=VOID[700])
    s.text(662, 106, "edge cases and failure cases.", size=9.5, fill=VOID[700])
    s.text(662, 142, "13 features", size=11, weight=700, fill=SUCCESS, font=MONO)

    # outcomes
    outcomes = [
        ("MVP", "13", SUCCESS, SUCCESS_S, "Shipped in Phase 1"),
        ("Phase 2", "18", ORBIT[600], ORBIT[50], "Depth, once we know how the core is used"),
        ("Phase 3", "16", ORBIT[600], ORBIT[50], "Creator tools and protocol maturity"),
        ("Phase 4", "11", ORBIT[600], ORBIT[50], "The business platform"),
        ("Phase 5", "6", ORBIT[600], ORBIT[50], "The ecosystem, last"),
        ("Rejected", "26", DANGER, DANGER_S, "Each with a stated reason, recorded permanently"),
    ]
    x = 0
    for name, count, col, bg, note in outcomes:
        s.rect(x, 190, 142, 96, r=10, fill=bg)
        s.text(x + 71, 222, count, size=24, anchor="middle", weight=700, fill=col)
        s.text(x + 71, 240, name, size=10.5, anchor="middle", weight=700, fill=VOID[900])
        words, line, lines = note.split(), "", []
        for wd in words:
            if len(line) + len(wd) > 22:
                lines.append(line); line = wd
            else:
                line = (line + " " + wd).strip()
        lines.append(line)
        for j, ln in enumerate(lines[:3]):
            s.text(x + 71, 256 + j * 11, ln, size=8, anchor="middle", fill=VOID[600])
        x += 152

    s.rect(0, 306, W, 112, r=12, fill=VOID[900])
    s.text(24, 334, "Nothing was silently dropped", size=13, weight=700, fill=VOID[0])
    for i, t in enumerate([
        "Every rejection is recorded with its reasoning, and the counter-argument is written down in advance — because these proposals will come back,",
        "from a growth team, an investor, or in response to a competitor's launch. A feed. Ads, \"just tastefully\". Short-form video. Read-your-messages AI.",
        "Address-book upload. Streaks. Unlimited free storage. The answers are already written, so they do not have to be re-derived under pressure."]):
        s.text(24, 358 + i * 17, t, size=9.5, fill=VOID[300])
    s.text(24, 410, "Part 10 — Scope Governance", size=9, weight=700, fill=AURORA[300], font=MONO)
    return "scope-funnel", s, "The triage: ~90 proposals in, 13 features out, 26 permanent rejections — each with its reason on the record."


def performance_budget():
    s = Svg(W, 440, VOID[0])
    s.kicker(0, 12, "Figure — Performance budgets, by device tier")
    s.text(0, 34, "Tier C is the design target, not the fallback. Any screen that only feels good on Tier A is unfinished.",
           size=10, fill=VOID[600])

    tiers = [("Tier A", "flagship, ≤ 2 years", "~15 % of market", ORBIT[300]),
             ("Tier B", "mainstream, 2–4 years", "~50 % of market", ORBIT[500]),
             ("Tier C", "entry-level, low RAM", "~35 % of market", ORBIT[800])]
    for i, (n, d, share, col) in enumerate(tiers):
        x = 636
        s.rect(x, 56 + i * 42, 264, 36, r=8, fill=VOID[50])
        s.rect(x, 56 + i * 42, 6, 36, r=3, fill=col)
        s.text(x + 18, 72 + i * 42, n, size=10.5, weight=700)
        s.text(x + 70, 72 + i * 42, d, size=9, fill=VOID[600])
        s.text(x + 18, 86 + i * 42, share, size=9, fill=VOID[500])

    budgets = [
        ("Cold launch to interactive", 450, 800, 1500, "ms", 1500),
        ("Touch → first visual response", 100, 100, 100, "ms", 1500),
        ("Send tap → bubble visible", 50, 50, 50, "ms", 1500),
        ("Search keystroke → results", 50, 50, 50, "ms", 1500),
        ("Send → delivered (p95)", 700, 700, 700, "ms", 1500),
    ]
    y = 62
    for name, a, b, c, unit, scale in budgets:
        s.text(0, y + 10, name, size=10, fill=VOID[800])
        bx = 250
        bw = 360
        for j, (v, col) in enumerate([(a, ORBIT[300]), (b, ORBIT[500]), (c, ORBIT[800])]):
            wpx = max(3, bw * v / scale)
            s.rect(bx, y + j * 9 - 2, wpx, 7, r=3.5, fill=col)
            if j == 2:
                s.text(bx + wpx + 8, y + 24, f"{a} / {b} / {c} {unit}", size=8.5, fill=VOID[600], font=MONO)
        y += 46

    mem = [("Idle", 120, 100, 80), ("Active + media", 220, 180, 140), ("Peak, any operation", 400, 350, 260)]
    s.text(0, 296, "Memory ceilings (MB) — stricter on weaker hardware, not looser", size=11, weight=700)
    s.text(0, 312, "Low-memory Android kills background apps aggressively. A large footprint turns every warm launch into a cold one.",
           size=9, fill=VOID[600])
    x = 0
    for name, a, b, c in mem:
        s.rect(x, 326, 190, 76, r=10, fill=VOID[50], stroke=VOID[200])
        s.text(x + 14, 348, name, size=10, weight=700)
        for j, (t, v) in enumerate([("A", a), ("B", b), ("C", c)]):
            s.text(x + 14 + j * 60, 372, t, size=8.5, fill=VOID[500])
            s.text(x + 14 + j * 60, 388, str(v), size=13, weight=700, fill=ORBIT[600 + j * 100] if j < 2 else ORBIT[800], font=MONO)
        x += 204

    s.rect(624, 326, 276, 76, r=10, fill=VOID[900])
    s.text(640, 348, "The budget process", size=10.5, weight=700, fill=VOID[0])
    s.text(640, 366, "Measured in CI on physical hardware,", size=8.5, fill=VOID[300])
    s.text(640, 379, "per pull request, per tier. A regression", size=8.5, fill=VOID[300])
    s.text(640, 392, "fails the build — not a warning, a ticket.", size=8.5, fill=VOID[300])

    s.text(0, 424, "Exceeding a budget requires an explicit trade: something else gives up an equivalent amount, recorded in the pull request. Budgets do not inflate quietly.",
           size=9.5, fill=VOID[600])
    return "performance-budgets", s, "The numbers defended on every pull request, on real hardware, at every tier."
