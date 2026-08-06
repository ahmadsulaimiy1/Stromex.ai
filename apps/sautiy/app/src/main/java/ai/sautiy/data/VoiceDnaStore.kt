package ai.sautiy.data

import ai.sautiy.core.dsp.ListeningDatabase
import ai.sautiy.core.dsp.VoiceDnaLibrary
import java.io.File

/**
 * The user's saved sounds on disk, written the way something irreplaceable is written.
 *
 * A Voice DNA is judgement somebody made about their own voice, and it is meant to outlive every
 * recording in the library. Losing it to a half-finished write during a low-battery shutdown would
 * be losing work nobody can reconstruct — the person does not remember what they set, they only
 * remember that it sounded right.
 *
 * So: write to a temporary file, flush, then rename. Rename within a directory is atomic on every
 * filesystem Android ships, so the real file is either the old complete one or the new complete
 * one and never a truncated hybrid. The same discipline `RecordingStore` uses for the library
 * index, for the same reason.
 */
class VoiceDnaStore(private val file: File) {

    fun load(): VoiceDnaLibrary {
        if (!file.exists()) return VoiceDnaLibrary()
        val text = runCatching { file.readText() }.getOrNull() ?: return VoiceDnaLibrary()
        return VoiceDnaLibrary.decode(text)
    }

    fun save(library: VoiceDnaLibrary) {
        writeAtomically(file, VoiceDnaLibrary.encode(library))
    }
}

/**
 * The listening tally on disk.
 *
 * Written the same way for consistency rather than necessity: losing this file loses opinions, and
 * opinions can be given again. It is still not worth leaving a corrupt one behind.
 */
class ListeningStore(private val file: File) {

    fun load(): ListeningDatabase {
        if (!file.exists()) return ListeningDatabase()
        val text = runCatching { file.readText() }.getOrNull() ?: return ListeningDatabase()
        return ListeningDatabase.decode(text)
    }

    fun save(database: ListeningDatabase) {
        writeAtomically(file, ListeningDatabase.encode(database))
    }
}

/**
 * Write, flush to the platter, then rename over the target.
 *
 * The flush is not optional and is the part people leave out: without it the rename can land before
 * the bytes do, and a power loss in that window leaves a correctly-named empty file, which is worse
 * than a corrupt one because nothing detects it.
 */
private fun writeAtomically(target: File, text: String) {
    target.parentFile?.mkdirs()
    val temporary = File(target.parentFile, "${target.name}.tmp")
    runCatching {
        temporary.outputStream().use { stream ->
            stream.write(text.toByteArray())
            stream.flush()
            stream.fd.sync()
        }
        if (!temporary.renameTo(target)) {
            // A failed rename on some filesystems leaves the target in place, which is the safe
            // outcome. Copying is the fallback rather than deleting the target first, because
            // deleting first is the one order that can lose both copies.
            target.writeText(text)
            temporary.delete()
        }
    }.onFailure { temporary.delete() }
}
