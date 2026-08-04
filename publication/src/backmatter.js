/* Appendices and index. Compiled from the parts; nothing here adds doctrine. */
const D = require('/tmp/node_modules/docx');
const { Paragraph, TextRun, InternalHyperlink, Bookmark, TabStopType, Tab, PageBreak } = D;
const { C, F, PAGE } = require('./theme');
const K = require('./content');

const P = (o) => new Paragraph(o);
const T = (t, o = {}) => new TextRun({ text: t, ...o });
const spacer = (h = 160) => P({ children: [T('')], spacing: { before: 0, after: h } });
const head = (a, t) => P({ style: 'FrontHeading',
  children: [new Bookmark({ id: a, children: [T(t)] })] });
const kicker = (t) => P({ style: 'Kicker', children: [T(t)] });
const body = (t, o = {}) => P({ style: 'Body', children: [T(t, o)] });
const lead = (t) => P({ style: 'Body', children: [T(t, { size: 23, color: C.void600 })] });
const link = (label, anchor, o = {}) => new InternalHyperlink({ anchor,
  children: [T(label, { color: C.orbit600, ...o })] });

// Parts 9 and 12 carry no N.M section numbers, so a reference to one of their
// sections resolves to the part itself rather than to a bookmark that is not there.
const VALID = new Set(
  Object.values(JSON.parse(require('fs').readFileSync(
    require('path').resolve(__dirname, '../build/sections.json'), 'utf8')))
    .flat().map((s) => s.anchor),
);
function resolve(ref) {
  const a = K.secAnchor(ref);
  return VALID.has(a) ? { anchor: a, label: '§' + ref }
    : { anchor: 'c_' + ref.split('.')[0], label: 'Part ' + ref.split('.')[0] };
}

// ---------------------------------------------------------------- Appendix A
const ADR_ROWS = [
  ['001', 'Flutter for every client platform',
    'Two native teams would mean two implementations of every subtle piece of encryption and sync logic — and two places for those bugs to differ.',
    'Flutter’s known jank sources become first-class engineering work'],
  ['002', 'A modular monolith in Go, not microservices',
    'Module boundaries are enforced by an import linter from day one, so extraction later is mechanical. Deployment complexity is deferred until a scaling profile actually diverges.',
    'Larger blast radius per deploy, mitigated by flags and staged rollout'],
  ['003', 'Signal Protocol via libsignal; Sender Keys; MLS deferred',
    'Cryptographic implementation bugs are silent, catastrophic, and fall hardest on the people most in need of protection. We do not write our own.',
    'Sender Keys are O(members): groups capped at 1,000 until MLS in Phase 3'],
  ['004', 'PostgreSQL for everything; ScyllaDB only on trigger',
    'Delivered envelopes are deleted, not archived. The hot dataset tracks undelivered traffic, not total history — which keeps Postgres viable far longer than intuition suggests.',
    'A migration is in our future if we succeed; the interface exists to absorb it'],
  ['005', 'AI never processes encrypted content without a visible grant',
    'On-device first; server-side only with a per-conversation, revocable, disclosed grant; otherwise the feature does not ship. The assistant conversation is a separate, labelled surface.',
    'Some AI features are worse than a competitor’s. We take the hit and say why'],
  ['006', 'LiveKit SFU with insertable-stream E2EE for group calls',
    'An MCU would mix server-side, which means plaintext server-side. Rejected outright.',
    'Operating an SFU fleet is real work; server-side recording is impossible'],
  ['007', 'Push notification payloads carry no content',
    'The simplest implementation hands the most-read text in the product to Apple and Google.',
    'A network round trip in the notification path, budgeted at p95 under 2 s'],
  ['008', 'Local-first architecture with an outbox',
    'A request/response client is unusable on an unreliable network, and offline support bolted on afterwards never really works.',
    'Local schema migrations become critical; every one is tested against real histories'],
  ['009', 'No advertising, ever; subscription and business revenue only',
    'An ad surface creates an incentive to build more inventory, and that incentive never reverses. It constrains architecture: no ad serving, no profiling pipeline, no engagement ranking.',
    'Slower revenue ramp; free users cost money; unit economics are a product constraint'],
  ['010', 'No address-book upload; username-first discovery',
    'Hashing a 10–15 digit number space provides essentially no protection. We decline to hold a social graph we promised not to build.',
    'Materially slower viral growth — the largest deliberate growth cost in the product'],
  ['011', 'SpaceTalk is greenfield, not an extension of StromeX',
    'Python’s concurrency model is a poor fit for hundreds of thousands of persistent sockets, and retrofitting a request/response codebase into a realtime one is usually slower than starting clean.',
    'Two stacks in one organisation. Open question if SpaceTalk is a rename'],
  ['012', 'Per-device identity keys; web as the MVP linked client',
    'A tethered companion device dies with the phone’s battery; a shared identity key means one compromised device compromises all of them.',
    'Fan-out is O(recipients × devices); history sync is explicit and user-controlled'],
];

