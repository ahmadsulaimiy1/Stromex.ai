"""Architecture, flow and process diagrams (Parts 4, 5, 6)."""
from svgkit import Svg, ORBIT, AURORA, VOID, SUCCESS, SUCCESS_S, WARNING, WARNING_S, \
    DANGER, DANGER_S, UI, MONO

W = 900


def system_architecture():
    s = Svg(W, 660, VOID[0])
    s.kicker(0, 12, "Figure — System architecture")

    # ---- device boundary
    s.rect(0, 30, 400, 250, r=14, fill=ORBIT[50], stroke=ORBIT[200], dash="5 4")
    s.text(16, 52, "The device", size=12, weight=700, fill=ORBIT[700])
    s.text(16, 68, "Source of truth for everything on screen", size=9.5, fill=VOID[500])

    s.box(16, 80, 178, 46, "Flutter UI", "presentation · application", fill=VOID[0], stroke=ORBIT[200])
    s.box(206, 80, 178, 46, "Domain logic", "pure Dart, no framework", fill=VOID[0], stroke=ORBIT[200])
    s.box(16, 136, 118, 58, "SQLite", ["Drift + SQLCipher", "messages · index"], fill=VOID[0], stroke=ORBIT[200])
    s.box(142, 136, 118, 58, "libsignal", ["Rust via FFI", "X3DH · ratchet"], fill=VOID[0], stroke=ORBIT[200])
    s.box(268, 136, 116, 58, "On-device AI", ["translate · ASR", "scam · search"], fill=AURORA["050"],
          stroke=AURORA[300], tcol=AURORA[800], scol=AURORA[700])
    s.box(16, 204, 368, 40, "Outbox", "durable, ordered, idempotent — drains when the network returns",
          fill=VOID[50], stroke=VOID[200])
    s.text(200, 266, "Plaintext never leaves this boundary unless the user grants it (ADR-005)",
           size=9.5, anchor="middle", fill=ORBIT[700], weight=600)

    # ---- transport
    s.arrow(200, 280, 200, 316, stroke=ORBIT[600])
    s.text(212, 302, "TLS 1.3 · pinned · protobuf over one WebSocket", size=9.5, fill=VOID[500])

    # ---- edge + gateway
    s.box(0, 320, 400, 44, "Gateway (Go)", "socket termination · auth · rate limit · fan-out",
          fill=ORBIT[500], stroke=ORBIT[600], tcol=VOID[0], scol=ORBIT[100])

    # ---- services
    s.rect(0, 386, 400, 128, r=14, fill=VOID[50], stroke=VOID[200])
    s.text(16, 408, "Services — a modular monolith, four deployables (ADR-002)", size=10.5,
           weight=600, fill=VOID[700])
    s.box(16, 420, 118, 76, "core", ["accounts · groups", "conversations", "channels"],
          fill=VOID[0], stroke=VOID[200])
    s.box(142, 420, 118, 76, "media", ["presigned URLs", "ciphertext only"], fill=VOID[0], stroke=VOID[200])
    s.box(268, 420, 116, 76, "push", ["APNs · FCM", "no content"], fill=VOID[0], stroke=VOID[200])

    # ---- stores
    s.rect(0, 536, 400, 106, r=14, fill=VOID[0], stroke=VOID[200])
    s.text(16, 558, "State", size=10.5, weight=600, fill=VOID[700])
    s.box(16, 568, 118, 58, "PostgreSQL", ["accounts · envelopes", "partitioned"], fill=VOID[50], stroke=VOID[200])
    s.box(142, 568, 118, 58, "Redis", ["presence · limits", "ephemeral"], fill=VOID[50], stroke=VOID[200])
    s.box(268, 568, 116, 58, "Object store", ["media ciphertext", "+ CDN"], fill=VOID[50], stroke=VOID[200])

    s.arrow(200, 364, 200, 384, stroke=VOID[400])
    s.arrow(200, 514, 200, 534, stroke=VOID[400])

    # ---- right column: realtime media + notes
    s.rect(440, 30, 460, 250, r=14, fill=VOID[50], stroke=VOID[200])
    s.text(456, 52, "Real-time media", size=12, weight=700, fill=VOID[900])
    s.text(456, 68, "Signalling rides the same WebSocket — no second stack", size=9.5, fill=VOID[500])
    s.box(456, 80, 200, 52, "1:1 call", ["peer-to-peer first (ICE/STUN)", "DTLS-SRTP end to end"],
          fill=VOID[0], stroke=VOID[200])
    s.box(672, 80, 212, 52, "TURN relay", ["only when NAT traversal fails"], fill=VOID[0], stroke=VOID[200])
    s.box(456, 144, 428, 60, "LiveKit SFU — group calls",
          ["insertable-stream E2EE (SFrame): the SFU forwards frames it cannot decrypt",
           "an MCU is rejected — server-side mixing means server-side plaintext"],
          fill=ORBIT[50], stroke=ORBIT[200], tcol=ORBIT[700], scol=VOID[600])
    s.box(456, 216, 428, 44, "Audio priority allocator",
          "audio takes its floor first; video receives only the remainder",
          fill=VOID[0], stroke=VOID[200])

    # ---- what the server can and cannot see
    s.rect(440, 320, 460, 330, r=14, fill=VOID[0], stroke=VOID[200])
    s.text(456, 344, "What the server holds", size=12, weight=700, fill=VOID[900])

    y = 356
    for label, detail, ok in [
        ("Routing metadata", "who talked to whom, when, message size", False),
        ("Undelivered envelopes", "ciphertext only — deleted on delivery, or at 30 days", False),
        ("Delivered envelopes", "not stored at all; the server is a relay, not an archive", True),
        ("Message content", "no key exists server-side to read it", True),
        ("Media", "client-encrypted per file; the store holds ciphertext", True),
        ("Search index", "none — the only index is on the device", True),
    ]:
        col = SUCCESS if ok else WARNING
        bg = SUCCESS_S if ok else WARNING_S
        s.rect(456, y, 428, 40, r=8, fill=bg)
        s.circle(474, y + 20, 5.5, fill=col)
        s.text(490, y + 17, label, size=11, weight=600, fill=VOID[900])
        s.text(490, y + 31, detail, size=9.5, fill=VOID[600])
        y += 44

    s.text(456, y + 14, "Green — cannot be read, even by us.   Amber — necessarily processed in order to route.",
           size=9.5, fill=VOID[500])
    return "system-architecture", s, "System architecture — the device is the source of truth; the server is a relay that cannot read what it carries."


