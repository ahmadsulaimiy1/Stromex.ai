package ai.sautiy.core.library

import java.time.ZoneId
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

class RecordingStoreTest {

    @get:Rule
    val folder: TemporaryFolder = TemporaryFolder()

    private var now = 1_700_000_000_000L
    private val utc = ZoneId.of("UTC")

    private fun store() = RecordingStore(folder.root.resolve("library.json")) { now }

    private fun entry(
        id: String,
        title: String = id,
        createdAt: Long = now,
        seconds: Int = 60,
    ) = RecordingEntry(
        id = id,
        title = title,
        takeId = "take-$id",
        createdAtEpochMs = createdAt,
        durationFrames = 48_000L * seconds,
        sampleRate = 48_000,
    )

    // --- Save, rename, delete -----------------------------------------------------------------

    @Test
    fun `a saved recording survives a restart`() {
        val file = folder.root.resolve("library.json")
        RecordingStore(file) { now }.save(entry("a", "Lecture one"))

        // A fresh store, as if the process had been killed and relaunched.
        val reopened = RecordingStore(file) { now }
        assertEquals(1, reopened.live().size)
        assertEquals("Lecture one", reopened.live().single().title)
    }

    @Test
    fun `saving the same id updates rather than duplicating`() {
        val store = store()
        store.save(entry("a", "First"))
        store.save(entry("a", "Second"))

        assertEquals(1, store.all().size)
        assertEquals("Second", store.find("a")?.title)
    }

    @Test
    fun `renaming keeps titles unique so two recordings cannot be confused`() {
        val store = store()
        store.save(entry("a", "Al-Fatihah"))
        store.save(entry("b", "Something else"))

        val renamed = store.rename("b", "Al-Fatihah")
        assertEquals("Al-Fatihah 2", renamed?.title)

        store.save(entry("c", "x"))
        assertEquals("Al-Fatihah 3", store.rename("c", "Al-Fatihah")?.title)
    }

    @Test
    fun `renaming to blank keeps the existing title rather than erasing it`() {
        val store = store()
        store.save(entry("a", "Lecture one"))
        assertEquals("Lecture one", store.rename("a", "   ")?.title)
    }

    @Test
    fun `delete moves to trash and states when it will go`() {
        val store = store()
        store.save(entry("a"))

        val trashed = store.trash("a")
        assertNotNull(trashed)
        assertTrue(trashed!!.isTrashed)
        assertTrue("Trashed recordings leave the main list", store.live().isEmpty())
        assertEquals(1, store.trashed().size)

        val purgeAt = trashed.purgeAtEpochMs()
        assertNotNull(purgeAt)
        assertEquals(
            "The row must be able to state the exact date",
            now + Library.TRASH_RETENTION_DAYS * 24L * 60 * 60 * 1000,
            purgeAt,
        )
    }

    @Test
    fun `a trashed recording can be restored intact`() {
        val store = store()
        store.save(entry("a", "Lecture one"))
        store.trash("a")

        val restored = store.restore("a")
        assertFalse(restored!!.isTrashed)
        assertEquals("Lecture one", store.live().single().title)
    }

    @Test
    fun `purging reports the orphaned take so the audio can be removed by its owner`() {
        // The store never deletes audio itself: one component owning both the index and the
        // media is how an index bug becomes lost recordings.
        val store = store()
        store.save(entry("a"))
        store.trash("a")

        assertEquals("take-a", store.purge("a"))
        assertTrue(store.all().isEmpty())
    }

    @Test
    fun `expired trash is purged and nothing else is`() {
        val store = store()
        store.save(entry("old"))
        store.save(entry("recent"))
        store.save(entry("live"))

        store.trash("old")
        now += 20L * 24 * 60 * 60 * 1000
        store.trash("recent")
        now += 11L * 24 * 60 * 60 * 1000 // "old" is now 31 days in the trash, "recent" is 11

        val orphans = store.purgeExpired()
        assertEquals(listOf("take-old"), orphans)
        assertNull(store.find("old"))
        assertNotNull("A recording inside its window must survive", store.find("recent"))
        assertNotNull("A live recording must never be touched", store.find("live"))
    }