function appendixA(APPARATUS) {
  const rows = ADR_ROWS.map((r) => [
    [link('ADR-' + r[0], 'a_' + r[0], { bold: true })],
    [T(r[1], { bold: true })],
    [T(r[2])],
    [T(r[3], { color: C.void600 })],
  ]);
  return [
    spacer(600),
    head('b_adr', 'Appendix A — Decision register'),
    lead('The twelve decisions with lasting consequence, in one view. Full records, with the alternatives considered and the conditions for revisiting each, are in Part 12.'),
    spacer(200),
    APPARATUS.dataTable(['#', 'Decision', 'Why', 'Cost accepted'], rows, [11, 21, 40, 28]),
    spacer(220),
    body('All twelve are Accepted at version 1.0. None has been superseded. An ADR is never edited after acceptance — a changed decision becomes a new record that supersedes the old one, so the reasoning behind a reversal stays legible.', { color: C.void600 }),
  ];
}

// ---------------------------------------------------------------- Appendix B
function appendixB(APPARATUS) {
  const perf = [
    ['Cold launch to interactive (p95)', '< 450 ms', '< 800 ms', '< 1,500 ms', 'Part 8 §8.2'],
    ['Frame rate floor', '60 fps', '60 fps', '60 fps', 'Part 8 §8.3'],
    ['Dropped frames, 10,000-message scroll', '< 0.5 %', '< 0.5 %', '< 0.5 %', 'Part 8 §8.3'],
    ['Touch → first visual response', '< 100 ms', '< 100 ms', '< 100 ms', 'Part 8 §8.4'],
    ['Send tap → bubble visible', '< 50 ms', '< 50 ms', '< 50 ms', 'Part 8 §8.4'],
    ['Send → delivered (p50 / p95)', '250 / 700 ms', '250 / 700 ms', '250 / 700 ms', 'Part 8 §8.4'],
    ['Search keystroke → local results', '< 50 ms', '< 50 ms', '< 50 ms', 'Part 8 §8.4'],
    ['Call initiate → callee ringing (p75)', '< 1.2 s', '< 1.2 s', '< 1.2 s', 'Part 8 §8.4'],
    ['Memory, idle', '< 120 MB', '< 100 MB', '< 80 MB', 'Part 8 §8.5'],
    ['Memory, peak', '< 400 MB', '< 350 MB', '< 260 MB', 'Part 8 §8.5'],
    ['Battery, idle connected', '< 1 %/h', '< 1 %/h', '< 1 %/h', 'Part 8 §8.6'],
    ['Battery, video call', '< 12 %/h', '< 12 %/h', '< 12 %/h', 'Part 8 §8.6'],
    ['Daily background data, idle account', '< 1 MB', '< 1 MB', '< 1 MB', 'Part 8 §8.6'],
    ['Crash-free sessions', '> 99.9 %', '> 99.9 %', '> 99.9 %', 'Part 8 §8.10'],
    ['Message delivery success', '100 %', '100 %', '100 %', 'Part 8 §8.10'],
  ];
  const targets = [
    ['On-device AI execution rate', '> 85 % of all invocations', 'the privacy promise made measurable', 'Part 5 §5.8'],
    ['Ungranted AI on encrypted content', 'zero, audited continuously', 'any non-zero result is a Sev-1 incident', 'Part 5 §5.8'],
    ['Scam-warning precision', '> 95 % per pattern class', 'automatic rollback below the threshold', 'Part 4 §4.7'],
    ['Notification opt-out rate', '< 10 %', 'the clearest measure of the calm promise', 'Part 5 §5.12'],
    ['Notifications from non-humans', 'zero, verified per release', 'audited across every notification type', 'Part 5 §5.12'],
    ['D30 retention (Phase 1 gate)', '≥ 40 %', 'not signups — the gate is retention', 'Part 9'],
    ['Subscription conversion (Phase 2 gate)', '≥ 3 %', 'with positive contribution margin', 'Part 9'],
    ['Accessibility automated checks', '100 % pass, zero suppressions', 'a launch requirement, not a Phase 2 item', 'Part 8 §8.9'],
    ['Groups at MVP', '≤ 1,000 members', 'derived from Sender Keys, not arbitrary', 'Part 5 §5.5'],
    ['Linked devices at MVP', '≤ 4', 'each an independent cryptographic identity', 'Part 5 §5.13'],
    ['File size, free / Plus', '2 GB / 10 GB', 'stated up front, not discovered at 99 %', 'Part 11 §11.2'],
    ['Creator take rate', '10 %', 'against a market standard of 30 %', 'Part 11 §11.3'],
  ];
  const xref = (s) => {
    const m = s.match(/§(\d+\.\d+)/);
    if (!m) return [link(s, 'c_' + s.match(/Part (\d+)/)[1], { size: 16 })];
    const t = resolve(m[1]);
    return [link(s.replace('§' + m[1], t.label.replace('Part ', '§')), t.anchor, { size: 16 })];
  };
  return [
    P({ children: [new PageBreak()] }),
    spacer(600),
    head('b_numbers', 'Appendix B — The numbers, consolidated'),
    lead('Every budget and target that a release is measured against, in one place. Device tiers are defined in Part 8 §8.7: Tier A flagship, Tier B mainstream, Tier C entry-level — and Tier C is the design target, not the fallback.'),
    spacer(200),
    kicker('PERFORMANCE BUDGETS — MEASURED IN CI, ON PHYSICAL HARDWARE, PER PULL REQUEST'),
    APPARATUS.dataTable(['Budget', 'Tier A', 'Tier B', 'Tier C', 'Source'],
      perf.map((r) => [[T(r[0])], [T(r[1], { font: F.mono, size: 15 })],
        [T(r[2], { font: F.mono, size: 15 })], [T(r[3], { font: F.mono, size: 15, bold: true })],
        xref(r[4])]), [36, 15, 15, 15, 19]),
    spacer(260),
    kicker('PRODUCT AND GOVERNANCE TARGETS'),
    APPARATUS.dataTable(['Target', 'Value', 'Why it is set there', 'Source'],
      targets.map((r) => [[T(r[0])], [T(r[1], { bold: true })], [T(r[2], { color: C.void600 })], xref(r[3])]),
      [28, 22, 34, 16]),
    spacer(220),
    body('A budget that is not measured in CI does not exist. Exceeding one requires an explicit trade — something else gives up an equivalent amount, recorded in the pull request — so budgets do not inflate quietly.', { color: C.void600 }),
  ];
}