def backend_services():
    s = Svg(W, 500, VOID[0])
    s.kicker(0, 12, "Figure — Backend services and their scaling triggers")

    cols = [
        ("gateway", ORBIT[500], VOID[0], ORBIT[100],
         ["WebSocket termination", "authentication", "connection state", "per-socket rate limit", "fan-out to devices"],
         "Stateful — holds sockets", ">150 K concurrent sockets\n→ add instances, shard by\n   consistent hash on user ID"),
        ("core", VOID[0], VOID[900], VOID[500],
         ["accounts · devices", "conversations · groups", "channels · profiles", "message envelopes", "prekey bundles"],
         "Stateless — scales flat", "Write CPU > 60 %\n→ read replicas, then\n   partition by user-ID range"),
        ("media", VOID[0], VOID[900], VOID[500],
         ["upload orchestration", "presigned URLs", "resumable transfers", "retention enforcement", "ciphertext only"],
         "Stateless — scales flat", "Egress cost per user\n→ CDN tiering and\n   longer edge TTLs"),
        ("push", VOID[0], VOID[900], VOID[500],
         ["APNs + FCM dispatch", "token lifecycle", "content-free envelopes", "priority selection", "invalid-token pruning"],
         "Queue-driven", "Dispatch backlog\n→ scale workers; push is\n   never in the send path"),
    ]
    x = 0
    for name, fill, tcol, scol, items, prop, trig in cols:
        s.rect(x, 30, 210, 200, r=12, fill=fill, stroke=ORBIT[600] if fill != VOID[0] else VOID[200])
        s.text(x + 16, 56, name, size=15, weight=700, fill=tcol, font=MONO)
        s.line(x + 16, 66, x + 194, 66, stroke=ORBIT[300] if fill != VOID[0] else VOID[200], sw=1)
        for i, it in enumerate(items):
            s.circle(x + 20, 84 + i * 20 - 3.5, 2, fill=scol)
            s.text(x + 30, 84 + i * 20, it, size=10, fill=tcol if fill == VOID[0] else ORBIT[50])
        s.text(x + 16, 214, prop, size=9.5, weight=600, fill=scol)

        s.rect(x, 244, 210, 96, r=12, fill=VOID[50], stroke=VOID[200])
        s.kicker(x + 16, 266, "Scaling trigger")
        for i, ln in enumerate(trig.split("\n")):
            s.text(x + 16, 284 + i * 14, ln, size=9.5, fill=VOID[600])
        x += 230

    s.rect(0, 362, W, 118, r=12, fill=ORBIT[50], stroke=ORBIT[200])
    s.text(20, 388, "Why a modular monolith and not microservices", size=12, weight=700, fill=ORBIT[700])
    for i, ln in enumerate([
        "Module boundaries inside core are enforced by an import linter from day one, so extracting a module later is a mechanical change.",
        "We take on the boundary discipline immediately and the deployment complexity only when a module's scaling profile actually diverges.",
        "A five-person backend team split across twelve services spends its time on distributed-systems debugging rather than on the product.",
    ]):
        s.text(20, 412 + i * 19, ln, size=10.5, fill=VOID[700])
    s.text(20, 470, "ADR-002", size=9.5, weight=700, fill=ORBIT[600], font=MONO)
    return "backend-services", s, "The four Phase 1 deployables, what each owns, and the measured trigger that would split it out."