    @Test
    fun `favourite and archive are one call and stick`() {
        val store = store()
        store.save(entry("a"))

        assertTrue(store.setFavourite("a", true)!!.favourite)
        assertTrue(store.setArchived("a", true)!!.archived)
        assertTrue("Archived recordings leave the main list", store.live().isEmpty())
        assertEquals(1, store.archived().size)
    }

    @Test
    fun `the live list is newest first`() {
        val store = store()
        store.save(entry("old", createdAt = now - 10_000))
        store.save(entry("new", createdAt = now))
        assertEquals(listOf("new", "old"), store.live().map { it.id })
    }

    // --- Durability ---------------------------------------------------------------------------

    @Test
    fun `a corrupt index does not take the recordings with it`() {
        val file = folder.root.resolve("library.json")
        RecordingStore(file) { now }.save(entry("a"))
        file.writeText("{ this is not json")

        // The takes are still on disk. Returning empty lets recovery rebuild rather than crash.
        assertTrue(RecordingStore(file) { now }.all().isEmpty())
    }

    @Test
    fun `no temporary file is left behind after a write`() {
        val store = store()
        store.save(entry("a"))
        val leftovers = folder.root.listFiles()?.filter { it.name.endsWith(".tmp") }.orEmpty()
        assertTrue("Atomic write left $leftovers behind", leftovers.isEmpty())
    }

    @Test
    fun `claimed take ids drive crash recovery`() {
        val store = store()
        store.save(entry("a"))
        store.save(entry("b"))
        assertEquals(setOf("take-a", "take-b"), store.claimedTakeIds())
    }

    // --- Naming --------------------------------------------------------------------------------

    @Test
    fun `a recording that is never named is still findable`() {
        // Chapter 13.2: the name is asked for after the take exists and never blocks, so the
        // default has to be something a person can reason about a month later.
        val title = Library.defaultTitle(1_700_000_000_000L, utc)
        assertTrue("Got '$title'", Regex("""\d{4}-\d{2}-\d{2} \d{2}\.\d{2}""").matches(title))
    }

    @Test
    fun `titles become safe file names without mangling what the user typed`() {
        assertEquals("Al-Fatihah.mp3", Library.toFileName("Al-Fatihah", "mp3"))
        assertEquals("Lecture 1-2.wav", Library.toFileName("Lecture 1/2", "wav"))
        assertEquals("recording.flac", Library.toFileName("   ", "flac"))
        assertTrue(Library.toFileName("a".repeat(500), "wav").length < 140)
    }

    @Test
    fun `a file name never contains a path separator or a wildcard`() {
        val hostile = """../../etc/passwd?*<>|:"""
        val name = Library.toFileName(hostile, "wav")
        for (bad in listOf("/", "\\", "?", "*", "<", ">", "|", ":")) {
            assertFalse("'$name' still contains $bad", name.contains(bad))
        }
    }
}

class LibrarySearchTest {

    private val utc = ZoneId.of("UTC")

    // 2023-11-14 was a Tuesday, 22:13 UTC.
    private val now = 1_699_999_999_000L

    private fun entry(
        id: String,
        title: String = id,
        createdAt: Long = now,
        tags: List<String> = emptyList(),
        collections: List<String> = emptyList(),
        markers: List<String> = emptyList(),
        transcript: String? = null,
        trashed: Boolean = false,
    ) = RecordingEntry(
        id = id,
        title = title,
        takeId = "take-$id",
        createdAtEpochMs = createdAt,
        durationFrames = 48_000,
        sampleRate = 48_000,
        tags = tags,
        collections = collections,
        markerLabels = markers,
        transcript = transcript,
        trashedAtEpochMs = if (trashed) createdAt else null,
    )