// ---------------------------------------------------------------- Appendix C
const GLOSSARY = [
  ['Aurora', 'The intelligence colour. Reserved absolutely for assistant output, so a reader can tell at a glance whether a person or a model produced something.', '2.3'],
  ['Callout panel', 'A tinted panel marking a passage that changes what you should do, not merely what you should know.', null],
  ['Channel', 'A one-to-many broadcast a subscriber chooses to receive, delivered chronologically to 100 % of subscribers. Not end-to-end encrypted, and labelled as such.', '5.6'],
  ['Conversation', 'The atomic unit of the product. A person, a group, a channel and the assistant are all rows in one list, differing in what they contain rather than where they live.', '3.1'],
  ['Device tier', 'A, B or C — flagship, mainstream, entry-level. Every performance budget is stated per tier, and Tier C is the design target.', '8.7'],
  ['Double Ratchet', 'The message-encryption ratchet providing forward secrecy and post-compromise security, used via libsignal for 1:1 messages.', '6.7'],
  ['Envelope', 'The routed unit the server stores: conversation, sender device, recipient device, sequence, ciphertext. The server can see who talked to whom and when, and nothing else.', '6.4'],
  ['Grant', 'An explicit, per-conversation, revocable permission for server-side AI processing, shown in the header and disclosed to every participant.', '4.1'],
  ['Local-first', 'The on-device database is the source of truth for the interface; the network updates it in the background rather than serving it.', '6.8'],
  ['MLS', 'Messaging Layer Security, RFC 9420. The group protocol that lifts the 1,000-member ceiling, scheduled for Phase 3.', '6.7'],
  ['Natural zone', 'The bottom 40 % of a phone screen, reachable by thumb without a regrip. Every high-frequency action lives there; no destructive action does.', '3.12'],
  ['Orbit', 'The brand action colour, hue ≈ 231°. One accent, so “what is the primary action here?” is answerable without thought.', '2.2'],
  ['Outbox', 'The durable, ordered, idempotent queue of local mutations that drains when connectivity returns. A failed send blocks only its own conversation.', '6.8'],
  ['Run', 'Consecutive messages from one sender within 60 seconds, grouped with tightened spacing so a burst reads as one utterance.', '2.10'],
  ['Sender Keys', 'The group-messaging scheme in which each sender holds a per-group chain key, rotated on every membership removal. O(members) on distribution — hence the 1,000-member cap.', '6.7'],
  ['SFrame', 'Frame-level encryption for real-time media, letting the SFU forward frames it cannot decrypt.', '6.9'],
  ['SFU', 'Selective Forwarding Unit. Routes media streams for group calls without mixing them — mixing would require server-side plaintext.', '6.9'],
  ['Standfirst', 'The italic line under a part title stating what that part governs.', null],
  ['Token tier', 'Primitive, semantic or component. Screens reference tier 3 only; reaching past it is a bug.', '7.1'],
  ['Void', 'The neutral scale, cool-tinted so it sits with Orbit rather than fighting it. The interface is 90 % neutral.', '2.5'],
  ['X3DH', 'Extended Triple Diffie-Hellman — the asynchronous key agreement that lets a first message be encrypted to a recipient who is offline.', '6.7'],
];