def sync_architecture():
    s = Svg(W, 490, VOID[0])
    s.kicker(0, 12, "Figure — Offline-first synchronisation")

    # outbound
    s.rect(0, 30, W, 200, r=14, fill=VOID[0], stroke=VOID[200])
    s.text(20, 54, "Outbound — the user says something", size=12, weight=700)
    steps = [
        ("1", "Compose", "draft persisted on\nevery keystroke pause"),
        ("2", "Local write", "SQLite first — the\nbubble is already on screen"),
        ("3", "Outbox row", "durable, ordered,\nidempotency key attached"),
        ("4", "Drain", "background worker,\nper-conversation order"),
        ("5", "Server sequence", "authoritative order assigned\n— never a device clock"),
        ("6", "Per-device fan-out", "one envelope per\nrecipient device"),
    ]
    x = 20
    for i, (n, t, d) in enumerate(steps):
        s.rect(x, 70, 122, 96, r=10, fill=VOID[50] if i < 4 else ORBIT[50],
               stroke=VOID[200] if i < 4 else ORBIT[200])
        s.circle(x + 18, 90, 10, fill=ORBIT[500] if i < 4 else ORBIT[600])
        s.text(x + 18, 94, n, size=11, anchor="middle", weight=700, fill=VOID[0])
        s.text(x + 34, 94, t, size=11, weight=600, fill=VOID[900])
        for j, ln in enumerate(d.split("\n")):
            s.text(x + 12, 124 + j * 14, ln, size=9, fill=VOID[600])
        if i < 5:
            s.arrow(x + 122, 118, x + 138, 118)
        x += 140
    s.text(20, 190, "50 ms", size=11, weight=700, fill=ORBIT[600], font=MONO)
    s.text(66, 190, "budget from send tap to bubble visible — steps 1–3 only; the network is not in this path.",
           size=10, fill=VOID[600])
    s.text(20, 212, "A failed send blocks only its own conversation. The queue never stalls as a whole.",
           size=10, fill=VOID[600])

    # inbound
    s.rect(0, 250, 560, 168, r=14, fill=VOID[0], stroke=VOID[200])
    s.text(20, 274, "Inbound — cursor, gap detection, acknowledgement", size=12, weight=700)
    s.box(20, 290, 150, 46, "Per-conversation cursor", "\"everything after N\"", fill=VOID[50], stroke=VOID[200], tsize=11)
    s.arrow(170, 313, 194, 313)
    s.box(194, 290, 150, 46, "Server streams", "envelopes in sequence", fill=VOID[50], stroke=VOID[200], tsize=11)
    s.arrow(344, 313, 368, 313)
    s.box(368, 290, 172, 46, "Decrypt → write → ack", "the ack is what permits deletion",
          fill=ORBIT[50], stroke=ORBIT[200], tsize=11, tcol=ORBIT[700])
    s.rect(20, 348, 520, 54, r=10, fill=WARNING_S)
    s.text(36, 370, "Sequence gap detected", size=11, weight=700, fill=WARNING)
    s.text(36, 388, "Automatic retransmit request. An unfillable gap becomes a visible marker in the transcript —",
           size=9.5, fill=VOID[700])
    s.text(36, 400, "never an invisible hole. Silent loss is the worst failure mode a messenger has.", size=9.5, fill=VOID[700])

    # conflict rules
    s.rect(580, 250, 320, 168, r=14, fill=VOID[50], stroke=VOID[200])
    s.text(600, 274, "Conflicts resolve by rule, never by asking", size=11.5, weight=700)
    rules = [("Ordering", "server sequence, always"),
             ("Edits", "last writer wins by device time;\nthe loser is kept in edit history"),
             ("Deletions", "always beat edits"),
             ("Membership", "server is authoritative"),
             ("Drafts", "per device — never synced")]
    y = 294
    for k, v in rules:
        s.text(600, y, k, size=10, weight=700, fill=ORBIT[700])
        for j, ln in enumerate(v.split("\n")):
            s.text(674, y + j * 12, ln, size=9.5, fill=VOID[600])
        y += 25 + (12 if "\n" in v else 0)

    s.text(0, 448, "The user is never shown a merge dialog. ADR-008.", size=10, fill=VOID[500])
    return "sync-architecture", s, "Local-first sync: the outbox guarantees ordering and delivery; gaps are surfaced rather than hidden."