    @Test
    fun `a title match outranks a transcript match`() {
        // A list that interleaves them makes the user read every row.
        val entries = listOf(
            entry("t", transcript = "we discussed the balance sheet at length"),
            entry("b", title = "Balance sheet review"),
        )
        val results = Library.search(entries, "balance sheet", now, utc)

        assertEquals(2, results.size)
        assertEquals("b", results.first().entry.id)
        assertEquals(MatchField.TITLE, results.first().field)
        assertEquals(MatchField.TRANSCRIPT, results.last().field)
    }

    @Test
    fun `the whole ranking order holds`() {
        val entries = listOf(
            entry("transcript", transcript = "ramadan lecture"),
            entry("marker", markers = listOf("ramadan")),
            entry("tag", tags = listOf("ramadan")),
            entry("title", title = "Ramadan night"),
        )
        assertEquals(
            listOf("title", "tag", "marker", "transcript"),
            Library.search(entries, "ramadan", now, utc).map { it.entry.id },
        )
    }

    @Test
    fun `a transcript hit shows why it matched`() {
        val entries = listOf(
            entry("a", transcript = "and then we came to the question of the balance sheet, which nobody enjoyed"),
        )
        val context = Library.search(entries, "balance sheet", now, utc).single().context
        assertTrue("Got '$context'", context.contains("balance sheet"))
        assertTrue("Context must show surrounding words", context.length > "balance sheet".length)
    }

    @Test
    fun `search is case insensitive and matches inside words`() {
        val entries = listOf(entry("a", title = "Al-Fatihah"))
        assertEquals(1, Library.search(entries, "fatihah", now, utc).size)
        assertEquals(1, Library.search(entries, "FATIHAH", now, utc).size)
    }

    @Test
    fun `trashed recordings never appear in search`() {
        val entries = listOf(entry("a", title = "Lecture", trashed = true))
        assertTrue(Library.search(entries, "lecture", now, utc).isEmpty())
    }

    @Test
    fun `an empty query returns nothing rather than everything`() {
        val entries = listOf(entry("a"), entry("b"))
        assertTrue(Library.search(entries, "   ", now, utc).isEmpty())
    }

    @Test
    fun `today and yesterday resolve against the device clock`() {
        val yesterday = now - 24L * 60 * 60 * 1000
        val entries = listOf(entry("today"), entry("yesterday", createdAt = yesterday))

        assertEquals(listOf("today"), Library.search(entries, "today", now, utc).map { it.entry.id })
        assertEquals(listOf("yesterday"), Library.search(entries, "yesterday", now, utc).map { it.entry.id })
    }

    @Test
    fun `this morning means today`() {
        assertEquals(
            listOf("a"),
            Library.search(listOf(entry("a")), "this morning", now, utc).map { it.entry.id },
        )
    }

    @Test
    fun `last week excludes this week`() {
        val eightDaysAgo = now - 8L * 24 * 60 * 60 * 1000
        val entries = listOf(entry("thisWeek"), entry("lastWeek", createdAt = eightDaysAgo))

        val results = Library.search(entries, "last week", now, utc).map { it.entry.id }
        assertEquals(listOf("lastWeek"), results)
    }

    @Test
    fun `a weekday name resolves to the most recent one that has happened`() {
        // now is a Tuesday; "last monday" is the day before.
        val monday = now - 24L * 60 * 60 * 1000
        val entries = listOf(entry("mon", createdAt = monday), entry("today"))

        assertEquals(
            listOf("mon"),
            Library.search(entries, "last monday", now, utc).map { it.entry.id },
        )
    }

    @Test
    fun `an unrecognised phrase matches nothing rather than guessing`() {
        // A search that returns confident wrong answers is worse than one that returns none.
        assertNull(DatePhrases.resolve("sometime around the eid before last", now, utc))
    }

    @Test
    fun `date phrases do not fire on ordinary words`() {
        assertNull(DatePhrases.resolve("balance sheet", now, utc))
        assertNull(DatePhrases.resolve("lecture", now, utc))
    }
}