function appendixC(APPARATUS) {
  return [
    P({ children: [new PageBreak()] }),
    spacer(600),
    head('b_glossary', 'Appendix C — Glossary'),
    lead('Terms as they are used in this document. Where a term has a governing definition, the section reference is authoritative and this entry is a summary of it.'),
    spacer(200),
    APPARATUS.dataTable(['Term', 'As used here', 'Governing section'],
      GLOSSARY.map((g) => [[T(g[0], { bold: true })], [T(g[1])],
        [g[2] ? link('Part ' + g[2].split('.')[0] + ' ' + resolve(g[2]).label,
          resolve(g[2]).anchor, { size: 16 }) : T('—', { color: C.void400 })]]),
      [16, 68, 16]),
  ];
}

// -------------------------------------------------------------------- Index
const INDEX = {
  'Accessibility': ['2.15', '3.11', '8.9'],
  'Address-book upload, declined': ['3.10', '11.6'],
  'Advertising, prohibition on': ['0.6', '11.1'],
  'AI assistant': ['4.2', '5.8'],
  'AI privacy boundaries': ['4.1', '4.9'],
  'AI transparency': ['4.10'],
  'Amendment procedure': ['0.10'],
  'Analytics': ['11.5'],
  'Animation philosophy': ['1.9', '3.3', '7.7'],
  'Appeals and moderation policy': ['11.7'],
  'Architecture principles': ['6.1'],
  'Assistant conversation, non-E2EE': ['4.1', '6.7'],
  'Audio priority rule': ['5.4', '6.9'],
  'Backend services': ['6.3'],
  'Battery budgets': ['8.6'],
  'Binary size': ['8.6'],
  'Biometric app lock': ['6.6'],
  'Blocking a contact': ['5.11'],
  'Brand personality': ['1.2'],
  'Brand voice': ['1.3'],
  'Bubble geometry': ['2.10', '5.1'],
  'Business platform': ['11.1'],
  'Buttons': ['2.14', '7.4'],
  'Calls, voice': ['5.3'],
  'Calls, video': ['5.4'],
  'Callouts and panels': ['7.2'],
  'Captions and transcription': ['4.6', '5.2'],
  'CI/CD': ['6.14'],
  'Channels': ['5.6', '10.4'],
  'Chaos testing': ['6.12'],
  'Child safety': ['11.7'],
  'Cold launch': ['8.2'],
  'Colour doctrine': ['2.1'],
  'Colour-blind safety, measured': ['2.15'],
  'Compliance regimes': ['11.9'],
  'Component inventory': ['7.2'],
  'Composer': ['2.14', '3.2'],
  'Conflict resolution, sync': ['3.7', '6.8'],
  'Contact discovery': ['3.10'],
  'Corner radius system': ['2.10'],
  'Creator economy': ['11.3'],
  'Cross-language communicator': ['13.3'],
  'Dark mode': ['2.6'],
  'Data retention': ['6.13'],
  'Decision rules': ['0.9'],
  'Deepfake detection, deferred': ['4.7'],
  'Design tokens': ['7.1'],
  'Device linking': ['5.13'],
  'Disappearing messages': ['5.1'],
  'Dogfooding': ['9.1'],
  'Elevation': ['2.8'],
  'Empty states': ['3.6'],
  'Encryption, end-to-end': ['6.7'],
  'Error handling': ['3.5'],
  'Executive gate conditions': ['9.1'],
  'Feed, permanent rejection of': ['10.5', '10.11'],
  'File sharing': ['5.9'],
  'Frame rate': ['8.3'],
  'Gestures': ['3.2', '7.8'],
  'Glass and translucency': ['2.9'],
  'Gradients': ['2.7'],
  'Groups': ['5.5'],
  'Growth strategy': ['11.6'],
  'Hypotheses, user': ['13.1'],
  'Icons': ['1.8', '7.3'],
  'Illustration style': ['1.7'],
  'Index of sections': ['0.1'],
  'Information architecture': ['3.1', '13.5'],
  'Internationalisation': ['11.8'],
  'Journeys, user': ['13.4'],
  'Keyboard operation': ['2.15'],
  'Language packs': ['4.4'],
  'Latency targets': ['8.4'],
  'Lists': ['2.14', '7.5'],
  'Loading behaviour': ['3.4'],
  'Local-first architecture': ['6.8'],
  'Logo philosophy': ['1.5'],
  'Media optimisation': ['8.8'],
  'Memory ceilings': ['8.5'],
  'Message requests': ['4.7'],
  'Messaging, secure': ['5.1'],
  'Mini-apps': ['10.9'],
  'Moderation architecture': ['11.7'],
  'Monitoring and observability': ['6.11'],
  'Motion tokens': ['7.7'],
  'Multi-device support': ['5.13'],
  'Naming rules': ['1.4'],
  'Navigation philosophy': ['3.1'],
  'Non-negotiable principles': ['0.6'],
  'Notifications': ['3.9', '5.12'],
  'Offline behaviour': ['3.7', '6.8'],
  'One-handed use': ['3.12'],
  'Onboarding': ['3.10', '13.4'],
  'Palette, Aurora': ['2.3'],
  'Palette, Orbit': ['2.2'],
  'Palette, Void': ['2.5'],
  'Payments': ['10.9'],
  'Performance budget process': ['8.11'],
  'Photography direction': ['1.6'],
  'Post-quantum cryptography': ['6.7'],
  'Privacy Centre': ['4.10'],
  'Profile system': ['5.11'],
  'Pull quotes': ['1.9'],
  'Push notifications': ['6.6'],
  'Reduced motion': ['1.9'],
  'Reply suggestions': ['4.3'],
  'Research programme': ['13.2'],
  'Risk register': ['11.10'],
  'Roadmap phases': ['9.1'],
  'Safety numbers': ['5.11', '6.7'],
  'Scalability triggers': ['6.10'],
  'Scam and fraud protection': ['4.7'],
  'Scope governance process': ['10.12'],
  'Search': ['3.8', '5.10'],
  'Security operations': ['6.15'],
  'Semantic colours': ['2.4'],
  'Sheets, dialogs and menus': ['7.6'],
  'Spacing system': ['2.11'],
  'Stories': ['5.7'],
  'Subscription plans': ['11.2'],
  'Summaries': ['4.5'],
  'Testing strategy': ['6.12'],
  'Thumb reach': ['3.12'],
  'Translation': ['4.4'],
  'Typography': ['2.13'],
  'Unit economics': ['11.4'],
  'Values': ['0.4'],
  'Version control of decisions': ['0.10'],
  'Vision, long-term': ['0.3'],
  'Voice notes': ['5.2'],
  'Widow and orphan control': ['2.13'],
};