def auth_flow():
    s = Svg(W, 560, VOID[0])
    s.kicker(0, 12, "Figure — Identity, session, and device linking")

    # registration
    s.rect(0, 30, 430, 240, r=14, fill=VOID[0], stroke=VOID[200])
    s.text(20, 54, "Registration", size=12, weight=700)
    seq = [("Choose a username", "@handle, globally unique — identity is not a phone number"),
           ("Add a recovery method", "phone or email, optional; if skipped the consequence is stated plainly"),
           ("Verify", "rate limited by IP, device attestation, proof-of-work under attack"),
           ("Generate keys on device", "identity key, signed prekey, one-time prekeys"),
           ("Publish prekey bundle", "public halves only — the private key never leaves")]
    y = 72
    for i, (t, d) in enumerate(seq):
        s.circle(34, y + 11, 10, fill=ORBIT[500])
        s.text(34, y + 15, str(i + 1), size=10.5, anchor="middle", weight=700, fill=VOID[0])
        s.text(54, y + 8, t, size=11, weight=600)
        s.text(54, y + 22, d, size=9.5, fill=VOID[600])
        if i < len(seq) - 1:
            s.line(34, y + 23, 34, y + 33, stroke=VOID[300], sw=1.5)
        y += 38

    # session
    s.rect(0, 288, 430, 200, r=14, fill=VOID[50], stroke=VOID[200])
    s.text(20, 312, "Session", size=12, weight=700)
    s.box(20, 326, 180, 50, "Device keypair", "long-lived, in the platform keystore",
          fill=VOID[0], stroke=VOID[200], tsize=11, ssize=9.5)
    s.box(214, 326, 196, 50, "Access token", "15 minutes", fill=VOID[0], stroke=VOID[200], tsize=11, ssize=9.5)
    s.arrow(200, 351, 212, 351)
    s.box(20, 388, 390, 44, "Refresh token — rotating, bound to the device key",
          "token theft without the device key is useless", fill=ORBIT[50], stroke=ORBIT[200],
          tsize=11, ssize=9.5, tcol=ORBIT[700])
    s.text(20, 456, "Biometric app lock gates the local database key only. It is not a server-side factor,", size=9.5, fill=VOID[600])
    s.text(20, 470, "and we do not claim that it is. Passkeys replace SMS wherever the platform allows (Phase 2).", size=9.5, fill=VOID[600])

    # device linking
    s.rect(470, 30, 430, 458, r=14, fill=VOID[0], stroke=VOID[200])
    s.text(490, 54, "Linking a second device", size=12, weight=700)
    s.text(490, 70, "Every device is an independent cryptographic identity. No primary device exists.",
           size=9.5, fill=VOID[600])

    lanes = [("New device", 500), ("Existing phone", 700)]
    for name, cx in lanes:
        s.text(cx, 96, name, size=10, anchor="middle", weight=700, fill=VOID[500])
        s.line(cx, 106, cx, 400, stroke=VOID[200], sw=1.5, dash="4 4")

    msgs = [(0, "QR code shown, valid 60 s", 126, False),
            (1, "Scan", 164, True),
            (1, "Safety number shown on BOTH screens — user confirms they match", 202, False),
            (1, "Choose history: none / 30 days / everything", 250, False),
            (1, "Transfer size shown before it starts", 288, False),
            (1, "Link confirmed", 326, False)]
    for lane, text, yy, right in msgs:
        if lane == 0:
            s.rect(490, yy - 14, 200, 26, r=6, fill=ORBIT[50])
            s.text(500, yy + 3, text, size=9.5, fill=ORBIT[700])
        else:
            s.rect(490, yy - 14, 396, 26 if "\n" not in text else 40, r=6, fill=VOID[50])
            s.text(500, yy + 3, text, size=9.5, fill=VOID[700])
        if right:
            s.arrow(516, yy + 18, 684, yy + 18, stroke=ORBIT[600])

    s.rect(490, 348, 396, 70, r=10, fill=WARNING_S)
    s.text(506, 370, "Every existing device is notified — loudly", size=11, weight=700, fill=WARNING)
    s.text(506, 388, "and a permanent entry is written to the device log: name, platform, when", size=9.5, fill=VOID[700])
    s.text(506, 402, "linked, last active, coarse region. Silent device addition is the attack that", size=9.5, fill=VOID[700])
    s.text(506, 416, "breaks end-to-end encryption for real people. ADR-012.", size=9.5, fill=VOID[700])
    return "auth-flow", s, "Registration, session handling, and the deliberately loud device-linking flow."


