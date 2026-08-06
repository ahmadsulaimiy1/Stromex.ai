package ai.sautiy.data

import ai.sautiy.core.codec.WavCodec
import ai.sautiy.core.record.CrashRecovery
import android.content.Context
import java.io.File

/**
 * Where SAUTIY keeps things, and why.
 *
 * All three directories are inside app-private internal storage. That is a deliberate
 * consequence of chapter 1.3.7: a recording is not visible to other apps, to a gallery scanner,
 * or to a backup agent unless the user exports it. Sharing happens through the export path,
 * per file, with a granted URI — never by leaving audio somewhere public and hoping.
 */
class SautiyFiles(private val context: Context) {

    /** Raw capture. Write-once WAV, never modified after the take ends (chapter 9.1). */
    val takes: File get() = context.filesDir.resolve("takes").apply { mkdirs() }

    /** Project descriptions: timelines, chains, markers. Small, serialisable, backed up. */
    val projects: File get() = context.filesDir.resolve("projects").apply { mkdirs() }

    /** Staging for files on their way to the share sheet or a document picker. */
    val exports: File get() = context.filesDir.resolve("exports").apply { mkdirs() }

    fun takeFile(id: String): File = takes.resolve("$id.wav")

    fun projectFile(id: String): File = projects.resolve("$id.json")

    /** The library index. One file, written atomically (see `RecordingStore`). */
    val libraryIndex: File get() = projects.resolve("library.json")

    /**
     * The user's own saved sounds.
     *
     * Separate from the library index because they have different lifetimes: recordings come and
     * go, and a Voice DNA is meant to outlive every one of them. Losing this file loses judgement
     * somebody made about their own voice, which is why it is written the same atomic way.
     */
    val voiceDnaFile: File get() = projects.resolve("voice-dna.json")

    /** What listeners have said about each preset. Opinions, so a loss costs nothing irreplaceable. */
    val listeningFile: File get() = projects.resolve("listening.json")

    /** Deletes the audio for a purged entry. Called only by the owner of the take, never by the store. */
    fun deleteTake(takeId: String): Boolean = takeFile(takeId).delete()

    /**
     * Free bytes on the volume holding the takes.
     *
     * Measured on the actual volume rather than assumed, because on a device with adopted
     * storage the answer differs from the one `Environment` would give.
     *
     * Null when the volume cannot be interrogated. Deliberately not `0`, which this returned before:
     * zero free bytes is a *measurement*, and it reads as "the disk is full" — enough to make
     * `storageIsCritical` true and interrupt a recording over a number nobody obtained.
     */
    fun freeBytes(): Long? = runCatching { takes.usableSpace }.getOrNull()

    /**
     * Takes on disk that no project claims — chapter 1.3.5's crash recovery.
     *
     * Because capture writes WAV incrementally, an unclaimed file is already complete and
     * playable. Recovery is a matter of noticing it, not of repairing it.
     */
    fun unclaimedTakes(claimedIds: Set<String>): List<CrashRecovery.Candidate> =
        takes.listFiles { file -> file.isFile && file.extension == "wav" }
            .orEmpty()
            .filter { it.nameWithoutExtension !in claimedIds }
            .mapNotNull { file ->
                runCatching {
                    val info = WavCodec.probe(file)
                    CrashRecovery.Candidate(
                        fileName = file.name,
                        frameCount = info.frameCount,
                        sampleRate = info.format.sampleRate,
                        lastModifiedEpochMs = file.lastModified(),
                    )
                }.getOrNull()
            }
            .let(CrashRecovery::worthOffering)

    /** Removes exports older than a day. They are copies; the originals are untouched. */
    fun pruneExportStaging(nowEpochMs: Long) {
        val cutoff = nowEpochMs - 24 * 60 * 60 * 1000
        exports.listFiles()?.forEach { file ->
            if (file.isFile && file.lastModified() < cutoff) file.delete()
        }
    }
}