function indexSection(folio) {
  const kids = [
    P({ children: [new PageBreak()] }),
    spacer(600),
    head('b_index', 'Index'),
    lead('Alphabetical, by subject. Each entry gives the governing section and its page. Section numbers are stable across editions; page numbers are for this one.'),
    spacer(200),
  ];
  const keys = Object.keys(INDEX).sort((a, b) => a.localeCompare(b));
  let letter = '';
  for (const k of keys) {
    const first = k[0].toUpperCase();
    if (first !== letter) {
      letter = first;
      kids.push(P({ style: 'IndexLetter', children: [T(letter)] }));
    }
    const refs = INDEX[k];
    const children = [T(k + '   ', { size: 17 })];
    refs.forEach((r, i) => {
      if (i) children.push(T('  ·  ', { color: C.void300, size: 16 }));
      const t = resolve(r);
      const pg = folio(t.anchor);
      children.push(new InternalHyperlink({ anchor: t.anchor,
        children: [T(t.label, { color: C.orbit600, size: 16 }),
          T(` ${pg}`, { color: C.void500, size: 16 })] }));
    });
    kids.push(P({ style: 'IndexEntry', children }));
  }
  kids.push(spacer(240));
  kids.push(P({ style: 'Body', children: [
    T('Section number first, then the page it begins on. ', { color: C.void600 }),
    T('Every reference in this index is a live link in both editions.', { color: C.void600 })] }));
  return kids;
}

// -------------------------------------------------------------------- close
function colophonEnd() {
  return [
    P({ children: [new PageBreak()] }),
    spacer(2600),
    P({ style: 'Kicker', children: [T('END OF DOCUMENT')] }),
    P({ style: 'TitlePageSub', children: [T('SpaceTalk Editorial Bible, Version 1.0.')] }),
    P({ style: 'Body', children: [T('Fourteen parts, four appendices, twenty figures, twelve decision records.', { color: C.void600 })] }),
    spacer(300),
    P({ style: 'PullQuote', children: [T('“Room to talk.”')] }),
  ];
}

module.exports = function backMatter(ir, figures, folio) {
  const APPARATUS = require('./apparatus');
  return [
    ...appendixA(APPARATUS),
    ...appendixB(APPARATUS),
    ...appendixC(APPARATUS),
    ...indexSection(folio),
    ...colophonEnd(),
  ];
};
