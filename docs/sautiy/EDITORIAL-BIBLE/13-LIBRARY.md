# Chapter 13 — Library & Asset Management

> The library is a panel, not a page. Nothing about managing recordings justifies leaving the
> studio.

---

## 13.1 The Row

Every recording presents, in one 48 dp row:

- A waveform thumbnail — the fastest way to recognise a recording is to see its shape
- Title
- Duration
- Date
- Favourite state, if set

Tapping the row opens it in the workspace. There is no detail screen, because there is nothing
a detail screen would say that the workspace does not already show better.

## 13.2 Naming

**A recording is never named before it exists.** The name is asked for after the take ends, it
never blocks, and it is pre-filled with something useful and honest — the date and time, or the
project and take number. A user who ignores the prompt entirely still has a findable library.

## 13.3 Organisation

| Concept | Is |
|---|---|
| **Collection** | A user-made group. A recording may be in several. |
| **Tag** | A short label. Proposed by intelligence, applied only by the user (chapter 11.5). |
| **Favourite** | A single flag, one tap, no confirmation. |
| **Archive** | Out of the main list, still fully present and searchable. |
| **Trash** | Deleted, recoverable, with the date it will go stated on the row. |

There is no folder hierarchy. Folders make people file things, filing is work, and search is
better at retrieval than memory of where something was put.

## 13.4 Search

One field, incremental, off the main thread, never blocking typing. Ranked in this order
(chapter 4.6):

1. Title
2. Tags and collection names
3. Marker labels
4. Transcript content, where one exists
5. Spoken-date phrases — "last Tuesday", "Ramadan", "this morning"

Results group by what matched, with the matching text shown in context, so the user can see
*why* a result is a result.

## 13.5 Deletion

- Delete moves to trash. It is not a question, because it is not final.
- The trash row states the exact date the item will be removed.
- Trash retention is **30 days**.
- Emptying the trash — the one genuinely irreversible action in the product — is the only place
  a confirmation appears, and it states how many recordings and how much audio will go.

This is the one place chapter 3.2.7's third permitted interruption applies.

## 13.6 Storage Honesty

The library states, always in terms the user can act on:

- Total recorded time held.
- Space used, and space free, in **minutes of recording remaining**, not only in bytes.
- The largest recordings first when space is short, so the user can act on the ones that matter.

## 13.7 Import

Audio shared into SAUTIY from elsewhere opens straight into the workspace as a new project.
Imported material is copied into SAUTIY's own storage rather than referenced, so a recording
cannot disappear because another app cleaned up. WAV, FLAC and the platform's supported
compressed formats are read.

---

### Implementation

`sautiy-core/.../codec/WavCodec.kt` (`probe` is fast enough to run on every row),
`app/.../data/SautiyFiles.kt` (three private directories: takes, projects, exports),
`app/.../ui/panels/PanelHost.kt` (`LibraryPanel`). Search ranking and trash retention live in
the core's library model, where they are testable.