def notification_flow():
    s = Svg(W, 400, VOID[0])
    s.kicker(0, 12, "Figure — A notification that the server cannot read")

    stages = [
        ("Sender", ["encrypts for each", "recipient device"], VOID[0], VOID[200], VOID[900]),
        ("Server", ["stores the envelope,", "cannot decrypt it"], VOID[50], VOID[200], VOID[900]),
        ("APNs / FCM", ["carries only:", "envelope id, conv hash,", "priority"], WARNING_S, "#F0C79A", VOID[900]),
        ("Device wakes", ["notification service", "extension, 24 MB limit"], VOID[0], VOID[200], VOID[900]),
        ("Fetch + decrypt", ["locally, on device"], ORBIT[50], ORBIT[200], ORBIT[700]),
        ("Notification text", ["built on the device", "from plaintext"], SUCCESS_S, "#9AD0AF", VOID[900]),
    ]
    x = 0
    for i, (t, ds, fill, stroke, tcol) in enumerate(stages):
        s.rect(x, 40, 132, 96, r=10, fill=fill, stroke=stroke)
        s.text(x + 66, 66, t, size=11.5, anchor="middle", weight=700, fill=tcol)
        for j, d in enumerate(ds):
            s.text(x + 66, 86 + j * 13, d, size=9, anchor="middle", fill=VOID[600])
        if i < len(stages) - 1:
            s.arrow(x + 132, 88, x + 152, 88, stroke=ORBIT[600])
        x += 152

    s.rect(0, 158, 440, 100, r=12, fill=VOID[50], stroke=VOID[200])
    s.text(20, 182, "The payload, in full", size=11.5, weight=700)
    s.rect(20, 194, 400, 46, r=8, fill=VOID[900])
    s.text(36, 214, "{ envelope_id, conversation_id_hash, priority }", size=11, fill=AURORA[300], font=MONO)
    s.text(36, 230, "no sender name, no preview, no content", size=9, fill=VOID[400], font=MONO)

    s.rect(460, 158, 440, 100, r=12, fill=ORBIT[50], stroke=ORBIT[200])
    s.text(480, 182, "Why it is built this way", size=11.5, weight=700, fill=ORBIT[700])
    s.text(480, 202, "The simplest implementation puts the message text in the payload —", size=9.5, fill=VOID[700])
    s.text(480, 216, "and hands the most-read text in the product to Apple and Google.", size=9.5, fill=VOID[700])
    s.text(480, 236, "If the fetch fails we show \"New message\" rather than nothing. ADR-007.", size=9.5, fill=VOID[600])

    s.rect(0, 280, W, 100, r=12, fill=VOID[0], stroke=VOID[200])
    s.text(20, 304, "What may notify a user", size=11.5, weight=700)
    ok = ["a message addressed to you", "an incoming call", "a security event on your account", "a completion you asked to be told about"]
    no = ["re-engagement prompts", "\"you have unread messages\"", "feature announcements, tips", "streaks, birthdays, \"friend is active\""]
    for i, t in enumerate(ok):
        s.circle(30, 324 + i * 15, 4, fill=SUCCESS)
        s.text(42, 328 + i * 15, t, size=9.5, fill=VOID[700])
    s.text(480, 304, "What may never notify a user", size=11.5, weight=700, fill=DANGER)
    for i, t in enumerate(no):
        s.line(486, 324 + i * 15, 494, 324 + i * 15, stroke=DANGER, sw=2)
        s.text(502, 328 + i * 15, t, size=9.5, fill=VOID[700])
    return "notification-flow", s, "Push carries a wake-up signal and nothing else; the notification text is assembled on the device."


