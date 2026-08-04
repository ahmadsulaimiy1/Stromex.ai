package ai.sautiy.data

import ai.sautiy.core.audio.AudioBuffer
import ai.sautiy.core.codec.WavStreamReader
import ai.sautiy.core.edit.SourceProvider
import java.io.File

/**
 * Reads source audio from the take files on disk — Editorial Bible chapter 16.2 and 16.3.
 *
 * This exists instead of holding captured audio in memory, and the difference is not an
 * optimisation. A ninety-minute lecture at 48 kHz is about 500 MB as 32-bit float; keeping it
 * in the heap would breach the constitutional in-memory ceiling four times over, and would do
 * it on exactly the recording that matters most to the person making it.
 *
 * **Each take keeps an open reader.** The first version of this class called
 * `WavCodec.readRange` per block, which re-opens the file *and re-parses every RIFF chunk* on
 * every call — at a 40 ms playback window that is twenty-five opens and twenty-five header
 * walks per second of audio, on the thread feeding the speaker. It played, so it passed a
 * casual test; it stuttered, and it was the reason playback felt slow. [WavStreamReader] parses
 * the header once and keeps the descriptor open, so a block read is a seek and a copy.
 *
 * A small LRU of recently read blocks sits on top, absorbing the overlap between consecutive
 * playback windows and the repeated reads of a scrub.
 */
class FileSourceProvider(
    private val files: SautiyFiles,
    private val cacheBlocks: Int = DEFAULT_CACHE_BLOCKS,
) : SourceProvider, AutoCloseable {

    private data class Key(val sourceId: String, val startFrame: Long, val frameCount: Int)

    private val cache = object : LinkedHashMap<Key, AudioBuffer>(16, 0.75f, true) {
        override fun removeEldestEntry(eldest: MutableMap.MutableEntry<Key, AudioBuffer>?): Boolean =
            size > cacheBlocks
    }

    /** One open reader per take. Opened on first use, closed together in [close]. */
    private val readers = HashMap<String, WavStreamReader?>()

    private fun readerFor(sourceId: String): WavStreamReader? = synchronized(readers) {
        if (readers.containsKey(sourceId)) return@synchronized readers[sourceId]
        val file: File = files.takeFile(sourceId)
        val reader = if (!file.isFile) null else runCatching { WavStreamReader(file) }.getOrNull()
        readers[sourceId] = reader
        reader
    }

    override fun read(sourceId: String, startFrame: Long, frameCount: Int): AudioBuffer {
        if (frameCount <= 0) return AudioBuffer.silence(1, 0, 48_000)

        val key = Key(sourceId, startFrame, frameCount)
        synchronized(cache) { cache[key] }?.let { return it }

        val reader = readerFor(sourceId) ?: return AudioBuffer.silence(1, frameCount, 48_000)

        // The reader pads reads that run past the end, so the renderer's arithmetic never has
        // to special-case the tail of a take. A read that fails outright still has to return
        // audio: a render is not the place to throw.
        val block = synchronized(reader) { runCatching { reader.read(startFrame, frameCount) } }
            .getOrElse { AudioBuffer.silence(1, frameCount, 48_000) }

        synchronized(cache) { cache[key] = block }
        return block
    }

    /** Drops a take's reader and its cached blocks, so a deleted or rewritten file is not held. */
    fun invalidate(sourceId: String) {
        synchronized(readers) { readers.remove(sourceId)?.close() }
        synchronized(cache) { cache.keys.removeAll { it.sourceId == sourceId } }
    }

    fun clear() {
        synchronized(cache) { cache.clear() }
    }

    override fun close() {
        synchronized(readers) {
            readers.values.forEach { it?.close() }
            readers.clear()
        }
        clear()
    }

    private companion object {
        /**
         * Sixteen blocks. At the playback window size that is under a second of audio held —
         * enough to absorb window overlap and scrubbing, far too little to matter against the
         * chapter 16.3 ceiling.
         */
        const val DEFAULT_CACHE_BLOCKS = 16
    }
}