def encryption_map():
    s = Svg(W, 520, VOID[0])
    s.kicker(0, 12, "Figure — Where the encryption promise starts and stops")

    rows = [
        ("1:1 messages", "Double Ratchet, per-device sessions", "End-to-end", True),
        ("Group messages", "Sender Keys; rotate on every removal", "End-to-end", True),
        ("Voice / video 1:1", "DTLS-SRTP, peer-to-peer where possible", "End-to-end", True),
        ("Group calls", "SFrame — the SFU forwards frames it cannot decrypt", "End-to-end", True),
        ("Media files", "per-file AES-256-GCM key, carried inside the envelope", "End-to-end", True),
        ("Stories", "encrypted to the chosen audience's device keys", "End-to-end", True),
        ("On-device AI", "translation, transcription, scam detection, search", "Never leaves", True),
        ("Channels", "a public broadcast to strangers is not a private conversation", "In transit + at rest", False),
        ("Assistant conversation", "you are talking to a server, and the interface says so", "In transit + at rest", False),
        ("Granted server AI", "explicit, per conversation, revocable, disclosed to all parties", "In transit + at rest", False),
    ]
    y = 34
    for label, detail, state, e2e in rows:
        fill = SUCCESS_S if e2e else WARNING_S
        col = SUCCESS if e2e else WARNING
        s.rect(0, y, 620, 38, r=8, fill=fill)
        s.circle(20, y + 19, 5, fill=col)
        s.text(36, y + 16, label, size=11, weight=600)
        s.text(36, y + 30, detail, size=9.5, fill=VOID[600])
        s.rect(490, y + 9, 120, 20, r=10, fill=col)
        s.text(550, y + 23, state, size=9, anchor="middle", weight=700, fill=VOID[0])
        y += 42

    s.rect(650, 34, 250, 210, r=12, fill=VOID[900])
    s.text(670, 60, "What we deliberately", size=11.5, weight=700, fill=VOID[0])
    s.text(670, 76, "did not build", size=11.5, weight=700, fill=VOID[0])
    for i, t in enumerate(["key escrow", "a server-side \"recover my\nmessages\" path", "plaintext cloud backup",
                           "a content-moderation\npipeline for private chats", "client-side scanning"]):
        yy = 100 + i * 28
        for j, ln in enumerate(t.split("\n")):
            s.text(686, yy + j * 12, ln, size=9.5, fill=VOID[300])
        s.line(670, yy - 3.5, 678, yy - 3.5, stroke=DANGER, sw=2)
        if "\n" in t:
            yy += 12
    s.text(670, 232, "Each is simple to build and", size=9, fill=VOID[400])

    s.rect(650, 256, 250, 200, r=12, fill=VOID[50], stroke=VOID[200])
    s.text(670, 280, "Honest limits", size=11.5, weight=700)
    for i, t in enumerate(["End-to-end encryption protects content",
                           "in transit and at rest on our servers.",
                           "",
                           "It does not protect against a",
                           "compromised device, a screenshot,",
                           "a malicious participant, or an",
                           "attacker who owns the OS.",
                           "",
                           "We say this in the product rather",
                           "than let marketing imply otherwise."]):
        s.text(670, 300 + i * 15, t, size=9.5, fill=VOID[700] if i < 7 else VOID[600])

    s.text(0, 476, "Sender Keys are O(members) on key distribution — which is exactly why groups are capped at 1,000 members at MVP.", size=10, fill=VOID[600])
    s.text(0, 494, "The cap is a published product decision derived from a protocol decision, not an arbitrary limit. MLS lifts it in Phase 3. ADR-003.", size=10, fill=VOID[600])
    return "encryption-map", s, "Every surface, and whether it is end-to-end encrypted — including the two that deliberately are not."
